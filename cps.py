import time
import board
import busio
from gpiozero import Servo
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

paper_value = 1
plastic_value = 2
matel_value = 3


i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
chan = AnalogIn(ads, ADS1115.P0)


from gpiozero import Servo
from time import sleep

servo = Servo(17)


def read_value():
    return chan.voltage



def turn_servo(value):
    if value == paper_value: 
        servo.min() 
    elif value == plastic_value:
        servo.min()
    else:
        servo.max()

    
