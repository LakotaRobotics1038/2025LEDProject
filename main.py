from uasyncio import sleep, run, create_task
from asyncio import Task
from umachine import Pin, UART, soft_reset
from neopixel import NeoPixel
from usys import stdin, print_exception
from uselect import poll, POLLIN
from rp2 import bootsel_button
from math import sin

class NeopixelController:
    def __init__(self) -> None:
        self.leds: list[NeoPixel] = []
        self.start: list[int] = []
        self.end: list[int] = []
        self.led_strip: list[int] = []
        self.led_count: list[int] = []
        self.tasks: "dict[int, list[tuple[str, None | Task[None]]]]" = {}
        self.modes: "dict[int, tuple[dict[str, object], ...]]" = {
        }
        self.character: str = ""

    def configure(
        self,
        config: "dict[int, tuple[tuple[int, dict[str, object]], ...]]",
        character: str,
    ) -> None:
        self.tasks = {
            pin: list(("", None) for _ in attributes) for pin, attributes in config.items()
        }
        self.modes = {
            pin: tuple(info[1] for info in attributes) for pin, attributes in config.items()
        }
        self.character: str = character
        index: int = 0
        for count, (pin, info) in enumerate(config.items()):
            index = 0
            self.leds.append(
                NeoPixel(Pin(pin), sum(length for length, _ in info)))
            for length, _ in info:
                self.led_strip.append(count)
                self.start.append(index)
                self.end.append(index + length)
                self.led_count.append(length)
                index += length

    def choose_pattern(self) -> None:
        for pin, tasks in self.tasks.items():
            for count, task in enumerate(tasks):
                if task[0] != self.character and self.modes[pin][count].get(self.character) != None:
                    if task[1] is not None:
                        try:
                            task[1].cancel()
                        except RuntimeError:
                            pass
                    self.tasks[pin][count] = (self.character, create_task(self.modes[pin][count][self.character]())) # type: ignore

    async def color_fade(
        self,
        strip: int,
        colors: "list[tuple[int, int, int]]",
        mix: int,
        step_delay: float,
        delay: float,
    ) -> None:
        while True:
            for count in range(len(colors)):
                for fade_step in range(mix + 1):
                    intermediate_color = tuple(int((1 - fade_step / mix) * rgb_1 + fade_step / mix * rgb_2) for rgb_1, rgb_2 in zip(colors[count], colors[(count + 1) % len(colors)]))
                    for led in range(self.led_count[strip]):
                        self.leds[self.led_strip[strip]][self.start[strip] + led] = intermediate_color # type: ignore
                    self.leds[self.led_strip[strip]].write()
                    await sleep(step_delay)
            await sleep(delay)

    async def static_color(
        self,
        strip: int,
        color: "tuple[int, int, int]",
        delay: int,
        kill: bool,
        kill_mode: str,
    ) -> None:
        for led in range(self.led_count[strip]):
            self.leds[self.led_strip[strip]][self.start[strip] + led] = color # type: ignore
        self.leds[self.led_strip[strip]].write()
        await sleep(delay)
        if kill:
            self.character = kill_mode
            self.choose_pattern()

    async def chasing(
        self,
        strip: int,
        base_color: "tuple[int, int, int]",
        chasing_color: "tuple[int, int, int]",
        mix: int,
        step_delay: float,
        length: int,
        frequency: int,
    ) -> None:
        intermediate_colors: "list[list[int]]" = [[int((1 - fade_step / mix) * rgb_1 + fade_step / mix * rgb_2) for rgb_1, rgb_2 in zip(base_color, chasing_color)] for fade_step in range(mix + 1)]
        position: int = 0
        while True:
            for led in range(self.led_count[strip]):
                self.leds[self.led_strip[strip]][self.start[strip] + led] = intermediate_colors[int((len(intermediate_colors) - 1) / (abs(sin(frequency * min(abs(position - led) / length, (self.led_count[strip] - abs(position - led)) / length))) + 1))] # type: ignore
            position = position + 1 if position < self.led_count[strip] else 0
            self.leds[self.led_strip[strip]].write()
            await sleep(step_delay)


async def set_mode(controller: NeopixelController) -> None:
    uart = UART(0, 9600, parity=None, stop=1, bits=8, tx=Pin(0), rx=Pin(1), timeout=10)
    select_poll: poll = poll()
    select_poll.register(stdin, POLLIN)

    while True:
        if bootsel_button() == 1:
            for led in controller.leds:
                led.fill((0, 0, 0))
                led.write()
            soft_reset()

        if uart.any() > 0:
            received_input = uart.read(1).decode("utf-8")
            if received_input != "\n":
                controller.character = received_input

        if select_poll.poll(0):
            received_input = stdin.read(1)
            if received_input != "\n":
                controller.character = received_input

        controller.choose_pattern()
        await sleep(0.1)

controller = NeopixelController()
controller.configure(
    config={
        2: (
            (2, {
                "D": lambda: controller.chasing(0, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
                "E": lambda: controller.color_fade(0, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0),
                "X": lambda: controller.chasing(0, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
                "G": lambda: controller.static_color(0, (0, 255, 0), 1, True, "D"),
            }),
            (2, {
                "D": lambda: controller.color_fade(1, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0),
                "E": lambda: controller.chasing(1, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
                "X": lambda: controller.color_fade(1, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0)
            }),
            (2, {
                "D": lambda: controller.chasing(2, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
                "E": lambda: controller.color_fade(2, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0),
                "X": lambda: controller.chasing(2, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
            }),
            (2, {
                "D": lambda: controller.color_fade(3, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0),
                "E": lambda: controller.chasing(3, (0, 0, 200), (200, 0, 200), 100, 0.1, 10, 1),
                "X": lambda: controller.color_fade(3, [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 128, 0.01, 0)
            }),
        ),
    },
    character="D",
)

try:
    run(set_mode(controller))
except Exception as e:
    print_exception(e)
finally:
    for led in controller.leds:
        led.fill((0, 0, 0))
        led.write()
    soft_reset()
