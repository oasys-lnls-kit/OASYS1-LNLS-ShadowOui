
## Caustic Widget

The Caustic Widget uses Shadow's retrace method to reconstruct the beam "caustic" around the desired image plane (e.g. the focal position), in a similar fashion that FocNew PostProcessor does, but allowing the visualization of the slices (XY and ZY, where Y is the beam propagation axis). It also calculates the minimum RMS, FWHM-cut and FWHM-histo1D. If mayavi package is installed it is also possible to see a 3D visualization with dynamic slicing, which can be very useful to understand beam propagation dynamic for non-trivial cases (for instance, for optical elements with combined alignment errors). The caustic data is saved to a hdf5 file, and can be analyzed without running the beamline.

### 2D visualization

![twoD](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidget2D.png "TWOD")

![data](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidgetData.png "DATA")

### 3D visualization

![threeD](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/CausticWidget3D.png "THREED")



