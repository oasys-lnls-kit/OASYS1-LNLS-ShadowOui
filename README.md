# OASYS1-LNLS-ShadowOui
The Brazilian Synchrotron Light Laboratory (LNLS) Optics Group is developing widgets with useful functions for OASYS1 

## Widgets

### Flux
The Flux widget calculates the total flux (in units of ph/s) and power (in Watts) after any ShadowOui optical element or at sample position. This is done by calculating the source spectrum and convolving with the beamline energy-dependent transmittance calculated with ShadowOui.

#### Bending Magnet

The Bending Magnet spectrum is calculated analytically as in X-ray Data Booklet [add link]. The analytical vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. [reference] 

#### Wiggler

The Wiggler spectrum is also calculated analytically as in X-ray Data Booklet [add link]. The analytical vertical angular distribution of the source is computed to account for partial acceptance of the vertical divergence. [reference]

#### Undulator

The Undulator (linear or elliptical) source spectrum is calculated numerically using SRW (Synchrotron Radiation Workshop) code [reference], taking into account the energy spread and finite emmitance of the electron beam.

** caution **

## Examples 

## References

## Authors

## License

## Acknowledgements
