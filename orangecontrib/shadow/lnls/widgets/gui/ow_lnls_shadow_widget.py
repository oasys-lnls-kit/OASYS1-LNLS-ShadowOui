from oasys.widgets import widget

from orangewidget import gui
from orangewidget.settings import Setting

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

from oasys.widgets.gui import ConfirmDialog

import xraylib

class LNLSShadowWidget(widget.OWWidget):
    is_weird_shadow_bug_fixed = False

    want_main_area=1

    is_automatic_run = Setting(True)

    error_id = 0
    warning_id = 0
    info_id = 0

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=True):
        super().__init__()

        if not show_automatic_box:
            self.TABS_AREA_HEIGHT = 620
        else:
            self.TABS_AREA_HEIGHT = 555

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")

        if show_automatic_box :
            gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    #########################################################
    #
    # This xraylib call prevents an anomalous behaviour of
    # SHADOW due to some unexplained python problem (apparently on the C-binder).
    # It happens sometimes after installing new non-pip libraries
    # I don't know how and why, but this call to xraylib removes the
    # problem
    #
    #########################################################

    def fixWeirdShadowBug(self):
        if not LNLSShadowWidget.is_weird_shadow_bug_fixed:
            try:
                xraylib.Refractive_Index_Re("LaB6", 10000, 4)
            except:
                pass

            LNLSShadowWidget.is_weird_shadow_bug_fixed = True
