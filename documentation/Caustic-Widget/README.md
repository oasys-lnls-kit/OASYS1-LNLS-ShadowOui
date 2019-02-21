
## Caustic Widget

The Caustic Widget uses Shadow's retrace method to reconstruct the beam "caustic" around the desired image plane (e.g. the focal position), in a similar fashion that FocNew PostProcessor does, but allowing the visualization of the slices (XY and ZY, where Y is the beam propagation axis). It also calculates the minimum RMS, FWHM-cut and FWHM-histo1D. If mayavi package is installed it is also possible to see a 3D visualization with interactive slicing, which can be very useful to understand the dynamics of the beam propagation for non-trivial cases (for instance, for optical elements with combined alignment errors). The caustic data is saved to a hdf5 file, and can be analyzed without running the beamline.

### 2D visualization

![twoD](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidget2D.png "TWOD")

![data](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidgetData.png "DATA")

### 3D visualization

- IMPORTANT: for 3D visualization, mayavi package must be installed in the OASYS enviroment. It has been tested successfully in VIRTUALENV virtual environments (oasys1env). For MINICONDA3 environments, installing mayavi is strongly discouraged!!

#### INSTALLING mayavi

```
source ~/oasys1env/bin/activate
pip install mayavi
deactivate
```

With mayavi, the user can have a view of the full caustic "volume", when 2D slices are not sufficient. The 3D visualization runs in a dedicated terminal which shows the slices positions. With the mouse cursor, one can rotate the 3D view, zoom in and out, and slide the slices, which automatically updates the 2D slices. Alternatively, you can click and drag over any of the 2D slices and it will update the others.

![threeD](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidget3D.png "THREED")



