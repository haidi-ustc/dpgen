import os
import warnings
import json
import dpdata
import dpgen.auto_test.lib.lammps as lammps
from dpgen import dlog
from monty.serialization import loadfn,dumpfn
from dpgen.auto_test.Task import Task
from dpgen.auto_test.lib.lammps import inter_deepmd, inter_meam, inter_eam_fs, inter_eam_alloy

supported_inter = ["deepmd", 'meam', 'eam_fs', 'eam_alloy']


class Lammps(Task):
    def __init__(self,
                 inter_parameter,
                 path_to_poscar):
        self.inter = inter_parameter
        self.inter_type = inter_parameter['type']
        assert self.inter_type in supported_inter
        self.set_inter_type_func()
        self.model = os.path.abspath(inter_parameter['model'])
        self.type_map = inter_parameter['type_map']
        self.path_to_poscar = path_to_poscar

    def set_inter_type_func(self):

        if self.inter_type == "deepmd":
            self.inter_func = inter_deepmd

        elif self.inter_type == 'meam':
            self.inter_func = inter_meam

        elif self.inter_type == 'eam_fs':
            self.inter_func = inter_eam_fs

        else:
            self.inter_func = inter_eam_alloy

    def set_model_param(self):

        if self.inter_type == "deepmd":
            model_name = os.path.basename(self.model)
            deepmd_version = self.inter.get("deepmd_version", "0.12")
            self.model_param = {'model_name': [model_name],
                                'param_type': self.type_map,
                                'deepmd_version': deepmd_version}
        elif self.inter_type == 'meam':
            model_name = list(map(os.path.basename, self.model))
            self.model_param = {'model_name': model_name,
                                'param_type': self.type_map}
        else:
            model_name = os.path.basename(self.model)
            self.model_param = {'model_name': model_name,
                                'param_type': self.type_map}

    def make_potential_files(self,
                             output_dir):
        cwd = os.getcwd()
        if self.inter_type == 'meam':
            model_lib = os.path.basename(self.model[0])
            model_file = os.path.basename(self.model[1])
            os.chdir(output_dir)
            if os.path.islink(model_lib):
                link_lib = os.readlink(model_lib)
                if not os.path.abspath(link_lib) == self.model[0]:
                    os.remove(model_lib)
                    os.symlink(os.path.relpath(self.model[0]), model_lib)
            else:
                os.symlink(os.path.relpath(self.model[0]), model_lib)

            if os.path.islink(model_file):
                link_file = os.readlink(model_file)
                if not os.path.abspath(link_file) == self.model[1]:
                    os.remove(model_file)
                    os.symlink(os.path.relpath(self.model[1]), model_file)
            else:
                os.symlink(os.path.relpath(self.model[1]), model_file)

            os.chdir(cwd)
        else:
            model_file = os.path.basename(self.model)
            os.chdir(output_dir)
            if os.path.islink(model_file):
                link_file = os.readlink(model_file)
                if not os.path.abspath(link_file) == self.model:
                    os.remove(model_file)
                    os.symlink(os.path.relpath(self.model), model_file)
            else:
                os.symlink(os.path.relpath(self.model), model_file)
            os.chdir(cwd)

        dumpfn(self.inter, os.path.join(output_dir, 'inter.json'), indent=4)

    def make_input_file(self,
                        output_dir,
                        task_type,
                        task_param):
        lammps.cvt_lammps_conf(os.path.join(output_dir, 'POSCAR'), os.path.join(output_dir, 'conf.lmp'))

        dumpfn(task_param, os.path.join(output_dir, 'task.json'), indent=4)

        etol = 1e-12
        ftol = 1e-6
        maxiter = 5000
        maxeval = 500000
        change_box = True
        B0 = 70
        bp = 0
        scale2equi = 1
        ntypes = len(self.type_map)
        reprod_opt = False
        static = False

        if 'etol' in task_param:
            etol = task_param['etol']
        if 'ftol' in task_param:
            ftol = task_param['ftol']
        if 'maxiter' in task_param:
            maxiter = task_param['maxiter']
        if 'maxeval' in task_param:
            maxeval = task_param['maxeval']
        if 'change_box' in task_param:
            change_box = task_param['change_box']
        if 'scale2equi' in task_param:
            scale2equi = task_param['scale2equi']
        if 'reprod_opt' in task_param:
            reprod_opt = task_param['reprod_opt']
        if 'static-opt' in task_param:
            static = task_param['static-opt']

        self.set_model_param()

        fc = ''
        if task_type == 'relaxation' \
                or (task_type == 'eos' and not change_box) \
                or (task_type == 'surface' and not static):
            fc = lammps.make_lammps_equi('conf.lmp', ntypes, self.inter_func, self.model_param,
                                         etol, ftol, maxiter, maxeval, change_box)

        if task_type == 'static' \
                or (task_type == 'surface' and static):
            fc = lammps.make_lammps_eval('conf.lmp', ntypes, self.inter_func, self.model_param)

        if task_type == 'elastic':
            fc = lammps.make_lammps_elastic('conf.lmp', ntypes, self.inter_func, self.model_param,
                                            etol, ftol, maxiter, maxeval)

        if task_type == 'vacancy' \
                or (task_type == 'interstitial'):
            fc = lammps.make_lammps_press_relax('conf.lmp', ntypes, scale2equi, self.inter_func,
                                                self.model_param, B0, bp, etol, ftol, maxiter, maxeval)

        if task_type == 'eos' and change_box:
            fc = lammps.make_lammps_press_relax('conf.lmp', ntypes, scale2equi[int(output_dir[-6])], self.inter_func,
                                                self.model_param, B0, bp, etol, ftol, maxiter, maxeval)
        if reprod_opt:
            fc = lammps.make_lammps_eval('conf.lmp', ntypes, self.inter_func, self.model_param)

        with open(os.path.join(output_dir, 'in.lammps'), 'w') as fp:
            fp.write(fc)

    def compute(self,
                output_dir, inter_param):
        log_lammps = os.path.join(output_dir, 'log.lammps')
        if not os.path.isfile(log_lammps):
            warnings.warn("cannot find log.lammps in " + output_dir + " skip")
            return None
        else:
            with open(log_lammps, 'r') as fp:
                if 'Total wall time:' not in fp.read():
                    warnings.warn("lammps not finished " + log_lammps + " skip")
                    return None
                else:
                    fp.seek(0)
                    lines = fp.read().split('\n')
                    for ii in lines:
                        if ("Total number of atoms" in ii) and (not 'print' in ii):
                            natoms = int(ii.split('=')[1].split()[0])
                        if ("Final energy per atoms" in ii) and (not 'print' in ii):
                            epa = float(ii.split('=')[1].split()[0])

                    dump = os.path.join(output_dir, 'dump.relax')
                    _tmp = inter_param['type_map']
                    dlog.debug(_tmp)
                    type_map = {k: v for v, k in _tmp.items()}
                    dlog.debug(type_map)
                    type_map_list = []
                    for ii in range(len(type_map)):
                        type_map_list.append(type_map[ii])
                    contcar = os.path.join(output_dir, 'CONTCAR')
                    d_dump = dpdata.System(dump, fmt='lammps/dump', type_map=type_map_list)
                    d_dump.to('vasp/poscar', contcar, frame_idx=-1)

                    # TODO parsing force via dpdata
                    # force = d_dump['forces']
                    force = ['tmp']

                    result_dict = {"energy": natoms * epa, "force": force*natoms*3}  # deal with dpdata bug
                    return result_dict

    def forward_files(self):
        if self.inter_type == 'meam':
            return ['conf.lmp', 'in.lammps', list(map(os.path.basename, self.model))]
        else:
            return ['conf.lmp', 'in.lammps', os.path.basename(self.model)]

    def forward_common_files(self):
        if self.inter_type == 'meam':
            return ['in.lammps', list(map(os.path.basename, self.model))]
        else:
            return ['in.lammps', os.path.basename(self.model)]

    def backward_files(self):
        return ['log.lammps', 'outlog', 'dump.relax']