# OASYS1-LNLS-ShadowOui
Widgets developed by the Brazilian Synchrotron Light Laboratory (LNLS) - Optics Group - with useful functions for OASYS1 

## Widgets

### - Flux Widget
The Flux widget calculates the total flux (in units of ph/s) and power (in Watts) after any ShadowOui optical element or at sample position. This is done by calculating the source spectrum and convolving with the beamline energy-dependent transmittance calculated with ShadowOui.

![gui](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/FluxWidgetGUI.png "GUI")

The Bending Magnet and Wiggler spectrum is calculated analytically as in [X-ray Data Booklet](http://xdb.lbl.gov/). The correct (not gaussian approximation) vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. This enables optimization of the simulation when the beamline vertical acceptance is not total. 

The Linear Undulator (elliptical undulator is to be implemented soon) source spectrum is calculated numerically using [SRW](https://github.com/ochubar/SRW) (Synchrotron Radiation Workshop) code (see ref. [1]), taking into account the energy spread and finite emittance of the electron beam. SRW is natively shipped with OASYS1 and should be enabled.

## Examples 

See the [Examples Folder](examples) for a few examples and usage tips of the Flux Widget.

## Method Details

![method](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/flux_method.png "Flux Method")

## References

[1] O. Chubar and P. Elleaume, Proc. EPAC-98, 1177 - 1179 (1998).

## Authors

- Artur Clarindo Pinto (artur.pinto@lnls.br)
- Sergio Augusto Lordano Luiz (sergio.lordano@lnls.br)
- Bernd Christian Meyer (bernd.meyer@lnls.br)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgements

The LNLS Optics Group is very grateful to Luca Rebuffi and Manuel Sanchez del Rio, for their developments in optical simulation and colaboration on this project. 
