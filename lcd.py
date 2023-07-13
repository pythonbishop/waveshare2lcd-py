import RPi.GPIO as GPIO
import spidev
import time
import numpy as np
from commands import *

GPIO.setmode(GPIO.BCM)

class Lcd:

    PIN_BL = 18
    PIN_DC = 16
    PIN_RST = 17

    def init(self):
        if GPIO.getmode() != GPIO.BCM:
            raise AssertionError("GPIO mode is not set to BCM")

        self.spi = spidev.SpiDev()

        GPIO.setup(self.PIN_BL, GPIO.OUT)
        GPIO.setup(self.PIN_RST, GPIO.OUT)
        GPIO.setup(self.PIN_DC, GPIO.OUT)
        self.bl_pwm = GPIO.PWM(self.PIN_BL, 1000)
        self.bl_pwm.start(100)

        self.spi.open(0, 0 )
        self.spi.max_speed_hz = 62000000
        self.spi.mode = 0b00

        # enter power-on sequence
        GPIO.output(self.PIN_RST, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.PIN_RST, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.PIN_RST, GPIO.HIGH)

        GPIO.output(self.PIN_BL, GPIO.HIGH)
        
        self.cmd(INVON)         # set display inversion ON
        self.cmd(MADCTL)        # set mode to RGB
        self.data(0x00)
        self.cmd(COLMOD)        # set color format to 18bits/pixel RGB666
        self.data(0x06)
        self.cmd(SLPOUT)        # exit sleep-in mode
        time.sleep(0.01)
        self.cmd(DISPON)        # turn on display

    def poweroff(self):
        GPIO.output(self.PIN_RST, GPIO.LOW)
        GPIO.output(self.PIN_DC, GPIO.LOW)
        GPIO.cleanup()
        self.spi.close()

    def cmd(self, code):
        GPIO.output(self.PIN_DC, GPIO.LOW)
        self.spi.writebytes([code])

    def data(self, val):
        GPIO.output(self.PIN_DC, GPIO.HIGH)
        self.spi.writebytes([val])

    def data_buffer(self, buffer):
        GPIO.output(self.PIN_DC, GPIO.HIGH)
        for i in range(0, len(buffer), 4096):
            self.spi.writebytes(buffer[i:i+4096])
    
    def color_byte_format(self, val):
        return (val << 2) & 255

    def color_format(self, r, g, b):
        return (r << 2) & 255, (g << 2) & 255, (b << 2) & 255

    def write_pixel(self, x, y, r, g, b):

        self.cmd(CASET)
        self.data(x >> 8)
        self.data(x & 255)
        self.data(x >> 8)
        self.data(x & 255)

        self.cmd(RASET)
        self.data(y >> 8)
        self.data(y & 255)
        self.data(y >> 8)
        self.data(y & 255)

        self.cmd(RAMWR)
        self.data_buffer(self.color_format(r, g, b))

    def write_frame(self, buffer):
        self.cmd(CASET)      # set column address range to full screen (0-240)
        self.data(0x00)
        self.data(0x00)
        self.data(0x00)
        self.data(0xEf)

        self.cmd(RASET)      # set row address range to full screen (0-320)
        self.data(0x00)
        self.data(0x00)
        self.data(0x01)
        self.data(0x3F)
        
        self.cmd(RAMWR)      # start frame memory write
        self.data_buffer(buffer)

    def test_blank(self):
        buffer = np.ones(240*320*3, dtype=np.uint8)
        buffer *= self.color_byte_format(63)
        self.write_frame(buffer.tolist())

    def test_bypixel(self):
        r = 63
        g = 33
        b = 0

        for y in range(320):
            for x in range(240):
                self.write_pixel(x, y, r, g, b)

    def test_backlight(self):
        for i in range(3):
            for t in range (100):
                self.bl_pwm.ChangeDutyCycle(t)
                time.sleep(0.02)

    def splash(self):
        buffer = np.zeros(240*320*3, dtype=np.uint8)

        r = 0
        g = 63
        b = 0
        i = 0

        for y in range(320):
            r += 63/320
            g -= 63/320
            for x in range(240):
                b += 63/240
                buffer[i] = (int(r) << 2) & 255
                i += 1
                buffer[i] = (int(g) << 2) & 255
                i += 1
                buffer[i] = (int(b) << 2) & 255
                i += 1
            b = 0

        self.write_frame(buffer.tolist())
    

if __name__ == "__main__":
    lcd = Lcd()

    lcd.init()
    lcd.test_blank()
    time.sleep(2)
    lcd.test_bypixel()
    time.sleep(2)
    lcd.splash()
    time.sleep(2)

    buffer = np.ones(240*320*3, dtype=np.uint8)
    buffer *= 0
    lcd.write_frame(buffer.tolist())
    time.sleep(2)

    buffer = np.ones(240*320*3, dtype=np.uint8)
    buffer *= lcd.color_byte_format(33)
    lcd.write_frame(buffer.tolist())
    time.sleep(2)

    buffer = np.ones(240*320*3, dtype=np.uint8)
    buffer *= lcd.color_byte_format(63)
    lcd.write_frame(buffer.tolist())
    time.sleep(2)

    lcd.poweroff()