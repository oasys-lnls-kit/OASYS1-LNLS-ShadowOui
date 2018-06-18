# Examples of OASYS1-LNLS-ShadowOui Widgets
In this folder you find a few examples of our widgets functionalities and limitations. 

## Flux Widget

### Example A: Flux of an undulator beam after a Double-Crystal Monochromator (DCM) 
In this example, a highly collimated undulator beam, modeled by a geometric source, passes through a Si(111) DCM, and the flux and power are computed using the Flux Widget. The flux is checked against SPECTRA code [refs] and the simple rule suggested by M. S. del Rio [refs]. 

For undulators, the user need to pass both the machine (energy and beam dimensions) and undulator parameters. While some of the parameters are intuitive, the following parameters are explained below:

- `Harmonic Number (n)`: This parameters is to be used together with `Target Energy (En)`, which will calculate the K-value automatically. 
- `Maximum Harmonic to include`: SRW will compute only the undulator harmonics within this value. Thus, this parameter must be always larger than the harmonic number you will use in the simulation.
- `Precision`: Precision for longitudinal/azimuthal integration in SRW. Please refer to SRW documentation.

### Example B: Flux of a Bending Magnet source after a multilayer mirror
In this example, we show how to calculate total flux and power contained in a broad band such as after a multilayer mirror. Also, the mirror acceptance is only 30 urad, so that the usage of the vertical partial acceptance (of divergence) can drastically reduce the number of rays needed. 

- `Partial Vertical Acceptance`: If `No`, it is supposed that the source widget is set in such way that the vertical divergence limits are larger than total vertical divergence of the source. If the divergence limits on the source widget does crop the beam, use the `Yes` option. This will calculate the vertical angular distribution of a bending magnet for each energy and integrate only inside the defined limits.
- `e-beam Divergence RMS V`: This is an optional parameter. If the value is 0 (zero), it will be ignored. If it is larger than 0, the electron beam divergence sigma (RMS) in the vertical direction will be convolved with the radiation angular probability density function to include the finite emittance. Note that the approximation that the radiation contribution is much large than the electron beam divergence is very good for most cases.







