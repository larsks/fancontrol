import machine
from micropython import const

PIN_D8 = const(15)
PIN_D7 = const(13)
PIN_D6 = const(12)
PIN_D5 = const(14)
PIN_D0 = const(16)
PIN_D4 = const(2)
PIN_D3 = const(0)
PIN_D2 = const(4)
PIN_D1 = const(5)
PIN_RX = const(3)
PIN_TX = const(1)

PIN_SCL = const(PIN_D1)
PIN_SDA = const(PIN_D2)
PIN_WAKE = const(PIN_D0)
PIN_SCLK = const(PIN_D5)
PIN_MISO = const(PIN_D6)
PIN_MOSI = const(PIN_D7)
PIN_CS = const(PIN_D8)


class I2C(machine.I2C):
    def __init__(self):
        super().__init__(machine.Pin(PIN_SCL), machine.Pin(PIN_SDA))
