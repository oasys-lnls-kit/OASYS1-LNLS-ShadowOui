"""

"""
# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>
# Copyright (c) 2009, Enthought, Inc.
# License: BSD Style.

import numpy as np
import optparse
from traits.api import HasTraits, Instance, Array, \
    on_trait_change
from traitsui.api import View, Item, HGroup, Group

from tvtk.api import tvtk
from tvtk.pyface.scene import Scene

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import SceneEditor, MayaviScene, \
                                MlabSceneModel                              
import h5py



################################################################################
# The object implementing the dialog
class VolumeSlicer(HasTraits):
    # The data to plot
    data = Array()

    # The 4 views displayed
    scene3d = Instance(MlabSceneModel, ())
    scene_x = Instance(MlabSceneModel, ())
    scene_y = Instance(MlabSceneModel, ())
    scene_z = Instance(MlabSceneModel, ())

    # The data source
    data_src3d = Instance(Source)

    # The image plane widgets of the 3D scene
    contour_3d = Instance(PipelineBase)
    ipw_3d_x = Instance(PipelineBase)
    ipw_3d_y = Instance(PipelineBase)
    ipw_3d_z = Instance(PipelineBase)

    _axis_names = dict(x=0, y=1, z=2)


    #---------------------------------------------------------------------------
    def __init__(self, **traits):
        super(VolumeSlicer, self).__init__(**traits)
        # Force the creation of the image_plane_widgets:
        self.contour_3d
        self.ipw_3d_x
        self.ipw_3d_y
        self.ipw_3d_z


    #---------------------------------------------------------------------------
    # Default values
    #---------------------------------------------------------------------------
    def _data_src3d_default(self):
        return mlab.pipeline.scalar_field(self.data,
                            figure=self.scene3d.mayavi_scene)
        
    def make_ipw_3d(self,axis_name,imageON=True):
        if imageON==True:
            ipw = mlab.pipeline.image_plane_widget(self.data_src3d,
                            figure=self.scene3d.mayavi_scene,
                            plane_orientation='%s_axes' % axis_name, 
                            name='Cut %s' % axis_name)
            
        else:
            ipw = mlab.pipeline.image_plane_widget(self.data_src3d,
                            figure=None,
                            plane_orientation='%s_axes' % axis_name, 
                            name='Cut %s' % axis_name)
                            
        return ipw

    def make_coutour(self):
        csurf = mlab.pipeline.contour_surface(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        contours=30, opacity=0.5)
        return csurf
    
    def _ipw_3d_c_default(self):
        return self.make_coutour()
    
    def _ipw_3d_x_default(self):
        return self.make_ipw_3d('x',True)

    def _ipw_3d_y_default(self):
        return self.make_ipw_3d('y',True)

    def _ipw_3d_z_default(self):
        return self.make_ipw_3d('z',True)

    #---------------------------------------------------------------------------
    # Scene activation callbaks
    #---------------------------------------------------------------------------
    @on_trait_change('scene3d.activated')
    def display_scene3d(self):
        outline = mlab.pipeline.outline(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        )       
        
        self.scene3d.mlab.view(40, 50)
        self.make_coutour()     
        mlab.orientation_axes()
        # Interaction properties can only be changed after the scene
        # has been created, and thus the interactor exists
        for ipw in (self.ipw_3d_x, self.ipw_3d_y):
            # Turn the interaction off
            ipw.ipw.interaction = 0
        for ipw in (self.ipw_3d_z):
             # Turn the interaction on
            ipw.ipw.interaction = 1
        
        self.scene3d.scene.background = (0, 0, 0)
        # Keep the view always pointing up
        self.scene3d.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleTerrain()


    def make_side_view(self, axis_name):
        scene = getattr(self, 'scene_%s' % axis_name)
       
        ###
#        if axis_name=='z':
#            pts = self.make_ipw_3d('z',False)
#            out = mlab.pipeline.probe_data(pts, 50, 50, 50)
#            print(out)
        ###
        # To avoid copying the data, we take a reference to the
        # raw VTK dataset, and pass it on to mlab. Mlab will create
        # a Mayavi source from the VTK without copying it.
        # We have to specify the figure so that the data gets
        # added on the figure we are interested in.
        outline = mlab.pipeline.outline(
                            self.data_src3d.mlab_source.dataset,
                            figure=scene.mayavi_scene,
                            )
        ipw = mlab.pipeline.image_plane_widget(
                            outline,
                            plane_orientation='%s_axes' % axis_name,
                            name='Cut view %s' % axis_name)
        
        
            
        setattr(self, 'ipw_%s' % axis_name, ipw)

        # Synchronize positions between the corresponding image plane
        # widgets on different views.
        ipw.ipw.sync_trait('slice_position',
                            getattr(self, 'ipw_3d_%s'% axis_name).ipw)

        # Make left-clicking create a crosshair
        ipw.ipw.left_button_action = 0
        # Add a callback on the image plane widget interaction to
        # move the others
        def move_view(obj, evt):
            position = obj.GetCurrentCursorPosition()
            for other_axis, axis_number in self._axis_names.items():
                if other_axis == axis_name:
                    continue
                ipw3d = getattr(self, 'ipw_3d_%s' % other_axis)
                ipw3d.ipw.slice_position = position[axis_number]
                if axis_name=='x':     
                        xpos,ypos,zpos = position
                        a = []
                        for i in range(100):                            
                            out = mlab.pipeline.probe_data(ipw, i, ypos, zpos)
                            a.append([out])
                        
                        print('Y, Z cut at '+'{0:.6f} um, {1:.6f} um'.format(y_array[int(ypos)]*1e3, z_array[int(zpos)]*1e3))
                        
                if axis_name=='y':     
                        xpos,ypos,zpos = position
                        a = []
                        for i in range(100):                            
                            out = mlab.pipeline.probe_data(ipw, xpos, i, zpos)
                            a.append([out])
                        
                        print('X, Z cut at '+'{0:.6f} um, {1:.6f} um'.format(x_array[int(xpos)]*1e3, z_array[int(zpos)]*1e3))
       

        ipw.ipw.add_observer('InteractionEvent', move_view)
        ipw.ipw.add_observer('StartInteractionEvent', move_view)

        # Center the image plane widget
        ipw.ipw.slice_position = 0.5*self.data.shape[
                    self._axis_names[axis_name]]
        
       
        
        # Position the view for the scene
        views = dict(x=( 0, 90),
                     y=(90, 90),
                     z=( 0,  0),
                     )
        scene.mlab.view(*views[axis_name])
        # 2D interaction: only pan and zoom
        scene.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleImage()
        scene.scene.background = (0, 0, 0)
        
        # Label:
        if axis_name=='x':   
            mlab.text(0.01, 0.9, 'Plane YZ', width=0.2)
        
        if axis_name=='y':   
            mlab.text(0.01, 0.9, 'Plane XZ', width=0.2)
        
        if axis_name=='z':   
            mlab.text(0.01, 0.9, 'Plane XY', width=0.2)
        
        
        
    

    @on_trait_change('scene_x.activated')
    def display_scene_x(self):
        return self.make_side_view('x')

    @on_trait_change('scene_y.activated')
    def display_scene_y(self):
        return self.make_side_view('y')

    @on_trait_change('scene_z.activated')
    def display_scene_z(self):
        return self.make_side_view('z')




    #---------------------------------------------------------------------------
    # The layout of the dialog created
    #---------------------------------------------------------------------------
    view = View(HGroup(
                  Group(
                       Item('scene_y',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       Item('scene_z',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       show_labels=False,
                  ),
                  Group(
                       Item('scene_x',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       Item('scene3d',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       show_labels=False,
                  ),
                ),
                resizable=True,
                title='Volume Slicer',
                )


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
        dset = dset_names[0]
        xS, xF, nx =  f[dset].attrs['xStart'], f[dset].attrs['xFin'], f[dset].attrs['nx']
        yS, yF, ny =  f[dset].attrs['yStart'], f[dset].attrs['yFin'], f[dset].attrs['ny']
        
        x_array = np.linspace(xS, xF, nx)[::-1]
        y_array = np.linspace(yS, yF, ny)[::-1]
        z_array = np.linspace(zStart, zFin, nz)
        
        for i in range(len(dset_names)-1):
                        
            dset = dset_names[i]
            mtx = np.array(f[dset])
            mtx = mtx[:,::-1][::-1,:]            
            
            if i==0:
                values = mtx
            else:
                values = np.dstack((values,mtx))
    #x, y, z = np.ogrid[-5:5:64j, -5:5:64j, -5:5:64j]
    #data = np.sin(3*x)/x + 0.05*z**2 + np.cos(3*y)
    data = values
    
    
    m = VolumeSlicer(data=data)
    m.configure_traits()
