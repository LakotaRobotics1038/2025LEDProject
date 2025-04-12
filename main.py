from uasyncio import sleep, run, create_task
from asyncio import Task
from umachine import Pin, UART
from neopixel import NeoPixel
from usys import stdin, print_exception
from uselect import poll, POLLIN

class NeopixelController:
    def configure(
        self,
        config: "dict[int, tuple[tuple[int, dict[str, object]], ...]]",
        character: str,
    ) -> None:
        self.leds: list[NeoPixel] = []
        self.start: list[int] = []
        self.led_strip: list[int] = []
        self.led_count: list[int] = []
        self.tasks: "dict[int, list[tuple[str, None | Task[None]]]]" = {
            pin: list(("", None) for _ in attributes) for pin, attributes in config.items()
        }
        self.modes: "dict[int, tuple[dict[str, object], ...]]" = {
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
                self.led_count.append(length)
                index += length

    def choose_pattern(self) -> None:
        for start_position, (pin, tasks) in enumerate(self.tasks.items()):
            for count, task in enumerate(tasks):
                if task[0] != self.character and self.modes[pin][count].get(self.character) != None:
                    if task[1] is not None:
                        try:
                            task[1].cancel()
                        except RuntimeError:
                            pass
                    self.tasks[pin][count] = (self.character, create_task(self.modes[pin][count][self.character](start_position + count))) # type: ignore

    async def color_fade(
        self,
        strip: int,
        colors: "tuple[tuple[int, int, int], ...]",
        mix: int,
        step_delay: float,
    ) -> None:
        while True:
            for count in range(len(colors)):
                for fade_step in range(mix + 1):
                    intermediate_color = tuple(int((1 - fade_step / mix) * rgb_1 + fade_step / mix * rgb_2) for rgb_1, rgb_2 in zip(colors[count], colors[(count + 1) % len(colors)]))
                    for led in range(self.led_count[strip]):
                        self.leds[self.led_strip[strip]][self.start[strip] + led] = intermediate_color # type: ignore
                    self.leds[self.led_strip[strip]].write()
                    await sleep(step_delay)

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
        speed: int,
    ) -> None:
        intermediate_colors: "list[list[int]]" = [[int((1 - fade_step / mix) * rgb_1 + fade_step / mix * rgb_2) for rgb_1, rgb_2 in zip(base_color, chasing_color)] for fade_step in range(mix + 1)]
        colors_length: int = len(intermediate_colors) - 1
        position: float = 0
        while True:
            for led in range(self.led_count[strip]):
                closest_position: float = abs(position - led)
                distance: float = min(closest_position, self.led_count[strip] - closest_position)
                equation: int = int(colors_length - colors_length / max(length / distance, 1)) if distance != 0 else 0
                self.leds[self.led_strip[strip]][self.start[strip] + led] = intermediate_colors[equation] # type: ignore
            position = position + 1 / mix if position < self.led_count[strip] else 0
            self.leds[self.led_strip[strip]].write()
            await sleep(step_delay / mix / speed)


async def set_mode(controller: NeopixelController) -> None:
    uart = UART(0, 9600, parity=None, stop=1, bits=8, tx=Pin(0), rx=Pin(1), timeout=10)
    select_poll: poll = poll()
    select_poll.register(stdin, POLLIN)

    while True:
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
        9: (
            (45, {
                "D": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 10, 0.01, 20, 50),
                "E": lambda pin: controller.color_fade(pin, ((255, 0, 0), (0, 255, 0), (0, 0, 255)), 128, 0.01),
                "X": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 10, 0.01, 20, 50),
                "G": lambda pin: controller.static_color(pin, (0, 255, 0), 0, False, ""),
            }),
        ),
        10: (
            (45, {
                "D": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 10, 0.01, 20, 50),
                "E": lambda pin: controller.color_fade(pin, ((255, 0, 0), (0, 255, 0), (0, 0, 255)), 128, 0.01),
                "X": lambda pin: controller.chasing(pin, (0, 0, 200), (200, 0, 200), 10, 0.01, 20, 50),
                "G": lambda pin: controller.static_color(pin, (0, 255, 0), 0, False, ""),
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