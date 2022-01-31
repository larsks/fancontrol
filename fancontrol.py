try:
    import asyncio
except ImportError:
    import uasyncio as asyncio  # type: ignore[no-redef]

import board
import machine
import mpu6050
import network
import ntptime
import simplelog
import switch
import time


class State:
    def __init__(self, context, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._ctx = context
        self._active = False
        self._log = simplelog.make_logger(self.__class__.__name__)

    async def __aenter__(self):
        self._state_enter = time.time()
        self._active = True
        self._log("enter {}".format(self))
        return self

    async def __aexit__(self, *args):
        self._state_exit = time.time()
        self._active = False
        self._log("exit {}".format(self))

    def __str__(self):
        return "<State {}>".format(self.__class__.__name__[5:])

    def time_in_state(self):
        if not self._active:
            return 0

        return time.time() - self._state_enter


def max_gyro_delta(cur, prev):
    maxdelta = max(
        abs(prev.GyroX - cur.GyroX),
        abs(prev.GyroY - cur.GyroY),
        abs(prev.GyroZ - cur.GyroZ),
    )

    return maxdelta


class StateIdle(State):
    async def __aenter__(self):
        await super().__aenter__()

        self._ctx.rgb.green()
        await self._ctx.switch.turn_off()

        self._log("discarding samples")
        for i in range(10):
            self._ctx.acc.read_sensors()
            await asyncio.sleep_ms(500)

        return self

    async def run(self):
        lastvals = None
        while True:
            vals = self._ctx.acc.read_sensors()
            if lastvals is not None:
                maxdelta = max_gyro_delta(vals, lastvals)
                self._log("got maxdelta {}".format(maxdelta), level=0)
                if maxdelta > self._ctx.min_gyro_delta:
                    return self._ctx.tracking
            lastvals = vals
            await asyncio.sleep(1)


class StateTracking(State):
    num_samples = 30

    async def __aenter__(self):
        await super().__aenter__()
        self._ctx.rgb.yellow()
        return self

    async def run(self):
        samples = bytearray(self.num_samples)
        lastvals = None
        pos = 0
        while True:
            if self.time_in_state() > self._ctx.max_motion_wait:
                return self._ctx.idle

            vals = self._ctx.acc.read_sensors()
            pos = (pos + 1) % self.num_samples

            if lastvals is not None:
                maxdelta = max_gyro_delta(vals, lastvals)
                self._log("got maxdelta {}".format(maxdelta), level=0)
                if maxdelta > self._ctx.min_gyro_delta:
                    samples[pos] = 1
                else:
                    samples[pos] = 0

                if sum(samples) > self.num_samples // 2:
                    return self._ctx.active

            lastvals = vals

            await asyncio.sleep(1)


class StateActive(State):
    num_samples = 60

    async def __aenter__(self):
        await super().__aenter__()
        self._ctx.rgb.red()
        await self._ctx.switch.turn_on()
        return self

    async def run(self):
        samples = bytearray(self.num_samples)
        pos = 0
        lastvals = None
        sufficient = False

        while True:
            vals = self._ctx.acc.read_sensors()
            pos = (pos + 1) % self.num_samples

            if lastvals is not None:
                maxdelta = max_gyro_delta(vals, lastvals)
                self._log("got maxdelta {}".format(maxdelta), level=0)
                if maxdelta > self._ctx.min_gyro_delta:
                    samples[pos] = 1
                else:
                    samples[pos] = 0

                if not sufficient and pos == 0:
                    self._log("collected sufficient samples")
                    sufficient = True

                if sufficient and sum(samples) < self.num_samples // 2:
                    return self._ctx.idle

            lastvals = vals

            await asyncio.sleep(1)


class Clock:
    def __init__(self):
        self._evt_time_valid = asyncio.Event()
        self._log = simplelog.make_logger("clock")

    async def run(self):
        while True:
            try:
                ntptime.settime()
            except OSError:
                # on failure, retry in 10 seconds
                self._log("failed to set time", level=2)
                await asyncio.sleep(10)
            else:
                # otherwise, retry in 4 hours
                self._log(
                    "set time to {}".format(simplelog.strftime(time.gmtime())), level=1
                )
                self._evt_time_valid.set()
                await asyncio.sleep(14400)

    async def wait_valid(self):
        await self._evt_time_valid.wait()


class RGBLed:
    def __init__(self, context, pin_red, pin_green, pin_blue):
        self._ctx = context
        self._pin_red = machine.PWM(machine.Pin(pin_red))
        self._pin_green = machine.PWM(machine.Pin(pin_green))
        self._pin_blue = machine.PWM(machine.Pin(pin_blue))

        self._pin_red.freq(500)
        self._pin_red.duty(0)

    def set_red(self, val):
        self._pin_red.duty(val)

    def set_green(self, val):
        self._pin_green.duty(val)

    def set_blue(self, val):
        self._pin_blue.duty(val)

    def set_rgb(self, vr, vg, vb):
        self.set_red(vr)
        self.set_green(vg)
        self.set_blue(vb)

    def red(self):
        self.set_rgb(512, 0, 0)

    def green(self):
        self.set_rgb(0, 512, 0)

    def blue(self):
        self.set_rgb(0, 0, 512)

    def yellow(self):
        self.set_rgb(400, 500, 0)

    def off(self):
        self.set_rgb(0, 0, 0)


class WIFIMonitor:
    def __init__(self, context):
        self._ctx = context
        self._sta_if = network.WLAN(network.STA_IF)
        self._evt_connected = asyncio.Event()
        self._log = simplelog.make_logger("wifi")

    async def run(self):
        self._log("waiting for wifi")
        while True:
            if self._sta_if.isconnected():
                self._log("wifi is connected")
                self._evt_connected.set()
                break

            await asyncio.sleep(1)

    async def wait_connected(self):
        await self._evt_connected.wait()


class Controller:
    def __init__(self, switch_address):
        self._log = simplelog.make_logger("controller")

        self.acc = mpu6050.MPU6050(board.I2C())

        self.idle = StateIdle(self)
        self.tracking = StateTracking(self)
        self.active = StateActive(self)
        self.current_state = self.idle
        self.clock = Clock()
        self.switch = switch.Switch(switch_address)
        self.rgb = RGBLed(self, board.PIN_D5, board.PIN_D6, board.PIN_D7)
        self.wifi = WIFIMonitor(self)

        self.min_gyro_delta = 30
        self.max_motion_wait = 60

    async def run(self):
        self.rgb.off()

        self._tasks = [
            asyncio.create_task(self.clock.run()),
            asyncio.create_task(self.wifi.run()),
        ]

        await self.wifi.wait_connected()

        try:
            while True:
                async with self.current_state as state:
                    self.current_state = await state.run()
        finally:
            self.switch.turn_off()

    def start_fancontrol(self):
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            pass
        finally:
            self.rgb.off()
            asyncio.run(self.switch.turn_off())
