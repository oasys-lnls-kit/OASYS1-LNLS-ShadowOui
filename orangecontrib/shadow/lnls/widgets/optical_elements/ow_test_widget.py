import os

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

import orangecanvas.resources as resources

from orangecontrib.shadow.lnls.widgets.gui.ow_lnls_shadow_widget import LNLSShadowWidget

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

class TestWidget(LNLSShadowWidget):
    name = "TEST"
    description = "this class is for test"
    icon = "icons/test.png"
    priority = 1
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi@elettra.eu"
    category = ""
    keywords = ["TEST"]

    inputs = [("Input Beam", ShadowBeam, "set_beam")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Beam",
                "id": "Beam"}]

    test_value = Setting(20.0)

    def __init__(self):
        super(TestWidget, self).__init__()

        self.runaction = widget.OWAction("Do Test", self)
        self.runaction.triggered.connect(self.do_test)
        self.addAction(self.runaction)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        new_mainArea = oasysgui.widgetBox(self.mainArea, "", addSpace=False, orientation="horizontal")

        box = oasysgui.widgetBox(new_mainArea, "Sub Area 1", addSpace=False, orientation="vertical", height=650)
        box = oasysgui.widgetBox(new_mainArea, "Sub Area 2", addSpace=False, orientation="vertical", height=650)

        box = oasysgui.widgetBox(self.controlArea, "Setting", addSpace=False, orientation="vertical", height=500, width=self.CONTROL_AREA_WIDTH - 20)

        oasysgui.lineEdit(box, self, "test_value", "Line 1", labelWidth=300, valueType=float, orientation="horizontal")

        # Here you decide the layout

        gui.button(box, self, "do test", callback=self.do_test)

    def set_beam(self, data):
        self.send("Beam", data)

    def do_test(self):

        path  = os.path.join(resources.package_dirname("orangecontrib.shadow.lnls"), "data", "test.dat")

        import numpy

        array = numpy.loadtxt(path, skiprows=1)

        print(array)
