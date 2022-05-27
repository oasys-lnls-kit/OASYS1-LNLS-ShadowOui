#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 12 09:34:33 2022

@author: joao.astolfo
"""
import Shadow
import sys

import inspect

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout, QLabel, QPushButton,
                             QCheckBox, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                             QTabWidget, QScrollArea, QGroupBox, QComboBox)
from Shadow import ShadowTools as ST
from orangewidget import gui
from oasys.widgets import gui as oasysgui, widget
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.python_script import PythonConsole
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from orangecontrib.shadow.lnls.widgets.utility.info import classes, funcs

from Shadow.ShadowLibExtensions import CompoundOE

import numpy
import Shadow
import inspect

class HybridInfo(widget.OWWidget):

    name = "WIP Hybrid Info"
    description = "Hybrid Info. !!! WIP !!!"
    icon = "icons/info.png"
    maintainer = "João Pedro Imbriani Astolfo"
    maintainer_email = "joao.astolfo(@at@)lnls.br"
    priority = 4
    category = "Info Tools"
    keywords = ["data", "file", "load", "read"]
    
    want_basic_layout = False

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    WIDGET_WIDTH = 950
    WIDGET_HEIGHT = 650

    want_main_area = 1
    want_control_area = 0

    input_beam = None


    def __init__(self, show_automatic_box=True):
        super().__init__()
        
        self.initializeUI()
        
        
    def initializeUI(self):
        geom = QApplication.desktop().availableGeometry()
        
        window_width  = round(min(geom.width()*0.98, self.WIDGET_WIDTH))
        window_height = round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))
        
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               window_width,
                               window_height))
        
        self.setWindowTitle('Hybrid Info')
        self.setupWidgets()
        
        self.show()
    
    
    def setupWidgets(self):
        
        main_grid = QGridLayout()
        
        # Create section labels
        self.setup_label = QLabel('Setup')
        self.setup_label.setFont(QFont('Arial', 12))
        self.setup_label.setAlignment(Qt.AlignCenter)
        scr_label = QLabel('Python Script')
        scr_label.setFont(QFont('Arial', 12))
        scr_label.setAlignment(Qt.AlignLeft)
        
# =============================================================================
#         Create setup section
# =============================================================================
        setup_v_box = QVBoxLayout()
        setup_v_box.setContentsMargins(0,0,0,0)#5, 5, 5, 5)
        
        setup_v_box.addWidget(self.setup_label)
        
        self.vbox = QVBoxLayout()
        self.wi = QGroupBox()
        self.wi.setLayout(self.vbox)
        self.scroll = QScrollArea()
    
        self.scroll.setWidget(self.wi)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(self.WIDGET_HEIGHT*0.75)
        self.scroll.setFixedWidth(self.WIDGET_WIDTH*0.25)
        setup_v_box.addWidget(self.scroll)
        
        # Create buttons
        # TODO: dinamically adjust groupbox height to fill blank spaces
        # Idea: Grid inside another grid
        update_button = QPushButton('Update')
        execute_button = QPushButton('Run Script')
        self.save_button = QPushButton('Save Script to File')
        update_button.clicked.connect(self.update_script)
        execute_button.clicked.connect(self.execute_script)
        self.save_button.clicked.connect(self.save_script)
        
        # Create hybrid checkboxes
        setup_v_box.addWidget(update_button)
        setup_v_box.addWidget(execute_button)
        setup_v_box.addWidget(self.save_button)
        
        setup_v_box.addStretch()
        
# =============================================================================
#         Create python script section
# =============================================================================
        self.scr_entry = QTextEdit()
        
        self.scr_console = PythonConsole(self.__dict__, self)
        
        scr_v_box = QVBoxLayout()
        scr_v_box.setContentsMargins(5, 5, 5, 5)
        
        scr_v_box.addWidget(scr_label)
        scr_v_box.addWidget(self.scr_entry, 3)
        scr_v_box.addWidget(self.scr_console)
        
        # Add more layouts to main grid
        main_grid.addLayout(setup_v_box, 0, 0, 1, 1)
        main_grid.addLayout(scr_v_box, 0, 1, 1, 4)
        
        self.setLayout(main_grid)
    
    
    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_script(self):
        try:
            self.scr_entry.setText(str(funcs.make_python_script_from_list(self.element_list)))
        except:
            self.scr_entry.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))
   
    
    def execute_script(self):
        self._script = str(self.scr_entry.toPlainText())
        self.scr_console.write("\nRunning script:\n")
        self.scr_console.push("exec(_script)")
        self.scr_console.new_prompt(sys.ps1)
        # FIXME: add optlnls as a required package (fix console error)


    def save_script(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", ".", "*.py")[0]

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.scr_entry.toPlainText()))
                file.close()

                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtWidgets.QMessageBox.Ok)
    
    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):

                # TODO: Code detection for more elements
                #
                # Crystals done
                # Gratings done
                # Lenses 
                # CRL 
                # KB (?) 
                # Transfocators 
                # 
                # Compound elements must be broken into more elements

                # TODO: If element_list is not empty, do not create new elements, just reuse the existing ones
                # 
                # 1. old_list, new_list
                # 2. if new_list == old_list, old_list = new_list
                # 3. if new_list != old_list, check each element and compare hybrid parameters
                
                self.input_beam = beam 
                
                if 'element_list' in globals():
                    pass
                else:
                    self.element_list = []
                    
                    self.scr_entry.setText('')
                    
                    for history_element in self.input_beam.getOEHistory():
                        temp_list = []
                        name = history_element._widget_class_name
                        
                        if not history_element._shadow_source_start is None:
                            new = classes.ElementSetup(name, 0, 0)
                            temp_list.append(new)
                            temp_list.append(history_element._shadow_source_start.src)
                            
                            self.element_list.append(temp_list)
                            
                        elif not history_element._shadow_oe_start is None:
                            
                            ### TODO: This section must be optimized (credo, que gambiarra) 
                            ### Improvements: check if element contains a list and break it into multiple elements
                            if type(history_element._shadow_oe_start) is ShadowCompoundOpticalElement:
                                
                                new_list = []
                                #if isinstance(history_element._shadow_oe_start, (Shadow.CompoundOE,Shadow.ShadowLibExtensions.CompoundOE)):
                                new_list.extend(history_element._shadow_oe_start._oe.list)
                                
                                # TODO: Improve parameter detection for 'Hybridable' Compound Optical Elements.
                                # Hybrid configuration window probably need to be different. For each case (sadness and sorrow)
                                if 'Lens' in name or 'CRL' in name or 'Transfocator' in name: can = True
                                else: can = False
                                
                                new = classes.ElementSetup(name, 0, 0, can_hybrid=can)
                                for i in new_list:
                                    temp_list = [new, i]
                                    self.element_list.append(temp_list)
                    
                            else:
                                distance = history_element._shadow_oe_start._oe.T_IMAGE
                                focallength = history_element._shadow_oe_start._oe.SIMAG
                                
                                if 'Crystal' in name or 'Zone Plate' in name: can = False
                                else: can = True
                                
                                new = classes.ElementSetup(name, distance, focallength, can_hybrid=can)
                                temp_list.append(new)
                                temp_list.append(history_element._shadow_oe_start._oe)
                            
                                self.element_list.append(temp_list)
                                
                        self.vbox.addWidget(new)
                    self.vbox.addStretch()

                try:
                    self.scr_entry.setText(str(funcs.make_python_script_from_list(self.element_list)))
                except:
                    self.scr_entry.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HybridInfo()
    sys.exit(app.exec_())