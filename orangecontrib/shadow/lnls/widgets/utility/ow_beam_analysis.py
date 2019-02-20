import copy
import sys
import time

import numpy
from PyQt5 import QtGui, QtWidgets
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

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
#    invertXY = Setting(0)
    fitType = Setting(0)
    cut = Setting(0)
    textA = Setting(0)
    textB = Setting(0)
    textC = Setting(0)
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
    
    plot_zeroPadding = Setting(0)
    gaussian_filter = Setting(0)
    
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
        
        gui.comboBox(histograms_box, self, "is_conversion_active", label="Is U.M. conversion active", labelWidth=250,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        plot_control_box = oasysgui.widgetBox(tab_gen, "Plot Controls", addSpace=True, orientation="vertical", height=440)
        
#        gui.checkBox(plot_control_box, self, "invertXY", "Invert X, Y")
        
        gui.comboBox(plot_control_box, self, "cut", label="Slices", labelWidth=250, callback=self.set_SlicePosition,
                     items=["1D histograms", "Cut at 0", "Cut at peak", "Cut at mean value", "Cut at position"], 
                     sendSelectedValue=False, orientation="horizontal")
        
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
                     items=["None", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "Title"], 
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textB", label="Text 2", labelWidth=250,
                     items=["None", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "Title"], 
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(plot_control_box, self, "textC", label="Text 3", labelWidth=250,
                     items=["None", "Mean Values", "Peak Values", "Data Range", "Slice FWHM", "Slice RMS", "FIT Mean", "FIT Peak", "FIT FWHM", "FIT RMS", "Title"], 
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
        
        oasysgui.lineEdit(adv_box, self, "plot_zeroPadding", "Large limits - zero padding (>0)",
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
        
#        fontsize=12
       
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
                      

    def clearResults(self):
        if ConfirmDialog.confirmed(parent=self):
            self.input_beam = None
            self.last_ticket = None

            if not self.plot_canvas is None:
                self.plot_canvas.clear()

            return True
        else:
            return False

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

    def replace_fig(self, beam, var_x, var_y,  title, xtitle, ytitle, xrange, yrange, nbins, nolost, xum, yum):

#        os.write(1, b'### Got here A ### \n')      
        beam  = self.read_shadow_beam(beam=beam)                                                               
#        os.write(1, b'### Got here B ### \n')
        
        self.analyze_beam(beam, invertXY = 0, overSampling = self.fwhm_oversampling,
                           cut=self.cut, textA=self.textA, textB=self.textB, textC=self.textC, fitType=self.fitType,
                           xlabel=self.get_titles()[2],ylabel=self.get_titles()[3], scale=self.scale)
        
#        os.write(1, b'### Got here C ### \n')
    def plot_xy(self, var_x, var_y, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_beam._beam
        
        #Collect beam info       
        info_beam = beam_to_plot.histo1(1)
        self.inten = ("{:.2f}".format(info_beam['intensity']))
        self.nrays = str(int(info_beam['nrays']))
        self.grays = str(int(info_beam['good_rays']))
        self.lrays = str(int(info_beam['nrays']-info_beam['good_rays'])) 

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

        self.unitFactorX=1.0
        self.unitFactorY=1.0
        xrange, yrange = self.get_ranges(beam_to_plot, var_x, var_y)

        self.replace_fig(beam_to_plot, var_x, var_y, title, xtitle, ytitle, xrange=xrange, yrange=yrange, nbins=100, nolost=self.rays, xum=xum, yum=yum)

    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                ShadowPlot.set_conversion_active(self.getConversionActive())

#                self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_bins, "Number of Bins")
                self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_binsX, "Number of Bins X")
                self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_binsY, "Number of Bins Y")

                x, y, auto_x_title, auto_y_title, xum, yum = self.get_titles()
              
                self.plot_xy(x, y, title='', xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

                plotted = True
            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def get_ranges(self, beam_to_plot, var_x, var_y):
        xrange = None
        yrange = None
        factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)
        factor2 = ShadowPlot.get_factor(var_y, self.workspace_units_to_cm)

        self.unitFactorX=factor1
        self.unitFactorY=factor2

        if self.x_range == 0 and self.y_range == 0:
            if self.cartesian_axis == 1:
                x_max = 0
                y_max = 0
                x_min = 0
                y_min = 0

                x, y, good_only = beam_to_plot.getshcol((var_x, var_y, 10))

                x_to_plot = copy.deepcopy(x)
                y_to_plot = copy.deepcopy(y)

                go = numpy.where(good_only == 1)
                lo = numpy.where(good_only != 1)

                if self.rays == 0:
                    x_max = numpy.array(x_to_plot[0:], float).max()
                    y_max = numpy.array(y_to_plot[0:], float).max()
                    x_min = numpy.array(x_to_plot[0:], float).min()
                    y_min = numpy.array(y_to_plot[0:], float).min()
                elif self.rays == 1:
                    x_max = numpy.array(x_to_plot[go], float).max()
                    y_max = numpy.array(y_to_plot[go], float).max()
                    x_min = numpy.array(x_to_plot[go], float).min()
                    y_min = numpy.array(y_to_plot[go], float).min()
                elif self.rays == 2:
                    x_max = numpy.array(x_to_plot[lo], float).max()
                    y_max = numpy.array(y_to_plot[lo], float).max()
                    x_min = numpy.array(x_to_plot[lo], float).min()
                    y_min = numpy.array(y_to_plot[lo], float).min()

                xrange = [x_min, x_max]
                yrange = [y_min, y_max]
        else:
            if self.x_range == 1:
                congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

                xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

            if self.y_range == 1:
                congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")

                yrange = [self.y_range_min / factor2, self.y_range_max / factor2]

        return xrange, yrange


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

####################################################################
######### BEAM ANALYSIS FUNCTIONS ##################################
####################################################################
     
    def gauss_function(self, x, a, x0, sigma):
        return a*numpy.exp(-(x-x0)**2/(2*sigma**2))
    
    def lorentz_function(self, x, a, x0, sigma):
        return a / (sigma * (1 + ((x - x0) / sigma )**2 ) )
    
    def lorentz_gauss_function(self, x, x0, a, sigma, b, gamma):
        return a*numpy.exp(-(x-x0)**2/(2*sigma**2)) + (b / (gamma * (1 + ((x - x0) / gamma )**2)))
    
    def calc_rms(self, x, f_x):
        return numpy.sqrt(numpy.sum(f_x*numpy.square(x))/numpy.sum(f_x) - (numpy.sum(f_x*x)/numpy.sum(f_x))**2)
    
    def fit_gauss(self, x, y, p0, maxfev):
    
        def gauss_function(x, a, x0, sigma):
            return a*numpy.exp(-(x-x0)**2/(2*sigma**2))
    
        try:
            popt, pcov = curve_fit(gauss_function, x, y, p0=p0, maxfev=maxfev)
            
        except ValueError:
            popt, pcov, perr = [0]*3, [0]*3, [0]*3        
            print("Could not fit data\n") 
        except RuntimeError:
            pcov = [0]*5      
            popt = p0
            print("Could not fit data\n") 
            
        perr = numpy.sqrt(numpy.diag(pcov))
        return popt, perr  
            
    def fit_lorentz(self, x, y, p0, maxfev):
    
        def lorentz_function(x, a, x0, sigma):
            return a / (sigma * (1 + ((x - x0) / sigma )**2 ) )
    
        try:
            popt, pcov = curve_fit(lorentz_function, x, y, p0=p0, maxfev=maxfev)
            
        except ValueError:
            popt, pcov = [0]*3, [0]*3        
            print("Could not fit data\n") 
        except RuntimeError:
            pcov = [0]*5      
            popt = p0
            print("Could not fit data\n") 
        
        perr = numpy.sqrt(numpy.diag(pcov))
        return popt, perr  
    
    def fit_lorentz_gauss(self, x, y, p0, maxfev):
    
        def lorentz_gauss_function(x, x0, a, sigma, b, gamma):
            return a*numpy.exp(-(x-x0)**2/(2*sigma**2)) + (b / (gamma * (1 + ((x - x0) / gamma )**2)))
    
        try:
            popt, pcov = curve_fit(lorentz_gauss_function, x, y, p0=p0, maxfev=maxfev)
            
        except ValueError:
            popt, pcov = [0]*3, [0]*3        
            print("Could not fit data\n") 
        except RuntimeError:
            pcov = [0]*5      
            popt = p0
            print("Could not fit data\n") 
        
        perr = numpy.sqrt(numpy.diag(pcov))
        return popt, perr
    
    def get_fwhm(self, x, y, oversampling=1, zero_padding=True, avg_correction=False, inmost_outmost=0, threshold=0.5, npoints=5):
        
        def add_zeros(array, n):
            aux = []
            for i in range(len(array)):
                aux.append(array[i])
            for k in range(n):
                aux.insert(0, 0)
                aux.append(0)
            return numpy.array(aux)
        
        def add_steps(array, n):
            aux = []
            step = (numpy.max(array)-numpy.min(array))/(len(array)-1)
            for i in range(len(array)):
                aux.append(array[i])
            for k in range(n):
                aux.insert(0, array[0] - (k+1)*step)
                aux.append(array[-1] + (k+1)*step)
            return numpy.array(aux)
        
        def interp_distribution(array_x,array_y,oversampling):
            dist = interp1d(array_x, array_y)
            x_int = numpy.linspace(numpy.min(array_x), numpy.max(array_x), int(len(array_x)*oversampling))
            y_int = dist(x_int)
            return x_int, y_int 
        
        
        if(oversampling > 1.0):
            array_x, array_y = interp_distribution(x, y, oversampling)
        else:
            array_x, array_y = x, y
            
        if(zero_padding):
            array_x = add_steps(x, 3)
            array_y = add_zeros(y, 3)
            
        try: 
            
            ### FIRST SEARCH (ROUGH) ###
            
            y_peak = numpy.max(array_y)
            threshold = threshold * y_peak
            idx_peak = (numpy.abs(array_y-y_peak)).argmin()
            
            if(idx_peak==0):
                left_hwhm_idx = 0
            else:
                if(inmost_outmost == 0): # INMOST
                    for i in range(idx_peak,0,-1):
                        if numpy.abs(array_y[i]-threshold)<numpy.abs(array_y[i-1]-threshold) and (array_y[i-1]-threshold)<0:
                            break                
                    left_hwhm_idx = i            
                else: # OUTMOST
                    for i in range(0,idx_peak):
                        if numpy.abs(array_y[i]-threshold)>numpy.abs(array_y[i-1]-threshold) and (array_y[i-1]-threshold)>0:
                            break                
                    left_hwhm_idx = i 
                
            if(idx_peak==len(array_y)-1):
                right_hwhm_idx = len(array_y)-1
            else:
                if(inmost_outmost == 0): # INMOST
                    for j in range(idx_peak,len(array_y)-2):
                        if numpy.abs(array_y[j]-threshold)<numpy.abs(array_y[j+1]-threshold) and (array_y[j+1]-threshold)<0:
                            break              
                    right_hwhm_idx = j
                else: # OUTMOST
                    for j in range(len(array_y)-2, idx_peak, -1):
                        if numpy.abs(array_y[j]-threshold)>numpy.abs(array_y[j+1]-threshold) and (array_y[j+1]-threshold)>0:
                            break              
                    right_hwhm_idx = j    
            
            fwhm = array_x[right_hwhm_idx] - array_x[left_hwhm_idx] 
            
            ### SECOND SEARCH (FINE) ###
#            npoints = 5 # to use for each side
            left_min = left_hwhm_idx-npoints if left_hwhm_idx-npoints >=0 else 0
            left_max = left_hwhm_idx+npoints+1 if left_hwhm_idx+npoints+1 < len(array_x) else -1
            right_min = right_hwhm_idx-npoints if right_hwhm_idx-npoints >=0 else 0
            right_max = right_hwhm_idx+npoints+1 if right_hwhm_idx+npoints+1 < len(array_x) else -1
            
#            left_fine_x, left_fine_y = interp_distribution(array_x[left_hwhm_idx-npoints: left_hwhm_idx+npoints+1], array_y[left_hwhm_idx-npoints: left_hwhm_idx+npoints+1], oversampling=int(oversampling*50))
#            right_fine_x, right_fine_y = interp_distribution(array_x[right_hwhm_idx-npoints: right_hwhm_idx+npoints+1], array_y[right_hwhm_idx-npoints: right_hwhm_idx+npoints+1], oversampling=int(oversampling*50))
            
            left_fine_x, left_fine_y = interp_distribution(array_x[left_min: left_max], array_y[left_min: left_max], oversampling=int(oversampling*50))
            right_fine_x, right_fine_y = interp_distribution(array_x[right_min: right_max], array_y[right_min: right_max], oversampling=int(oversampling*50))
            
            
            if(inmost_outmost == 0): # INMOST
                for i in range(len(left_fine_y)-1, 0, -1):
                    if numpy.abs(left_fine_y[i]-threshold)<numpy.abs(left_fine_y[i-1]-threshold) and (left_fine_y[i-1]-threshold)<0:
                            break                
                left_hwhm_idx = i 
                
                for j in range(0,len(right_fine_y)-2):
                    if numpy.abs(right_fine_y[j]-threshold)<numpy.abs(right_fine_y[j+1]-threshold) and (right_fine_y[j+1]-threshold)<0:
                        break              
                right_hwhm_idx = j
                    
            elif(inmost_outmost == 1): # OUTMOST
                for i in range(0, len(left_fine_y)-1):
                    if numpy.abs(left_fine_y[i]-threshold)<numpy.abs(left_fine_y[i+1]-threshold) and (left_fine_y[i+1]-threshold)>0:
                        break                
                left_hwhm_idx = i
                
                for j in range(len(right_fine_y)-2, 0, -1):
                    if numpy.abs(right_fine_y[j]-threshold)<numpy.abs(right_fine_y[j-1]-threshold) and (right_fine_y[j-1]-threshold)>0:
                        break              
                right_hwhm_idx = j
            
            
            fwhm = right_fine_x[right_hwhm_idx] - left_fine_x[left_hwhm_idx]               
                
            if(avg_correction):
                avg_y = (left_fine_y[left_hwhm_idx]+ right_fine_y[right_hwhm_idx])/2.0
                popt_left = numpy.polyfit(left_fine_x[left_hwhm_idx-1 : left_hwhm_idx+2], left_fine_y[left_hwhm_idx-1 : left_hwhm_idx+2] , 1) 
                popt_right = numpy.polyfit(right_fine_x[right_hwhm_idx-1 : right_hwhm_idx+2], right_fine_y[right_hwhm_idx-1 : right_hwhm_idx+2] , 1) 
                
                x_left = (avg_y-popt_left[1])/popt_left[0]
                x_right = (avg_y-popt_right[1])/popt_right[0]
                fwhm = x_right - x_left 

                return [fwhm, x_left, x_right, avg_y, avg_y]
            else:

                return [fwhm, left_fine_x[left_hwhm_idx], right_fine_x[right_hwhm_idx], left_fine_y[left_hwhm_idx], right_fine_y[right_hwhm_idx]]
#                return [fwhm, left_fine_x[left_hwhm_idx], right_fine_x[right_hwhm_idx], left_fine_y[left_hwhm_idx], right_fine_y[right_hwhm_idx], right_fine_x, right_fine_y, left_fine_x, left_fine_y]
            
        except ValueError:
            fwhm = 0.0        
            print("Could not calculate fwhm\n")   
            return [fwhm, 0, 0, 0, 0]
    
    def find_peak(self, xz):
        zmax = [0, 0]; xmax = [0, 0]
    
        for i in range(len(xz[:,0])):
            for j in range(len(xz[0,:])):
                
                if(xz[i,j] > zmax[1]):
                    zmax[0] = j
                    zmax[1] = xz[i,j]
                                    
                if(xz[i,j] > xmax[1]):
                    xmax[0] = i
                    xmax[1] = xz[i,j]
                    
        return xmax, zmax


    def read_shadow_beam(self, beam):   

        histo2D = beam.histo2(col_h=self.x_column_index+1, col_v=self.y_column_index+1, nbins_h=self.number_of_binsX, nbins_v=self.number_of_binsY, nolost=self.rays, ref=self.weight_column_index)
        
        x_axis = histo2D['bin_h_center']
        z_axis = histo2D['bin_v_center']
        xz = histo2D['histogram']
        
        if(self.plot_zeroPadding==0):
            
            XZ = numpy.zeros((self.number_of_binsY+1,self.number_of_binsX+1))
            XZ[1:,0] = z_axis
            XZ[0,1:] = x_axis
            XZ[1:,1:] = numpy.array(xz).transpose()
            
            if(self.gaussian_filter != 0):
                XZ[1:,1:] = ndimage.gaussian_filter(numpy.array(xz).transpose(), self.gaussian_filter)
            
        else:

            x_step = x_axis[1]-x_axis[0]
            z_step = z_axis[1]-z_axis[0]
            fct = self.plot_zeroPadding
            XZ = numpy.zeros((self.number_of_binsY+15, self.number_of_binsX+15))
            XZ[8:self.number_of_binsY+8,0] = z_axis
            XZ[0,8:self.number_of_binsX+8] = x_axis
            XZ[8:self.number_of_binsY+8,8:self.number_of_binsX+8] = numpy.array(xz).transpose()
            
            XZ[1,0] = numpy.min(z_axis) - (numpy.max(z_axis) - numpy.min(z_axis))*fct
            XZ[2:-1,0] = numpy.linspace(z_axis[0] - 6*z_step, z_axis[-1] + 6*z_step, self.number_of_binsY+12)
            XZ[-1,0] = numpy.max(z_axis) + (numpy.max(z_axis) - numpy.min(z_axis))*fct
            
            XZ[0,1] = numpy.min(x_axis) - (numpy.max(x_axis) - numpy.min(x_axis))*fct
            XZ[0,2:-1] = numpy.linspace(x_axis[0] - 6*x_step, x_axis[-1] + 6*x_step, self.number_of_binsX+12)
            XZ[0,-1] = numpy.max(x_axis) + (numpy.max(x_axis) - numpy.min(x_axis))*fct
            
            if(self.gaussian_filter != 0):
                XZ[3:self.number_of_binsY+3,3:self.number_of_binsX+3] = ndimage.gaussian_filter(numpy.array(xz).transpose(), self.gaussian_filter)
        
        return XZ
    
    def set_ticks_size(self, ax, fontsize):
        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(fontsize)
        for tick in ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(fontsize)
            
    def analyze_beam(self, beam2D, cut=0, textA=0, textB=0, textC=0, fitType=0, 
                     overSampling=200.0, zeroPadding=False, 
                     unitFactor=1.0, xlabel='X', ylabel='Z', units='', 
                     invertXY=False, scale=0, showPlot=False):
        
        if(invertXY):        
            z_axis = beam2D[0,1:]*self.unitFactorY
            x_axis = beam2D[1:,0]*self.unitFactorY        
            xz = numpy.array(beam2D[1:,1:]).transpose()
        
        else:       
            z_axis = numpy.array(beam2D[1:,0]*self.unitFactorY)
            x_axis = numpy.array(beam2D[0,1:]*self.unitFactorX)
            xz = numpy.array(beam2D[1:,1:])
            
        if(float(self.integral) > 0.0):
            rays_integral = numpy.sum(xz) * (x_axis[int(len(x_axis)/2 + 1)]-x_axis[int(len(x_axis)/2)]) * (z_axis[int(len(z_axis)/2 + 1)]-z_axis[int(len(z_axis)/2)])
            xz = xz / rays_integral # probability density function (integral equal to 1)
            xz = xz * float(self.integral) # distribution in physical units [unit = unit[integral] / (unit[x_azis] * unit[z_axis])] 
        #os.write(1, b'### Got here 2 ### \n')

        x_cut_coord = 0.0
        z_cut_coord = 0.0
       
        # FIND MEAN VALUE
        z_int = numpy.array([numpy.sum(xz[i,1:]) for i in range(len(z_axis))])
        x_int = numpy.array([numpy.sum(xz[1:,j]) for j in range(len(x_axis))])
        z_mean = numpy.average(z_axis, weights=z_int)
        x_mean = numpy.average(x_axis, weights=x_int)
#        os.write(1, b'### Got here 3 ### \n')
        # FIND PEAK VALUES
        xmax, zmax = self.find_peak(xz)
        
        if(cut==0): # PLOT INTEGRATED DISTRIBUTION
            z_cut = numpy.array([numpy.sum(xz[i,1:]) for i in range(len(z_axis))])*(x_axis[int(len(x_axis)/2 + 1)]-x_axis[int(len(x_axis)/2)])
            x_cut = numpy.array([numpy.sum(xz[1:,j]) for j in range(len(x_axis))])*(z_axis[int(len(z_axis)/2 + 1)]-z_axis[int(len(z_axis)/2)])
            
        elif(cut==1): # PLOT CUT AT ZERO
            z_cut = xz[:, numpy.abs(x_axis).argmin()]
            x_cut = xz[numpy.abs(z_axis).argmin(), :]
        
        elif(cut==2): # PLOT CUT AT PEAK
            x_cut_coord = x_axis[zmax[0]]
            z_cut_coord = z_axis[xmax[0]]
            z_cut = xz[:, zmax[0]]
            x_cut = xz[xmax[0], :]

        elif(cut==3): # PLOT CUT AT MEAN VALUE OF INTEGRATED DISTRIBUTION
            x_cut_coord = x_axis[numpy.abs(x_axis-x_mean).argmin()]
            z_cut_coord = z_axis[numpy.abs(z_axis-z_mean).argmin()]
            z_cut = xz[:, numpy.abs(x_axis-x_mean).argmin()]
            x_cut = xz[numpy.abs(z_axis-z_mean).argmin(), :]
            
        elif(cut==4): # PLOT CUT AT CUSTOM VALUES
            x_cut_coord = x_axis[numpy.abs(x_axis-self.x_cut_pos).argmin()]
            z_cut_coord = z_axis[numpy.abs(z_axis-self.y_cut_pos).argmin()]
            z_cut = xz[:, numpy.abs(x_axis-self.x_cut_pos).argmin()]
            x_cut = xz[numpy.abs(z_axis-self.y_cut_pos).argmin(), :]
            pass
        
#        os.write(1, b'### Got here 4 ### \n')
        z_cut_rms = self.calc_rms(z_axis, z_cut)
        x_cut_rms = self.calc_rms(x_axis, x_cut)
        
        if(self.plot_zeroPadding != 0):
            z_cut_fwhm = self.get_fwhm(z_axis, z_cut, oversampling=overSampling, zero_padding=False, avg_correction=False, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext, npoints=1)
            x_cut_fwhm = self.get_fwhm(x_axis, x_cut, oversampling=overSampling, zero_padding=False, avg_correction=False, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext, npoints=1)
        else:
            z_cut_fwhm = self.get_fwhm(z_axis, z_cut, oversampling=overSampling, zero_padding=True, avg_correction=False, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
            x_cut_fwhm = self.get_fwhm(x_axis, x_cut, oversampling=overSampling, zero_padding=True, avg_correction=False, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
        
            # ==================================================================== #
        # === FITTING DISTRIBUTIONS ========================================== #
        # ==================================================================== #
        
        if(fitType != 0):
            
            if(fitType==1):
    
                popt_z_cut, perr_z_cut = self.fit_gauss(z_axis, z_cut, [numpy.max(z_cut), z_mean, z_cut_rms], 10000)
                z_cut_fit = self.gauss_function(z_axis, popt_z_cut[0], popt_z_cut[1], popt_z_cut[2])
                        
                popt_x_cut, perr_x_cut = self.fit_gauss(x_axis, x_cut, [numpy.max(x_cut), x_mean, x_cut_rms], 10000)
                x_cut_fit = self.gauss_function(x_axis, popt_x_cut[0], popt_x_cut[1], popt_x_cut[2])
                
            elif(fitType==2):
    
                poptl_z_cut, perrl_z_cut = self.fit_lorentz(z_axis, z_cut, [numpy.max(z_cut), z_mean, z_cut_rms], 10000)
                z_cut_fit = self.lorentz_function(z_axis, poptl_z_cut[0], poptl_z_cut[1], poptl_z_cut[2])
                
                poptl_x_cut, perrl_x_cut = self.fit_lorentz(x_axis, x_cut, [numpy.max(x_cut), x_mean, x_cut_rms], 10000)
                x_cut_fit = self.lorentz_function(x_axis, poptl_x_cut[0], poptl_x_cut[1], poptl_x_cut[2])
    
            elif(fitType==3):

                poptlg_z_cut, perrlg_z_cut = self.fit_lorentz_gauss(z_axis, z_cut, [z_mean, numpy.max(z_cut), z_cut_rms, numpy.max(z_cut), z_cut_rms], 10000)
                z_cut_fit = self.lorentz_gauss_function(z_axis, poptlg_z_cut[0], poptlg_z_cut[1], poptlg_z_cut[2], poptlg_z_cut[3], poptlg_z_cut[4])
        
                poptlg_x_cut, perrlg_x_cut = self.fit_lorentz_gauss(x_axis, x_cut, [x_mean, numpy.max(x_cut), x_cut_rms, numpy.max(x_cut), x_cut_rms], 10000)
                x_cut_fit = self.lorentz_gauss_function(x_axis, poptlg_x_cut[0], poptlg_x_cut[1], poptlg_x_cut[2], poptlg_x_cut[3], poptlg_x_cut[4])
          
            if(self.plot_zeroPadding != 0):
                z_cut_fit_fwhm = self.get_fwhm(z_axis, z_cut_fit, oversampling=overSampling, zero_padding=False, avg_correction=True, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
                x_cut_fit_fwhm = self.get_fwhm(x_axis, x_cut_fit, oversampling=overSampling, zero_padding=False, avg_correction=True, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
            else:
                z_cut_fit_fwhm = self.get_fwhm(z_axis, z_cut_fit, oversampling=overSampling, zero_padding=True, avg_correction=True, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
                x_cut_fit_fwhm = self.get_fwhm(x_axis, x_cut_fit, oversampling=overSampling, zero_padding=True, avg_correction=True, threshold=self.fwhm_threshold, inmost_outmost=self.fwhm_int_ext)
            
            z_cut_fit_rms = self.calc_rms(z_axis, z_cut_fit)
            x_cut_fit_rms = self.calc_rms(x_axis, x_cut_fit)
            
#        os.write(1, b'### Got here 5 ### \n')
        # ==================================================================== #
        # === PLOTTING DATA ================================================== #
        # ==================================================================== #
    
#        
        fontsize=12
#       
        self.ax2D.clear()
        self.axX.clear()
        self.axY.clear()
        self.axT.clear()

        self.axY.invert_xaxis()
        # Adjust Ticks
        self.axX.xaxis.set_major_locator(plt.MaxNLocator(5))
        self.axY.xaxis.set_major_locator(plt.MaxNLocator(2))
        self.axY.yaxis.set_major_locator(plt.MaxNLocator(5))
        self.axX.minorticks_on()
        self.axY.minorticks_on()
        self.ax2D.minorticks_on()
        
        self.set_ticks_size(self.axX, fontsize)
        self.set_ticks_size(self.axY, fontsize)
        self.set_ticks_size(self.ax2D, fontsize)
            
        self.axX.xaxis.set_tick_params(which='both', direction='in', top=True, bottom=True, labelbottom=False)
        self.axX.yaxis.set_tick_params(which='both', direction='in', top=True, bottom=True, labelleft=False, labelright=True, labelsize=fontsize)
        self.axX.yaxis.set_tick_params(which='both', direction='in', left=True, right=True)
        self.axY.yaxis.set_tick_params(which='both', direction='in', left=True, right=True, labelleft=False, labelright=False)
        self.axY.xaxis.set_tick_params(which='both', direction='in', top=True, bottom=True)
        self.ax2D.yaxis.set_label_position("right")
        self.ax2D.tick_params(axis='both', which='both', direction='out', left=True,top=True,right=True,bottom=True,labelleft=False,labeltop=False, labelright=True,labelbottom=True, labelsize=fontsize)#, width=1.3)
        self.axT.tick_params(axis='both',which='both',left=False,top=False,right=False,bottom=False,labelleft=False,labeltop=False, labelright=False,labelbottom=False)
        
        
        self.axX.grid(which='both', alpha=0.2, linewidth=0.3)
        self.axY.grid(which='both', alpha=0.2, linewidth=0.3)
        
        # Write Labels
        if(self.hor_label != ''):
            self.ax2D.set_xlabel(self.hor_label, fontsize=fontsize)
        else:    
            self.ax2D.set_xlabel(xlabel + ' ' + units, fontsize=fontsize)
            
        if(self.vert_label != ''):
            self.ax2D.set_ylabel(self.vert_label, fontsize=fontsize)
        else:
            self.ax2D.set_ylabel(ylabel + ' ' + units, fontsize=fontsize)
            
        # Plots data    
        if(scale==0):
            self.ax2D.pcolormesh(x_axis, z_axis, xz) # 2D data
            
        elif(scale==1):
            # If there is a negative or zero number, it will be replaced by half minimum value higher than 0.
            if(numpy.min(xz) <= 0.0):
                xz_min_except_0 = numpy.min(xz[xz>0])
                xz[xz<=0.0] = xz_min_except_0/2.0
                self.ax2D.pcolormesh(x_axis, z_axis, xz, norm=LogNorm(vmin=xz.min(), vmax=xz.max()))
    
            else:
                self.ax2D.pcolormesh(x_axis, z_axis, xz, norm=LogNorm(vmin=xz.min(), vmax=xz.max()))
            
            self.axX.set_yscale('log')
            self.axY.set_xscale('log')
        
        self.ax2D.axvline(x=x_cut_coord, color='k', linestyle='--', alpha=0.1)
        self.ax2D.axhline(y=z_cut_coord, color='k', linestyle='--', alpha=0.1)
        self.axX.axvline(x=x_cut_coord, color='k', linestyle='--', alpha=0.1)
        self.axY.axhline(y=z_cut_coord, color='k', linestyle='--', alpha=0.1)
        
        ###### TESTING ####
#        def interp_distribution(array_x,array_y,oversampling):
#            dist = interp1d(array_x, array_y)
#            x_int = numpy.linspace(numpy.min(array_x), numpy.max(array_x), int(len(array_x)*oversampling))
#            y_int = dist(x_int)
#            return x_int, y_int 
#        
#        x_axis, x_cut = interp_distribution(x_axis, x_cut, oversampling=overSampling)
#        z_axis, z_cut = interp_distribution(z_axis, z_cut, oversampling=overSampling)
        
#        self.axX.plot(x_axis, x_cut, 'o-C0', markersize=6)
#        self.axY.plot(z_cut, z_axis, 'o-C0', markersize=6)
#        self.axX.plot(x_cut_fwhm[5], x_cut_fwhm[6], 'oC2', markersize=4) # Refined array for FWHM calc
#        self.axX.plot(x_cut_fwhm[7], x_cut_fwhm[8], 'oC2', markersize=4) # Refined array for FWHM calc
        
        self.axX.plot(x_axis, x_cut, '-C0')
        self.axY.plot(z_cut, z_axis, '-C0')
        self.axX.plot([x_cut_fwhm[1], x_cut_fwhm[2]], [x_cut_fwhm[3], x_cut_fwhm[4]], '+C0', markersize=12) # FWHM marks
        self.axY.plot([z_cut_fwhm[3], z_cut_fwhm[4]], [z_cut_fwhm[1], z_cut_fwhm[2]], '+C0', markersize=12) # FWHM marks

        if(fitType != 0):        
            
            self.axX.plot(x_axis, x_cut_fit, 'C1--')
            self.axY.plot(z_cut_fit, z_axis, 'C1--')
            self.axX.plot([x_cut_fit_fwhm[1], x_cut_fit_fwhm[2]], [x_cut_fit_fwhm[3], x_cut_fit_fwhm[4]], '+C1', markersize=12) # FWHM marks
            self.axY.plot([z_cut_fit_fwhm[3], z_cut_fit_fwhm[4]], [z_cut_fit_fwhm[1], z_cut_fit_fwhm[2]], '+C1', markersize=12) # FWHM marks
#        os.write(1, b'### Got here 3 ### \n')
        
        # Defines limits
        if(self.x_range != 0):
            self.ax2D.set_xlim(self.x_range_min, self.x_range_max)
            self.axX.set_xlim(self.x_range_min, self.x_range_max)
        else:
            self.ax2D.set_xlim(x_axis[0],x_axis[-1])

            
        
        if(self.y_range != 0):
            self.ax2D.set_ylim(self.y_range_min, self.y_range_max)
            self.axY.set_ylim(self.y_range_min, self.y_range_max)
        else:
            self.ax2D.set_ylim(z_axis[0],z_axis[-1])

       
        # Updating Y limits
#        self.axX.set_ylim(numpy.min(x_cut) - (numpy.max(x_cut)-numpy.min(x_cut))/10, numpy.max(x_cut) + (numpy.max(x_cut)-numpy.min(x_cut))/10)
#        self.axY.set_xlim(numpy.max(z_cut) + (numpy.max(z_cut)-numpy.min(z_cut))/10, numpy.min(z_cut) - (numpy.max(z_cut)-numpy.min(z_cut))/10)
        
        self.axX.set_ylim(0 - (numpy.max(x_cut)-numpy.min(x_cut))/10, numpy.max(x_cut) + (numpy.max(x_cut)-numpy.min(x_cut))/10)
        self.axY.set_xlim(numpy.max(z_cut) + (numpy.max(z_cut)-numpy.min(z_cut))/10, 0 - (numpy.max(z_cut)-numpy.min(z_cut))/10)
        
        
        hor_label = 'X'
        vert_label = 'Y'
        
        # MEAN COORDINATES    
        text1  = hor_label+' MEAN = {0:.3f}\n'.format(x_mean)
        text1 += vert_label+' MEAN = {0:.3f}\n\n'.format(z_mean)
        
        # PEAK COORDINATES
        text2  = hor_label+' PEAK = {0:.3f}\n'.format(x_axis[zmax[0]])
        text2 += vert_label+' PEAK = {0:.3f}\n'.format(z_axis[xmax[0]])

        # DATA RANGE
        text3  = hor_label+' RANGE = {0:.3f}\n'.format(x_axis[-1] - x_axis[0])
        text3 += vert_label+' RANGE = {0:.3f}\n'.format(z_axis[-1] - z_axis[0])

        # CUT FWHM
        text4  = hor_label+' FWHM = {0:.3f}\n'.format(x_cut_fwhm[0])
        text4 += vert_label+' FWHM = {0:.3f}\n'.format(z_cut_fwhm[0])
        
        # CUT RMS
        text5  = hor_label+' RMS = {0:.3f}\n'.format(x_cut_rms)
        text5 += vert_label+' RMS = {0:.3f}\n'.format(z_cut_rms)
        
        text6 = ''; text7 = ''; text8 = ''; text9 = ''; # IF FIT IS DISABLED
        
        if(fitType != 0):
            
            # MEAN COORDINATES
            text6  = hor_label+' MEAN = {0:.3f}\n'.format(numpy.average(x_axis, weights=x_cut_fit))
            text6 += vert_label+' MEAN = {0:.3f}\n'.format(numpy.average(z_axis, weights=z_cut_fit))
            
            # PEAK COORDINATES
            text7  = hor_label+' PEAK = {0:.3f}\n'.format(x_axis[numpy.abs(x_cut_fit - numpy.max(x_cut_fit)).argmin()])
            text7 += vert_label+' PEAK = {0:.3f}\n'.format(z_axis[numpy.abs(z_cut_fit - numpy.max(z_cut_fit)).argmin()])
            
            # CUT FIT FWHM
            text8  = hor_label+' FWHM = {0:.3f}\n'.format(x_cut_fit_fwhm[0])
            text8 += vert_label+' FWHM = {0:.3f}\n'.format(z_cut_fit_fwhm[0])
            
            # CUT FIT RMS
            text9  = hor_label+' RMS = {0:.3f}\n'.format(x_cut_fit_rms)
            text9 += vert_label+' RMS = {0:.3f}\n'.format(z_cut_fit_rms)
        
        #TITLE
        if(len(self.plottitle) <= 20):
            text10 = self.plottitle
        else:
            text10 = self.plottitle[:20] + '\n' + self.plottitle[20:41]
                
        def text(x):
            return {
                1 : [text1, 'C0'],
                2 : [text2, 'C0'],
                3 : [text3, 'C0'],
                4 : [text4, 'C0'],
                5 : [text5, 'C0'],
                6 : [text6, 'C1'],
                7 : [text7, 'C1'],
                8 : [text8, 'C1'],
                9 : [text9, 'C1'],
                10 : [text10, 'black']
            }.get(x, ['', ''])       
        
        [text_box1, color1] = text(textA)
        [text_box2, color2] = text(textB)        
        [text_box3, color3] = text(textC)        
 
        self.xz = xz
        self.x_axis = x_axis
        self.z_axis = z_axis    
    
        self.axT.text(self.LTborder + 0.02, self.RBborder + self.width_main + self.space + self.X_or_Y - 0.05, text_box1, color=color1, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=10, transform= self.axT.transAxes)
        self.axT.text(self.LTborder + 0.02, self.RBborder + self.width_main + self.space + self.X_or_Y - 0.35, text_box2, color=color2, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=10, transform= self.axT.transAxes)
        self.axT.text(self.LTborder + 0.02, self.RBborder + self.width_main + self.space + self.X_or_Y - 0.65, text_box3, color=color3, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=10, transform= self.axT.transAxes)
            
        self.figure.canvas.draw()
        



