# OASYS1-LNLS-ShadowOui
Widgets developed by the Brazilian Synchrotron Light Laboratory (LNLS) - Optics Group - with useful functions for OASYS1 

## Installation

The procedure recommended is to install this package in develop mode, which makes it easy to uninstall afterwards, if desired. Make sure to use the correct python3 - the procedure below will work for OASYS1 standard installation using miniconda at home directory.

```
git clone https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui
cd OASYS1-LNLS-ShadowOui
~/miniconda3/bin/python3 setup.py develop
```

To uninstall it, simply run the command below and delete the folder.

```
~/miniconda3/bin/python3 setup.py develop --uninstall
```

## Widgets

### Flux Widget
The Flux widget calculates the total flux (in units of ph/s) and power (in Watts) after any ShadowOui optical element or at sample position. This is done by calculating the source spectrum and convolving with the beamline energy-dependent transmittance calculated with ShadowOui.

![gui](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/FluxWidgetGUI.png "GUI")

The Bending Magnet and Wiggler spectrum is calculated analytically as in [X-ray Data Booklet](http://xdb.lbl.gov/). The correct (not gaussian approximation) vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. This enables optimization of the simulation when the beamline vertical acceptance is not total. 

The Linear Undulator (elliptical undulator is to be implemented soon) source spectrum is calculated numerically using [SRW](https://github.com/ochubar/SRW) (Synchrotron Radiation Workshop) code (see ref. [1]), taking into account the energy spread and finite emittance of the electron beam. SRW is natively shipped with OASYS1 and should be enabled.

### Examples 

See the [Examples Folder](examples) for a few examples and usage tips of the Flux Widget.

### User's Guideline

To use Flux Widget, just link the desired optical element (or source) widget to the Flux Widget and modify the parameters corresponding to the source.

**IMPORTANT NOTE**: In `Calculation Settings` tab, the user must define the source vertical and horizontal acceptance range where the flux will be calculated. Usually, the acceptance limits must the same as those defined at the source widget. However, when using bending magnet and wiggler sources, the source divergence distribution may have rays outside the defined limits. In this case, the user must adjust the acceptance limits on the Flux Widget, so that its spectrum corresponds well to the Shadow distribution. To degub the results, all the intermediate steps of the calculation are shown in other tabs (Source Spectrum, Beamline Transmittance, Histogram, Source Acceptance and Output)

### Method Details

![method](https://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui/blob/master/images/flux_method.png "Flux Method")

## References

[1] [O. Chubar and P. Elleaume, Proc. EPAC-98, 1177 - 1179 (1998)](https://accelconf.web.cern.ch/AccelConf/e98/PAPERS/THP01G.PDF).

## Authors

- Artur Clarindo Pinto (artur.pinto@lnls.br)
- Sergio Augusto Lordano Luiz (sergio.lordano@lnls.br)
- Bernd Christian Meyer (bernd.meyer@lnls.br)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgements

The LNLS Optics Group is very grateful to Luca Rebuffi and Manuel Sanchez del Rio, for their developments in optical simulation and colaboration on this project. 
