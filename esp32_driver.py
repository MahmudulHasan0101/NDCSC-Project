from machine import Pin, PWM, UART
import time

class Motor:
    def __init__(self, in1, in2):
        self.in1 = Pin(in1, Pin.OUT)
        self.in2 = Pin(in2, Pin.OUT)

    def set_direction(self, direction):
        if direction > 0:
            self.in1.value(1)
            self.in2.value(0)
        elif direction < 0:
            self.in1.value(0)
            self.in2.value(1)
        else:
            self.in1.value(0)
            self.in2.value(0)


class DriverGroup:
    def __init__(self, left_motors, right_motors, left_pwm_pin, right_pwm_pin, freq=5000):
        self.left_motors = left_motors
        self.right_motors = right_motors
        self.left_pwm = PWM(Pin(left_pwm_pin), freq=freq, duty=0)
        self.right_pwm = PWM(Pin(right_pwm_pin), freq=freq, duty=0)

    def drive(self, left_val, right_val):
        self._drive_side(self.left_motors, left_val, self.left_pwm)
        self._drive_side(self.right_motors, right_val, self.right_pwm)

    def _drive_side(self, motors, value, pwm):
        duty = min(max(abs(value) * 1023 // 100, 0), 1023)  
        for m in motors:
            m.set_direction(value)
        pwm.duty(duty)


lefts = [
    Motor(21, 19),
    Motor(14, 27),
    Motor(22, 23)
]

rights = [
    Motor(8, 5),
    Motor(26, 25),
    Motor(32, 33)
]

driver = DriverGroup(lefts, rights, left_pwm_pin=2, right_pwm_pin=4)

uart = UART(2, baudrate=115200, tx=17, rx=16)

buffer = b""

while True:
    if uart.any():
        buffer += uart.read()
        if b"\n" in buffer:
            lines = buffer.split(b"\n")
            for line in lines[:-1]:
                line = line.strip().decode()
                if line.startswith("[") and line.endswith("]"):
                    try:
                        values = line[1:-1].split(',')
                        left_val = int(values[0])
                        right_val = int(values[1])
                        driver.drive(left_val, right_val)
                    except Exception as e:
                        uart.write("Parse error: {}\n".format(e))
            buffer = lines[-1]
    time.sleep(0.02)
