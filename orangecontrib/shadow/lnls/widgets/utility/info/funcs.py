#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 18 16:51:43 2022

@author: joao.astolfo
"""
import Shadow
import inspect
import numpy

def make_python_script_from_list(element_list, script_file=""):
    """
    program to build automatically a python script to run shadow3
    the system is read from a list of instances of Shadow.Source and Shadow.OE
    :argument list of optical_elements A python list with intances of Shadow.Source and Shadow.OE objects
    :param script_file: a string with the name of the output file (default="", no output file)
    :return: template with the script
    """

    template = """import Shadow
import numpy as np
from optlnls.hybrid import run_hybrid

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, ShadowSource


beam = ShadowBeam()
"""

    n_elements = len(element_list)
    params = []
    for i, element in enumerate(element_list):
        if isinstance(element[1], Shadow.Source):
            template += "oe0 = Shadow.Source()\n"
        elif isinstance(element[1], Shadow.OE):
            template += "oe%d = Shadow.OE()\n"%(i)
        elif isinstance(element[1], Shadow.IdealLensOE):
            template += "oe%d = Shadow.IdealLensOE()\n"%(i)
        else:
            raise Exception("Error: Element not known")
        
        with element[0].hybrid_dialog.param as elem:
            params.append('''beam, diff_plane={0}, calcType={1}, dist_to_img_calc={2},
                          distance={3}, focal_length_calc={4},
                          focallength={5}, nf={6}, nbins_x={7}, nbins_z={8}, npeak={9},
                          fftnpts={10}, write_file={11}, automatic={12},
                          send_original_beam={13}'''.format(elem.diff_plane, elem.calcType,
            elem.dist_to_img_calc, elem.distance, elem.focallength_calc, elem.focallength_value, elem.nfc,
            elem.nbins_x, elem.nbins_z, elem.npeaks, elem.fft, elem.write_file, elem.automatic, elem.send_original_beam))

    template += "\n#\n# Define variables. See meaning of variables in: \n" \
                "#  https://raw.githubusercontent.com/srio/shadow3/master/docs/source.nml \n" \
                "#  https://raw.githubusercontent.com/srio/shadow3/master/docs/oe.nml\n#\n"

    for ioe, oe1B in enumerate(element_list):
        template += "\n"
        if isinstance(oe1B[1], Shadow.Source):
            oe1 = Shadow.Source()
        elif isinstance(oe1B[1],Shadow.OE):
            oe1 = Shadow.OE()
        elif isinstance(oe1B[1],Shadow.IdealLensOE):
            oe1 = Shadow.IdealLensOE()
        else:
            raise Exception("Error: Element not known")

        if isinstance(oe1B[1], Shadow.IdealLensOE):
            template += "oe"+str(ioe)+".T_SOURCE = "+str(oe1B[1].T_SOURCE).strip()+"\n"
            template += "oe"+str(ioe)+".T_IMAGE = "+str(oe1B[1].T_IMAGE).strip()+"\n"
            template += "oe"+str(ioe)+".focal_x = "+str(oe1B[1].focal_x).strip()+"\n"
            template += "oe"+str(ioe)+".focal_z = "+str(oe1B[1].focal_z).strip()+"\n"
        else:
            memB = inspect.getmembers(oe1B[1])
            mem = inspect.getmembers(oe1)
            for i, var in enumerate(memB):
                ivar = mem[i]
                ivarB = memB[i]
                if ivar[0].isupper():
                    if isinstance(ivar[1],numpy.ndarray):
                        if not( (ivar[1] == ivarB[1]).all()) :
                            line = "oe"+str(ioe)+"."+ivar[0]+" = np.array("+str(ivarB[1].tolist())+ ")\n"
                            template += line
                    else:
                        if ivar[1] != ivarB[1]:
                            if isinstance(ivar[1],(str,bytes)):
                                line = "oe"+str(ioe)+"."+ivar[0]+" = "+str(ivarB[1]).strip()+"\n"
                                #line = re.sub('\s{2,}', ' ',line)
                                if "SPECIFIED" in line:
                                    pass
                                else:
                                    template += line
                            else:
                                line = "oe"+str(ioe)+"."+ivar[0]+" = "+str(ivarB[1])+"\n"
                                template += line
     
    template += """\n##########################\n
# Run SHADOW to create the source
src = ShadowSource(oe0)
beam = ShadowBeam().traceFromSource(src)"""

    template_oeA = """\n
# Run optical element {0}
print("    Running optical element: %d"%({0}))
oe_{0} = ShadowOpticalElement(oe{0})"""

    for i in range(1, n_elements):
        template += template_oeA.format(i,"%02d"%(i))
        if isinstance(element_list[i][1],Shadow.OE):
            template += "\nbeam = beam.traceFromOE(beam, oe_{0}, widget_class_name='{1}')".format(i, element_list[i][0].hybrid_dialog.name)
            if element_list[i][0].use_hybrid:
                template += '\nbeam = run_hybrid('+params[i]+')'
        elif isinstance(element_list[i][1],Shadow.IdealLensOE):
            template += "\nbeam = beam.traceIdealLensOE(beam, oe_{0}, widget_class_name='{1}')".format(i, element_list[i][0].hybrid_dialog.name)
            if element_list[i][0].use_hybrid:
                template += '\nbeam = run_hybrid('+params[i]+')'
                
            
    template += """\n

# Shadow.ShadowTools.plotxy(beam._beam,1,3,nbins=101,nolost=1,title="Real space")
# Shadow.ShadowTools.plotxy(beam._beam,1,4,nbins=101,nolost=1,title="Phase space X")
# Shadow.ShadowTools.plotxy(beam._beam,3,6,nbins=101,nolost=1,title="Phase space Z")"""

    if script_file != "":
        open(script_file, "wt").write(template)
        print("File written to disk: %s"%(script_file))

    return template