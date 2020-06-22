import os,sys,json,glob,shutil
import dpdata
import numpy as np
from monty.serialization import loadfn,dumpfn
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
__package__ = 'auto_test'
from .context import make_kspacing_kpoints
from .context import setUpModule

from pymatgen.io.vasp import Incar
from dpgen.auto_test.common_equi import make_equi,post_equi
from dpgen.auto_test.calculator import make_calculator

class Test01(unittest.TestCase):
    jdata={
              "structures":    ["confs/hp-Li"],
              "interaction": {
                  "type":      "vasp",
                  "incar":     "vasp_input/INCAR.rlx",
                  "potcar_prefix":".",
                  "potcars":    {"Si": "vasp_input/POTCAR"}
              },
              "relaxation": {
                         "ediff": 1e-7,
                         "ediffg": -0.01,
                         "encut": 650,
                         "kspacing": 0.1,
                         "kgamma": False
              }
             }
    def tearDown(self):
        if os.path.exists('confs/hp-Li/relaxation'):
            shutil.rmtree('confs/hp-Li/relaxation')

    def test_make_equi (self):
        confs=self.jdata["structures"]
        inter_param=self.jdata["interaction"]
        relax_param=self.jdata["relaxation"]
        make_equi(confs,inter_param,relax_param)
        
        target_path = 'confs/hp-Li/relaxation'
        source_path = 'vasp_input'
       
        incar0 = Incar.from_file(os.path.join('vasp_input', 'INCAR.rlx'))
        incar1 = Incar.from_file(os.path.join(target_path, 'INCAR'))
        self.assertFalse(incar0 == incar1)
        incar0['KSPACING'] = 0.1
        incar0['EDIFF'] = 1e-7
        self.assertTrue(incar0 == incar1)

        with open(os.path.join('vasp_input', 'POTCAR')) as fp:
            pot0 = fp.read()
        with open(os.path.join(target_path, 'POTCAR')) as fp:
            pot1 = fp.read()
        self.assertEqual(pot0, pot1)

        self.assertTrue(os.path.isfile(os.path.join(target_path, 'KPOINTS')))

        task_json_file=os.path.join(target_path, 'task.json')
        self.assertTrue(os.path.isfile(task_json_file))
        task_json=loadfn(task_json_file)
        self.assertEqual(task_json,relax_param)

        inter_json_file=os.path.join(target_path, 'inter.json')
        self.assertTrue(os.path.isfile(inter_json_file))
        inter_json=loadfn(inter_json_file)
        self.assertEqual(inter_json,inter_param)

        self.assertTrue(os.path.islink(os.path.join(target_path, 'POSCAR')))


    def test_post_equi(self):
        confs=self.jdata["structures"]
        inter_param=self.jdata["interaction"]
        relax_param=self.jdata["relaxation"]
        target_path = 'confs/hp-Li/relaxation'
        source_path = 'equi/vasp'

        poscar=os.path.join(source_path,'POSCAR')
        make_equi(confs,inter_param,relax_param)
        shutil.copy(os.path.join(source_path,'OUTCAR'),os.path.join(target_path,'OUTCAR'))
        shutil.copy(os.path.join(source_path,'CONTCAR'),os.path.join(target_path,'CONTCAR'))
        post_equi(confs,inter_param)

        result_json_file=os.path.join(target_path, 'result.json')
        result_json=loadfn(result_json_file)
        self.assertTrue(os.path.isfile(result_json_file))
        #self.assertEqual(inter_json,inter_param)
        #calc=make_calculator(inter_param, poscar)