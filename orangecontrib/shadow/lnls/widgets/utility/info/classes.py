#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 18 16:49:20 2022

@author: joao.astolfo
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout, QLabel, QPushButton,
                             QCheckBox, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                             QTabWidget, QScrollArea, QGroupBox, QComboBox, QMessageBox)
from orangewidget import gui
from oasys.widgets import gui as oasysgui#, widget


class ElementSetup(QWidget):
    def __init__(self, name, distance, focallength, use_hybrid=False, can_hybrid=False):
        super().__init__()
        
        can_hybrid = can_hybrid
        self.use_hybrid = use_hybrid
        
        self.name = name
        self.distance = distance
        self.focallength = focallength
        self.hybrid_dialog = HybridConfig(self.name, distance=self.distance, focallength_value=self.focallength,
                                          diff_plane=1, calcType=0, dist_to_img_calc=0, focallength_calc=0, nfc=0,
                                          nbins_x=100, nbins_z=100, npeak=10, fftnpts=1e5, write_file=0,
                                          automatic=1, send_original_beam=False)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.use_hybrid)
        self.label = QLabel(self.name)
        self.label.setAlignment(Qt.AlignCenter)
        self.setup_button = QPushButton('Setup')
        self.setup_button.setEnabled(self.use_hybrid)
        
        self.checkbox.stateChanged.connect(self.state_changed)
        self.setup_button.clicked.connect(self.hybrid_configuration)
        
        self.checkbox.setVisible(can_hybrid)
        self.setup_button.setVisible(can_hybrid)
        
        self.initialize()
        
        
    def initialize(self):
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.checkbox)
        self.hbox.addWidget(self.label)
        self.hbox.addWidget(self.setup_button)
        
        self.setLayout(self.hbox)
    
    
    def state_changed(self):
        if self.checkbox.isChecked():
            self.setup_button.setEnabled(True)
            self.use_hybrid = True
        else:
            self.setup_button.setEnabled(False)
            self.use_hybrid = False
    
    
    def hybrid_configuration(self):
        self.hybrid_dialog.show()
            

class HybridConfig(QWidget):
    def __init__(self, name, **kwargs):#distance=0, focallength_value=0,#,):
        super().__init__()
        
        self.name = name
        
        self.distance = kwargs.get('distance')
        self.focallength_value = kwargs.get('focallength_value')
        
        self.diff_plane = kwargs.get('diff_plane')
        self.calcType = kwargs.get('calcType')
        self.dist_to_img_calc = kwargs.get('dist_to_img_calc')
        self.focallength_calc = kwargs.get('focallength_calc')
        self.nfc = kwargs.get('nfc')
        self.nbins_x = kwargs.get('nbins_x')
        self.nbins_z = kwargs.get('nbins_z')
        self.npeaks = kwargs.get('npeak')
        self.fft = kwargs.get('fftnpts')
        self.write_file = kwargs.get('write_file')
        self.automatic = kwargs.get('automatic')
        self.send_original_beam = kwargs.get('send_original_beam')
        
        self.start_param = self.parameters(self.distance, self.focallength_value, self.diff_plane, self.calcType,
                                     self.dist_to_img_calc, self.focallength_calc, self.nfc,self.nbins_x,
                                     self.nbins_z, self.npeaks, self.fft, self.write_file, self.automatic,
                                     self.send_original_beam)
        
        self.param = self.start_param
        
        self.initializeUI(name)
        
    class parameters():
        def __init__(self, *args):
            #super().__init__()
            
            if len(args) > 0:
                self.distance = args[0]
                self.focallength_value = args[1]
                
                self.diff_plane = args[2]
                self.calcType = args[3]
                self.dist_to_img_calc = args[4]
                self.focallength_calc = args[5]
                self.nfc = args[6]
                self.nbins_x = args[7]
                self.nbins_z = args[8]
                self.npeaks = args[9]
                self.fft = args[10]
                self.write_file = args[11]
                self.automatic = args[12]
                self.send_original_beam = args[13]
        
        def __enter__(self):
            return self
        
        def __exit__(self, type, value, tb):
            pass
        
        def __eq__(self, other):
            # TODO: Search a way to improve this function. How can I compare each property of two objects without calling each one?
            if (self.distance == other.distance and
                self.focallength_value == other.focallength_value and
                self.diff_plane == other.diff_plane and
                self.calcType == other.calcType and
                self.dist_to_img_calc == other.dist_to_img_calc and
                self.focallength_calc == other.focallength_calc and
                self.nfc == other.nfc and
                self.nbins_x == other.nbins_x and
                self.nbins_z == other.nbins_z and
                self.npeaks == other.npeaks and
                self.fft == other.fft and
                self.write_file == other.write_file and
                self.automatic == other.automatic and
                self.send_original_beam == other.send_original_beam): return True
            else: return False
        
    def initializeUI(self, name):
        
        self.setGeometry(100, 100, 400, 600)
        self.setWindowTitle('{0} - Hybrid Setup'.format(name))
        
        self.setupTabs()
        
        self.show
        
        
    def setupTabs(self):
        
        main_tabs = oasysgui.tabWidget(self)
        self.tab_bas = oasysgui.createTabPage(main_tabs, "Basic Settings")
        self.tab_adv = oasysgui.createTabPage(main_tabs, "Advanced Settings")
        
        self.setBasicTab()
        self.setAdvancedTab()
        
        self.set_DiffPlane()
        self.set_DistanceToImageCalc()
        
        save_button = QPushButton('Save Changes')
        save_button.clicked.connect(self.save)
        
        main_v_box = QVBoxLayout()
        main_v_box.addWidget(main_tabs)
        main_v_box.addWidget(save_button)
        
        self.setLayout(main_v_box)
        
        
    def setBasicTab(self):
        #########################
        #calculation_box = QGroupBox('Calculation Parameters')
        calculation_box = oasysgui.widgetBox(self.tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=120)
        
        ##### Diffraction Plane
        gui.comboBox(calculation_box, self, "diff_plane", label="Diffraction Plane", labelWidth=310,
                                              items=["Sagittal", "Tangential", "Both (2D)", "Both (1D+1D)"],
                                              callback=self.set_DiffPlane, sendSelectedValue=False, orientation="horizontal")
        
        self.calc = gui.comboBox(calculation_box, self, "calcType", label="Calculation Type", labelWidth=150,
                                 items=['Diffraction by Simple Aperture',
                                        'Diffraction by Mirror or Grating Size',
                                        'Diffraction by Mirror Size + Figure Errors',
                                        'Diffraction by Grating Size + Figure Errors',
                                        'Diffraction by Lens/C.R.L./Transf. Size',
                                        'Diffraction by Lens/C.R.L./Transf. Size + Thickness Errors'],
                                 callback=self.set_CalculationType, sendSelectedValue=False, orientation="vertical")
        
        self.get_visible_items()
        
        #####################
        numerical_box = oasysgui.widgetBox(self.tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=140)
        
        self.nbins = oasysgui.lineEdit(numerical_box, self, "nbins_x", "Number of bins for I(Sagittal) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.nbint = oasysgui.lineEdit(numerical_box, self, "nbins_z", "Number of bins for I(Tangential) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(numerical_box, self, "npeaks", "Number of diffraction peaks", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(numerical_box, self, "fft", "Number of points for FFT", labelWidth=260, valueType=int, orientation="horizontal")
        
        ##########################
        optional_box = oasysgui.widgetBox(self.tab_bas, "Optional file output", addSpace=False, orientation="vertical")
        
        gui.comboBox(optional_box, self, "write_file", label="Files to write out", labelWidth=220,
                                  items=["None", "Debug (star.xx)"],
                                  sendSelectedValue=False,
                                  orientation="horizontal")
    
    
    def setAdvancedTab(self):
        #################
        propagation_box = oasysgui.widgetBox(self.tab_adv, "Propagation Parameters", addSpace=True, orientation="vertical", height=240)
        
        gui.comboBox(propagation_box, self, "dist_to_img_calc", label="Distance to image", labelWidth=150,
                                    items=["Use O.E. Image Plane Distance", "Specify Value"],
                                    callback=self.set_DistanceToImageCalc, sendSelectedValue=False, orientation="horizontal")
        
        self.dist = oasysgui.lineEdit(propagation_box, self, "distance", "Distance to Image value", labelWidth=260, valueType=float, orientation="horizontal")

        self.nf = gui.comboBox(propagation_box, self, "nfc", label="Near Field Calculation", labelWidth=310,
                               items=["No", "Yes"], callback=self.set_NF,
                               sendSelectedValue=False, orientation="horizontal")

        self.focal_length_calc = gui.comboBox(propagation_box, self, "focallength_calc", label="Focal Length", labelWidth=180,
                                                 items=["Use O.E. Focal Distance", "Specify Value"],
                                                 callback=self.set_FocalLengthCalc, sendSelectedValue=False,
                                                 orientation="horizontal")

        self.focal_length = oasysgui.lineEdit(propagation_box, self, "focallength_value", "Focal Length value", labelWidth=200, valueType=float, orientation="horizontal")

        congruence_box = oasysgui.widgetBox(self.tab_adv, "Calculation Congruence Parameters", addSpace=True, orientation="vertical", height=200)

        gui.comboBox(congruence_box, self, "automatic", label="Analize geometry to avoid unuseful calculations", labelWidth=310,
                                    items=["No", "Yes"],
                                    sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(congruence_box, self, "send_original_beam", label="Send Original Beam in case of failure", labelWidth=310,
                                 items=["No", "Yes"],
                                 sendSelectedValue=False, orientation="horizontal")
        
    
    def get_visible_items(self):
        for i in range (self.calc.count()):
            self.calc.view().setRowHidden(i, True)
        
        if ('ScreenSlits' in self.name):
            self.calc.view().setRowHidden(0, False)
            self.calcType = 0
            self.calc.setCurrentIndex(0)
        
        elif ('Mirror' in self.name):
            self.calc.view().setRowHidden(1, False)
            self.calc.view().setRowHidden(2, False)
            self.calcType = 1
            self.calc.setCurrentIndex(1)
            
        elif ('Grating' in self.name):
            self.calc.view().setRowHidden(1, False)
            self.calc.view().setRowHidden(3, False)
            self.calcType = 1
            self.calc.setCurrentIndex(1)
        
        elif ('Lens' in self.name or 'CRL' in self.name or 'Transfocator' in self.name):
            self.calc.view().setRowHidden(4, False)
            self.calc.view().setRowHidden(5, False)
            self.calcType = 4
            self.calc.setCurrentIndex(4)
    
    
    def set_DiffPlane(self):
        self.nbins.setEnabled(self.diff_plane == 0 or self.diff_plane == 2)
        self.nbint.setEnabled(self.diff_plane == 1 or self.diff_plane == 2)

        self.set_CalculationType()


    def set_CalculationType(self):
        if self.calcType > 0 and self.calcType < 4 and self.diff_plane != 2:
            self.nf.setEnabled(True)
        else:
            self.nf.setEnabled(False)
            self.nfc = 0

        self.set_NF()


    def set_NF(self):
        if self.nfc == 0:
            self.focal_length_calc.setEnabled(False)
            self.focal_length.setEnabled(False)
        else:
            self.focal_length_calc.setEnabled(True)
            self.focal_length.setEnabled(True)

        self.set_FocalLengthCalc()


    def set_FocalLengthCalc(self):
         self.focal_length.setEnabled(self.focallength_calc == 1)


    def set_DistanceToImageCalc(self):
         self.dist.setEnabled(self.dist_to_img_calc == 1)
    
         
    def save(self):
        self.param = self.parameters(self.distance, self.focallength_value, self.diff_plane, self.calcType,
                                     self.dist_to_img_calc, self.focallength_calc, self.nfc,self.nbins_x,
                                     self.nbins_z, self.npeaks, self.fft, self.write_file, self.automatic,
                                     self.send_original_beam)
        
        self.start_param = self.param
        
        
    def closeEvent(self, event):        
        self.param = self.parameters(self.distance, self.focallength_value, self.diff_plane, self.calcType,
                                     self.dist_to_img_calc, self.focallength_calc, self.nfc,self.nbins_x,
                                     self.nbins_z, self.npeaks, self.fft, self.write_file, self.automatic,
                                     self.send_original_beam)
        
        if not self.param == self.start_param:
            quit = QMessageBox.question(self, 'Save Changes?', '''Do you want to save the changes you made to this optical element hybrid configuration?
                                        \nYour changes will be lost if you do not save them.''',
                                        QMessageBox.Close | QMessageBox.Cancel | QMessageBox.Save, QMessageBox.Save)
            
            if quit == QMessageBox.Save:
                self.save()
                event.accept()
            elif quit == QMessageBox.Close:
                event.accept()
            else:
                event.ignore()
    