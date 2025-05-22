from machine import Pin, PWM
import utime

# --- Configuration ---
HALL_PIN = 14
PWM_PIN = 15
PWM_FREQ = 1000
T_SAMPLE_MS = 100

# --- Fixed Point Q16.16 Helpers ---
FIXED_SHIFT = 16
FIXED_SCALE = 1 << FIXED_SHIFT
def to_fixed(x): return int(x * FIXED_SCALE)
def from_fixed(x): return x / FIXED_SCALE
def fixed_mul(a, b): return (a * b) >> FIXED_SHIFT

# --- PI Controller Parameters (tune these) ---
Kp = to_fixed(0.2)   # Proportional gain
Ki = to_fixed(0.1)   # Integral gain per sample interval
INTEGRAL_MIN = to_fixed(-100.0)
INTEGRAL_MAX = to_fixed(100.0)

# --- Target velocity ---
TARGET_VELOCITY = to_fixed(100.0)  # Target in units/sec, fixed-point

# --- Globals ---
pulse_count = 0
integral = 0

# --- Hardware Setup ---
def pulse_callback(pin):
    global pulse_count
    pulse_count += 1

hall_sensor = Pin(HALL_PIN, Pin.IN, Pin.PULL_DOWN)
hall_sensor.irq(trigger=Pin.IRQ_RISING, handler=pulse_callback)

pwm = PWM(Pin(PWM_PIN))
pwm.freq(PWM_FREQ)

def compute_velocity(sample_ms):
    global pulse_count
    start = pulse_count
    utime.sleep_ms(sample_ms)
    count = pulse_count - start
    return to_fixed(count / (sample_ms / 1000))  # pulses/sec → fixed point

def set_pwm_output(percent_fixed):
    percent = from_fixed(percent_fixed)
    percent = max(0.0, min(100.0, percent))  # Clamp
    duty_u16 = int((percent / 100.0) * 65535)
    pwm.duty_u16(duty_u16)

# --- Control Loop ---
while True:
    measured_velocity = compute_velocity(T_SAMPLE_MS)
    error = TARGET_VELOCITY - measured_velocity

    # Proportional term
    P_out = fixed_mul(Kp, error)

    # Integral term with windup guard
    integral += fixed_mul(Ki, error)
    if integral > INTEGRAL_MAX:
        integral = INTEGRAL_MAX
    elif integral < INTEGRAL_MIN:
        integral = INTEGRAL_MIN

    # PI Output
    output = P_out + integral

    # Clamp output to 0–100% (in fixed-point)
    output = max(to_fixed(0), min(to_fixed(100), output))

    # Output to PWM
    set_pwm_output(output)

    # Debug info
    print(f"Measured: {from_fixed(measured_velocity):.2f}, Output: {from_fixed(output):.2f}%")