#!/usr/bin/env python
import numpy as np
from dpdata.periodic_table import Element
from pymatgen.core.units import ang_to_bohr 

def make_pwdft_input(sys_data, fp_pp_files, fp_input):
    with open(fp_input,'r') as f:
         ret=f.read()
    ret += "\n#pseudo potential\n\n"
    ret += "PeriodTable:  %s\n"%fp_pp_files[0]
    ret += "Pseudo_Type:  HGH\n"
    ret += "\n#structure\n\n"
    st=sys_data.to_pymatgen_structure()[0]
#    print(st)
#    assert st.lattice.is_orthogonal
    ret += "begin Super_Cell\n%.6f %.6f %.6f\nend  Super_Cell\n\n"%tuple(map(lambda x: ang_to_bohr*x, st.lattice.abc))
    nsp = len(st.symbol_set)
    ret +="Atom_Types_Num %d\n" %nsp
    for sp in st.symbol_set:
        ele=Element(sp)
        ret +="Atom_Type: %d\n"%ele.Z
        coords=[tuple(site.frac_coords.tolist()) for site in st if site.species_string==sp]
        ret +="begin Atom_Red\n"
        for coord in coords:
            ret += "%.8f %.8f %.8f\n"%coord
        ret +="end Atom_Red\n"
        ret += "\n"
    ret += "\n"
    return ret
if __name__=="__main__":
   from dpdata import System
   sys_data=System('POSCAR')
   fp_pp_files='HGHPBE_HLiCOFSiP.bin'
   fp_input="temp.in"
   ret=make_pwdft_input(sys_data, fp_pp_files, fp_input)
   print(ret)
