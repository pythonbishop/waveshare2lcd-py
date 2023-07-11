import RPi.GPIO as GPIO
import spidev
import time
import numpy as np
from commands import *

PIN_BL = 23
PIN_DC = 16
PIN_RST = 17

spi = spidev.SpiDev()

def init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(PIN_BL, GPIO.OUT)
    GPIO.setup(PIN_RST, GPIO.OUT)
    GPIO.setup(PIN_DC, GPIO.OUT)

    GPIO.output(PIN_BL, GPIO.HIGH)

    spi.open(0, 0)
    spi.max_speed_hz = 62500000
    spi.mode = 0b00

    GPIO.output(PIN_RST, GPIO.HIGH)
    time.sleep(0.01)
    GPIO.output(PIN_RST, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(PIN_RST, GPIO.HIGH)

    GPIO.output(PIN_BL, GPIO.HIGH)

    cmd(INVON)
    cmd(WRCTRLD)            # set brightness control, BL control, display dimming off
    data(0x24)
    cmd(WRDISBV)            # write highest display brightness
    data(0xFF)
    cmd(COLMOD)             # set color mode to 18bits/pixel RGB666
    data(0x06)
    cmd(SLPOUT)             # exit sleep-in mode
    time.sleep(0.01)
    cmd(DISPON)             # turn on display


def poweroff():
    GPIO.output(PIN_RST, GPIO.LOW)
    GPIO.output(PIN_DC, GPIO.LOW)
    GPIO.cleanup()
    spi.close()

def cmd(code):
    GPIO.output(PIN_DC, GPIO.LOW)
    spi.writebytes([code])

def data(val):
    GPIO.output(PIN_DC, GPIO.HIGH)
    spi.writebytes([val])

def data_buffer(buffer):
    GPIO.output(PIN_DC, GPIO.HIGH)
    for i in range(0, len(buffer), 4096):
        spi.writebytes(buffer[i:i+4096])

def write_pixel(x, y, r, g, b):
    p = np.zeros(3, dtype=np.uint8)
    p[0] = (r << 2) & 255
    p[1] = (g << 2) & 255
    p[2] = (b << 2) & 255

    cmd(CASET)
    data(x >> 8)
    data(x & 255)
    data(x >> 8)
    data(x & 255)

    cmd(RASET)
    data(y >> 8)
    data(y & 255)
    data(y >> 8)
    data(y & 255)

    cmd(RAMWR)
    data(p)


def test_blank():
    buffer = np.zeros(240*320*3, dtype=np.uint8).tolist()

    # set address ranges to full 240x320 display
    
    cmd(CASET)      # set column address range
    data(0x00)      # 0x0000 to 0x00Ef
    data(0x00)
    data(0x00)
    data(0xEf)

    cmd(RASET)      # set row address range
    data(0x00)      # 0x0000 to 0x013f
    data(0x00)
    data(0x01)
    data(0x3F)
    
    cmd(RAMWR)      # start frame memory write
    for i in range(0, 240*320*3):
        data(0x00)

def test_bypixel():
    r = 25
    g = 25
    b = 25

    for x in range(240):
        for y in range(320):
            write_pixel(x, y, r, g, b)

init()
test_blank()
time.sleep(3)
poweroff()