# 2025LEDProject

The LED project for FRC team 1038

## Simulation Website

<https://wokwi.com/projects/new/circuitpython-pi-pico>

## Setting up the project

1. Clone the project
2. Install MicroPico extension from the workspace recommended
3. `CTRL+SHIFT+P` and run `MicroPico: Configure project`

## Configuration

To configure the LEDs, edit the parameter in the `configure` function on the `NeopixelController` object. On the `config` parameter, add the port number as the key and a tuple as the object. The values inside this tuple will be the 