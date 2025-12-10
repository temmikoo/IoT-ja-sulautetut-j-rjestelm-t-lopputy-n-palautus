import time
from machine import I2C


class I2cLcd:
    """Minimal driver for AMC1602AR-B-B6WTDW-I2C (RW1063 / AC780S)"""

    def __init__(self, i2c: I2C, addr=0x3C, cols=16, rows=2):
        self.i2c = i2c
        self.addr = addr
        self.cols = cols
        self.rows = rows
        self._init_lcd()

    def _cmd(self, b):
        self.i2c.writeto(self.addr, bytes([0x00, b]))

    def _data(self, b):
        self.i2c.writeto(self.addr, bytes([0x40, b]))

    def _init_lcd(self):
        time.sleep_ms(50)
        # --- init sequence (from RW1063 datasheet) ---
        self._cmd(0x38)  # Function set
        time.sleep_us(120)
        self._cmd(0x0C)  # Display ON, no cursor
        time.sleep_us(120)
        self._cmd(0x01)  # Clear
        time.sleep_ms(2)
        self._cmd(0x06)  # Entry mode
        time.sleep_us(120)

    def clear(self):
        self._cmd(0x01)
        time.sleep_ms(2)

    def home(self):
        self._cmd(0x02)
        time.sleep_ms(2)

    def move_to(self, col, row):
        addr = col + (0x40 if row else 0x00)
        self._cmd(0x80 | addr)

    def putstr(self, text):
        for c in text:
            self._data(ord(c))

    def put_line(self, text, row=0):
        self.move_to(0, row)
        self.putstr(text[: self.cols])
