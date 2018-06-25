# Examples of OASYS1-LNLS-ShadowOui Widgets
In this folder you find a few examples of our widgets functionalities and limitations. Please remember to change the working directory and running preprocessors before running source/trace.

## Flux Widget

### Example A: Flux of an undulator beam after a Double-Crystal Monochromator (DCM) 
In this example, a highly collimated undulator beam, modeled by a geometric source, passes through a Si(111) DCM, and the flux and power are computed using the Flux Widget. The flux is checked against [SPECTRA code](http://spectrax.org/spectra/index.html) (see ref. [1]) and the simple rule suggested by M. S. del Rio (see ref. [2]). 

![widgetsA](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/ExampleA_widgets.png "widgetsA")

For undulators, the user need to pass both the machine (energy and beam dimensions) and undulator parameters. While some of the parameters are intuitive, the following parameters are explained below:

- `Harmonic Number (n)`: This parameters is to be used together with `Target Energy (En)`, which will calculate the K-value automatically. 
- `Maximum Harmonic to include`: SRW will compute only the undulator harmonics within this value. Thus, this parameter must be always larger than the harmonic number you will use in the simulation, or at least equal.
- `Precision`: Precision for longitudinal/azimuthal integration in SRW. Please refer to SRW documentation.

The undulator is set to use the 7th harmonic at 10 keV, and the source parameters are as in the figure below:

![fluxA](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/ExampleA_flux.png "fluxA")

As one can see, the total flux is calculated to be 4.00e+12 ph/s/100mA. To double-check the results, we use SPECTRA to calculate the flux at 10 keV, which yields 3.26e+13 ph/s/0.1%bw/100mA (very close to SRW calculation, shown in the Source Spectrum Tab). We can multiply this value to the simple factor 0.135 (see ref. [2]) to account for the Si(111) DCM bandwidth, which gives 4.4e+12 ph/s/100mA, that is in reasonable agreement with the Flux Widget calculation. It is important to note that the factor used is an approximation (generaly a good one), and in this simulation, the beam is not perfectly collimated, so small deviations are expected. 

The Output Tab shows a comprehensive summary of the parameters used, for debbuging (figure below). It is important to check if the source acceptance limits used match the source widget divergence distribution. The horizontal (H) and vertical (V) Divergence Limits parameters, in the Calculation Settings Tab, can be used to adjust the acceptance limits, if needed.

![outputA](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/ExampleA_output.png "outputA")


### Example B: Flux of a Bending Magnet source after a multilayer mirror
In this example, we show how to calculate total flux and power contained in a broad band such as after a multilayer mirror. Also, the mirror acceptance is only 30 microradians, so that the usage of the vertical partial acceptance (of divergence) can drastically reduce the number of rays needed. 

- `Partial Vertical Acceptance`: If `No`, it is supposed that the source widget is set with vertical divergence limits larger than the total vertical divergence of the beam. If the divergence limits on the source widget does crop the beam, use the `Yes` option. This will calculate the vertical angular distribution of a bending magnet for each energy and integrate only inside the defined limits.
- `e-beam Divergence RMS V`: This is an optional parameter. If the value is 0 (zero), it will be ignored. If it is larger than 0, the electron beam divergence sigma (RMS) in the vertical direction will be convolved with the radiation angular probability density function to include the finite emittance. Note that the approximation that the radiation contribution is much larger than the electron beam divergence is very good for most cases.

The bending magnet parameters are the ESRF standard ones, and the first harmonic of the multilayer is set to about 32.0 keV (figure below).
 
![widgetsB](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/ExampleB_widgets.png "widgetsB")

In this example we have two branches in the workspace. In branch A, the source is optimized to the plane mirror vertical acceptance, which is 30 microradians. In branch B, the divergence is not limited, so there are rays with angles larger than the mirror acceptance, which decreases the overall beamline transmittance. In this case, the acceptance is limited by a slit. 

This examples shows that both simulations give the same result, despite the branch A configuration needs much less rays in the source and yields better statistics at the end. Note that the calculated source spectrum and beamline transmittance are different for the two configurations, but the final spectrum (called Beamline Spectrum) is the same (figure below).

![compB](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/ExampleB_comparison.png "comparisonB")

In the vertical angular distribution figure above, the gray solid line represents the acceptance limits of the source (which can be defined by the user), and the black solid line represents the distribution Full Width at Half Maximum (FWHM).

## References 

[1] [T. Tanaka and H. Kitamura, Journal of Synchrotron Radiation 8, 1221 (2001)](https://doi.org/10.1107/S090904950101425X)

[2] [Manuel Sanchez del Rio, Olivier Mathon, Proc. SPIE 5536, (2004)](https://doi.org/10.1117/12.559326)



