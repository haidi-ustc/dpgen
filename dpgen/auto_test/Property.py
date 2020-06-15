import os,glob,json
from abc import ABC,abstractmethod

class Property (ABC) :
    @abstractmethod
    def __init__ (self,
                  parameter) :
        """
        Constructor

        Parameters
        ----------
        parameters : dict
                A dict that defines the property.
        """
        pass        

    @abstractmethod
    def make_confs(self, 
                   path_to_work,
                   path_to_equi, 
                   refine = False):
        """
        Make configurations needed to compute the property. 
        The tasks directory will be named as path_to_work/task.xxxxxx
        IMPORTANT: handel the case when the directory exists.

        Parameters
        ----------
        path_to_work : str
                The path where the tasks for the property are located 
        path_to_equi : str
                -refine == False: The path to the directory that equilibrated the configuration.
                -refine == True: The path to the directory that has property confs.
        refine: str
                To refine existing property confs or generate property confs from a equilibrated conf
        
        Returns
        -------
        task_list: list of str
                The list of task directories.
        """
        pass

    @property
    @abstractmethod
    def task_type(self):
        """
        Return the type of each computational task, for example, 'relaxation', 'static'....
        """
        pass

    @property
    @abstractmethod
    def task_param(self):
        """
        Return the parameter of each computational task, for example, {'ediffg': 1e-4}
        """
        pass

    def compute(self,
                output_file,
                print_file,
                path_to_work):
        """
        Postprocess the finished tasks to compute the property. 
        Output the result to a json database
        
        Parameters
        ----------
        output_file:
                The file to output the property in json format
        print_file:
                The file to output the property in txt format
        path_to_work:
                The working directory where the computational tasks locate.
        """
        path_to_work = os.path.abs_path(path_to_work)
        task_dirs = os.path.join(path_to_work, 'task.[0-9]*[0-9]')
        task_dirs.sort()        
        all_res = []
        for ii in task_dirs:
            with open(os.path.join(ii, 'inter.json')) as fp:
                idata = json.load(fp)
            poscar = os.path.join(ii, 'POSCAR')
            task = make_task(idata, poscar)
            res = task.compute(ii)
            all_res.append(res)
        res, ptr = self.cmpt(task_dirs, all_res)
        with open(output_file, 'w') as fp:
            json.dump(fp, res, indent=4)
        with open(print_file, 'w') as fp:
            fp.write(ptr)

        
    @abstractmethod
    def _compute_lower(self, 
                       output_file,
                       all_tasks,
                       all_res):
        """
        Compute the property.

        Parameters
        ----------
        output_file:
                The file to output the property
        all_tasks : list of str
                The list of directories to the tasks
        all_res : list of str
                The list of results
        
        Returns:
        -------
        res_data: dist
                The dict storing the result of the property
        ptr_data: str
                The result printed in string format
        """
        pass
