import sys
import time

# from orangecontrib.shadow.lnls.widgets.utility.plot import plot_beam
from optlnls.plot import plot_beam

import numpy
from PyQt5 import QtGui, QtWidgets
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import os
from scipy import ndimage

class PlotXY(AutomaticElement):

    name = "Beam Analysis"
    description = "Display beam data and calculate its properties"
    icon = "icons/beam_analysis_icon.png"
    authors = "Artur C Pinto, Sergio A Lordano Luiz, Bernd C Meyer, Luca Rebuffi"
    maintainer = "Sergio Lordano"
    maintainer_email = "sergio.lordano@lnls.br"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 640
    IMAGE_HEIGHT = 640

    want_main_area=1
    plot_canvas=None
    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(0)
    y_column_index=Setting(2)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    y_range=Setting(0)
    y_range_min=Setting(0.0)
    y_range_max=Setting(0.0)

    weight_column_index = Setting(23)
    rays=Setting(1)
    cartesian_axis=Setting(1)

#    number_of_bins=Setting(100)

#    title=Setting("X,Z")

#    keep_result=Setting(0)
    last_ticket=None

    is_conversion_active = Setting(1)

    number_of_binsX=Setting(100)
    number_of_binsY=Setting(100)
    x_cut_pos=Setting(0.0)
    y_cut_pos=Setting(0.0)    
    fitType = Setting(0)
    cut = Setting(0)
    textA = Setting(0)
    textB = Setting(0)
    textC = Setting(0)
    textD = Setting(0)
    invertXY = Setting(0)
    scale = Setting(0)
    hor_label = Setting('')
    vert_label = Setting('')
    plottitle=Setting('Title')
    output_filename = Setting('default.png')
    output_datfilename = Setting('default_histo2D.dat')
    integral = Setting('0.0')
    
    fwhm_int_ext = Setting(0)
    fwhm_oversampling = Setting(200.0)
    fwhm_threshold = Setting(0.5)
    
    plot_zeroPadding_z = Setting(0) 
    plot_zeroPadding_x = Setting(0)

    #units_definition = Setting(0) #0: mm, 1: um, 2: nm

    gaussian_filter = Setting(0)

    #export_slices = Setting(0)
    
    inten=Setting(0)
    nrays=Setting(0)
    grays=Setting(0)
    lrays=Setting(0)
    
    def __init__(self):
        super().__init__()

        gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=45)
        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Calculations Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=120)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"], labelWidth=260,
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=50)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=50)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250, 
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = oasysgui.widgetBox(tab_set, "Variables Settings", addSpace=True, orientation="vertical", height=350)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="X Column",labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: E\u03c3 X",
                                            "8: E\u03c3 Y",
                                            "9: E\u03c3 Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase \u03c3",
                                            "15: Phase \u03c0",
                                            "16: E\u03c0 X",
                                            "17: E\u03c0 Y",
                                            "18: E\u03c0 Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                            "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                            "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                            "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                            "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                            "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                            "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                            "34: Power = Intensity * Energy",
                                     ],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="X Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="Y Column",labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: E\u03c3 X",
                                            "8: E\u03c3 Y",
                                            "9: E\u03c3 Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase \u03c3",
                                            "15: Phase \u03c0",
                                            "16: E\u03c0 X",
                                            "17: E\u03c0 Y",
                                            "18: E\u03c0 Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                            "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                            "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                            "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                            "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                            "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                            "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                            "34: Power = Intensity * Energy",
                                     ],

                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_YRange()

        self.weight_column = gui.comboBox(general_box, self, "weight_column_index", label="Weight", labelWidth=70,
                                         items=["0: No Weight",
                                                "1: X",
                                                "2: Y",
                                                "3: Z",
                                                "4: X'",
                                                "5: Y'",
                                                "6: Z'",
                                                "7: E\u03c3 X",
                                                "8: E\u03c3 Y",
                                                "9: E\u03c3 Z",
                                                "10: Ray Flag",
                                                "11: Energy",
                                                "12: Ray Index",
                                                "13: Optical Path",
                                                "14: Phase \u03c3",
                                                "15: Phase \u03c0",
                                                "16: E\u03c0 X",
                                                "17: E\u03c0 Y",
                                                "18: E\u03c0 Z",
                                                "19: Wavelength",
                                                "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                                "21: Theta (angle from Y axis)",
                                                "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                                "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                                "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                                "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                                "26: |K|",
                                                "27: K X",
                                                "28: K Y",
                                                "29: K Z",
                                                "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                                "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                                "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                                "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                                "34: Power = Intensity * Energy",
                                         ],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "cartesian_axis", label="Cartesian Axis",labelWidth=300,
                                     items=["No",
                                            "Yes"],
                                     sendSelectedValue=False, orientation="horizontal")
###

#        units_box = oasysgui.widgetBox(tab_set, "Physical Units in Distribution", addSpace=True, orientation="vertical", height=60)

#        oasysgui.lineEdit(units_box, self, "integral", "Integral (e.g. Total Flux/Power)",
#                          labelWidth=250, valueType=str, orientation="horizontal")
        
        export_box = oasysgui.widgetBox(tab_set, "Export 2D Histogram", addSpace=True, orientation="vertical", height=90)

        oasysgui.lineEdit(export_box, self, "output_datfilename", "File name to save", controlWidth=180,
                          labelWidth=250, valueType=str, orientation="horizontal")
        
        gui.button(export_box, self, "Export Data", callback=self.export_histo, height=25)


#        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="horizontal", height=80)
#
#        gui.checkBox(incremental_box, self, "keep_result", "Keep Result")
#        gui.button(incremental_box, self, "Clear", callback=self.clearResults)

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=115)

        oasysgui.lineEdit(histograms_box, self, "number_of_binsX", "Number of Bins X", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(histograms_box, self, "number_of_binsY", "Number of Bins Y", labelWidth=250, valueType=int, orientation="horizontal")
        
        gui.comboBox(histograms_box, self, "is_conversion_active", label="Convert to " + u"\u03BC" + "m or " + u"\u03BC" + "rad?", labelWidth=250,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        plot_control_box = oasysgui.widgetBox(tab_gen, "Plot Controls", addSpace=True, orientation="vertical", height=440)
        
#        gui.checkBox(plot_control_box, self, "invertXY", "Invert X, Y")
        
        gui.comboBox(plot_control_box, self, "cut", label="Slices", labelWidth=250, callback=self.set_SlicePosition,
                     items=["1D histograms", "Cut at 0", "Cut at peak", "Cut at mean value", "Cut at position"], 
                     sendSelectedValue=False, orientation="horizontal")
        
        """gui.comboBox(plot_control_box, self, "units_definition", label="Units", labelWidth=250,
                     items=["mm", "um", "nm"], sendSelectedValue=False, orientation="horizontal")"""
        
        self.slice_box = oasysgui.widgetBox(plot_control_box, "", addSpace=False, orientation="vertical", height=50)
#        self.slice_box_empty = oasysgui.widgetBox(plot_control_box, "", addSpace=False, orientation="vertical", height=100)

        oasysgui.lineEdit(self.slice_box, self, "x_cut_pos", "X position to cut", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.slice_box, self, "y_cut_pos", "Y position to cut", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_SlicePosition()
        
        oasysgui.lineEdit(plot_control_box, self, "integral", "Total Flux (Power) in ph/s (W) [optional]",
                          controlWidth=70, labelWidth=300, valueType=str, orientation="horizontal")
        
        gui.comboBox(plot_control_box, self, "fitType", label="Fitting", labelWidth=250,
                     items=["None", "Gauss", "Lorentz", "Gauss-Lorentz"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "scale", label="Scale", labelWidth=250,
                     items=["Linear", "Logarithmic"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textA", label="Text 1", labelWidth=250,
                     items=["None", "Title", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "Slice Maximum", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "FIT Maximum"], 
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textB", label="Text 2", labelWidth=250,
                     items=["None", "Title", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "Slice Maximum", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "FIT Maximum"], 
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textC", label="Text 3", labelWidth=250,
                     items=["None", "Title", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "Slice Maximum", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "FIT Maximum"], 
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textD", label="Text 4", labelWidth=250,
                     items=["None", "Title", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "Slice Maximum", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "FIT Maximum"],
                     sendSelectedValue=False, orientation="horizontal")
        
        oasysgui.lineEdit(plot_control_box, self, "plottitle", "Title / Description (< 40 char)", controlWidth=180,
                          labelWidth=250, valueType=str, orientation="horizontal")
        
        oasysgui.lineEdit(plot_control_box, self, "hor_label", "Horizontal Label", controlWidth=180,
                          labelWidth=250, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(plot_control_box, self, "vert_label", "Vertical Label", controlWidth=180,
                          labelWidth=250, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(plot_control_box, self, "output_filename", "File Name to save", controlWidth=180,
                          labelWidth=250, valueType=str, orientation="horizontal")
        
        gui.button(plot_control_box, self, "Export Figure", callback=self.save_fig, height=25)
        
        adv_box = oasysgui.widgetBox(tab_gen, "Advanced Controls", addSpace=True, orientation="vertical", height=160)
        
        gui.comboBox(adv_box, self, "fwhm_int_ext", label="FWHM innermost / outermost", labelWidth=250,
                     items=["Innermost", "Outermost"], sendSelectedValue=False, orientation="horizontal")
        
        oasysgui.lineEdit(adv_box, self, "fwhm_threshold", "Threshold for FWHM (0 <-> 1)",
                          labelWidth=250, valueType=float, orientation="horizontal")
        
        oasysgui.lineEdit(adv_box, self, "fwhm_oversampling", "Oversampling factor for FWHM (>1)",
                          labelWidth=250, valueType=float, orientation="horizontal")
        
        oasysgui.lineEdit(adv_box, self, "plot_zeroPadding_z", "Zero padding Z (>0)",
                          labelWidth=250, valueType=float, orientation="horizontal")
        
        oasysgui.lineEdit(adv_box, self, "plot_zeroPadding_x", "Zero padding X (>0)",
                          labelWidth=250, valueType=float, orientation="horizontal")
        
        
        oasysgui.lineEdit(adv_box, self, "gaussian_filter", "Smooth factor - gaussian filter (>0)",
                          labelWidth=250, valueType=float, orientation="horizontal")   

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")
        
        output_box = oasysgui.widgetBox(plot_tab, "", addSpace=True, orientation="horizontal",
                                        height=650, width=2.0*self.CONTROL_AREA_WIDTH)  

        self.image_box = gui.widgetBox(output_box, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = oasysgui.textArea(height=600, width=600)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)
        
         ################### RAYS INFO ##################                     
                                   
        box_info = oasysgui.widgetBox(output_box, "Info", addSpace=True, orientation="vertical",
                                      height=600, width=0.4*self.CONTROL_AREA_WIDTH)
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

        #############################
        ### CREATE PLOT CANVAS
        #############################

        self.figure = Figure()
        self.figure.patch.set_facecolor('white')
        self.plot_canvas = FigureCanvasQTAgg(self.figure)
        self.image_box.layout().addWidget(self.plot_canvas)
        
        self.figure.set_size_inches((5,5))
               
        self.space = 0.02
        self.LTborder = 0.04
        self.RBborder = 0.15
        self.X_or_Y = 0.28 
        self.width_main = 1 - self.RBborder - self.LTborder - self.X_or_Y - self.space
    
        rect_2D = [self.LTborder + self.X_or_Y + self.space, self.RBborder, self.width_main, self.width_main]
        rect_X =  [self.LTborder + self.X_or_Y + self.space, self.RBborder + self.width_main + self.space, self.width_main, self.X_or_Y]
        rect_Y =  [self.LTborder, self.RBborder, self.X_or_Y, self.width_main]
        rect_T =  [self.LTborder, self.RBborder + self.width_main + self.space, self.X_or_Y, self.X_or_Y]
        
        self.ax2D = self.figure.add_axes(rect_2D)
        self.axX  = self.figure.add_axes(rect_X, sharex=self.ax2D)
        self.axY  = self.figure.add_axes(rect_Y, sharey=self.ax2D)
        self.axT  = self.figure.add_axes(rect_T)


    def save_fig(self):
        self.figure.savefig(self.output_filename, dpi=200)

    def export_histo(self):
        
        header  = '#2D histrogram\n'
        header += '#Z units: ' + '#Rays weighted by intensity' + '\n'
        header += '#{0:.8e}'.format(self.x_axis[0]) + '#xmin' + '\n'
        header += '#{0:.8e}'.format(self.x_axis[-1]) + '#xmax' + '\n'
        header += '#{0}'.format(len(self.x_axis)) + '#nx' + '\n'
        header += '#{0:.8e}'.format(self.z_axis[0]) + '#ymin' + '\n'
        header += '#{0:.8e}'.format(self.z_axis[-1]) + '#ymax' + '\n'
        header += '#{0}'.format(len(self.z_axis)) + '#ny' + '\n' 
        
        with open(self.output_datfilename, 'w') as outfile:
            
            outfile.write(header)
            for line in self.xz:
                for column in line:
                    outfile.write('{0:.8e}\t'.format(column))
                outfile.write('\n')
            

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)
        
    def set_SlicePosition(self):
        self.slice_box.setVisible(self.cut == 4)
#        self.slice_box_empty.setVisible(self.y_range != 4)

    def plot_results(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            
            if not ShadowCongruence.checkEmptyBeam(self.input_beam):
                return False
            
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            beam_to_plot = self.input_beam._beam
            
            info_beam = beam_to_plot.histo1(1, nolost=1)
            self.inten = ("{:.2f}".format(info_beam['intensity']))
            self.nrays = str(int(info_beam['nrays']))
            self.grays = str(int(info_beam['good_rays']))
            self.lrays = str(int(info_beam['nrays'] - info_beam['good_rays']))

            if self.image_plane == 1:
                new_shadow_beam = self.input_beam.duplicate(history=False)
                dist = 0.0

                if self.image_plane_rel_abs_position == 1:  # relative
                    dist = self.image_plane_new_position
                else:  # absolute
                    if self.input_beam.historySize() == 0:
                        historyItem = None
                    else:
                        historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                    if historyItem is None: image_plane = 0.0
                    elif self.input_beam._oe_number == 0: image_plane = 0.0
                    else: image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                    dist = self.image_plane_new_position - image_plane

                self.retrace_beam(new_shadow_beam, dist)
                beam_to_plot = new_shadow_beam._beam

            beam2D = self.read_shadow_beam(beam=beam_to_plot)
            self.analyze_beam(beam2D)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)
            return True

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception
            return False


    def get_titles(self):
        
        auto_x_title = self.x_column.currentText().split(":", 2)[1]
        auto_y_title = self.y_column.currentText().split(":", 2)[1]
        xum = auto_x_title + " "
        yum = auto_y_title + " "
        self.title = auto_x_title + "," + auto_y_title
        x = self.x_column_index + 1
        if x == 1 or x == 2 or x == 3:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "m]"
                auto_x_title = auto_x_title + " [$\mu$m]"
            else:
                xum = xum + " [" + self.workspace_units_label + "]"
                auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 4 or x == 5 or x == 6:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "rad]"
                auto_x_title = auto_x_title + " [$\mu$rad]"
            else:
                xum = xum + " [rad]"
                auto_x_title = auto_x_title + " [rad]"
        elif x == 11:
            xum = xum + "[eV]"
            auto_x_title = auto_x_title + " [eV]"
        elif x == 13:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 14:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 15:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 19:
            xum = xum + "[Å]"
            auto_x_title = auto_x_title + " [Å]"
        elif x == 20:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 21:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x >= 25 and x <= 28:
            xum = xum + "[Å-1]"
            auto_x_title = auto_x_title + " [Å-1]"
        y = self.y_column_index + 1
        if y == 1 or y == 2 or y == 3:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "m]"
                auto_y_title = auto_y_title + " [$\mu$m]"
            else:
                yum = yum + " [" + self.workspace_units_label + "]"
                auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 4 or y == 5 or y == 6:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "rad]"
                auto_y_title = auto_y_title + " [$\mu$rad]"
            else:
                yum = yum + " [rad]"
                auto_y_title = auto_y_title + " [rad]"
        elif y == 11:
            yum = yum + "[eV]"
            auto_y_title = auto_y_title + " [eV]"
        elif y == 13:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 14:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 15:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 19:
            yum = yum + "[Å]"
            auto_y_title = auto_y_title + " [Å]"
        elif y == 20:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 21:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y >= 25 and y <= 28:
            yum = yum + "[Å-1]"
            auto_y_title = auto_y_title + " [Å-1]"

        return x, y, auto_x_title, auto_y_title, xum, yum

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays, bad content, bad limits or axes",
                                           QtWidgets.QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam, dist):
            new_shadow_beam._beam.retrace(dist)

    def getConversionActive(self):
        return self.is_conversion_active==1

     
    def read_shadow_beam(self, beam):   

        histo2D = beam.histo2(col_h=self.x_column_index+1, col_v=self.y_column_index+1, nbins_h=self.number_of_binsX, nbins_v=self.number_of_binsY, nolost=self.rays, ref=self.weight_column_index)
        
        x_axis = histo2D['bin_h_center']
        z_axis = histo2D['bin_v_center']
        xz = histo2D['histogram']
                    
        XZ = numpy.zeros((self.number_of_binsY+1,self.number_of_binsX+1))
        XZ[1:,0] = z_axis
        XZ[0,1:] = x_axis
        XZ[1:,1:] = numpy.array(xz).transpose()
        
        if(self.gaussian_filter != 0):
            XZ[1:,1:] = ndimage.gaussian_filter(numpy.array(xz).transpose(), self.gaussian_filter)
        
        return XZ
            
            
    def analyze_beam(self, beam2D):

        var_x, var_y, _, _, _, _ = self.get_titles()

        ShadowPlot.set_conversion_active(self.getConversionActive())
        self.unitFactorX = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)
        self.unitFactorY = ShadowPlot.get_factor(var_y, self.workspace_units_to_cm)
                
        plot = plot_beam(
            beam2D,
            show_plot=False,
            cut=self.cut,
            textA=self.textA,
            textB=self.textB,
            textC=self.textC,
            textD=self.textD,
            outfilename=self.output_filename,
            export_slices=False, # not implemented
            fitType=self.fitType,
            overSampling=self.fwhm_oversampling,
            fwhm_zeroPadding=(self.plot_zeroPadding_x != 0 or self.plot_zeroPadding_z != 0),
            xlabel=self.hor_label if self.hor_label else self.get_titles()[2],
            ylabel=self.vert_label if self.vert_label else self.get_titles()[3],
            zlabel = '',
            units = '', #um to default, future use for other units
            unitFactorX = self.unitFactorX,
            unitFactorY = self.unitFactorY,
            plot_title=self.plottitle,
            invertXY=self.invertXY,
            scale=self.scale,
            fwhm_threshold=self.fwhm_threshold,
            fwhm_int_ext=self.fwhm_int_ext,
            x_cut_pos=self.x_cut_pos,
            y_cut_pos=self.y_cut_pos,
            x_range=(self.x_range == 1),
            y_range=(self.y_range == 1),
            x_range_min=self.x_range_min,
            x_range_max=self.x_range_max,
            y_range_min=self.y_range_min,
            y_range_max=self.y_range_max,
            integral=float(self.integral) if self.integral.replace(',', '.') else 0.0,
            zero_pad_x=self.plot_zeroPadding_x,
            zero_pad_y=self.plot_zeroPadding_z,
            figure=self.figure,
            ax2D=self.ax2D,
            axX=self.axX,
            axY=self.axY,
            axT=self.axT
        )

        self.xz = plot['xz']
        self.x_axis = plot['x_axis']
        self.z_axis = plot['z_axis']
        
        self.figure.canvas.draw()
