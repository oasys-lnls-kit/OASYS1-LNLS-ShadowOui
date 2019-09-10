# -*- coding: utf-8 -*-

import os
import sys
import time
import numpy


from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream, TTYGrabber
from oasys.widgets import congruence
from silx.gui.plot.Colormap import Colormap

from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor

import orangecanvas.resources as resources

from orangecontrib.shadow.lnls.widgets.gui.ow_lnls_shadow_widget import LNLSShadowWidget

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

import Shadow.ShadowTools as st
from orangecontrib.shadow.util.shadow_util import ShadowCongruence


try:
    from scipy.interpolate import interp1d
    from scipy.integrate import simps
    from scipy.special import kv
    from scipy.integrate import quad
    import scipy.constants as codata
except ImportError:
    raise ImportError('FLUX needs module scipy')
    
try:    
    from oasys_srw.srwlib import SRWLMagFldU, SRWLMagFldH, SRWLPartBeam, SRWLStokes, srwl
    #from oasys_srw.srwlpy import CalcStokesUR
except ImportError:
    raise ImportError('FLUX needs module srwlib and srwlpy')
    
class FluxWidget(LNLSShadowWidget):
    name = "Flux"
    description = "Calculate flux and power at any position"
    icon = "icons/flux_icon.png"
    authors = "Artur C Pinto, Sergio A Lordano Luiz, Bernd C Meyer, Luca Rebuffi"
    maintainer_email = "artur.pinto@lnls.br"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read","flux"]

    inputs = [("Input Beam", ShadowBeam, "set_beam")]

    IMAGE_WIDTH = 380
    IMAGE_HEIGHT = 320
    
    want_main_area=1
    plot_canvas=None
    plot_canvas2=None
    plot_canvas3=None
    plot_canvas4=None    
    input_beam=None
    
    retrive_source_parameters = Setting(False)

    source_type=Setting(0)
    storage_energy=Setting(3.0)
    current=Setting(0.1)
    mag_field=Setting(3.2)
    k_wiggler=Setting(12.0)    
    n_periods=Setting(20)
    w_period=Setting(0.04)
    und_period=Setting(0.021)
    und_length=Setting(2.4)
    k_value=Setting(1.922968)
    c_En=Setting(10000.0)
    und_n=Setting(7)
    use_vert_acc = Setting(0)
    ebeam_vert_sigma = Setting(0.0)
    en_spread=Setting(0.085e-2)
    max_h=Setting(9)
    prec=Setting(1.0)      
    
    sigma_x=Setting(19.1e-3)
    sigma_z=Setting(2.0e-3)
    div_x=Setting(13.0e-6)
    div_z=Setting(1.3e-6)     
    lim_i_x=Setting(0)
    lim_f_x=Setting(0)
    lim_i_z=Setting(0)
    lim_f_z=Setting(0)
      
    number_of_bins=Setting(101)     
             
    inten=Setting(0)
    nrays=Setting(0)
    grays=Setting(0)
    lrays=Setting(0)
    flux_total=Setting(0)
    power_total=Setting(0)
    keep_result=Setting(0)
    showflux=Setting(0)
    showpower=Setting(0)
    output_filename=Setting("output.dat")
    fig_filename=Setting("output.png")
   
    def __init__(self):
        super().__init__()
        
        ############### CONTROL AREA #####################        
        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH+8)
        
        gui.checkBox(self.general_options_box, self, 'retrive_source_parameters', 'Get Source Parameters', callback=self.get_parameters_from_source)
        
        gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=35,width=100)
        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)        
        self.tabs_setting.setFixedHeight(550)
        

        ### Tabs inside control area ###
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Source Settings")
        tab_config = oasysgui.createTabPage(self.tabs_setting, "Calculation Settings" )

        ### Source Setting tab (tab_gen) ###    
        screen_box = oasysgui.widgetBox(tab_gen, "Source Description", addSpace=True, orientation="vertical", height=500)

        self.source_combo = gui.comboBox(screen_box, self, "source_type", label="Source Type",
                                            items=["Bending Magnet", "Wiggler","Linear Undulator"],callback=self.set_Source, labelWidth=260,orientation="horizontal")
        gui.separator(screen_box)

        self.kind_of_source_box_1 = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=400)        


        self.kind_of_source_box_1_1 = oasysgui.widgetBox(self.kind_of_source_box_1, "", addSpace=False, orientation="vertical")
        
        self.le_st_energy = oasysgui.lineEdit(self.kind_of_source_box_1_1, self, "storage_energy", "Energy [GeV]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        self.le_mag_f = oasysgui.lineEdit(self.kind_of_source_box_1_1, self, "mag_field", "Magnet Field Value [T]",
                           labelWidth=260, callback=self.B_K_wiggler, valueType=float, orientation="horizontal")

        ### Exclusive Wiggler parameters ###                        
        self.kind_of_source_box_1_2 = oasysgui.widgetBox(self.kind_of_source_box_1, "", addSpace=False, orientation="vertical", height=100)

        self.le_K_w = oasysgui.lineEdit(self.kind_of_source_box_1_2, self, "k_wiggler", "K-value",
                           labelWidth=260, callback=self.K_B_wiggler, valueType=float, orientation="horizontal")
        
        self.le_np = oasysgui.lineEdit(self.kind_of_source_box_1_2, self, "n_periods", "Number of Periods",
                           labelWidth=260, valueType=int, orientation="horizontal")
        
        self.le_wp = oasysgui.lineEdit(self.kind_of_source_box_1_2, self, "w_period", "Wiggler Period [m]",
                           labelWidth=260, valueType=float, orientation="horizontal")

        self.kind_of_source_box_1_1b = oasysgui.widgetBox(self.kind_of_source_box_1, "", addSpace=False, orientation="vertical")
        
        ### Vertical Acceptance options for Bending Magnet and Wiggler sources ###
        self.check_vert_acc = gui.comboBox(self.kind_of_source_box_1_1b, self, "use_vert_acc", label="Partial Vertical Acceptance",
                                            items=["No", "Yes"], callback=self.set_Source, labelWidth=260,orientation="horizontal")
        
        self.kind_of_source_box_1_1c = oasysgui.widgetBox(self.kind_of_source_box_1, "", addSpace=False, orientation="vertical")
        
        self.ebeam_divz = oasysgui.lineEdit(self.kind_of_source_box_1_1c, self, "ebeam_vert_sigma", "e-beam Divergence RMS V [rad]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        

        ### Exclusive Linear Undulator parameters ###   
            ### Machine Paremeters ###
        self.kind_of_source_box_1_3 = oasysgui.widgetBox(self.kind_of_source_box_1, "", addSpace=True, orientation="vertical", height=400)

        self.le_st_energy_und = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "storage_energy", "Energy [GeV]",
                           labelWidth=260, valueType=float, orientation="horizontal")
    
        self.le_es = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "en_spread", "Energy Spread",
                           labelWidth=260, valueType=float, orientation="horizontal")
    
        self.le_sx = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "sigma_x", "Size RMS H [mm]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        self.le_sz = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "sigma_z", "Size RMS V [mm]",
                           labelWidth=260, valueType=float, orientation="horizontal")
    
        self.le_emx = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "div_x", "Divergence RMS H [rad]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        self.le_emz = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "div_z", "Divergence RMS V [rad]",
                           labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_source_box_1_3)
        gui.separator(self.kind_of_source_box_1_3)
        
            ### Undulator Paremeters ###
        self.le_up = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "und_period", "Undulator Period [m]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        self.le_ul = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "und_length", "Undulator Length [m]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        self.le_ce = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "und_n", "Harmonic Number (n)",
                           labelWidth=260, valueType=int, orientation="horizontal")
        
        self.le_ce = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "c_En", "Target Energy (En) [eV]",
                           labelWidth=260, callback=self.En_K_und, valueType=float, orientation="horizontal")
        
        self.le_kv = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "k_value", "K-value",
                           labelWidth=260, callback=self.K_En_und, valueType=float, orientation="horizontal")     
        
        self.le_mh = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "max_h", "Maximum Harmonic to include",
                           labelWidth=260, valueType=int, orientation="horizontal")
        
        self.le_pr = oasysgui.lineEdit(self.kind_of_source_box_1_3, self, "prec", "Precision (>1)",
                           labelWidth=260, valueType=float, orientation="horizontal")
        
        ### Call set_Source function ###
        self.set_Source()
        
        ### Calculation Settings tab (tab_config) ###  
        config_box = oasysgui.widgetBox(tab_config, "Define Flux Calculation Settings", addSpace=True, orientation="vertical", height=200)
        
        self.nb = oasysgui.lineEdit(config_box, self, "number_of_bins", "Number of Bins", 
                          labelWidth=220, valueType=int, controlWidth=100, orientation="horizontal")        
        
        self.mxa = oasysgui.lineEdit(config_box, self, "lim_i_x", "Source Acceptance -X [rad] ", 
                          labelWidth=220, valueType=float, controlWidth=100, orientation="horizontal") 
        
        self.pxa = oasysgui.lineEdit(config_box, self, "lim_f_x", "Source Acceptance +X [rad] ", 
                          labelWidth=220, valueType=float, controlWidth=100, orientation="horizontal") 
        
        self.mxz = oasysgui.lineEdit(config_box, self, "lim_i_z", "Source Acceptance -Z [rad] ", 
                          labelWidth=220, valueType=float, controlWidth=100, orientation="horizontal")
        
        self.pxz = oasysgui.lineEdit(config_box, self, "lim_f_z", "Source Acceptance +Z [rad] ", 
                          labelWidth=220, valueType=float, controlWidth=100, orientation="horizontal")
        
        print_box = oasysgui.widgetBox(tab_config, "Save Data", addSpace=True, orientation="vertical", height=260)

#        self.flux_is_displayed = False
#        self.power_is_displayed = False        
        gui.checkBox(print_box, self, "showflux", "Show Flux", callback=self.showFlux)
        gui.checkBox(print_box, self, "showpower", "Show Power", callback=self.showPower)
        
        self.select_file_box = oasysgui.widgetBox(print_box, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.select_file_box, self, "output_filename", "File Name",
                          labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(print_box, self, "Save Data to txt", callback=self.down_data, height=35,width=200)
        
        gui.separator(self.select_file_box)
        self.select_file_box2 = oasysgui.widgetBox(print_box, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(self.select_file_box2, self, "fig_filename", "Figure Name",
                          labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(print_box, self, "Save Figure", callback=self.down_fig, height=35, width=200)

    
       
        ############### MAIN AREA #####################
        
        self.tabs_flux = oasysgui.tabWidget(self.mainArea)
        self.tabs_flux.setFixedWidth(2*self.CONTROL_AREA_WIDTH)  
     

        ### Tabs Inside the main area ###
        plotflux_tab = oasysgui.createTabPage(self.tabs_flux, "Beamline Spectrum")       
        plotsource_tab = oasysgui.createTabPage(self.tabs_flux, "Source Spectrum")
        transm_tab = oasysgui.createTabPage(self.tabs_flux, "Beamline Transmittance")
        histo_tab = oasysgui.createTabPage(self.tabs_flux, "Histogram")
        vert_acc_tab = oasysgui.createTabPage(self.tabs_flux, "Source Acceptance")
        output_tab = oasysgui.createTabPage(self.tabs_flux, "Ouput")       
        
      
        ### Area for Beamline Flux Plot, inside plotflux_tab ###        
        output_box = oasysgui.widgetBox(plotflux_tab, "", addSpace=True, orientation="horizontal",
                                        height=650, width=2.5*self.CONTROL_AREA_WIDTH)       
        self.image_box = gui.widgetBox(output_box, "Element Flux", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(2*self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(1.75*self.IMAGE_WIDTH)
        self.plot_canvas = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=True)
        self.plot_canvas.setDefaultPlotLines(True)
        self.plot_canvas.setActiveCurveColor(color='blue')
                
        
        ### Area for Source Flux Plot, inside plotflux_tab ###
        self.image_box2 = gui.widgetBox(plotsource_tab, "Source Flux", addSpace=True, orientation="vertical")
        self.image_box2.setFixedHeight(2*self.IMAGE_HEIGHT)
        self.image_box2.setFixedWidth(2*self.IMAGE_WIDTH)
        self.plot_canvas2 = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=True)
        self.plot_canvas2.setDefaultPlotLines(True)
        self.plot_canvas2.setActiveCurveColor(color='blue')
        
        ### Area for Transmission Plot, inside plotflux_tab ###
        self.image_box3 = gui.widgetBox(transm_tab, "Transmission", addSpace=True, orientation="vertical")
        self.image_box3.setFixedHeight(2*self.IMAGE_HEIGHT)
        self.image_box3.setFixedWidth(2*self.IMAGE_WIDTH)
        self.plot_canvas3 = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=True)
        self.plot_canvas3.setDefaultPlotLines(True)
        self.plot_canvas3.setActiveCurveColor(color='blue')
        
        ### Area for Histograms Plot, inside plotflux_tab ###
        self.image_box4 = gui.widgetBox(histo_tab, "Histogram", addSpace=True, orientation="vertical")
        self.image_box4.setFixedHeight(2*self.IMAGE_HEIGHT)
        self.image_box4.setFixedWidth(2*self.IMAGE_WIDTH)
        self.plot_canvas4 = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=True)
        self.plot_canvas4.setDefaultPlotLines(True)
        self.plot_canvas4.setActiveCurveColor(color='blue') 
        
        ### Area for Source Acceptance Plot, inside plotflux_tab ###
        acc_box = oasysgui.widgetBox(vert_acc_tab, "", addSpace=True, orientation="vertical",
                                        height=650, width=2.5*self.CONTROL_AREA_WIDTH)
        
        ### Colormap plot - source vertical acceptance ###
        self.image_box5 = gui.widgetBox(acc_box, "Source Acceptance (Bending Magnet and Wiggler only)", addSpace=True, orientation="horizontal")
        self.image_box5.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box5.setFixedWidth(2*self.IMAGE_WIDTH)
        self.plot_canvas5 = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=False)
        self.colormap = Colormap(name='temperature')
        self.plot_canvas5.setDefaultColormap(self.colormap)        
        
        ### Curve plot - vertical acceptance ###
        self.image_box6 = gui.widgetBox(acc_box, "Vertical Acceptance", addSpace=True, orientation="horizontal")
        self.image_box6.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box6.setFixedWidth(2*self.IMAGE_WIDTH)
        self.plot_canvas6 = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=False)
        self.plot_canvas6.setDefaultPlotLines(True)
        self.plot_canvas6.setActiveCurveColor(color='blue')
        
                
        #### Area for output info ############
        self.shadow_output = oasysgui.textArea()
        out_box = oasysgui.widgetBox(output_tab, "System Output", addSpace=True, orientation="horizontal", height=600)
        out_box.layout().addWidget(self.shadow_output)
        
        
        ################### RAYS INFO ##################                     
                                   
        box_info = oasysgui.widgetBox(output_box, "Info", addSpace=True, orientation="vertical",
                                      height=600, width=0.3*self.CONTROL_AREA_WIDTH)
        
        inten_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_i = QtWidgets.QLabel("Intensity")
        self.label_i.setFixedWidth(100)
        inten_info_box.layout().addWidget(self.label_i)
        self.inten_v = gui.lineEdit(inten_info_box, self, "inten", "", tooltip=" Intensity ", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.inten_v.setReadOnly(True)

        nrays_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_nr = QtWidgets.QLabel("Total Rays")
        self.label_nr.setFixedWidth(100)
        nrays_info_box.layout().addWidget(self.label_nr)
        self.nrays_v = gui.lineEdit(nrays_info_box, self, "nrays", "", tooltip=" Total Rays ", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.nrays_v.setReadOnly(True)

        grays_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_gr = QtWidgets.QLabel("Total Good Rays")
        self.label_gr.setFixedWidth(100)
        grays_info_box.layout().addWidget(self.label_gr)
        self.grays_v = gui.lineEdit(grays_info_box, self, "grays", "", tooltip=" Total Good Rays ", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.grays_v.setReadOnly(True)

        lrays_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_lr = QtWidgets.QLabel("Total Lost Rays")
        self.label_lr.setFixedWidth(100)
        lrays_info_box.layout().addWidget(self.label_lr)
        self.lrays_v = gui.lineEdit(lrays_info_box, self, "lrays", "", tooltip=" Total Lost Rays ", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.lrays_v.setReadOnly(True)      
                
        flux_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_ft = QtWidgets.QLabel("Total Flux \n [ph/s/100mA]")
        self.label_ft.setFixedWidth(150)
        flux_info_box.layout().addWidget(self.label_ft)
        self.fluxT = gui.lineEdit(flux_info_box, self, "flux_total", "", tooltip=" Total Flux", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.fluxT.setReadOnly(True)   
                
        power_info_box = gui.widgetBox(box_info, "", addSpace=True, orientation="vertical")
        self.label_pt = QtWidgets.QLabel("Total Power \n [W/100mA]")
        self.label_pt.setFixedWidth(150)
        power_info_box.layout().addWidget(self.label_pt)
        self.powerT = gui.lineEdit(power_info_box, self, "power_total", "", tooltip=" Total Power", 
								controlWidth=100, valueType=str, orientation="horizontal")
        self.powerT.setReadOnly(True)     
        
        ### Creates 'Run' function for Flux widget ###
        self.runaction = widget.OWAction("Run", self)
        self.runaction.triggered.connect(self.plot_results)
        self.addAction(self.runaction)
        
#################################################################################
#################################################################################
#################################################################################
#################################################################################
        
    
    ### Show or hide source     
    def set_Source(self):
        self.kind_of_source_box_1.setVisible(self.source_type<=2)
        self.kind_of_source_box_1_1.setVisible(self.source_type<2)
        self.kind_of_source_box_1_2.setVisible(self.source_type==1)
        self.kind_of_source_box_1_3.setVisible(self.source_type==2)
        self.kind_of_source_box_1_1b.setVisible(self.source_type<2)
        self.kind_of_source_box_1_1c.setVisible(self.use_vert_acc==1 and self.source_type<2)
      
    
    ### Calculates Wiggler Magnetic Filed from a given K-Value
    def K_B_wiggler(self):
        self.mag_field = round(self.k_wiggler/(93.364*self.w_period),6)        
    
    ### Calculates Wiggler K-Vlaue from Magnetic Filed 
    def B_K_wiggler(self):        
        self.k_wiggler = round(93.364*self.w_period*self.mag_field, 6)
                    
    ### Calculates undulator K-Value from a given Energy        
    def En_K_und(self):
        self.k_value = round(numpy.sqrt(2*9.4963425587*self.storage_energy**2/(self.und_period*self.c_En/self.und_n)-2),6)    
        
    ### Calculates undulator central Energy from a given K-Value
    def K_En_und(self):        
        self.c_En = round(9.4963425587*self.und_n*self.storage_energy**2/((1+self.k_value**2/2.0)*self.und_period),6)      
   
    
    ### Colect input beam ###
    def set_beam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                if self.keep_result == 1 and not self.input_beam is None:
                    self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                    
                else:
                    self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays, bad content, bad limits or axes",
                                           QtWidgets.QMessageBox.Ok)
                

    ### Get Source Info - For Bending Magnet, Geometrical Source and Undulator Gaussian ###
    def get_parameters_from_source(self):
        if(hasattr(self, 'input_beam')):
            try:
                Source = self.input_beam.history[0]._shadow_source_end.src
                
                if not (Source.HDIV1==0 or Source.HDIV2==0 or Source.VDIV1==0 or Source.VDIV2==0):
                    self.lim_i_x = Source.HDIV1
                    self.lim_f_x = Source.HDIV2
                    self.lim_i_z = Source.VDIV1
                    self.lim_f_z = Source.VDIV2
                    self.mxa.setDisabled(self.retrive_source_parameters)
                    self.pxa.setDisabled(self.retrive_source_parameters)
                    self.mxz.setDisabled(self.retrive_source_parameters)
                    self.pxz.setDisabled(self.retrive_source_parameters)
                
                # Bending Magnet
                if self.source_type == 0:
                    self.storage_energy = Source.BENER
                    self.le_st_energy.setDisabled(self.retrive_source_parameters)
                    self.mag_field = (1e9/codata.c)*self.storage_energy/Source.R_MAGNET
                    self.le_mag_f.setDisabled(self.retrive_source_parameters)
                    self.ebeam_vert_sigma = Source.EPSI_Z/Source.SIGMAZ
                    self.ebeam_divz.setDisabled(self.retrive_source_parameters)
                    
                # Wiggler - Beam does not propagate parameters
                elif self.source_type == 1:
                    self.storage_energy = Source.BENER
                    self.le_st_energy.setDisabled(self.retrive_source_parameters)
#                    self.mag_field = 
#                    self.k_wiggler = 
#                    self.n_periods =
#                    self.w_period =
                    self.ebeam_vert_sigma = Source.EPSI_Z/Source.SIGMAZ
                    self.ebeam_divz.setDisabled(self.retrive_source_parameters)
                    
                #Geometrical Source or Undulator Gaussian
                elif self.source_type == 2:
                    self.sigma_x = Source.SIGMAX
                    self.le_sx.setDisabled(self.retrive_source_parameters)
                    self.sigma_z = Source.SIGMAZ
                    self.le_sz.setDisabled(self.retrive_source_parameters)
                    self.div_x = Source.SIGDIX
                    self.le_emx.setDisabled(self.retrive_source_parameters)
                    self.div_z = Source.SIGDIZ
                    self.le_emz.setDisabled(self.retrive_source_parameters)
                    
                    self.c_En = (Source.PH1 + Source.PH2)/2
                    self.le_ce.setDisabled(self.retrive_source_parameters)
                    self.En_K_und()
                    self.le_kv.setDisabled(self.retrive_source_parameters)
            except:
                QtWidgets.QMessageBox.critical(self, "Error",
                                               "Unable to retrive source data.",
                                               QtWidgets.QMessageBox.Ok)
        else:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "No input beam! Please run the previous widget.",
                                           QtWidgets.QMessageBox.Ok)

    ### Call plot functions ###
    def plot_results(self):
        
        if self.retrive_source_parameters:
            self.get_parameters_from_source()

        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_bins, "Number of Bins")
                self.getConversion()
                self.plot_xy()

                plotted = True

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)
            return False


    def plot_xy(self):
        beam_to_plot = self.input_beam._beam       

       #Intesity Spectrum at Sample
        En = beam_to_plot.getshonecol(11, nolost=1)
        I = beam_to_plot.getshonecol(23, nolost=1)
        self.histoI = numpy.histogram(En, self.number_of_bins, weights=I)[0]
        self.En_coord = numpy.linspace(numpy.min(En), numpy.max(En),self.number_of_bins)
        
       #Collect intensity from Shadow Source
        En0 = beam_to_plot.getshonecol(11, nolost=0)
        I0 = numpy.ones(len(En0))
        
       #Creates source histogram from sample energy range
        I0_new = I0[numpy.logical_and(En0>=numpy.min(En),En0<=numpy.max(En))]
        En0_new = En0[numpy.logical_and(En0>=numpy.min(En),En0<=numpy.max(En))]
        self.histoI0 = numpy.histogram(En0_new, self.number_of_bins , weights=I0_new)[0] 

       #Collect beam info       
        info_beam = beam_to_plot.histo1(1, nolost=1)
        self.inten = ("{:.2f}".format(info_beam['intensity']))
        self.nrays = str(int(info_beam['nrays']))
        self.grays = str(int(info_beam['good_rays']))
        self.lrays = str(int(info_beam['nrays']-info_beam['good_rays'])) 
                       
        self.current = 0.1 #always normalized to 100 mA
        
        ##### Get source acceptance #####  
        if (self.lim_i_x == 0) or (self.lim_i_z == 0):
            
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Set Source Acceptance in the Calculation Settings tab!!",
                                           QtWidgets.QMessageBox.Ok)
        
        self.checkFields()
        self.hor_accep = (self.lim_f_x + self.lim_i_x)*1e3
        self.ver_accep = (self.lim_f_z + self.lim_i_z)*1e3
        
        sp = '            ' # spacing for identation 
        self.print_date_i()
        print( sp + 'Source parameters:')
        
       #Select source type and calculate spectrum
        if self.source_type == 0:
  
           self.source_spec = self.BM_spectrum(E=self.storage_energy,I=self.current,B=self.mag_field,ph_energy=self.En_coord,hor_acc_mrad=self.hor_accep)
           print(sp+sp+'E = {0} GeV'.format(self.storage_energy) + '\n' + sp+sp+'I = {0} A'.format(self.current) + '\n' + sp+sp+'B = {0} T'.format(self.mag_field) + '\n' )
           
           
        if self.source_type == 1:

           self.n_periods = self.n_periods
           self.source_spec = self.Wiggler_spectrum(self.storage_energy,self.current,self.mag_field,self.n_periods,self.En_coord,self.hor_accep)
           print(sp+sp+'E = {0} GeV'.format(self.storage_energy) + '\n' + sp+sp+'I = {0} A'.format(self.current) + '\n' + sp+sp+'B = {0} T'.format(self.mag_field) + '\n' + sp+sp+'N periods = {0} '.format(self.n_periods) + '\n' )

        if self.source_type == 2:
            e = 1.60217662e-19; m_e = 9.10938356e-31; pi = 3.141592654; c = 299792458;
            B = 2*pi*m_e*c*self.k_value/(e*self.und_period)
            mag_field=[self.und_period,self.und_length, 0, B, 0, 0, +1, +1]
            electron_beam=[self.sigma_x*1e-3, self.sigma_z*1e-3, self.div_x, self.div_z, self.storage_energy, self.en_spread, self.current]
            sampling_mesh=[10.0, round(-self.lim_i_x*10.0, 8), round(self.lim_f_x*10.0, 8), round(-self.lim_i_z*10.0, 8), round(self.lim_f_z*10.0, 8)]    
            precision = [self.max_h, self.prec, self.prec]
            energy_grid=[self.En_coord[0],self.En_coord[-1], self.number_of_bins]            

            print(sp+sp+"Parameters passed to SRWLMagFldH():")
            print(sp+sp+sp+"_n=1, _h_or_v='v', _B={0}, _ph={1}, _s={2}, _a=1".format(mag_field[3], mag_field[5], mag_field[7]))
            print(sp+sp+"Parameters passed to SRWLMagFldH():")
            print(sp+sp+sp+"_n=1, _h_or_v='h', _B={0}, _ph={1}, _s={2}, _a=1".format(mag_field[2], mag_field[4], mag_field[6]))
            print(sp+sp+"Parameters passed to SRWLMagFldU():")
            print(sp+sp+sp+"_arHarm=[SRWLMagFldH_v, SRWLMagFldH_h], _per={0}, _nPer={1}".format(mag_field[0], int(round(mag_field[1]/mag_field[0]))))
            print(sp+sp+"Parameters passed to SRWLPartBeam():")
            print(sp+sp+sp+"_Iavg={0}, _gamma={1}/0.510998902e-03".format(electron_beam[6], electron_beam[4]))
            print(sp+sp+sp+"_arStatMom2=[0=({0})**2, 2=({1})**2, 3=({2})**2,".format(electron_beam[0], electron_beam[2], electron_beam[1]))
            print(sp+sp+sp+"                         5=({0})**2, 10=({1})**2]".format(electron_beam[3], electron_beam[5]))
             
            print(sp+sp+"Precision array passed to CalcStokesUR():")
            print(sp+sp+sp+"[0=1, 1={0}, 2={1}, 3={2}, 4=1]".format(precision[0], precision[1], precision[2]))
            print(sp+sp+"Energy Grid array: ")
            print(sp+sp+sp, energy_grid)
            print(sp+sp+"Radiation Sampling array: ")
            print(sp+sp+sp, sampling_mesh, '\n')
           
            os.write(1, b'########### Running SRW Undulator Spectrum! ############### \n')
            self.source_spec = self.srw_undulator_spectrum(mag_field, electron_beam, energy_grid, sampling_mesh, precision)
            os.write(1, b'########### Source Spectrum Done! ############### \n')
        
        
        print(sp+'Source acceptance limits used for source spectrum calculation:')
        print(sp+sp+'-X = '+'{:.3e}'.format(-self.lim_i_x)+' rad')
        print(sp+sp+'+X = '+'{:.3e}'.format(self.lim_f_x)+' rad')
        print(sp+sp+'-Z = '+'{:.3e}'.format(-self.lim_i_z)+' rad')
        print(sp+sp+'+Z = '+'{:.3e}'.format(self.lim_f_z)+' rad' + '\n')
           
        
        # Calculates Vertical acceptance for Bending Magnet and Wiggler sources
        self.vert_acc = numpy.ones((len(self.En_coord)))
        if(self.source_type<2 and self.use_vert_acc==1):
            
            self.acc_dict = self.BM_vertical_acc(E=self.storage_energy, B=self.mag_field, ph_energy=self.En_coord, 
                                                 div_limits=[-self.lim_i_z, self.lim_f_z], e_beam_vert_div=self.ebeam_vert_sigma)
            self.vert_acc = self.acc_dict['acceptance']

        
        #Flux Spectrum at Sample
        self.T1 = self.histoI/self.histoI0
        Flux_eV = self.source_spec*(1000.0/self.En_coord)
        Flux_sample = Flux_eV*self.T1*self.vert_acc
        Power_sample = Flux_eV*self.T1*self.vert_acc*self.En_coord*1.60217662e-19
 
        self.Flux = (simps(Flux_sample,x=self.En_coord)*(0.1/self.current))    #Integrate the Flux and normalize to 100 mA
        self.Power = (simps(Power_sample,x=self.En_coord)*(0.1/self.current))
        
        self.flux_total = ("{:.2e}".format(self.Flux))
        self.power_total = ("{:.2e}".format(self.Power))
        
        print(sp+'### Results ###')
        print(sp+sp+'Total Flux = {:.3e}'.format(self.Flux) + ' ph/s/100 mA')
        print(sp+sp+'Total Power = {:.3e}'.format(self.Power)+' W')
        print('\n')
                     
        #Plot Flux after element
        self.beamline_flux = self.source_spec*self.T1*self.vert_acc
        self.plot_canvas.clear()
        self.plot_canvas.setGraphYLabel("Flux [ph/s/100mA/0.1%bW]")
        self.plot_canvas.setGraphXLabel("Energy [eV]")        
        self.plot_canvas.setGraphTitle('Beamline Spectrum')
        self.plot_canvas.addCurve(self.En_coord,self.beamline_flux,color='blue',symbol='.',linewidth=2)
        self.image_box.layout().addWidget(self.plot_canvas)
#        self.showflux = 0
#        self.showpower = 0
        self.showFlux()
        self.showPower()
#        
        #Plot Source Flux 
        self.plot_canvas2.clear()
        self.plot_canvas2.setGraphYLabel("Flux [ph/s/100mA/0.1%bW]")
        self.plot_canvas2.setGraphXLabel("Energy [eV]")
        self.plot_canvas2.setGraphTitle('Source Spectrum')        
        self.plot_canvas2.addCurve(self.En_coord,self.source_spec*self.vert_acc,color='blue',symbol='.',linewidth=2)
        self.image_box2.layout().addWidget(self.plot_canvas2)
        
#        
        #Plot Transmission 
        self.plot_canvas3.clear()
        self.plot_canvas3.setGraphYLabel("Transmission")
        self.plot_canvas3.setGraphXLabel("Energy [eV]")       
        self.plot_canvas3.setGraphTitle('Beamline Transmission')
        self.plot_canvas3.addCurve(self.En_coord,self.T1,color='blue',symbol='.',linewidth=2)
        self.image_box3.layout().addWidget(self.plot_canvas3)

#
        #Plot Histogram 
        self.plot_canvas4.clear()
        self.plot_canvas4.setGraphYLabel("Intensity")
        self.plot_canvas4.setGraphXLabel("Energy [eV]")     
        self.plot_canvas4.setGraphTitle('Intensity Histograms')
        self.plot_canvas4.addCurve(self.En_coord,self.histoI0,legend='Source',color='green')                   
        self.plot_canvas4.addCurve(self.En_coord,self.histoI,legend='Element',color='red')
        self.image_box4.layout().addWidget(self.plot_canvas4)
        
        #Plot Acceptance
        if(self.source_type<2 and self.use_vert_acc==1):
            self.plot_canvas5.clear()            
            self.plot_canvas5.addImage(self.acc_dict["PDF"].transpose(),origin=(numpy.min(self.En_coord),1e3*numpy.min(self.acc_dict["Psi"])),
                                       scale=((numpy.max(self.En_coord)-numpy.min(self.En_coord))/self.number_of_bins,
                                              1e3*(numpy.max(self.acc_dict["Psi"])-numpy.min(self.acc_dict["Psi"]))/len(self.acc_dict["PDF"][0,:])))
            self.plot_canvas5.addCurve(self.En_coord,1e3*self.acc_dict["rwhm"],color='black',linewidth=1.5,legend='right')
            self.plot_canvas5.addCurve(self.En_coord,1e3*self.acc_dict["lwhm"],color='black',linewidth=1.5,legend='left')
            self.plot_canvas5.addCurve([numpy.min(self.En_coord),numpy.max(self.En_coord)],
                                       [-self.lim_i_z*1e3,-self.lim_i_z*1e3],color='gray',linewidth=1.5,legend='i_z')
            self.plot_canvas5.addCurve([numpy.min(self.En_coord),numpy.max(self.En_coord)],
                                       [self.lim_f_z*1e3,self.lim_f_z*1e3],color='gray',linewidth=1.5,legend='f_z')
            
            pos = [0.12, 0.2, 0.82, 0.70]
    
            self.plot_canvas5._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
            self.plot_canvas5._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
            self.plot_canvas5._backend.ax.set_position(pos)
            self.plot_canvas5._backend.ax2.set_position(pos)
            
            self.image_box5.layout().addWidget(self.plot_canvas5)               
            self.plot_canvas5.setGraphXLabel("Energy [keV]")
            self.plot_canvas5.setGraphYLabel("Vert. div. distribution [mrad]")
        
            self.plot_canvas6.clear()            
            self.plot_canvas6.addCurve(self.En_coord,self.acc_dict["acceptance"],color='blue',symbol='.',linewidth=2)    
            
            self.plot_canvas6._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
            self.plot_canvas6._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
            self.plot_canvas6._backend.ax.set_position(pos)
            self.plot_canvas6._backend.ax2.set_position(pos)
            
            self.plot_canvas6.setGraphXLabel("Energy [keV]")
            self.plot_canvas6.setGraphYLabel("Acceptance Factor")    
            self.image_box6.layout().addWidget(self.plot_canvas6)
            
        self.print_date_f() 
        
        
    def writeStdOut(self, text):        
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam, dist):
            new_shadow_beam._beam.retrace(dist)

    def getConversion(self):
        if self.workspace_units_label == "cm":
             self.conv = 1e4
        if self.workspace_units_label == "mm":
            self.conv = 1e3
        if self.workspace_units_label == "m":
            self.conv = 1e6

    def checkFields(self):        
        self.lim_i_x  = congruence.checkPositiveNumber(self.lim_i_x , "Source Acceptance -X [rad]")
        self.lim_f_x  = congruence.checkPositiveNumber(self.lim_f_x , "Source Acceptance +X [rad]")
        self.lim_i_z  = congruence.checkPositiveNumber(self.lim_i_z , "Source Acceptance -Z [rad]")
        self.lim_f_z  = congruence.checkPositiveNumber(self.lim_f_z , "Source Acceptance +Z [rad]")
        
    #########################################################################
    ############ SOURCE SPECTRUM CALCULATION FUNCTIONS ######################
    #########################################################################
    
    def srw_undulator_spectrum(self, mag_field=[], electron_beam=[], energy_grid=[], sampling_mesh=[], precision=[]):
        """
        Calls SRW to calculate spectrum for a planar or elliptical undulator\n
        :mag_field: list containing: [period [m], length [m], Bx [T], By [T], phase Bx = 0, phase By = 0, Symmetry Bx = +1, Symmetry By = -1]
        :electron_beam: list containing: [Sx [m], Sy [m], Sx' [rad], Sy'[rad], Energy [GeV], Energy Spread [dE/E], Current [A]]
        :energy_grid: list containing: [initial energy, final energy, number of energy points]
        :sampling_mesh: list containing: [observation plane distance from source [m], range -X [m], , range+X [m], range -Y [m], range +Y [m]]
        :precision: list containing: [h_max: maximum harmonic number to take into account, longitudinal precision factor, azimuthal precision factor (1 is standard, >1 is more accurate]
        """     
    
        #***********Undulator
        und = SRWLMagFldU([SRWLMagFldH(1, 'v', mag_field[3], mag_field[5], mag_field[7], 1), 
                           SRWLMagFldH(1, 'h', mag_field[2], mag_field[4], mag_field[6], 1)], 
                           mag_field[0], int(round(mag_field[1]/mag_field[0])))
           
        #***********Electron Beam
        eBeam = SRWLPartBeam()
        eBeam.Iavg = electron_beam[6] #average current [A]
        eBeam.partStatMom1.x = 0. #initial transverse positions [m]
        eBeam.partStatMom1.y = 0.
        eBeam.partStatMom1.z = -(mag_field[1]/2 + mag_field[0]*2) #initial longitudinal positions (set in the middle of undulator)
        eBeam.partStatMom1.xp = 0 #initial relative transverse velocities
        eBeam.partStatMom1.yp = 0
        eBeam.partStatMom1.gamma = electron_beam[4]/0.51099890221e-03 #relative energy
        sigEperE = electron_beam[5] #0.00089 #relative RMS energy spread
        sigX = electron_beam[0] #33.33e-06 #horizontal RMS size of e-beam [m]
        sigXp = electron_beam[2] #16.5e-06 #horizontal RMS angular divergence [rad]
        sigY = electron_beam[1] #2.912e-06 #vertical RMS size of e-beam [m]
        sigYp = electron_beam[3] #2.7472e-06 #vertical RMS angular divergence [rad]
        #2nd order stat. moments:
        eBeam.arStatMom2[0] = sigX*sigX #<(x-<x>)^2> 
        eBeam.arStatMom2[1] = 0 #<(x-<x>)(x'-<x'>)>
        eBeam.arStatMom2[2] = sigXp*sigXp #<(x'-<x'>)^2> 
        eBeam.arStatMom2[3] = sigY*sigY #<(y-<y>)^2>
        eBeam.arStatMom2[4] = 0 #<(y-<y>)(y'-<y'>)>
        eBeam.arStatMom2[5] = sigYp*sigYp #<(y'-<y'>)^2>
        eBeam.arStatMom2[10] = sigEperE*sigEperE #<(E-<E>)^2>/<E>^2
        
        #***********Precision Parameters
        arPrecF = [0]*5 #for spectral flux vs photon energy
        arPrecF[0] = 1 #initial UR harmonic to take into account
        arPrecF[1] = precision[0] #final UR harmonic to take into account
        arPrecF[2] = precision[1] #longitudinal integration precision parameter
        arPrecF[3] = precision[2] #azimuthal integration precision parameter
        arPrecF[4] = 1 #calculate flux (1) or flux per unit surface (2)
            
        #***********UR Stokes Parameters (mesh) for Spectral Flux
        stkF = SRWLStokes() #for spectral flux vs photon energy
        stkF.allocate(energy_grid[2], 1, 1) #numbers of points vs photon energy, horizontal and vertical positions
        stkF.mesh.zStart = sampling_mesh[0] #longitudinal position [m] at which UR has to be calculated
        stkF.mesh.eStart = energy_grid[0] #initial photon energy [eV]
        stkF.mesh.eFin = energy_grid[1] #final photon energy [eV]
        stkF.mesh.xStart = sampling_mesh[1] #initial horizontal position [m]
        stkF.mesh.xFin = sampling_mesh[2] #final horizontal position [m]
        stkF.mesh.yStart = sampling_mesh[3] #initial vertical position [m]
        stkF.mesh.yFin = sampling_mesh[4] #final vertical position [m]
               
        
        #**********************Calculation (SRWLIB function calls)
        #print('   Performing Spectral Flux (Stokes parameters) calculation ... ')
        srwl.CalcStokesUR(stkF, eBeam, und, arPrecF)
        #print('done')
        
        return numpy.array(stkF.arS[0:energy_grid[2]])    
    
    def BM_spectrum(self, E, I, B, ph_energy, hor_acc_mrad=1.0):
        """
        Calculates the emitted spectrum of a Bending Magnet (vertically integrated) whithin a horizontal acceptance\n
        Units: [ph/s/0.1%bw]\n
        :E: Storage Ring energy [GeV]
        :I: Storage Ring current [A]
        :B: Magnetic Field value [T]    
        :ph_energy: Array of Photon Energies [eV]
        :hor_acc_mrad: Horizontal acceptance [mrad]
        """
        
        def bessel_f(y):
            return kv(5.0/3.0, y)    
            
        e_c = 665*(E**2)*B # eV
        y = ph_energy/e_c
        int_K53 = numpy.zeros((len(y)))
        for i in range(len(y)):
            int_K53[i] = quad(lambda x: kv(5.0/3.0, x), y[i], numpy.inf)[0]
        G1_y = y*int_K53
        BM_Flux = (2.457*1e13)*E*I*G1_y*hor_acc_mrad
        
        return BM_Flux
    
    def Wiggler_spectrum(self, E, I, B, N_periods, ph_energy, hor_acc_mrad=1.0):
        """
        Calculates the emitted spectrum of a Wiggler (vertically integrated) whithin a horizontal acceptance\n
        Units: [ph/s/0.1%bw]\n
        :E: Storage Ring energy [GeV]
        :I: Storage Ring current [A]
        :B: Magnetic Field value [T]    
        :N_periods: Number of Periods
        :ph_energy: Array of Photon Energies [eV]
        :hor_acc_mrad: Horizontal acceptance [mrad]
        """
        
        def bessel_f(y):
            return kv(5.0/3.0, y)    
            
        e_c = 665*(E**2)*B # eV
        y = ph_energy/e_c
        int_K53 = numpy.zeros((len(y)))
        for i in range(len(y)):
            int_K53[i] = quad(lambda x: kv(5.0/3.0, x), y[i], numpy.inf)[0]
        G1_y = y*int_K53
        W_Flux = (2.457*1e13)*E*I*G1_y*hor_acc_mrad*(2*N_periods)
        
        return W_Flux    
    
    def print_date_i(self):
        print('\n'+'EXECUTION BEGAN AT: ', end='')
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '\n')
    
    def print_date_f(self):
        print('\n'+'EXECUTION FINISHED AT: ', end='')
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '\n')
        
    def showFlux(self):
                
        if(self.showflux == 1):
            
            plot_ftext = 'Total Flux' + '\n  ' + self.flux_total + '\n  ' + 'ph/s/100mA' 
            eRange = numpy.max(self.En_coord) - numpy.min(self.En_coord)
            fluxRange = numpy.max(self.beamline_flux) - numpy.min(self.beamline_flux) 
            self.plot_canvas.remove(legend='fMarker', kind='marker')
            self.plot_canvas.addMarker(x=numpy.min(self.En_coord)+eRange*0.02, y=numpy.min(self.beamline_flux)+fluxRange*0.98, legend='fMarker', text=plot_ftext, color='black', selectable=True, draggable=True, symbol='none')
        
        if(self.showflux == 0):
            self.plot_canvas.remove(legend='fMarker', kind='marker')
            
    def showPower(self):

        if(self.showpower == 1):            
                
            plot_ptext = 'Total Power' + '\n  ' + self.power_total + '\n  ' + 'W/100mA'
            eRange = numpy.max(self.En_coord) - numpy.min(self.En_coord)
            fluxRange = numpy.max(self.beamline_flux) - numpy.min(self.beamline_flux) 
            self.plot_canvas.remove(legend='pMarker', kind='marker')
            self.plot_canvas.addMarker(x=numpy.min(self.En_coord)+eRange*0.02, y=numpy.min(self.beamline_flux)+fluxRange*0.85, legend='pMarker', text=plot_ptext, color='black', selectable=True, draggable=True, symbol='none')
        
        if(self.showpower == 0):
            self.plot_canvas.remove(legend='pMarker', kind='marker')

            
    def down_data(self):
        numpy.savetxt(self.output_filename, 
                      numpy.array([self.En_coord,
                                   self.histoI0,
                                   self.histoI,
                                   self.T1,
                                   self.source_spec*self.vert_acc,
                                   self.T1*self.source_spec*self.vert_acc]).T, 
                      fmt='%.8e',
                      header='Total Flux [ph/s/100mA]  \n' + self.flux_total + '\n' + 'Total Power [W/100mA] \n' + self.power_total + '\n' +
                             'Energy [eV] \
                              Source Histogram \
                              Beamline Histogram \
                              Transmission \
                              Source Spectrum [ph/s/100mA/0.1%bW] \
                              Beamline Spectrum [ph/s/100mA/0.1%bW]')       
    def down_fig(self):
        
        self.plot_canvas.saveGraph(self.fig_filename, fileFormat='png', dpi=400)
    
    def BM_vertical_acc(self, E=3.0, B=3.2, ph_energy=1915.2, div_limits=[-1.0e-3, 1.0e-3], e_beam_vert_div=0.0, plot=False):

        """
        Calculates the vertical angular flux probability density function (pdf) for \
        a Bending Magnet or Wiggler and compares it to divergence limits to calculate \
        the relative vertcal acceptance.\n
        Return: Dictionary containing vertical angular distribution, fwhm and acceptance factor (energy-dependent)  \n
        :E: Storage Ring energy [GeV]
        :B: Magnetic Field value [T]    
        :ph_energy: Photon Energy - single value or array - [eV]
        :div_limits: Divergence limits array for which acceptance must be calculated [rad]
        :e_beam_vert_div: electron beam vertical divergence sigma [rad]. Not taken into account if equal to None.
        :plot: boolean: True or False if you want the distribution to be shown.
        """
        import numpy
        from scipy.special import kv
        from scipy.integrate import simps
        
        def gaussian_pdf(x, x0, sigma): # gaussian probability density function (PDF)
            return (1/(numpy.sqrt(2*numpy.pi*sigma**2)))*numpy.exp(-(x-x0)**2/(2*sigma**2))
        
        def calc_vert_dist(e_relative):
            G = (e_relative/2.0)*(gamma_psi**(1.5))    
            K13_G = kv(1.0/3.0, G)
            K23_G = kv(2.0/3.0, G)
              
            dN_dOmega  = (1.33e13)*(E**2)*I*(e_relative**2)*(gamma_psi**2)
            dN_dOmega *= ( (K23_G**2) + (((gamma**2) * (psi**2))/(gamma_psi))*(K13_G**2) )   
            
            return dN_dOmega
        
        if(not(hasattr(ph_energy, "__len__"))): # for single energies
            ph_energy = numpy.array([ph_energy])
        
        I = 0.1 # [A] -> result independent
        gamma = E/0.51099890221e-03
        e_c = 665*(E**2)*B # [eV]    
        energy_relative = ph_energy/e_c
        
        # calculate graussian approximation to define psi mesh
        int_K53 = quad(lambda x: kv(5.0/3.0, x), energy_relative[0], numpy.inf)[0]
        K23 = kv(2.0/3.0, energy_relative[0]/2)
        vert_angle_sigma = numpy.sqrt(2*numpy.pi/3)/(gamma*energy_relative[0])*int_K53/((K23)**2)
        if(e_beam_vert_div > 0.0):
            vert_angle_sigma = numpy.sqrt(vert_angle_sigma**2 + e_beam_vert_div**2) # calculates gaussian PDF of the e-beam vertical divergence
        
        psi = numpy.linspace(-vert_angle_sigma*2, vert_angle_sigma*2, 1000) # vertical angle array
        gamma_psi = 1 + (gamma**2) * (psi**2) # factor dependent on gamma and psi
        psi_minus = numpy.abs(psi - div_limits[0]).argmin() # first psi limit index
        psi_plus = numpy.abs(psi - div_limits[1]).argmin() # second psi limit index
        
        vert_pdf = numpy.zeros((len(ph_energy), len(psi)))
        vert_acceptance = numpy.zeros((len(ph_energy)))
        lwhm = numpy.zeros((len(ph_energy)))
        rwhm = numpy.zeros((len(ph_energy)))
        fwhm = numpy.zeros((len(ph_energy)))
        
        if(e_beam_vert_div > 0.0):
            e_beam_pdf = gaussian_pdf(psi, 0, e_beam_vert_div) # calculates gaussian PDF of the e-beam vertical divergence
            
        for i in range(len(ph_energy)):
            vert_pdf[i] = calc_vert_dist(energy_relative[i]) 
            vert_pdf[i] /= simps(y=vert_pdf[i], x=psi)
            
            if(e_beam_vert_div > 0.0): # convolves radiation and e-beam angular distributions
                
                conv_dist = numpy.convolve(vert_pdf[i], e_beam_pdf, mode='same')
                conv_dist_norm = simps(y=conv_dist, x=psi)
                conv_pdf = conv_dist / conv_dist_norm # convolved PDF
                vert_pdf[i] = conv_pdf
                
            vert_acceptance[i] = simps(vert_pdf[i][psi_minus:psi_plus+1], x=psi[psi_minus:psi_plus+1])
            # calculates FWHM 
            peak = numpy.max(vert_pdf[i])
            peak_idx = numpy.abs(vert_pdf[i]-peak).argmin()
            lwhm[i] = psi[numpy.abs(vert_pdf[i][:peak_idx] - peak/2).argmin()]
            rwhm[i] = psi[numpy.abs(vert_pdf[i][peak_idx:] - peak/2).argmin() + peak_idx]
            fwhm[i] = rwhm[i] - lwhm[i]
    
       
        if(plot==True and len(vert_pdf)==1):
            from matplotlib import pyplot as plt
            plt.figure()
            plt.plot(psi*1e3, vert_pdf[0], 'C0.-')
            plt.ylabel('$Flux \ PDF$')
            plt.xlabel('$\psi \ [mrad]$')
            plt.ylim(0, numpy.max(vert_pdf)*1.1)
            plt.fill_between(psi*1e3, vert_pdf[i], where=numpy.logical_and(psi>=psi[psi_minus], psi<=psi[psi_plus]))
            plt.axvline(x=psi[psi_minus]*1e3)
            plt.axvline(x=psi[psi_plus]*1e3)
            plt.plot(lwhm*1e3, peak/2, 'C1+', markersize=12)
            plt.plot(rwhm*1e3, peak/2, 'C1+', markersize=12)
            plt.show()
            
        if(plot==True and len(vert_pdf)>1):
            from matplotlib import pyplot as plt
            plt.figure()
            plt.imshow(vert_pdf.transpose(), extent=[ph_energy[0], ph_energy[-1], psi[0]*1e3, psi[-1]*1e3], aspect='auto')
            plt.xlabel('$Energy \ [eV]$')
            plt.ylabel('$\psi \ [mrad]$')
            plt.plot(ph_energy, lwhm*1e3, '--', color='white', linewidth=1.0, alpha=0.4)
            plt.plot(ph_energy, rwhm*1e3, '--', color='white', linewidth=1.0, alpha=0.4)
            plt.axhline(y=div_limits[0]*1e3, color='gray', alpha=0.5)
            plt.axhline(y=div_limits[1]*1e3, color='gray', alpha=0.5)
            plt.minorticks_on()
            plt.ylim([-vert_angle_sigma*1.75e3, vert_angle_sigma*1.75e3])
            plt.show()
    
        output = {"Psi": psi,
                  "PDF": vert_pdf,
                  "acceptance": vert_acceptance,
                  "lwhm": lwhm,
                  "rwhm": rwhm,
                  "fwhm": fwhm}
    
        return output

        
    
   
