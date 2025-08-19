# 2025LEDProject

The LED project for FRC team 1038

## Simulation Website

<https://wokwi.com/projects/new/micropython-pi-pico>

## Setting up the project

1. Clone the project
2. Install MicroPico extension from the workspace recommended
3. `CTRL+SHIFT+P` and run `MicroPico: Upload project to Pico`

## Configuration

To configure the LEDs, edit the parameters in the `configure` function on the `NeopixelController` object:
```
controller = NeopixelController()
controller.configure(
    ...
)
```

The configure function takes in a parameter as a dictionary to hold all the configuration information and another parameter to hold the current mode, represented as a letter. This dictionary accepts the port number as the key and a tuple as the object. The values inside this tuple will be the config of partitions of the LED strip.

```
controller = NeopixelController()
controller.configure(
    {
        2: (
            ...,
            ...
        ),
        3: (
            ...,
            ...
        ),
        4: (
            ...,
            ...
        )
    },
    "D"
)
```

Since the program allows for partitioning LED strips to run different effects on the same strip at once, each tuple representing the leds port has it's own set of tuples with two values: the number of LEDs with that configuration and the configuration applied to the selected LEDs, which is represented as a dictionary.

```
controller = NeopixelController()
controller.configure(
    {
        2: (
            (5, {
                ...
            }),
            (12, {
                ...
            })
        ),
        3: (
            (10, {
                ...
            }),
            (7, {
                ...
            }),
        ),
        4: (
            (3, {
                ...
            }),
            (4, {
                ...
            })
        )
    },
    "D"
)
```

The dictionary configuration of each LED partition takes in a single character as the key and a lambda as the value. The single character key represents the trigger to the lambda. When the Pico receives a character, the lambda will activate if the received character matches with the key.

```
controller = NeopixelController()
controller.configure(
    {
        2: (
            (5, {
                "D": lambda: ...,
                "F": lambda: ...,
            }),
            (12, {
                "G": lambda: ...,
                "T": lambda: ...,
            })
        ),
        3: (
            (10, {
                "H": lambda: ...,
                "D": lambda: ...,
            }),
            (7, {
                "J": lambda: ...,
                "P": lambda: ...,
            }),
        ),
        4: (
            (3, {
                "V": lambda: ...,
                "F": lambda: ...,
            }),
            (4, {
                "S": lambda: ...,
                "A": lambda: ...,
            })
        )
    },
    "D"
)
```

The lambda takes in one parameter: the pin. It calls a function on the `NeopixelController` object with the pin as its first parameter and the remaining configuration options proceeding it.

```
controller = NeopixelController()
controller.configure(
    {
        2: (
            (5, {
                "D": lambda pin: controller.color_fade(pin, ((0, 0, 255), (255, 0, 255)), 128, 0.01),
                "F": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 20, 0.01, 20, 50),
            }),
            (12, {
                "G": lambda pin: controller.color_fade(pin, ((255, 0, 0), (0, 255, 0), (0, 0, 255)), 128, 0.01),
                "T": lambda pin: controller.color_fade(pin, ((0, 0, 255), (255, 0, 255)), 128, 0.01),
            })
        ),
        3: (
            (10, {
                "H": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 20, 0.01, 20, 50),
                "D": lambda pin: controller.static_color(pin, (0, 255, 0), 1, True, "D"),
            }),
            (7, {
                "J": lambda pin: controller.static_color(pin, (0, 255, 0), 1, True, "D"),
                "P": lambda pin: controller.color_fade(pin, ((0, 0, 255), (255, 0, 255)), 128, 0.01),
            }),
        ),
        4: (
            (3, {
                "V": lambda pin: controller.color_fade(pin, ((255, 0, 0), (0, 255, 0), (0, 0, 255)), 128, 0.01),
                "F": lambda pin: controller.color_fade(pin, ((0, 0, 255), (255, 0, 255)), 128, 0.01),
            }),
            (4, {
                "S": lambda pin: controller.color_fade(pin, ((0, 0, 255), (255, 0, 255)), 128, 0.01),
                "A": lambda pin: controller.color_fade(pin, ((255, 0, 0), (0, 255, 0), (0, 0, 255)), 128, 0.01),
            })
        )
    },
    "D"
)
```