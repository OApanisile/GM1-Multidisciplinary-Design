from machine import Pin, time_pulse_us
import time

TRIG = Pin(3, Pin.OUT)
ECHO = Pin(2, Pin.IN)

def get_distance():
    TRIG.low()
    time.sleep_us(2)
    TRIG.high()
    time.sleep_us(10)
    TRIG.low()

    duration = time_pulse_us(ECHO, 1, 30000)  # Wait max 30 ms
    distance_cm = duration / 58.0  # Speed of sound calculation
    return distance_cm

while True:
    distance = get_distance()
    print("Distance:", distance, "cm")
    time.sleep(1)