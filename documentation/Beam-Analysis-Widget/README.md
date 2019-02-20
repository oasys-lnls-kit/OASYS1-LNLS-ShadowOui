
## Beam Analysis
The Beam Analysis is based on the PlotXY widget and gives some options to the user. The idea of this widget is to extract from ShadowOui better figures, with meaninful results. For instance, it is possible calculate not only the beam full-width-half-maximum (FWHM), but also its root-mean-square (RMS), mean value, peak position and data range. The 1D slices may be the 1D histogram (as plotXY), or a cut at a given position (a few options are implemented: cut at (0,0), at peak position, at mean value or at a user given position). It can also fit the beam profile to gaussian and lorentzian distributions (and their sum). All the properties mentioned can be calculated for the fitted distribution as well.

Apart from the statistical calculations, it is also possible to customize the axis labels, add a small text with a description of the simulation to the figure, and show up to 3 texts in the figure (with beam size, for example). The figure can then be exported to a png file. The 2D histogram can also be exported as a matrix that can be readily imported in python, excel, or anything else. 

![BAgui](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/BeamAnalysisGUI.png "BAGUI")

### Options (Calculations Settings Tab)

#### Plot Controls

1. Slices: the 1D slices showing the X and Y intensities profiles can be the 1D histogram (as in plotXY) or a cut at a given position (where cut means a single line or column of the 2D histogram). The implemented options are: cut at (0,0), at peak position, at mean value or at a user given position.

2. Total Flux (Power) in ph/s (Watt): if you know the total flux (or power) at the image plane, use this to input its value in ph/s (or Watt). The ordinates axis of the 1D plots will show then the flux or power distribution. If the Slices are any of the cut options, the units will be ph/s/mm^2 or W/mm^2 (or ph/s/um^2 or W/um^2, depending wether U.M. conversion is active or not - note that, for now, this will only work for workspaces in mm units). If the Slices are 1D histrograms, the units will be ph/s/mm or W/mm (or ph/s/um or W/um).

3. Fitting: None, Gaussi, Lorentz or Lorentz+Gauss. If different from None, it will try to fit the slices to the desired distribution. The Lorentz+Gauss option will fit a sum of a lorentzian and a gaussian distribution. It generally fits quasi-gaussian beams better than the other 2 options. Although it has no physical meaning, it can be useful to "filter" the histogram high frequency noises and thus usually gives more accurate FWHM values. 

4. Scale: Data can be shown in Linear or Logarithmic scales.

5. Text 1, 2, 3: These three options allow the user to add texts to the figure, showing the beam FWHM or RMS, for instance, or the fit FWHM, RMS. The option called "Title" will add to the figure the text given in the field below (Title / Description). This is very useful to record, in the picture, relevant parameters to the simulation (for instance, the position where you are observing the beam, energy, source parameters, and so on).

6. Title / Description: This field is used to write a text that can be displayed in the figure. The limit is around 40 characters, and the line break is not automatic (one has to include spaces until the line is broke at the desired position).

7. Horizontal / Vertical Label: These fields can be used to overwrite the abcissa and ordinate axes labels. 

8. File Name to Save: any name with .png extension

9. Export Figure: This button is used to save the displayed figure to disk in png format. Note that it saves the displayed figure, but it does not updates the figrue. Use the Refresh button to update the figure before exporting the figure.

#### Advanced Options

This box (below Plot Controls) contains some other few options that should be used with care.

![adv](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/BeamAnalysisAdvanced.png "ADV")

1. FWHM innermost / outermost: sometimes the beam presents more than one peak. In this case, Innermost will search the firsts half-widths-half-maximum from the peak to the borders. Outermost will search from the borders to the peak.

2. Threshold for FWHM: must be a value between 0 and 1, relative to the peak intensity. This options allows to calculate the beam full-width not only at half-maximum (0.5), but also at any other value, for instance one-tenth-maximum (0.1).

3. Oversampling factor for FWHM: if this factor is greater than 1, it will interpolate the slice distribution and resample the distribution with a number of points equal to the original number of points time this factor, to increase resolution in the calculation. Otherwise the resolution is limited to the original bin width.

4. Large limits: If the plot range is user defined, it is possible that one or two axes limits are larger than the actual data. In this case, the area without data will be shown in white. If the user wants to consider this area as zero, one can set this value to add zeros to the axes borders (zero padding), virtually increasing the data range. This number is the increasing factor (eg. 1 means 100% increase, thus doubling the ranges).
 
5. Gaussian Filter: this option can be used to apply a gaussian filter to the 2D histogram, if the data is too noisy. This is the factor given as argument to scipy.ndimage.gaussian_filter. 













