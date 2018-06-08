# OASYS1-LNLS-ShadowOui
Widgets developed by the Brazilian Synchrotron Light Laboratory (LNLS) - Optics Group - with useful functions for OASYS1 

## Widgets

### Flux Widget
The Flux widget calculates the total flux (in units of ph/s) and power (in Watts) after any ShadowOui optical element or at sample position. This is done by calculating the source spectrum and convolving with the beamline energy-dependent transmittance calculated with ShadowOui.

#### Bending Magnet

The Bending Magnet spectrum is calculated analytically as in [X-ray Data Booklet](http://xdb.lbl.gov/). The analytical vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. [1] 

#### Wiggler

The Wiggler spectrum is also calculated analytically as in [X-ray Data Booklet](http://xdb.lbl.gov/). The analytical vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. [1]

#### Undulator

The Undulator (linear or elliptical) source spectrum is calculated numerically using [SRW](https://github.com/ochubar/SRW) (Synchrotron Radiation Workshop) code [2], taking into account the energy spread and finite emmitance of the electron beam.

## Examples 

## Method Details

## References

[1] James A. Clarke (2004). The Science and Technology of Undulators and Wigglers. New York, NY: Oxford University Press Inc.
[2] O. Chubar and P. Elleaume, Proc. EPAC-98, 1177 - 1179 (1998).

## Authors

- Artur Clarindo Pinto
- Sergio Augusto Lordano Luiz
- Bernd Christian Meyer

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgements

The LNLS Optics Group is very grateful to Luca Rebuffi and Manuel Sanchez del Rio, for their developments in optical simulation and colaboration on this project. 
