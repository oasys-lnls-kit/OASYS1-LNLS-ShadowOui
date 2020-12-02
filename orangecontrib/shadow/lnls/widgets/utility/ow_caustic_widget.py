# -*- coding: utf-8 -*-

import os

import sys
import time
#import numpy
import h5py
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream, TTYGrabber
from oasys.widgets import congruence
from silx.gui.plot.Colormap import Colormap
from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QPalette, QColor, QFont

import orangecanvas.resources as resources
from orangecontrib.shadow.lnls.widgets.gui.ow_lnls_shadow_widget_c import LNLSShadowWidgetC
from orangecontrib.shadow.util.shadow_objects import ShadowBeam
import Shadow.ShadowTools as st
from orangecontrib.shadow.util.shadow_util import ShadowCongruence


    
class CausticWidget(LNLSShadowWidgetC):
    name = "Caustic"
    description = "Caustic widget"
    icon = "icons/caustic_icon.png"
    authors = "Sergio A Lordano Luiz, Artur C Pinto, Bernd C Meyer, Luca Rebuffi"
    maintainer_email = "sergio.lordano@lnls.br"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read", "caustic"]

    inputs = [("Input Beam", ShadowBeam, "set_beam")]

    IMAGE_WIDTH = 600
    IMAGE_HEIGHT = 350
    
    want_main_area=1
    
    auto_xy_ranges = Setting(0)
    x_column_index = Setting(0)
    y_column_index = Setting(2)
    weight_column_index = Setting(23)
    x_range_min = Setting(-0.010)
    x_range_max = Setting(+0.010)
    x_nbins = Setting(200)
    x_pixel = Setting(1)
    y_range_min = Setting(-0.010)
    y_range_max = Setting(+0.010)
    y_nbins = Setting(200)
    y_pixel = Setting(1)
    z_range_min = Setting(-5.0)
    z_range_max = Setting(+5.0)
    z_step = Setting(0.1)
    nz = Setting(101)
    z_offset = Setting(0.0)
    save_filename = Setting('caustic_to_save.h5')
    load_filename = Setting('caustic_to_load.h5')
    
    x_units = Setting(1)
    y_units = Setting(1)
    z_units = Setting(1)
    x_cut_position = Setting(0)
    y_cut_position = Setting(0)    
    z_cut_position = Setting(0)    
    plot2D_x_range_min = Setting(0.0)
    plot2D_x_range_max = Setting(0.0)
    plot2D_y_range_min = Setting(0.0)
    plot2D_y_range_max = Setting(0.0)
    plot2D_z_range_min = Setting(0.0)
    plot2D_z_range_max = Setting(0.0)    
    plot2D_z_range_minXZ = Setting(0.0)
    plot2D_z_range_maxXZ = Setting(0.0)    
    plot2D_z_range_minYZ = Setting(0.0)
    plot2D_z_range_maxYZ = Setting(0.0)    
    scale = Setting(0)
    quick_preview = Setting(1)
    
    def __init__(self):
        super().__init__()
        
        ############### CONTROL AREA #####################        
        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)
        

#        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)        
#        self.tabs_setting.setFixedHeight(550)
        

        ### Tabs inside control area ###
        tab1 = oasysgui.createTabPage(self.tabs_setting, "Run Options", height=840)
        tab2 = oasysgui.createTabPage(self.tabs_setting, "Plot Options" )


        ### Run Options Tab
        gui.button(tab1, self, "Run Caustic", callback=self.run_caustic, height=35,width=100)
        general_box = oasysgui.widgetBox(tab1, "Variables Settings", addSpace=True, orientation="vertical", height=380)

        gui.checkBox(general_box, self, "auto_xy_ranges", "Internal Calculated X,Y Ranges", callback=self.calc_rangesXY)

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


        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        self.le_x_range_min = oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_x_range_max = oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_nbins", "Number of Bins X", callback=self.nx_to_step, labelWidth=220, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_pixel", "Pixel Size X", callback=self.step_to_nx, labelWidth=220, valueType=float, orientation="horizontal")
        

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


        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_nbins", "Number of Bins Y", callback=self.ny_to_step, labelWidth=220, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_pixel", "Pixel Size Y", callback=self.step_to_ny, labelWidth=220, valueType=float, orientation="horizontal")

        self.weight_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=30)
        self.weight_column = gui.comboBox(self.weight_box, self, "weight_column_index", label="Weight", labelWidth=70,
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
       
        caustic_box = oasysgui.widgetBox(tab1, "Caustic Settings", addSpace=True, orientation="vertical", height=220)        

        self.zrange_box = oasysgui.widgetBox(caustic_box, "", addSpace=True, orientation="vertical", height=180)
        oasysgui.lineEdit(self.zrange_box, self, "z_range_min", "Z Min [mm]", callback=self.step_and_nz, labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zrange_box, self, "z_range_max", "Z Max [mm]", callback=self.step_and_nz, labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zrange_box, self, "z_step", "Z Step [mm]", callback=self.step_to_nz, labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zrange_box, self, "nz", "Z Number of Points", callback=self.nz_to_step, labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.zrange_box, self, "z_offset", "Z Offset", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zrange_box, self, "save_filename", "HDF5 File Name", labelWidth=120, valueType=str, orientation="horizontal")
        
        ### 2D Plot Options Tab
#        button_box1 = oasysgui.widgetBox(tab2, "", addSpace=True, orientation="vertical", height=68, width=150)
#        button_box2 = oasysgui.widgetBox(tab2, "", addSpace=True, orientation="vertical", height=68, width=150)
#        gui.button(button_box1, self, "Load and Refresh", callback=self.load_and_refresh, height=28, width=140)
#        gui.button(button_box2, self, "Save 2D Plots", callback=self.save_2D_plots, height=28, width=140)

        self.options2D_box = oasysgui.widgetBox(tab2, "Read File", addSpace=True, orientation="vertical", height=160)

        gui.checkBox(self.options2D_box, self, "quick_preview", "Plot Quick Preview")

        button_file_box = oasysgui.widgetBox(self.options2D_box, "", addSpace=False, orientation="horizontal")
        self.le_load_filename = oasysgui.lineEdit(button_file_box, self, "load_filename", "HDF5 File Name (.h5)", 
                                                  controlWidth=160, labelWidth=160, valueType=str, orientation="horizontal")
        button_file = gui.button(button_file_box, self, u"\U0001F50D", callback=self.selectOptimizeFile)
        button_file.setFixedWidth(40)
        
        button_box = oasysgui.widgetBox(self.options2D_box, "", addSpace=False, orientation="horizontal")

        button1 = gui.button(button_box, self, "Load and Refresh", callback=self.load_and_refresh)
        font = QFont(button1.font())
        font.setBold(True)
        button1.setFont(font)
        palette = QPalette(button1.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button1.setPalette(palette) # assign new palette
        button1.setFixedHeight(28)
        button1.setFixedWidth(180)

        button2 = gui.button(button_box, self, "Save 2D Plots", callback=self.save_2D_plots)
        font = QFont(button2.font())
        font.setBold(True)
        button2.setFont(font)
        palette = QPalette(button2.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Green'))
        button2.setPalette(palette) # assign new palette
        button2.setFixedHeight(28)
        button2.setFixedWidth(180)

        button_box2 = oasysgui.widgetBox(self.options2D_box, "", addSpace=False, orientation="vertical")

        button3 = gui.button(button_box2, self, "Launch 3D Visualization", callback=self.launch_mayavi)
        font = QFont(button3.font())
        font.setBold(True)
        button3.setFont(font)
        palette = QPalette(button3.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button3.setPalette(palette) # assign new palette
        button3.setFixedHeight(28)
        button3.setFixedWidth(364)


        
#        gui.button(self.options2D_box, self, "Refresh Plots ", callback=self.refresh2D, height=25, width=150)
#        gui.separator(self.options2D_box, 10)
        
        self.options2D_box0 = oasysgui.widgetBox(tab2, "User Units", addSpace=True, orientation="vertical", height=140)
        gui.comboBox(self.options2D_box0, self, "x_units", label="X units", labelWidth=260,
                     items=["mm", "\u00B5m", "nm"], sendSelectedValue=False, orientation="horizontal")
        gui.comboBox(self.options2D_box0, self, "y_units", label="Y units", labelWidth=260,
                     items=["mm", "\u00B5m", "nm"], sendSelectedValue=False, orientation="horizontal")
        gui.comboBox(self.options2D_box0, self, "z_units", label="Z units", labelWidth=260,
                     items=["m", "mm", "\u00B5m", "nm"], sendSelectedValue=False, orientation="horizontal")
        gui.comboBox(self.options2D_box0, self, "scale", label="Colormap Scale", labelWidth=260,
                     items=["linear", "logarithmic"], sendSelectedValue=False, orientation="horizontal")
        
        self.options2D_box1 = oasysgui.widgetBox(tab2, "Slice Coordinates (in User Units)", addSpace=True, orientation="vertical", height=125)
        
        oasysgui.lineEdit(self.options2D_box1, self, "y_cut_position", "Y position for Hor. slice", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.options2D_box1, self, "x_cut_position", "X position for Vert. slice", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.options2D_box1, self, "z_cut_position", "Z position for Transversal slice", labelWidth=260, valueType=float, orientation="horizontal")
        
        self.options2D_box2 = oasysgui.widgetBox(tab2, "Ranges for 2D Plots (in User Units)", addSpace=True, orientation="vertical", height=125)
        
        xrange_box = oasysgui.widgetBox(self.options2D_box2, "", addSpace=True, orientation="horizontal", height=25)
        oasysgui.lineEdit(xrange_box, self, "plot2D_x_range_min", "X Min", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(xrange_box, self, "plot2D_x_range_max", "X Max", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
#        gui.separator(self.options2D_box2, 5)

        yrange_box = oasysgui.widgetBox(self.options2D_box2, "", addSpace=True, orientation="horizontal", height=25)
        oasysgui.lineEdit(yrange_box, self, "plot2D_y_range_min", "Y Min", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(yrange_box, self, "plot2D_y_range_max", "Y Max", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
#        gui.separator(self.options2D_box2, 5)

        zrange_box1 = oasysgui.widgetBox(self.options2D_box2, "", addSpace=True, orientation="horizontal", height=25)
        oasysgui.lineEdit(zrange_box1, self, "plot2D_z_range_min", "Z Min", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zrange_box1, self, "plot2D_z_range_max", "Z Max", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
#        gui.separator(self.options2D_box2, 10)
#        gui.separator(self.options2D_box2, 10)
#        gui.separator(self.options2D_box2, 10)
        
        self.options2D_box3 = oasysgui.widgetBox(tab2, "Ranges for fitting (in User Units)", addSpace=True, orientation="vertical", height=95)
        
        zrange_box2 = oasysgui.widgetBox(self.options2D_box3, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(zrange_box2, self, "plot2D_z_range_minXZ", "Z Min (XZ fit)", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zrange_box2, self, "plot2D_z_range_maxXZ", "Z Max (XZ fit)", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
#        gui.separator(self.options2D_box2, 5)
        
        zrange_box3 = oasysgui.widgetBox(self.options2D_box3, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(zrange_box3, self, "plot2D_z_range_minYZ", "Z Min (YZ fit)", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zrange_box3, self, "plot2D_z_range_maxYZ", "Z Max (YZ fit)", labelWidth=100, controlWidth=60, valueType=float, orientation="horizontal")
        
        
        ############### MAIN AREA #####################
        
        self.tabs_plots = oasysgui.tabWidget(self.mainArea)
        self.tabs_plots.setFixedWidth(3*self.CONTROL_AREA_WIDTH)  
#        self.tabs_plots.setFixedWidth(800)       

        ### Tabs Inside the main area ###
        tab3 = oasysgui.createTabPage(self.tabs_plots, "2D Visualization")
        tab4 = oasysgui.createTabPage(self.tabs_plots, "2D Analysis" )
#        tab5 = oasysgui.createTabPage(self.tabs_plots, "3D Visualization")
      
      
        ### Area for 2D plots    
        output2D_box1 = oasysgui.widgetBox(tab3, "", addSpace=True, orientation="horizontal",
                                           height=355, width=3*self.CONTROL_AREA_WIDTH)       
        
        self.image_boxXZ = gui.widgetBox(output2D_box1, "XZ Slice", addSpace=True, orientation="vertical")
        self.image_boxXZ.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_boxXZ.setFixedWidth(1.2*self.IMAGE_WIDTH)
        self.figureXZ = Figure()
        self.figureXZ.patch.set_facecolor('white')
        self.plot_canvasXZ = FigureCanvasQTAgg(self.figureXZ)
        self.image_boxXZ.layout().addWidget(self.plot_canvasXZ)
        self.axXZ = self.figureXZ.add_axes([0.15, 0.15, 0.8, 0.75])
        
        self.image_boxXY = gui.widgetBox(output2D_box1, "Cross Section (XY Slice)", addSpace=True, orientation="vertical")
        self.image_boxXY.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_boxXY.setFixedWidth(0.8*self.IMAGE_WIDTH)
        self.figureXY = Figure()
        self.figureXY.patch.set_facecolor('white')
        self.plot_canvasXY = FigureCanvasQTAgg(self.figureXY)
        self.image_boxXY.layout().addWidget(self.plot_canvasXY)
        self.figureXY.set_size_inches((5,5))
        self.axXY = self.figureXY.add_axes([0.2, 0.15, 0.7, 0.75])
        
        output2D_box2 = oasysgui.widgetBox(tab3, "", addSpace=True, orientation="horizontal",
                                           height=355, width=3*self.CONTROL_AREA_WIDTH)      

        self.image_boxYZ = gui.widgetBox(output2D_box2, "YZ Slice", addSpace=True, orientation="vertical")
        self.image_boxYZ.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_boxYZ.setFixedWidth(1.2*self.IMAGE_WIDTH)
        self.figureYZ = Figure()
        self.figureYZ.patch.set_facecolor('white')
        self.plot_canvasYZ = FigureCanvasQTAgg(self.figureYZ)
        self.image_boxYZ.layout().addWidget(self.plot_canvasYZ)
        self.axYZ = self.figureYZ.add_axes([0.15, 0.15, 0.8, 0.75])
            
        self.shadow_output = oasysgui.textArea()
        out_box = oasysgui.widgetBox(output2D_box2, "System Output", addSpace=True, orientation="horizontal")
        out_box.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        out_box.setFixedWidth(0.8*self.IMAGE_WIDTH)
        out_box.layout().addWidget(self.shadow_output)
        
        ###### 2D Plot Analysis
        
        analysis2D_box1 = oasysgui.widgetBox(tab4, "", addSpace=True, orientation="horizontal",
                                           height=355, width=3*self.CONTROL_AREA_WIDTH)       
        
        self.image_box11 = gui.widgetBox(analysis2D_box1, "X FWHM", addSpace=True, orientation="vertical")
        self.image_box11.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_box11.setFixedWidth(1.0*self.IMAGE_WIDTH)
        self.figure11 = Figure()
        self.figure11.patch.set_facecolor('white')
        self.plot_canvas11 = FigureCanvasQTAgg(self.figure11)
        self.image_box11.layout().addWidget(self.plot_canvas11)
        self.ax11 = self.figure11.add_axes([0.15, 0.15, 0.8, 0.75])
        
        self.image_box12 = gui.widgetBox(analysis2D_box1, "Y FWHM", addSpace=True, orientation="vertical")
        self.image_box12.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_box12.setFixedWidth(1.0*self.IMAGE_WIDTH)
        self.figure12 = Figure()
        self.figure12.patch.set_facecolor('white')
        self.plot_canvas12 = FigureCanvasQTAgg(self.figure12)
        self.image_box12.layout().addWidget(self.plot_canvas12)
#        self.figure12.set_size_inches((5,5))
        self.ax12 = self.figure12.add_axes([0.15, 0.15, 0.8, 0.75])

        analysis2D_box2 = oasysgui.widgetBox(tab4, "", addSpace=True, orientation="horizontal",
                                           height=355, width=3*self.CONTROL_AREA_WIDTH)       
        
        self.image_box21 = gui.widgetBox(analysis2D_box2, "X RMS", addSpace=True, orientation="vertical")
        self.image_box21.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_box21.setFixedWidth(1.0*self.IMAGE_WIDTH)
        self.figure21 = Figure()
        self.figure21.patch.set_facecolor('white')
        self.plot_canvas21 = FigureCanvasQTAgg(self.figure21)
        self.image_box21.layout().addWidget(self.plot_canvas21)
        self.ax21 = self.figure21.add_axes([0.15, 0.15, 0.8, 0.75])        

        self.image_box22 = gui.widgetBox(analysis2D_box2, "Y RMS", addSpace=True, orientation="vertical")
        self.image_box22.setFixedHeight(1.0*self.IMAGE_HEIGHT)
        self.image_box22.setFixedWidth(1.0*self.IMAGE_WIDTH)
        self.figure22 = Figure()
        self.figure22.patch.set_facecolor('white')
        self.plot_canvas22 = FigureCanvasQTAgg(self.figure22)
        self.image_box22.layout().addWidget(self.plot_canvas22)
#        self.figure12.set_size_inches((5,5))
        self.ax22 = self.figure22.add_axes([0.15, 0.15, 0.8, 0.75])        
        
        
        ### Creates 'Run' function for widget ###
        self.runaction = widget.OWAction("Load and Refresh", self)
        self.runaction.triggered.connect(self.load_and_refresh)
        self.addAction(self.runaction)
        
#################################################################################
#################################################################################
#################################################################################
#################################################################################

    def step_to_nx(self):
        self.x_nbins = int( (self.x_range_max - self.x_range_min)/self.x_pixel + 1 )
    
    def nx_to_step(self):
        self.x_pixel = round((self.x_range_max - self.x_range_min)/(self.x_nbins - 1), 13)
        self.x_nbins = int( round((self.x_range_max - self.x_range_min)/self.x_pixel + 1 ))

    def step_to_ny(self):
        self.y_nbins = int( (self.y_range_max - self.y_range_min)/self.y_pixel + 1 )
    
    def ny_to_step(self):
        self.y_pixel = round((self.y_range_max - self.y_range_min)/(self.y_nbins - 1), 13)
        self.y_nbins = int( round( (self.y_range_max - self.y_range_min)/self.y_pixel + 1 ))
        
    def calc_rangesXY(self):
        #self.set_beam(beam)
        #if ShadowCongruence.checkEmptyBeam(self.input_beam):
        #if(isinstance(self.input_beam, [ShadowBeam])):    
        if(hasattr(self, 'input_beam')):
            self.le_x_range_min.setDisabled(self.auto_xy_ranges)
            self.le_x_range_max.setDisabled(self.auto_xy_ranges)
            self.le_y_range_min.setDisabled(self.auto_xy_ranges)
            self.le_y_range_max.setDisabled(self.auto_xy_ranges)
            
            if(self.auto_xy_ranges):
                self.xy_ranges = self.get_good_ranges(self.input_beam._beam.duplicate(), 
                                                      self.z_range_min, self.z_range_max,
                                                      self.x_column_index+1, self.y_column_index+1)
            
            self.x_range_min = round(self.xy_ranges[0], 9)
            self.x_range_max = round(self.xy_ranges[1], 9)
            self.y_range_min = round(self.xy_ranges[2], 9)
            self.y_range_max = round(self.xy_ranges[3], 9)
            
            self.ny_to_step()
            self.nx_to_step()

        else:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "No input beam! Please run the previous widget.",
                                           QtWidgets.QMessageBox.Ok)

    def calc_pixelsXY(self):
        pass

    def selectOptimizeFile(self):
        self.le_load_filename.setText(oasysgui.selectFileFromDialog(self, self.load_filename, "Open Caustic .h5 File"))

    def step_and_nz(self):
        try:
            self.nz = int( (self.z_range_max - self.z_range_min)/self.z_step + 1 )
            self.z_step = (self.z_range_max - self.z_range_min)/(self.nz - 1) 
        except:
            pass
        
    def step_to_nz(self):
        try:
            self.nz = int( (self.z_range_max - self.z_range_min)/self.z_step + 1 )
        except:
            pass

    def nz_to_step(self):
        try:
            self.z_step = (self.z_range_max - self.z_range_min)/(self.nz - 1) 
        except:
            pass

    def load_and_refresh(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        try:
            congruence.checkLessOrEqualThan(self.plot2D_x_range_min, self.plot2D_x_range_max, "Plot X range min", "Plot X range max")
            congruence.checkLessOrEqualThan(self.plot2D_y_range_min, self.plot2D_y_range_max, "Plot Y range min", "Plot Y range max")
            congruence.checkLessOrEqualThan(self.plot2D_z_range_min, self.plot2D_z_range_max, "Plot Z range min", "Plot Z range max")        
            congruence.checkLessOrEqualThan(self.plot2D_z_range_minXZ, self.plot2D_z_range_maxXZ, "Fit Z range min", "Fit Z range max")   
            congruence.checkLessOrEqualThan(self.plot2D_z_range_minYZ, self.plot2D_z_range_maxYZ, "Fit Z range min", "Fit Z range max")               
            good_to_plot = 1
        
        except Exception as exception:
            good_to_plot = 0
            QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)      
            
        if(good_to_plot):
            try:
                congruence.checkDir(self.load_filename)
            except Exception:
                sys.stdout.write('Failed (File not found in this directory)\n')
                QtWidgets.QMessageBox.critical(self, "Error", 'Please enter a valid file name', QtWidgets.QMessageBox.Ok)
                
            try:
                self.print_date_i

                sys.stdout.write('\nLoading Caustic and Running Analysis...\n')
                
                if(self.quick_preview):
                    self.plot_quick_preview(self.load_filename,
                                            scale=self.scale,
                                            xrange=[self.plot2D_x_range_min, self.plot2D_x_range_max],
                                            yrange=[self.plot2D_y_range_min, self.plot2D_y_range_max],
                                            zrange=[self.plot2D_z_range_min, self.plot2D_z_range_max],
                                            zrangeXZ=[self.plot2D_z_range_minXZ, self.plot2D_z_range_maxXZ],
                                            zrangeYZ=[self.plot2D_z_range_minYZ, self.plot2D_z_range_maxYZ],
                                            xunits=self.x_units, yunits=self.y_units, zunits=self.z_units)
                
                else:
                    self.outdict = self.plot_shadow_caustic(self.load_filename, self.x_cut_position, self.y_cut_position, self.z_cut_position, 
                                                            0, 0, scale=self.scale,
                                                            xrange=[self.plot2D_x_range_min, self.plot2D_x_range_max],
                                                            yrange=[self.plot2D_y_range_min, self.plot2D_y_range_max],
                                                            zrange=[self.plot2D_z_range_min, self.plot2D_z_range_max],
                                                            zrangeXZ=[self.plot2D_z_range_minXZ, self.plot2D_z_range_maxXZ],
                                                            zrangeYZ=[self.plot2D_z_range_minYZ, self.plot2D_z_range_maxYZ],
                                                            xunits=self.x_units, yunits=self.y_units, zunits=self.z_units)
                self.print_date_f
            except Exception as exception:
                good_to_plot = 0
                QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)  
        
        else:
            sys.stdout.write('Failed to Run Caustic.\n')


    ### Colect input beam ###
    def set_beam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):

                self.input_beam = beam

                if self.is_automatic_run:
#                    self.run()
                    pass
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays, bad content, bad limits or axes",
                                           QtWidgets.QMessageBox.Ok)
    
    ### Call plot functions ###
    def run_caustic(self):


        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                self.x_nbins = congruence.checkStrictlyPositiveNumber(self.x_nbins, "Number of Bins X")
                self.y_nbins = congruence.checkStrictlyPositiveNumber(self.y_nbins, "Number of Bins Y")
                self.nz = congruence.checkStrictlyPositiveNumber(self.nz, "Number of Z Points")
                congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")
                congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")
                congruence.checkLessThan(self.z_range_min, self.z_range_max, "Z range min", "Z range max")                
                
#                self.getConversion()
#                self.plot_xy()

                self.print_date_i()
                sys.stdout.write("Running Caustic... ")
                sys.stdout.flush()
                self.run_shadow_caustic(filename=self.save_filename, beam=self.input_beam._beam.duplicate(), 
                                        zStart=self.z_range_min, zFin=self.z_range_max, nz=self.nz, zOffset=self.z_offset,
                                        colh=self.x_column_index+1, colv=self.y_column_index+1, colref=self.weight_column_index,
                                        nbinsh=self.x_nbins, nbinsv=self.y_nbins, 
                                        xrange=[self.x_range_min, self.x_range_max],
                                        yrange=[self.y_range_min, self.y_range_max])
                sys.stdout.write('...finished!')
                self.print_date_f()
                plotted = True

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)
            return False

    def save_2D_plots(self):
#        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        filename, ext = os.path.splitext(self.load_filename)
        if not(self.plot_quick_preview):
            np.savetxt(filename + '_' + self.time_string + '.txt', [self.outtext], fmt="%s")
        
        self.figureXZ.savefig(filename + '_XZ.png', dpi=300)
        self.figureYZ.savefig(filename + '_YZ.png', dpi=300)
        self.figureXY.savefig(filename + '_XY.png', dpi=300)
        self.figure11.savefig(filename + '_X_FWHM.png', dpi=300)
        self.figure12.savefig(filename + '_Y_FWHM.png', dpi=300)
        self.figure21.savefig(filename + '_X_RMS.png', dpi=300)
        self.figure22.savefig(filename + '_Y_RMS.png', dpi=300)
        
        print("\nPlots saved to disk!\n")
        
  
    def launch_mayavi(self):
#        axXZ
        
        try:
            congruence.checkDir(self.load_filename)   
        except Exception:
            sys.stdout.write('3D visualization failed (File not found in this directory)\n')
            QtWidgets.QMessageBox.critical(self, "Error", 'Please enter a valid file name', QtWidgets.QMessageBox.Ok)
            
        try:
            import mayavi.mlab
            import platform
            
            mayavi_path = os.path.split(__file__)[0] 
            
            if platform.system() == 'Linux':
                command_str = "gnome-terminal -e 'bash -c \" python {0} -f {1} ; exec bash\"'".format(os.path.join(mayavi_path, 'volume_slicer_mayavi.py'), os.path.join(os.getcwd(), self.load_filename))
            if platform.system() == 'Windows':
                command_str = "cmd /c python {0} -f {1} ".format(os.path.join(mayavi_path, 'volume_slicer_mayavi.py'), os.path.join(os.getcwd(), self.load_filename))
            os.system(command_str)         
            
        except ImportError:
            raise ImportError("For 3D visualization, please 'pip install mayavi' in the oasys environment")
        
        
    def writeStdOut(self, text):        
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()


    def calc_rms(self, x, f_x):
            return np.sqrt(np.sum(f_x*np.square(x))/np.sum(f_x) - (np.sum(f_x*x)/np.sum(f_x))**2)
    
    def get_fwhm(self, x, y, oversampling=1, zero_padding=False, avg_correction=False, debug=False):
       
       
        def add_zeros(array):
            aux = []
            aux.append(0)
            for i in range(len(array)):
                aux.append(array[i])
            aux.append(0)
            return np.array(aux)
        
        def add_steps(array):
            aux = []
            step = (np.max(array)-np.min(array))/(len(array)-1)
            aux.append(array[0]-step)
            for i in range(len(array)):
                aux.append(array[i])
            aux.append(array[-1]+step)
            return np.array(aux)
        
        def interp_distribution(array_x,array_y,oversampling):
            dist = interp1d(array_x, array_y)
            x_int = np.linspace(np.min(array_x), np.max(array_x), int(len(x)*oversampling))
            y_int = dist(x_int)
            return x_int, y_int 
        
        if(oversampling > 1.0):
            array_x, array_y = interp_distribution(x, y, oversampling)
        else:
            array_x, array_y = x, y
            
        if(zero_padding):
            array_x = add_steps(x)
            array_y = add_zeros(y)
            
        try:    
            y_peak = np.max(array_y)
            idx_peak = (np.abs(array_y-y_peak)).argmin()
            #x_peak = array_x[idx_peak]
            if(idx_peak==0):
                left_hwhm_idx = 0
            else:
                #left_hwhm_idx = (np.abs(array_y[:idx_peak]-y_peak/2)).argmin()
    #            for i in range(idx_peak,0,-1):
                for i in range(0,idx_peak):
    #                if np.abs(array_y[i]-y_peak/2)<np.abs(array_y[i-1]-y_peak/2) and (array_y[i-1]-y_peak/2)<0:
                    if np.abs(array_y[i]-y_peak/2)>np.abs(array_y[i-1]-y_peak/2) and (array_y[i-1]-y_peak/2)>0:
                        break                
                left_hwhm_idx = i     
                
            if(idx_peak==len(array_y)-1):
                right_hwhm_idx = len(array_y)-1
            else:
                #right_hwhm_idx = (np.abs(array_y[idx_peak:]-y_peak/2)).argmin() + idx_peak
    #            for j in range(idx_peak,len(array_y)):
                for j in range(len(array_y)-2, idx_peak, -1):
    #                if np.abs(array_y[j]-y_peak/2)<np.abs(array_y[j+1]-y_peak/2) and (array_y[j+1]-y_peak/2)<0:
                    if np.abs(array_y[j]-y_peak/2)>np.abs(array_y[j+1]-y_peak/2) and (array_y[j+1]-y_peak/2)>0:
                        break              
                right_hwhm_idx = j
                
            fwhm = array_x[right_hwhm_idx] - array_x[left_hwhm_idx]               
                
            if(avg_correction):
                avg_y = (array_y[left_hwhm_idx]+array_y[right_hwhm_idx])/2.0
                popt_left = np.polyfit(np.array([array_x[left_hwhm_idx-1],array_x[left_hwhm_idx],array_x[left_hwhm_idx+1]]),
                                       np.array([array_y[left_hwhm_idx-1],array_y[left_hwhm_idx],array_y[left_hwhm_idx+1]]),1)                                   
                popt_right = np.polyfit(np.array([array_x[right_hwhm_idx-1],array_x[right_hwhm_idx],array_x[right_hwhm_idx+1]]),
                                       np.array([array_y[right_hwhm_idx-1],array_y[right_hwhm_idx],array_y[right_hwhm_idx+1]]),1)
                x_left = (avg_y-popt_left[1])/popt_left[0]
                x_right = (avg_y-popt_right[1])/popt_right[0]
                fwhm = x_right - x_left
                
                return [fwhm, x_left, x_right, avg_y, avg_y]
            else:
                return [fwhm, array_x[left_hwhm_idx], array_x[right_hwhm_idx], array_y[left_hwhm_idx], array_y[right_hwhm_idx]]
                
            if(debug):
                print(y_peak)
                print(idx_peak)
                print(left_hwhm_idx, right_hwhm_idx)
                print(array_x[left_hwhm_idx], array_x[right_hwhm_idx])            
            
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
                    
        return zmax, xmax
    
    def gaussian_beam(self, z, s0, z0, beta):
        return s0*np.sqrt(1 + ((z-z0)/beta)**2)
    
    def weighted_avg_and_std(self, values, weights):
        """
        By EOL - stackoverflow - 10/03/2010
        Return the weighted average and standard deviation.
        values, weights -- Numpy ndarrays with the same shape.
        """
        try:
            average = np.average(values, weights=weights)
            variance = np.average((values-average)**2, weights=weights)  # Fast and numerically precise
            return (average, np.sqrt(variance))
        except:
            print('   Mean and RMS values could not be calculated.')
            return (np.nan, np.nan)

    def get_good_ranges(self, beam, zStart, zFin, colh, colv):
        
        r_z0h = beam.get_good_range(icol=colh, nolost=1)
        r_z0v = beam.get_good_range(icol=colv, nolost=1)
        
        beam_copy = beam.duplicate()
        beam_copy.retrace(zStart)
        r_zStarth = beam_copy.get_good_range(icol=colh, nolost=1)
        r_zStartv = beam_copy.get_good_range(icol=colv, nolost=1)
        
        beam_copy = beam.duplicate()
        beam_copy.retrace(zFin)
        r_zFinh = beam_copy.get_good_range(icol=colh, nolost=1)
        r_zFinv = beam_copy.get_good_range(icol=colv, nolost=1)
        
        rh_min = np.min(r_z0h + r_zStarth + r_zFinh)
        rh_max = np.max(r_z0h + r_zStarth + r_zFinh)
        rv_min = np.min(r_z0v + r_zStartv + r_zFinv)
        rv_max = np.max(r_z0v + r_zStartv + r_zFinv)
    
        return [rh_min, rh_max, rv_min, rv_max] 
    
#    def initialize_hdf5(self, h5_filename, zStart, zFin, nz, zOffset, colh, colv, colref, nbinsh, nbinsv, good_rays, offsets=None):
#        with h5py.File(h5_filename, 'w') as f:
#            f.attrs['begin time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#            f.attrs['zStart'] = zStart
#            f.attrs['zFin'] = zFin
#            f.attrs['nz'] = nz
#            f.attrs['zOffset'] = zOffset
#            f.attrs['zStep'] = int((zFin - zStart) / (nz - 1))
#            f.attrs['col_h'] = colh
#            f.attrs['col_v'] = colv
#            f.attrs['col_ref'] = colref
#            f.attrs['nbins_h'] = nbinsh
#            f.attrs['nbins_v'] = nbinsv
#            f.attrs['good_rays'] = good_rays
#            if offsets is not None:
#                f.attrs['offsets'] = offsets
#            
#    
#    def append_dataset_hdf5(self, filename, data, z, zOffset, nz, tag, t0, ndigits):
#        
#        mean_h, rms_h = self.weighted_avg_and_std(data['bin_h_center'], data['histogram_h']) 
#        mean_v, rms_v = self.weighted_avg_and_std(data['bin_v_center'], data['histogram_v'])
#        fwhm_h = self.get_fwhm(data['bin_h_center'], data['histogram_h'])
#        fwhm_v = self.get_fwhm(data['bin_v_center'], data['histogram_v'])
#        
#        with h5py.File(filename, 'a') as f:
#            dset = f.create_dataset('step_{0:0{ndigits}d}'.format(tag, ndigits=ndigits),
#                                    data=np.array(data['histogram'], dtype=np.float), compression="gzip")
#            dset.attrs['z'] = z + zOffset
#            dset.attrs['xStart'] = data['bin_h_center'].min()
#            dset.attrs['xFin'] = data['bin_h_center'].max()
#            dset.attrs['nx'] = data['nbins_h']
#            dset.attrs['yStart'] = data['bin_v_center'].min()
#            dset.attrs['yFin'] = data['bin_v_center'].max()
#            dset.attrs['ny'] = data['nbins_v']
#            dset.attrs['mean_h'] = mean_h
#            dset.attrs['mean_v'] = mean_v
#            dset.attrs['rms_h'] = rms_h
#            dset.attrs['rms_v'] = rms_v
#            dset.attrs['fwhm_h'] = fwhm_h
#            dset.attrs['fwhm_v'] = fwhm_v
#            dset.attrs['ellapsed time (s)'] = round(time.time() - t0, 3)
#            
#            try:
#                dset.attrs['fwhm_h_shadow'] = data['fwhm_h']
#                dset.attrs['center_h_shadow'] = (data['fwhm_coordinates_h'][0] + data['fwhm_coordinates_h'][1]) / 2.0
#            except:
#                print('   CAUSTIC WARNING: FWHM X could not be calculated by Shadow')
#                dset.attrs['fwhm_h_shadow'] = np.nan
#                dset.attrs['center_h_shadow'] = np.nan
#            try:
#                dset.attrs['fwhm_v_shadow'] = data['fwhm_v']
#                dset.attrs['center_v_shadow'] = (data['fwhm_coordinates_v'][0] + data['fwhm_coordinates_v'][1]) / 2.0
#            except:
#                print('   CAUSTIC WARNING: FWHM Y could not be calculated by Shadow')
#                dset.attrs['fwhm_v_shadow'] = np.nan
#                dset.attrs['center_v_shadow'] = np.nan

    #def append_dataset_hdf5(self, filename, data, z, zOffset, nz, tag, t0, ndigits):

    def initialize_hdf5(self, h5_filename, zStart, zFin, nz, zOffset, colh, colv, colref, nbinsh, nbinsv, good_rays, offsets=None):
        with h5py.File(h5_filename, 'w') as f:
            f.attrs['begin time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f.attrs['zStart'] = zStart
            f.attrs['zFin'] = zFin
            f.attrs['nz'] = nz
            f.attrs['zOffset'] = zOffset
            f.attrs['zStep'] = int((zFin - zStart) / (nz - 1))
            f.attrs['col_h'] = colh
            f.attrs['col_v'] = colv
            f.attrs['col_ref'] = colref
            f.attrs['nbins_h'] = nbinsh
            f.attrs['nbins_v'] = nbinsv
            f.attrs['good_rays'] = good_rays
            if offsets is not None:
                f.attrs['offsets'] = offsets
            
    
    def append_dataset_hdf5(self, filename, data, z, zOffset, nz, tag, t0, ndigits):
        
        mean_h, rms_h = self.weighted_avg_and_std(data['bin_h_center'], data['histogram_h']) 
        mean_v, rms_v = self.weighted_avg_and_std(data['bin_v_center'], data['histogram_v'])
        fwhm_h = self.get_fwhm(data['bin_h_center'], data['histogram_h'])
        fwhm_v = self.get_fwhm(data['bin_v_center'], data['histogram_v'])
        
        with h5py.File(filename, 'a') as f:
            dset = f.create_dataset('step_{0:0{ndigits}d}'.format(tag, ndigits=ndigits),
                                    data=np.array(data['histogram'], dtype=np.float), compression="gzip")
            dset.attrs['z'] = z + zOffset
            dset.attrs['xStart'] = data['bin_h_center'].min()
            dset.attrs['xFin'] = data['bin_h_center'].max()
            dset.attrs['nx'] = data['nbins_h']
            dset.attrs['yStart'] = data['bin_v_center'].min()
            dset.attrs['yFin'] = data['bin_v_center'].max()
            dset.attrs['ny'] = data['nbins_v']
            dset.attrs['mean_h'] = mean_h
            dset.attrs['mean_v'] = mean_v
            dset.attrs['rms_h'] = rms_h
            dset.attrs['rms_v'] = rms_v
            dset.attrs['fwhm_h'] = fwhm_h
            dset.attrs['fwhm_v'] = fwhm_v
            dset.attrs['ellapsed time (s)'] = round(time.time() - t0, 3)
            
            try:
                dset.attrs['fwhm_h_shadow'] = data['fwhm_h']
                dset.attrs['center_h_shadow'] = (data['fwhm_coordinates_h'][0] + data['fwhm_coordinates_h'][1]) / 2.0
            except:
                print('CAUSTIC WARNING: FWHM X could not be calculated by Shadow')
                dset.attrs['fwhm_h_shadow'] = np.nan
                dset.attrs['center_h_shadow'] = np.nan
            try:
                dset.attrs['fwhm_v_shadow'] = data['fwhm_v']
                dset.attrs['center_v_shadow'] = (data['fwhm_coordinates_v'][0] + data['fwhm_coordinates_v'][1]) / 2.0
            except:
                print('CAUSTIC WARNING: FWHM Y could not be calculated by Shadow')
                dset.attrs['fwhm_v_shadow'] = np.nan
                dset.attrs['center_v_shadow'] = np.nan
                
            if (tag == nz - 1):
                f.attrs['end time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def read_caustic(self, filename, write_attributes=False, plot=False, plot2D=False, print_minimum=False):
        
        with h5py.File(filename, 'r+') as f:
        
            dset_names = list(f.keys())
            
            center_shadow = np.zeros((len(dset_names), 2), dtype=float)
            center = np.zeros((len(dset_names), 2), dtype=float)
            rms = np.zeros((len(dset_names), 2), dtype=float)
            fwhm = np.zeros((len(dset_names), 2), dtype=float)
            fwhm_shadow = np.zeros((len(dset_names), 2), dtype=float)
            
            ###### READ DATA #######################
            
            zStart = f.attrs['zStart']
            zFin = f.attrs['zFin']
            nz = f.attrs['nz']
                    
            #if(plot2D): 
            xStart = f[dset_names[0]].attrs['xStart']
            xFin = f[dset_names[0]].attrs['xFin']
            nx = f[dset_names[0]].attrs['nx']
            yStart = f[dset_names[0]].attrs['yStart']
            yFin = f[dset_names[0]].attrs['yFin']
            ny = f[dset_names[0]].attrs['ny']
                
            histoH = np.zeros((nx, nz))
            histoV = np.zeros((ny, nz))
            
            z_points = np.linspace(zStart, zFin, nz)
            
            for i, dset in enumerate(dset_names):
                #dset_keys = list(f[dset].attrs.keys())
            
                center_shadow[i,0] = f[dset].attrs['center_h_shadow']
                center_shadow[i,1] = f[dset].attrs['center_v_shadow']
                center[i,0] = f[dset].attrs['mean_h']    
                center[i,1] = f[dset].attrs['mean_v']
                rms[i,0] = f[dset].attrs['rms_h']    
                rms[i,1] = f[dset].attrs['rms_v']
                fwhm[i,0] = f[dset].attrs['fwhm_h'][0]
                fwhm[i,1] = f[dset].attrs['fwhm_v'][0]
                fwhm_shadow[i,0] = f[dset].attrs['fwhm_h_shadow']    
                fwhm_shadow[i,1] = f[dset].attrs['fwhm_v_shadow']
                
                #if(plot2D):
                histo2D = np.array(f[dset])
                histoH[:,i] = histo2D.sum(axis=1)
                histoV[:,i] = histo2D.sum(axis=0)
                    
        #### FIND MINIMUMS AND ITS Z POSITIONS
    
        rms_min = [np.min(rms[:,0]), np.min(rms[:,1])]
        fwhm_min = [np.min(fwhm[:,0]), np.min(fwhm[:,1])]
        fwhm_shadow_min = [np.min(fwhm_shadow[:,0]), np.min(fwhm_shadow[:,1])]
    
        rms_min_z=np.array([z_points[np.abs(rms[:,0]-rms_min[0]).argmin()],
                            z_points[np.abs(rms[:,1]-rms_min[1]).argmin()]])
    
        fwhm_min_z=np.array([z_points[np.abs(fwhm[:,0]-fwhm_min[0]).argmin()],
                             z_points[np.abs(fwhm[:,1]-fwhm_min[1]).argmin()]])
    
        fwhm_shadow_min_z=np.array([z_points[np.abs(fwhm_shadow[:,0]-fwhm_shadow_min[0]).argmin()],
                                    z_points[np.abs(fwhm_shadow[:,1]-fwhm_shadow_min[1]).argmin()]])
    
        center_rms = np.array([center[:,0][np.abs(z_points-rms_min_z[0]).argmin()],
                               center[:,1][np.abs(z_points-rms_min_z[1]).argmin()]])
    
        center_fwhm = np.array([center[:,0][np.abs(z_points-fwhm_min_z[0]).argmin()],
                                center[:,1][np.abs(z_points-fwhm_min_z[1]).argmin()]])
    
        center_fwhm_shadow = np.array([center[:,0][np.abs(z_points-fwhm_shadow_min_z[0]).argmin()],
                                       center[:,1][np.abs(z_points-fwhm_shadow_min_z[1]).argmin()]])
     
        
        outdict = {'zStart': zStart,
                   'zFin': zFin,
                   'nz': nz,
                   'center_h_array': center[:,0], 
                   'center_v_array': center[:,1],
                   'center_shadow_h_array': center_shadow[:,0], 
                   'center_shadow_v_array': center_shadow[:,1],
                   'rms_h_array': rms[:,0], 
                   'rms_v_array': rms[:,1],
                   'fwhm_h_array': fwhm[:,0], 
                   'fwhm_v_array': fwhm[:,1],
                   'fwhm_shadow_h_array': fwhm_shadow[:,0], 
                   'fwhm_shadow_v_array': fwhm_shadow[:,1],
                   'rms_min_h': rms_min[0],
                   'rms_min_v': rms_min[1],
                   'fwhm_min_h': fwhm_min[0],
                   'fwhm_min_v': fwhm_min[1],
                   'fwhm_shadow_min_h': fwhm_shadow_min[0],
                   'fwhm_shadow_min_v': fwhm_shadow_min[1],
                   'z_rms_min_h': rms_min_z[0],
                   'z_rms_min_v': rms_min_z[1],
                   'z_fwhm_min_h': fwhm_min_z[0],
                   'z_fwhm_min_v': fwhm_min_z[1],
                   'z_fwhm_shadow_min_h': fwhm_shadow_min_z[0],
                   'z_fwhm_shadow_min_v': fwhm_shadow_min_z[1],
                   'center_rms_h': center_rms[0],
                   'center_rms_v': center_rms[1],
                   'center_fwhm_h': center_fwhm[0],
                   'center_fwhm_v': center_fwhm[1],
                   'center_fwhm_shadow_h': center_fwhm_shadow[0],
                   'center_fwhm_shadow_v': center_fwhm_shadow[1]}#,
                   #'histoHZ': histoH,
                   #'histoVZ': histoV}
        
        if(write_attributes):
            with h5py.File(filename, 'a') as f:
                for key in list(outdict.keys()):
                    f.attrs[key] = outdict[key]
                    
                f.create_dataset('histoXZ', data=histoH, dtype=np.float, compression="gzip")
                f.create_dataset('histoYZ', data=histoV, dtype=np.float, compression="gzip")
                
        if(print_minimum):
            print('\n   ****** \n' + '   Z min (rms-hor): {0:.3e}'.format(rms_min_z[0]))
            print('   Z min (rms-vert): {0:.3e}\n   ******'.format(rms_min_z[1]))
            
        if(plot):
            
            plt.figure()
            plt.title('rms')
            plt.plot(z_points, rms[:,0], label='rms_h')
            plt.plot(z_points, rms[:,1], label='rms_v')
            plt.legend()
            plt.minorticks_on()
            plt.grid(which='both', alpha=0.2)    
        
            plt.figure()
            plt.title('fwhm')
            plt.plot(z_points, fwhm[:,0], label='fwhm_h')
            plt.plot(z_points, fwhm[:,1], label='fwhm_v')
            plt.plot(z_points, fwhm_shadow[:,0], label='fwhm_h_shadow')
            plt.plot(z_points, fwhm_shadow[:,1], label='fwhm_v_shadow')
            plt.legend()
            plt.minorticks_on()
            plt.grid(which='both', alpha=0.2)    
            
            plt.figure()
            plt.title('center')
            plt.plot(z_points, center[:,0], label='center_h')
            plt.plot(z_points, center_shadow[:,0], label='center_h_shadow')
            plt.legend()
            plt.minorticks_on()
            plt.grid(which='both', alpha=0.2)    
            
            plt.figure()
            plt.title('center')
            plt.plot(z_points, center[:,1], label='center_v')
            plt.plot(z_points, center_shadow[:,1], label='center_v_shadow')
            plt.legend()
            plt.minorticks_on()
            plt.grid(which='both', alpha=0.2)    
                
            plt.show()
            
        if(plot2D):
            
            plt.figure()
            plt.title('XZ')
            plt.imshow(histoH, extent=[zStart, zFin, xStart, xFin], origin='lower', aspect='auto')
            plt.xlabel('Z')
            plt.ylabel('Horizontal')
    
            plt.figure()
            plt.title('YZ')
            plt.imshow(histoV, extent=[zStart, zFin, yStart, yFin], origin='lower', aspect='auto')
            plt.xlabel('Z')
            plt.ylabel('Vertical')
            
        if(plot2D == 'log'):
            
            xc_min_except_0 = np.min(histoH[histoH>0])
            histoH[histoH<=0.0] = xc_min_except_0/2.0
            
            plt.figure()
            plt.title('XZ')
            plt.imshow(histoH, extent=[zStart, zFin, xStart, xFin], origin='lower', aspect='auto',
                       norm=LogNorm(vmin=xc_min_except_0/2.0, vmax=np.max(histoH)))
            plt.xlabel('Z')
            plt.ylabel('Horizontal')
    
            yc_min_except_0 = np.min(histoV[histoV>0])
            histoV[histoV<=0.0] = yc_min_except_0/2.0
    
            plt.figure()
            plt.title('YZ')
            plt.imshow(histoV, extent=[zStart, zFin, yStart, yFin], origin='lower', aspect='auto',
                       norm=LogNorm(vmin=xc_min_except_0/2.0, vmax=np.max(histoV)))
            plt.xlabel('Z')
            plt.ylabel('Vertical')
        
        
        return outdict
                
    def run_shadow_caustic(self, filename, beam, zStart, zFin, nz, zOffset, colh, colv, colref, nbinsh, nbinsv, xrange, yrange):
    
        t0 = time.time()
        good_rays = beam.nrays(nolost=1)
        self.initialize_hdf5(filename, zStart, zFin, nz, zOffset, colh, colv, colref, nbinsh, nbinsv, good_rays)
        z_points = np.linspace(zStart, zFin, nz)
        for i in range(nz):        
            beam.retrace(z_points[i]);
            histo = beam.histo2(col_h=colh, col_v=colv, nbins_h=nbinsh, nbins_v=nbinsv, nolost=1, ref=colref, xrange=xrange, yrange=yrange);
            self.append_dataset_hdf5(filename, data=histo, z=z_points[i], zOffset=zOffset, nz=nz, tag=i+1, t0=t0, ndigits=len(str(nz)))
        self.read_caustic(filename, write_attributes=True)
    
    def plot_quick_preview(self, filename, scale=0, 
                            xrange=[0,0], yrange=[0,0], zrange=[0,0], zrangeXZ=[0,0], zrangeYZ=[0,0], xunits=0, yunits=0, zunits=0):
    
        self.print_date_i()     
        
        if(xunits==0): 
            ylabelXZ = 'mm'
            xlabelXY = 'mm'
            xf=1.0
        elif(xunits==1):
            ylabelXZ = '\u00B5m'
            xlabelXY = '\u00B5m'
            xf=1e3
        elif(xunits==2):
            ylabelXZ = 'nm'
            xlabelXY = 'nm'
            xf=1e6

        if(yunits==0): 
            ylabelYZ = 'mm'
            ylabelXY = 'mm'
            yf=1.0
        elif(yunits==1):
            ylabelYZ = '\u00B5m'
            ylabelXY = '\u00B5m'
            yf=1e3
        elif(yunits==2):
            ylabelYZ = 'nm'
            ylabelXY = 'nm'
            yf=1e6

        if(zunits==0): 
            xlabelYZ = 'm'
            xlabelXZ = 'm'
            zf=1e-3
        if(zunits==1): 
            xlabelYZ = 'mm'
            xlabelXZ = 'mm'
            zf=1.0
        elif(zunits==2):
            xlabelYZ = '\u00B5m'
            xlabelXZ = '\u00B5m'
            zf=1e3
        elif(zunits==3):
            xlabelYZ = 'nm'
            xlabelXZ = 'nm'
            zf=1e6
            
        with h5py.File(filename, 'r+') as f:
            
            dset_names = list(f.keys())
            
            if not 'histoXZ' in dset_names:
                
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "This caustic hdf5 file is not compatible with quick preview.",
                                           QtWidgets.QMessageBox.Ok) 
                return 0
            
            zStart = f.attrs['zStart']
            zFin = f.attrs['zFin']
            nz = f.attrs['nz']
            z_points = np.linspace(zStart, zFin, nz)

            
            xmin = f[dset_names[3]].attrs['xStart'] # [3] is because [0] is a histogram 2D
            xmax = f[dset_names[3]].attrs['xFin']
            ymin = f[dset_names[3]].attrs['yStart']
            ymax = f[dset_names[3]].attrs['yFin']
            
            rms_h_array = f.attrs['rms_h_array']
            rms_v_array = f.attrs['rms_v_array']
            fwhm_h_array = f.attrs['fwhm_h_array']            
            fwhm_v_array = f.attrs['fwhm_v_array']        
            fwhm_shadow_h_array = f.attrs['fwhm_shadow_h_array']            
            fwhm_shadow_v_array = f.attrs['fwhm_shadow_v_array']
            histoHZ = np.array(f['histoXZ'])
            histoVZ = np.array(f['histoYZ'])
            
            self.time_string = f.attrs['end time']
            
        self.axXZ.clear()
        self.axXZ.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.axXZ.set_ylabel('X ' + '[' + ylabelXZ + ']')
        self.axXZ.set_title('Integrated over Y axis')
        self.axXZ.minorticks_on()
        self.axXZ.tick_params(which='both', axis='both', direction='out', right=True, top=True)

        self.axYZ.clear()        
        self.axYZ.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.axYZ.set_ylabel('Y ' + '[' + ylabelYZ + ']')
        self.axYZ.set_title('Integrated over X axis')
        self.axYZ.minorticks_on()
        self.axYZ.tick_params(which='both', axis='both', direction='out', right=True, top=True)
        
        self.axXY.clear()
        #self.axXY.set_xlabel('X ' + '[' + xlabelXY + ']')
        #self.axXY.set_ylabel('Y ' + '[' + ylabelXY + ']')
        #self.axXY.set_title('Slice at Z = {0:.6f} '.format(z_to_plot) + xlabelXZ)
        #self.axXY.minorticks_on()
        #self.axXY.tick_params(which='both', axis='both', direction='out', right=True, top=True)
        #self.axXY.hlines(y=y_pts_local[y_cut_idx]*yf, xmin=ranges_to_plot[0]*xf, xmax=ranges_to_plot[1]*xf, alpha=0.4, color='white', linestyle='--')
        #self.axXY.vlines(x=x_pts_local[x_cut_idx]*xf, ymin=ranges_to_plot[2]*yf, ymax=ranges_to_plot[3]*yf, alpha=0.4, color='white', linestyle='--')
        
        if(scale==0):

            self.axXZ.imshow(histoHZ, extent=[zStart*zf, zFin*zf, xmin*xf, xmax*xf], aspect='auto', origin='lower')        
            self.axYZ.imshow(histoVZ, extent=[zStart*zf, zFin*zf, ymin*yf, ymax*yf], aspect='auto', origin='lower')
            #self.axXY.imshow(mtx_to_plot, extent=[xmin*xf, xmax*xf, ymin*yf, ymax*yf], aspect='auto', origin='lower')
            
        elif(scale==1):

            xc_min_except_0 = np.min(histoHZ[histoHZ>0])
            histoHZ[histoHZ<=0.0] = xc_min_except_0/2.0
            self.axXZ.imshow(histoHZ, extent=[zStart*zf, zFin*zf, xmin*xf, xmax*xf], aspect='auto', origin='lower', norm=LogNorm(vmin=xc_min_except_0/2.0, vmax=np.max(histoHZ)))
    
            yc_min_except_0 = np.min(histoVZ[histoVZ>0])
            histoVZ[histoVZ<=0.0] = yc_min_except_0/2.0
            self.axYZ.imshow(histoVZ, extent=[zStart*zf, zFin*zf, ymin*yf, ymax*yf], aspect='auto', origin='lower', norm=LogNorm(vmin=yc_min_except_0/2.0, vmax=np.max(histoVZ)))

            #xy_min_except_0 = np.min(mtx_to_plot[mtx_to_plot>0])
            #mtx_to_plot[mtx_to_plot<=0.0] = xy_min_except_0/2.0
            #self.axXY.imshow(mtx_to_plot, extent=[xmin*xf, xmax*xf, ymin*yf, ymax*yf], aspect='auto', origin='lower', norm=LogNorm(vmin=xy_min_except_0/2.0, vmax=np.max(mtx_to_plot)))
                        
        ##############
        ## 2D Analysis
        ##############
        
#        plt.figure()
        self.ax11.clear()
        self.ax11.plot(z_points*zf, fwhm_h_array*xf, '-o', label='internal', alpha=0.6)
        self.ax11.plot(z_points*zf, fwhm_shadow_h_array*xf, '-o', label='shadow', alpha=0.3)
        #if not(popt1[0]==0 and popt1[1]==0 and popt1[2]==0): 
        #    self.ax11.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt1[0], popt1[1], popt1[2])*xf, 'C0--', alpha=0.8)
        #if not(popt3[0]==0 and popt3[1]==0 and popt3[2]==0): 
        #    self.ax11.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt3[0], popt3[1], popt3[2])*xf, 'k--', alpha=0.4)
        self.ax11.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.ax11.set_ylabel('X FWHM ' + '[' + ylabelXZ + ']')
        self.ax11.set_title('Integrated over Y axis')
        self.ax11.minorticks_on()
        self.ax11.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax11.grid(which='both', alpha=0.1)
        self.ax11.legend(loc='best', fontsize=8)

#        plt.figure()
        self.ax12.clear()
        self.ax12.plot(z_points*zf, fwhm_v_array*yf, '-o', label='internal', alpha=0.6)
        self.ax12.plot(z_points*zf, fwhm_shadow_v_array*yf, '-o', label='shadow', alpha=0.3)
        #if not(popt4[0]==0 and popt4[1]==0 and popt4[2]==0): 
        #    self.ax12.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt4[0], popt4[1], popt4[2])*yf, 'C0--', alpha=0.8)
        #if not(popt6[0]==0 and popt6[1]==0 and popt6[2]==0): 
        #    self.ax12.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt6[0], popt6[1], popt6[2])*yf, 'k--', alpha=0.4)
        self.ax12.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.ax12.set_ylabel('Y FWHM ' + '[' + ylabelYZ + ']')
        self.ax12.set_title('Integrated over X axis')
        self.ax12.minorticks_on()
        self.ax12.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax12.grid(which='both', alpha=0.1)
        self.ax12.legend(loc='best', fontsize=8)
            
       
#        plt.figure()
        self.ax21.clear()
        self.ax21.plot(z_points*zf, rms_h_array*xf, '-o', alpha=0.6)
        #if not(popt2[0]==0 and popt2[1]==0 and popt2[2]==0): 
        #    self.ax21.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt2[0], popt2[1], popt2[2])*xf, 'k--', alpha=0.6)
        self.ax21.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.ax21.set_ylabel('X RMS ' + '[' + ylabelXZ + ']')
        self.ax21.set_title('Integrated over Y axis')
        self.ax21.minorticks_on()
        self.ax21.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax21.grid(which='both', alpha=0.1)

#        plt.figure()
        self.ax22.clear()
        self.ax22.plot(z_points*zf, rms_v_array*yf, '-o', alpha=0.6)
        #if not(popt5[0]==0 and popt5[1]==0 and popt5[2]==0): 
        #    self.ax22.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt5[0], popt5[1], popt5[2])*yf, 'k--', alpha=0.6)
        self.ax22.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.ax22.set_ylabel('Y RMS ' + '[' + ylabelYZ + ']')
        self.ax22.set_title('integrated over X axis')
        self.ax22.minorticks_on()
        self.ax22.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax22.grid(which='both', alpha=0.1)

        if not(xrange[0]==0.0 and xrange[1]==0.0):
            self.axXZ.set_ylim(xrange[0], xrange[1])
            #self.axXY.set_xlim(xrange[0], xrange[1])       

        if not(yrange[0]==0.0 and yrange[1]==0.0):
            self.axYZ.set_ylim(yrange[0], yrange[1])
            #self.axXY.set_ylim(yrange[0], yrange[1]) 
            
        if not(zrange[0]==0.0 and zrange[1]==0.0):
            self.axXZ.set_xlim(zrange[0], zrange[1])
            self.axYZ.set_xlim(zrange[0], zrange[1])
            self.ax11.set_xlim(zrange[0], zrange[1])
            self.ax12.set_xlim(zrange[0], zrange[1])            
            self.ax21.set_xlim(zrange[0], zrange[1])
            self.ax22.set_xlim(zrange[0], zrange[1])
            
        self.figureXZ.canvas.draw()
        self.figureYZ.canvas.draw()
        self.figureXY.canvas.draw()
        self.figure11.canvas.draw()
        self.figure12.canvas.draw()
        self.figure21.canvas.draw()
        self.figure22.canvas.draw()
            
        self.print_date_f()    

    
    def plot_shadow_caustic(self, filename, cut_pos_x=0.0, cut_pos_y=0.0, cut_pos_z=0.0, nx=0, ny=0, scale=0, 
                            xrange=[0,0], yrange=[0,0], zrange=[0,0], zrangeXZ=[0,0], zrangeYZ=[0,0], xunits=0, yunits=0, zunits=0):
        
        self.print_date_i()     
        
        if(xunits==0): 
            ylabelXZ = 'mm'
            xlabelXY = 'mm'
            xf=1.0
        elif(xunits==1):
            ylabelXZ = '\u00B5m'
            xlabelXY = '\u00B5m'
            xf=1e3
        elif(xunits==2):
            ylabelXZ = 'nm'
            xlabelXY = 'nm'
            xf=1e6

        if(yunits==0): 
            ylabelYZ = 'mm'
            ylabelXY = 'mm'
            yf=1.0
        elif(yunits==1):
            ylabelYZ = '\u00B5m'
            ylabelXY = '\u00B5m'
            yf=1e3
        elif(yunits==2):
            ylabelYZ = 'nm'
            ylabelXY = 'nm'
            yf=1e6

        if(zunits==0): 
            xlabelYZ = 'm'
            xlabelXZ = 'm'
            zf=1e-3
        if(zunits==1): 
            xlabelYZ = 'mm'
            xlabelXZ = 'mm'
            zf=1.0
        elif(zunits==2):
            xlabelYZ = '\u00B5m'
            xlabelXZ = '\u00B5m'
            zf=1e3
        elif(zunits==3):
            xlabelYZ = 'nm'
            xlabelXZ = 'nm'
            zf=1e6
        
        with h5py.File(filename, 'r+') as f:
            
            zStart = f.attrs['zStart']
            zFin = f.attrs['zFin']
            nz = f.attrs['nz']
            z_points = np.linspace(zStart, zFin, nz)
            dset_names = list(f.keys())
            del dset_names[0:2] # bug correction for new caustic
            z_to_plot = z_points[np.abs(z_points - cut_pos_z/zf).argmin()]
            self.time_string = f.attrs['end time']
            
            #####################
            # find maximum ranges
            #####################
            xy_range = np.zeros((len(dset_names), 6))
            
            for i in range(len(dset_names)):
            
                dset = dset_names[i]
                xy_range[i] = np.array([f[dset].attrs['xStart'], f[dset].attrs['xFin'], 
                                        f[dset].attrs['yStart'], f[dset].attrs['yFin'],
                                        f[dset].attrs['nx'], f[dset].attrs['ny']])
            
            xmin = np.min(xy_range[:,0])
            xmax = np.max(xy_range[:,1])
            ymin = np.min(xy_range[:,2])
            ymax = np.max(xy_range[:,3])
            if(nx==0): nx = int(np.max(xy_range[:,4]))
            if(ny==0): ny = int(np.max(xy_range[:,5]))
            
            #####################
            # interpolate cuts
            #####################
            
            x_pts_global = np.linspace(xmin, xmax, nx)
            y_pts_global = np.linspace(ymin, ymax, ny)
            
            x_caustic = np.zeros((nx, len(dset_names)))
            y_caustic = np.zeros((ny, len(dset_names)))
            x_properties = np.zeros((5, len(dset_names)))
            y_properties = np.zeros((5, len(dset_names)))    

            #####################
            # do caustic
            #####################
            
            for i in range(len(dset_names)):
                
                dset = dset_names[i]
                mtx = np.array(f[dset]).transpose()
                if(f[dset].attrs['z']==z_to_plot):
                    mtx_to_plot = mtx
                    ranges_to_plot = [f[dset].attrs['xStart'], f[dset].attrs['xFin'], f[dset].attrs['yStart'], f[dset].attrs['yFin']]
                x_pts_local = np.linspace(f[dset].attrs['xStart'], f[dset].attrs['xFin'], f[dset].attrs['nx'])
                y_pts_local = np.linspace(f[dset].attrs['yStart'], f[dset].attrs['yFin'], f[dset].attrs['ny'])
                x_cut_idx = np.abs(x_pts_local - cut_pos_x/xf).argmin()
                y_cut_idx = np.abs(y_pts_local - cut_pos_y/yf).argmin() 
                x_cut = mtx[y_cut_idx, :]
                y_cut = mtx[:, x_cut_idx]
                
                #### correct ranges for each dataset 
                
                if(x_pts_local[0] > xmin):
                    x_pts_local = np.insert(x_pts_local, 0, xmin)
                    x_cut = np.insert(x_cut, 0, 0)
            
                if(x_pts_local[-1] < xmax):
                    x_pts_local = np.insert(x_pts_local, -1, xmax)
                    x_cut = np.insert(x_cut, -1, 0)
        
                if(y_pts_local[0] > ymin):
                    y_pts_local = np.insert(y_pts_local, 0, ymin)
                    y_cut = np.insert(y_cut, 0, 0)
            
                if(y_pts_local[-1] < ymax):
                    y_pts_local = np.insert(y_pts_local, -1, ymax)
                    y_cut = np.insert(y_cut, -1, 0)    
                    
                #### interpolate and sample at global coordinates
                
                x_cut_interp = interp1d(x=x_pts_local, y=x_cut, kind='linear')
                y_cut_interp = interp1d(x=y_pts_local, y=y_cut, kind='linear')
                
                x_cut_global = x_cut_interp(x_pts_global)
                y_cut_global = y_cut_interp(y_pts_global)
                
                x_caustic[:, i] = x_cut_global 
                y_caustic[:, i] = y_cut_global
                
                #### calculate properties
                
                x_properties[0][i] = self.get_fwhm(x_pts_local, x_cut, oversampling=200, zero_padding=False)[0]
                x_properties[1][i] = self.calc_rms(x_pts_local, x_cut)
                x_properties[2][i] = np.max(x_cut)
                x_properties[3][i] = x_pts_local[np.abs(x_cut - np.max(x_cut)).argmin()]
                x_properties[4][i] = f[dset].attrs['fwhm_h_shadow'] 
        
                y_properties[0][i] = self.get_fwhm(y_pts_local, y_cut, oversampling=200, zero_padding=False)[0]
                y_properties[1][i] = self.calc_rms(y_pts_local, y_cut)
                y_properties[2][i] = np.max(y_cut)
                y_properties[3][i] = y_pts_local[np.abs(y_cut - np.max(y_cut)).argmin()]
                y_properties[4][i] = f[dset].attrs['fwhm_v_shadow']
        
       
                if(0): # Calculate 2D peak positions
                    xpeak_idx, ypeak_idx = self.find_peak(f[dset])
                    x_properties[4][i] = x_pts_local[xpeak_idx[0]] 
                    y_properties[4][i] = y_pts_local[ypeak_idx[0]]
        #### fit fwhm and rms
        total_limits = np.linspace(0, len(z_points)-1, len(z_points), dtype=int)
        
        if not(zrangeXZ[0]==0 and zrangeXZ[1]==0):
            flXZ = np.where(np.logical_and(z_points>=zrangeXZ[0]/zf, z_points<=zrangeXZ[1]/zf)) # limits for fitting
        else:
            flXZ = total_limits
            
        if not(zrangeYZ[0]==0 and zrangeYZ[1]==0):
            flYZ = np.where(np.logical_and(z_points>=zrangeYZ[0]/zf, z_points<=zrangeYZ[1]/zf)) # limits for fitting
        else:
            flYZ = total_limits
        
        try:
#            sys.stdout.write('\n beta guess = {0:.6f}\n'.format(x_properties[0][int(nz/2)]/((x_properties[0][-1] -x_properties[0][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))))
            popt1, pcov1 = curve_fit(f=self.gaussian_beam, xdata=z_points[flXZ], ydata=x_properties[0][flXZ], 
                                     p0=[x_properties[0][int(nz/2)], z_points[int(nz/2.2)], x_properties[0][int(nz/2)]/((x_properties[0][-1] -x_properties[0][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt1=[0]*3 
        try:
            popt2, pcov2 = curve_fit(f=self.gaussian_beam, xdata=z_points[flXZ], ydata=x_properties[1][flXZ], 
                                     p0=[x_properties[1][int(nz/2)], z_points[int(nz/2.2)], x_properties[1][int(nz/2)]/((x_properties[1][-1] -x_properties[1][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt2=[0]*3 
        try:
            popt3, pcov3 = curve_fit(f=self.gaussian_beam, xdata=z_points[flXZ], ydata=x_properties[4][flXZ], 
                                     p0=[x_properties[4][int(nz/2)], z_points[int(nz/2.2)], x_properties[4][int(nz/2)]/((x_properties[4][-1] -x_properties[4][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt3=[0]*3
        try:
            popt4, pcov4 = curve_fit(f=self.gaussian_beam, xdata=z_points[flYZ], ydata=y_properties[0][flYZ], 
                                     p0=[y_properties[0][int(nz/2)], z_points[int(nz/2.2)], y_properties[0][int(nz/2)]/((y_properties[0][-1] -y_properties[0][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt4=[0]*3
        try:
            popt5, pcov5 = curve_fit(f=self.gaussian_beam, xdata=z_points[flYZ], ydata=y_properties[1][flYZ], 
                                     p0=[y_properties[1][int(nz/2)], z_points[int(nz/2.2)], y_properties[1][int(nz/2)]/((y_properties[1][-1] -y_properties[1][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt5=[0]*3
        try:
            popt6, pcov6 = curve_fit(f=self.gaussian_beam, xdata=z_points[flYZ], ydata=y_properties[4][flYZ], 
                                     p0=[y_properties[4][int(nz/2)], z_points[int(nz/2.2)], x_properties[4][int(nz/2)]/((x_properties[4][-1] -x_properties[4][int(nz/2)]) / (z_points[-1] - z_points[int(nz/2)]))], maxfev=5000)
        except:
            popt6=[0]*3
        
        save_filename, ext = os.path.splitext(filename)
    

            
        outdict = {"z_points":z_points*zf,
                   "fwhm_x_cut":x_properties[0]*xf,
                   "fwhm_y_cut":y_properties[0]*yf,
                   "fwhm_x_histo":x_properties[4]*xf,
                   "fwhm_y_histo":y_properties[4]*yf,
                   "rms_x_cut":x_properties[1]*xf,
                   "rms_y_cut":y_properties[1]*yf,
                   "peak_x_cut":x_properties[2],
                   "peak_y_cut":y_properties[2],
                   "z_peak_x_cut":x_properties[3]*zf,
                   "z_peak_y_cut":y_properties[3]*zf,
                   "popt_fwhm_x_cut":[popt1[0]*xf, popt1[1]*zf, popt1[2]*zf],
                   "popt_rms_x_cut":[popt2[0]*xf, popt2[1]*zf, popt2[2]*zf],
                   "popt_fwhm_x_histo":[popt3[0]*xf, popt3[1]*zf, popt3[2]*zf],
                   "popt_fwhm_y_cut":[popt4[0]*yf, popt4[1]*zf, popt4[2]*zf],
                   "popt_rms_y_cut":[popt5[0]*yf, popt5[1]*zf, popt5[2]*zf],
                   "popt_fwhm_y_histo":[popt6[0]*yf, popt6[1]*zf, popt6[2]*zf]} 
            
        
        self.outtext  = "File name: " + filename + '\n'
        self.outtext += "Cuts at positions: (" + "X = {0:.6f} ".format(x_pts_local[x_cut_idx]*xf) + xlabelXY + "; Y = {0:.6f} ".format(y_pts_local[y_cut_idx]*yf) + ylabelXY + "; Z = {0:.6f} ".format(z_to_plot*zf) + xlabelXZ + ')\n'
        
        self.outtext += "\nXZ Slice: \n"
        self.outtext += "Cut Minimum (FWHM, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_fwhm_x_cut"][0], outdict["popt_fwhm_x_cut"][1], ylabelXZ, xlabelXZ)
        self.outtext += "Histo Minimum (FWHM, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_fwhm_x_histo"][0], outdict["popt_fwhm_x_histo"][1], ylabelXZ, xlabelXZ)
        self.outtext += "Cut Minimum (RMS, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_rms_x_cut"][0], outdict["popt_rms_x_cut"][1], ylabelXZ, xlabelXZ)
        self.outtext += "Minimum Z (average) = {0:.3f} {1}\n".format(np.mean([outdict["popt_fwhm_x_cut"][1], outdict["popt_fwhm_x_histo"][1], outdict["popt_rms_x_cut"][1]]), xlabelXZ)
        self.outtext += "Betas: (cut-FWHM, histo-FWHM, cut-RMS) = {0:.6f}, {1:.6f}, {2:.6f} {3}\n".format(outdict["popt_fwhm_x_cut"][2], outdict["popt_fwhm_x_histo"][2], outdict["popt_rms_x_cut"][2], xlabelXZ)

        self.outtext += "\nYZ Slice: \n"
        self.outtext += "Cut Minimum (FWHM, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_fwhm_y_cut"][0], outdict["popt_fwhm_y_cut"][1], ylabelYZ, xlabelYZ)
        self.outtext += "Histo Minimum (FWHM, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_fwhm_y_histo"][0], outdict["popt_fwhm_y_histo"][1], ylabelYZ, xlabelYZ)
        self.outtext += "Cut Minimum (RMS, Z) = ({0:.3f} {2}, {1:.3f} {3}) \n".format(outdict["popt_rms_y_cut"][0], outdict["popt_rms_y_cut"][1], ylabelYZ, xlabelYZ)
        self.outtext += "Minimum Z (average) = {0:.3f} {1}\n".format(np.mean([outdict["popt_fwhm_y_cut"][1], outdict["popt_fwhm_y_histo"][1], outdict["popt_rms_y_cut"][1]]), xlabelXZ)
        self.outtext += "Betas: (cut-FWHM, histo-FWHM, cut-RMS) = {0:.6f}, {1:.6f}, {2:.6f} {3}\n".format(outdict["popt_fwhm_y_cut"][2], outdict["popt_fwhm_y_histo"][2], outdict["popt_rms_y_cut"][2], xlabelYZ)
        

        #self.time_string = time.strftime("%Y-%m-%d-%Hh-%Mm-%Ss", time.localtime())
        sys.stdout.write(self.outtext)
        self.print_date_f()        

        #################
        ### CAUSTIC PLOTS
        #################
        
        self.axXZ.clear()
        self.axXZ.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.axXZ.set_ylabel('X ' + '[' + ylabelXZ + ']')
        self.axXZ.set_title('Slice at Y = {0:.6f} '.format(y_pts_local[y_cut_idx]*yf) + ylabelXY)
        self.axXZ.minorticks_on()
        self.axXZ.tick_params(which='both', axis='both', direction='out', right=True, top=True)
        self.axXZ.vlines(x=z_to_plot*zf, ymin=ranges_to_plot[0]*xf, ymax=ranges_to_plot[1]*xf, alpha=0.4, color='white', linestyle='--')

        self.axYZ.clear()        
        self.axYZ.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.axYZ.set_ylabel('Y ' + '[' + ylabelYZ + ']')
        self.axYZ.set_title('Slice at X = {0:.6f} '.format(x_pts_local[x_cut_idx]*xf) + xlabelXY)
        self.axYZ.minorticks_on()
        self.axYZ.tick_params(which='both', axis='both', direction='out', right=True, top=True)
        self.axYZ.vlines(x=z_to_plot*zf, ymin=ranges_to_plot[2]*yf, ymax=ranges_to_plot[3]*yf, alpha=0.4, color='white', linestyle='--')
        
        self.axXY.clear()
        self.axXY.set_xlabel('X ' + '[' + xlabelXY + ']')
        self.axXY.set_ylabel('Y ' + '[' + ylabelXY + ']')
        self.axXY.set_title('Slice at Z = {0:.6f} '.format(z_to_plot) + xlabelXZ)
        self.axXY.minorticks_on()
        self.axXY.tick_params(which='both', axis='both', direction='out', right=True, top=True)
        self.axXY.hlines(y=y_pts_local[y_cut_idx]*yf, xmin=ranges_to_plot[0]*xf, xmax=ranges_to_plot[1]*xf, alpha=0.4, color='white', linestyle='--')
        self.axXY.vlines(x=x_pts_local[x_cut_idx]*xf, ymin=ranges_to_plot[2]*yf, ymax=ranges_to_plot[3]*yf, alpha=0.4, color='white', linestyle='--')
        
        if(scale==0):

            self.axXZ.imshow(x_caustic, extent=[zStart*zf, zFin*zf, xmin*xf, xmax*xf], aspect='auto', origin='lower')        
            self.axYZ.imshow(y_caustic, extent=[zStart*zf, zFin*zf, ymin*yf, ymax*yf], aspect='auto', origin='lower')
            self.axXY.imshow(mtx_to_plot, extent=[xmin*xf, xmax*xf, ymin*yf, ymax*yf], aspect='auto', origin='lower')
            
        elif(scale==1):

            xc_min_except_0 = np.min(x_caustic[x_caustic>0])
            x_caustic[x_caustic<=0.0] = xc_min_except_0/2.0
            self.axXZ.imshow(x_caustic, extent=[zStart*zf, zFin*zf, xmin*xf, xmax*xf], aspect='auto', origin='lower', norm=LogNorm(vmin=xc_min_except_0/2.0, vmax=np.max(x_caustic)))
    
            yc_min_except_0 = np.min(y_caustic[y_caustic>0])
            y_caustic[y_caustic<=0.0] = yc_min_except_0/2.0
            self.axYZ.imshow(y_caustic, extent=[zStart*zf, zFin*zf, ymin*yf, ymax*yf], aspect='auto', origin='lower', norm=LogNorm(vmin=yc_min_except_0/2.0, vmax=np.max(y_caustic)))

            xy_min_except_0 = np.min(mtx_to_plot[mtx_to_plot>0])
            mtx_to_plot[mtx_to_plot<=0.0] = xy_min_except_0/2.0
            self.axXY.imshow(mtx_to_plot, extent=[xmin*xf, xmax*xf, ymin*yf, ymax*yf], aspect='auto', origin='lower', norm=LogNorm(vmin=xy_min_except_0/2.0, vmax=np.max(mtx_to_plot)))
                        
        ##############
        ## 2D Analysis
        ##############
        
#        plt.figure()
        self.ax11.clear()
        self.ax11.plot(z_points*zf, x_properties[0]*xf, '-o', label='cut', alpha=0.6)
        self.ax11.plot(z_points*zf, x_properties[4]*xf, '-o', label='histogram', alpha=0.3)
        if not(popt1[0]==0 and popt1[1]==0 and popt1[2]==0): 
            self.ax11.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt1[0], popt1[1], popt1[2])*xf, 'C0--', alpha=0.8)
        if not(popt3[0]==0 and popt3[1]==0 and popt3[2]==0): 
            self.ax11.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt3[0], popt3[1], popt3[2])*xf, 'k--', alpha=0.4)
        self.ax11.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.ax11.set_ylabel('X FWHM ' + '[' + ylabelXZ + ']')
        self.ax11.set_title('Slice at Y = {0:.6f} '.format(y_pts_local[y_cut_idx]*yf) + ylabelXY)
        self.ax11.minorticks_on()
        self.ax11.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax11.grid(which='both', alpha=0.1)
        self.ax11.legend(loc='best', fontsize=8)

#        plt.figure()
        self.ax12.clear()
        self.ax12.plot(z_points*zf, y_properties[0]*yf, '-o', label='cut', alpha=0.6)
        self.ax12.plot(z_points*zf, y_properties[4]*yf, '-o', label='histogram', alpha=0.3)
        if not(popt4[0]==0 and popt4[1]==0 and popt4[2]==0): 
            self.ax12.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt4[0], popt4[1], popt4[2])*yf, 'C0--', alpha=0.8)
        if not(popt6[0]==0 and popt6[1]==0 and popt6[2]==0): 
            self.ax12.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt6[0], popt6[1], popt6[2])*yf, 'k--', alpha=0.4)
        self.ax12.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.ax12.set_ylabel('Y FWHM ' + '[' + ylabelYZ + ']')
        self.ax12.set_title('Slice at X = {0:.6f} '.format(x_pts_local[x_cut_idx]*xf) + xlabelXY)
        self.ax12.minorticks_on()
        self.ax12.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax12.grid(which='both', alpha=0.1)
        self.ax12.legend(loc='best', fontsize=8)
            
       
#        plt.figure()
        self.ax21.clear()
        self.ax21.plot(z_points*zf, x_properties[1]*xf, '-o', alpha=0.6)
        if not(popt2[0]==0 and popt2[1]==0 and popt2[2]==0): 
            self.ax21.plot(z_points[flXZ]*zf, self.gaussian_beam(z_points[flXZ], popt2[0], popt2[1], popt2[2])*xf, 'k--', alpha=0.6)
        self.ax21.set_xlabel('Z ' + '[' + xlabelXZ + ']')
        self.ax21.set_ylabel('X RMS ' + '[' + ylabelXZ + ']')
        self.ax21.set_title('Slice at Y = {0:.6f} '.format(y_pts_local[y_cut_idx]*yf) + ylabelXY)
        self.ax21.minorticks_on()
        self.ax21.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax21.grid(which='both', alpha=0.1)

#        plt.figure()
        self.ax22.clear()
        self.ax22.plot(z_points*zf, y_properties[1]*yf, '-o', alpha=0.6)
        if not(popt5[0]==0 and popt5[1]==0 and popt5[2]==0): 
            self.ax22.plot(z_points[flYZ]*zf, self.gaussian_beam(z_points[flYZ], popt5[0], popt5[1], popt5[2])*yf, 'k--', alpha=0.6)
        self.ax22.set_xlabel('Z ' + '[' + xlabelYZ + ']')
        self.ax22.set_ylabel('Y RMS ' + '[' + ylabelYZ + ']')
        self.ax22.set_title('Slice at X = {0:.6f} '.format(x_pts_local[x_cut_idx]*xf) + xlabelXY)
        self.ax22.minorticks_on()
        self.ax22.tick_params(which='both', axis='both', direction='in', right=True, top=True)
        self.ax22.grid(which='both', alpha=0.1)

        if not(xrange[0]==0.0 and xrange[1]==0.0):
            self.axXZ.set_ylim(xrange[0], xrange[1])
            self.axXY.set_xlim(xrange[0], xrange[1])       

        if not(yrange[0]==0.0 and yrange[1]==0.0):
            self.axYZ.set_ylim(yrange[0], yrange[1])
            self.axXY.set_ylim(yrange[0], yrange[1]) 
            
        if not(zrange[0]==0.0 and zrange[1]==0.0):
            self.axXZ.set_xlim(zrange[0], zrange[1])
            self.axYZ.set_xlim(zrange[0], zrange[1])
            self.ax11.set_xlim(zrange[0], zrange[1])
            self.ax12.set_xlim(zrange[0], zrange[1])            
            self.ax21.set_xlim(zrange[0], zrange[1])
            self.ax22.set_xlim(zrange[0], zrange[1])
            
        self.figureXZ.canvas.draw()
        self.figureYZ.canvas.draw()
        self.figureXY.canvas.draw()
        self.figure11.canvas.draw()
        self.figure12.canvas.draw()
        self.figure21.canvas.draw()
        self.figure22.canvas.draw()
        
        return outdict

    def print_date_i(self):
        print('\n'+'EXECUTION BEGAN AT: ', end='')
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '\n')
    
    def print_date_f(self):
        print('\n'+'EXECUTION FINISHED AT: ', end='')
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '\n')

#    def print_date_i(self):
##        sys.stdout.write('lala')
#        start_text = '\n###############\n'+'EXECUTION BEGAN AT: '+ time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n'
#        sys.stdout.write(start_text)
#        sys.stdout.flush()
##        print()
#    
#    def print_date_f(self):
##        sys.stdout.write('lala')
#        finish_text = '\n'+'EXECUTION FINISHED AT: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n###############\n'
#        sys.stdout.write(finish_text)
#        sys.stdout.flush()
#        print()

