# Author: Gael Varoquais <gael.varoquais@normalesup.org>
# Copyright (c) 2009, Enthought, Inc.
# License: BSD Style.

import numpy as np
import h5py
import optparse

import sys
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget

class VolumeSlicerPyVista(MainWindow):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Volume Slicer (PyVista)")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.grid_layout = QGridLayout(self.main_widget)

        self.data = pv.ImageData()
        self.data.dimensions = data.shape
        self.data.point_data["values"] = data.flatten(order="F")  

        # The 4 views displayed
        self.scene3d = QtInteractor(self)
        self.scene_x = QtInteractor(self)
        self.scene_y = QtInteractor(self)
        self.scene_z = QtInteractor(self)
        
        # Add the views to the grid layout
        self.grid_layout.addWidget(self.scene_y, 0, 0) 
        self.grid_layout.addWidget(self.scene_z, 1, 0) 
        self.grid_layout.addWidget(self.scene_x, 0, 1) 
        self.grid_layout.addWidget(self.scene3d, 1, 1) 
        
        self.make_3d_view()
        self.make_side_view()
        
    def reset_views(self):
        self.make_3d_view()
        self.make_side_view()
    
    def make_3d_view(self):
                
        self.scene3d.clear_plane_widgets()
        
        self.scene3d.add_text("3D View", font_size=10)
        self.scene3d.add_volume(self.data, cmap="viridis", opacity="linear", show_scalar_bar=False) 
        self.scene3d.add_checkbox_button_widget(callback=lambda value: self.reset_views(), position=(850, 40), size=30, value=False)
        self.scene3d.add_text("Reset Views", font_size=10, position=("lower_right"))
        
        self.scene3d.add_plane_widget(callback=self.update_x_slice, normal='x', normal_rotation=False)
        self.scene3d.add_plane_widget(callback=self.update_y_slice, normal='y', normal_rotation=False)
        self.scene3d.add_plane_widget(callback=self.update_z_slice, normal='z', normal_rotation=False)

        self.scene3d.show_axes()
        
    def make_side_view(self):
        
        center = self.data.center
        
        self.scene_x.add_text("Cross section YZ Plane (X slice)", font_size=12)
        self.scene_x.add_mesh(self.data.slice(normal='x', origin=center), name='slice_x', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_x.disable()
        self.scene_x.view_yz()
        self.scene_x.zoom_camera(2)
        
        self.scene_y.add_text("XZ Plane (Y slice)", font_size=10)
        self.scene_y.add_mesh(self.data.slice(normal='y', origin=center), name='slice_y', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_y.disable()
        self.scene_y.view_xz()
        self.scene_y.zoom_camera(2)
        
        self.scene_z.add_text("XY Plane (Z slice)", font_size=10)
        self.scene_z.add_mesh(self.data.slice(normal='z', origin=center), name='slice_z', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_z.disable()
        self.scene_z.view_xy()
        self.scene_z.zoom_camera(1.3)

    def update_x_slice(self, normal, origin):
        self.scene_x.add_mesh(self.data.slice(normal=normal, origin=origin), name='slice_x', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_x.zoom_camera(2)
        
    def update_y_slice(self, normal, origin):
        self.scene_y.add_mesh(self.data.slice(normal=normal, origin=origin), name='slice_y', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_y.zoom_camera(2)
        
    def update_z_slice(self, normal, origin):
        self.scene_z.add_mesh(self.data.slice(normal=normal, origin=origin), name='slice_z', cmap="viridis", show_scalar_bar=False, reset_camera = True)
        self.scene_z.zoom_camera(1.3)

if __name__=='__main__':

    p = optparse.OptionParser()
    p.add_option('-f', '--infile', dest='infile', metavar='FILE', default='', help='input file name')
    opt, args = p.parse_args()    
    
    filename=opt.infile

    with h5py.File(filename, 'r+') as f:
            
        zStart = f.attrs['zStart']
        zFin = f.attrs['zFin']
        nz = f.attrs['nz']
        
        dset_names = list(f.keys())
        
        #####################
        # find maximum ranges
        #####################
        xy_range = np.zeros((len(dset_names), 4))
        dset = dset_names[2]
        xS, xF, nx =  f[dset].attrs['xStart'], f[dset].attrs['xFin'], f[dset].attrs['nx']
        yS, yF, ny =  f[dset].attrs['yStart'], f[dset].attrs['yFin'], f[dset].attrs['ny']
        
        x_array = np.linspace(xS, xF, nx)[::-1]
        y_array = np.linspace(yS, yF, ny)[::-1]
        z_array = np.linspace(zStart, zFin, nz)
        
        for i in range(len(dset_names)-2):
                        
            dset = dset_names[i+2]
            mtx = np.array(f[dset])
            mtx = mtx[:,::-1][::-1,:]            
            
            if i==0:
                values = mtx
            else:
                values = np.dstack((values,mtx))
    #x, y, z = np.ogrid[-5:5:64j, -5:5:64j, -5:5:64j]
    #data = np.sin(3*x)/x + 0.05*z**2 + np.cos(3*y)        
    data = values
    
    app = QApplication(sys.argv)
    window = VolumeSlicerPyVista(data)
    window.show()
    sys.exit(app.exec())