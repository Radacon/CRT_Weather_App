#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import colorsys

# --- Pin definitions (BCM numbering) ---
# Encoder Inputs
ENCODER_PHASE_A = 23   # Encoder phase A
ENCODER_PHASE_B = 24   # Encoder phase B
BUTTON_PIN      = 25   # Push button (normally open, with pull-down)

# LED Outputs (PWM-capable)
LED_BLUE  = 17       # Blue LED
LED_GREEN = 27       # Green LED
LED_RED   = 22       # Red LED

# CRT Power Control
CRT_POWER_PIN = 6    # CRT Power control pin

# --- Global variables for encoder tracking ---
half_steps = 0
last_printed_position = 0

# Global PWM objects for the LED channels
pwm_red = None
pwm_green = None
pwm_blue = None

def update_leds(full_position):
    """
    Map the encoder full position (mod 24) to a hue value and update the RGB LED PWM.
    Uses full saturation and brightness.
    """
    global pwm_red, pwm_green, pwm_blue
    # Map the position to a hue value [0, 1)
    hue = (full_position % 24) / 24.0
    # Convert HSV to RGB; colorsys returns values in [0,1]
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    # Convert to duty cycles (0-100%)
    duty_r = r * 100
    duty_g = g * 100
    duty_b = b * 100
    pwm_red.ChangeDutyCycle(duty_r)
    pwm_green.ChangeDutyCycle(duty_g)
    pwm_blue.ChangeDutyCycle(duty_b)
    print(f"Encoder position: {full_position} | Hue: {hue:.2f} => R: {duty_r:5.1f}%, G: {duty_g:5.1f}%, B: {duty_b:5.1f}%")

def encoder_callback(channel):
    """
    Processes rising edges on the encoder channels.
    Uses the state of the complementary channel to determine rotation direction.
    Counts half-steps so that one full detent corresponds to 2 half-steps.
    """
    global half_steps, last_printed_position
    if channel == ENCODER_PHASE_A:
        # For a rising edge on phase A: if phase B is LOW, assume clockwise.
        if GPIO.input(ENCODER_PHASE_B) == GPIO.LOW:
            half_steps += 1
        else:
            half_steps -= 1
    elif channel == ENCODER_PHASE_B:
        # For a rising edge on phase B: if phase A is HIGH, assume clockwise.
        if GPIO.input(ENCODER_PHASE_A) == GPIO.HIGH:
            half_steps += 1
        else:
            half_steps -= 1

    # Only update when a full detent has been reached (i.e. every 2 half-steps)
    if half_steps % 2 == 0:
        full_position = half_steps // 2
        if full_position != last_printed_position:
            direction = "CW" if full_position > last_printed_position else "CCW"
            print(f"Encoder rotated {direction}. New position: {full_position}")
            last_printed_position = full_position
            update_leds(full_position)

def button_callback(channel):
    """
    When the button is pressed (GPIO reads HIGH with pull-down):
      - Turn off all LED outputs.
      - Toggle the CRT Power control (GPIO 6).
    When the button is released, restore the current LED color.
    """
    if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        print("Button pressed! Turning off all LEDs and toggling CRT Power control.")
        # Turn off LEDs
        pwm_red.ChangeDutyCycle(0)
        pwm_green.ChangeDutyCycle(0)
        pwm_blue.ChangeDutyCycle(0)
        # Toggle CRT Power control pin
        #current_state = GPIO.input(CRT_POWER_PIN)
        new_state = GPIO.LOW if current_state == GPIO.HIGH else GPIO.HIGH
        #GPIO.output(CRT_POWER_PIN, new_state)
        print(f"CRT Power control (GPIO {CRT_POWER_PIN}) set to {'ON' if new_state == GPIO.HIGH else 'OFF'}.")
    else:
        print("Button released! Restoring LED color.")
        update_leds(last_printed_position)

def main():
    global pwm_red, pwm_green, pwm_blue

    GPIO.setmode(GPIO.BCM)

    # --- Setup encoder inputs (with internal pull-ups) ---
    GPIO.setup(ENCODER_PHASE_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_PHASE_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # --- Setup push button input (with internal pull-down) ---
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # --- Setup LED outputs and initialize PWM ---
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)
    
    # Setup CRT Power control output and initialize to OFF (LOW)
    GPIO.setup(CRT_POWER_PIN, GPIO.OUT)
    GPIO.output(CRT_POWER_PIN, GPIO.LOW)
    
    # Create PWM channels at 1 kHz frequency
    pwm_red = GPIO.PWM(LED_RED, 1000)
    pwm_green = GPIO.PWM(LED_GREEN, 1000)
    pwm_blue = GPIO.PWM(LED_BLUE, 1000)
    
    # Start PWM with 0% duty cycle (LEDs off)
    pwm_red.start(0)
    pwm_green.start(0)
    pwm_blue.start(0)
    
    # --- Setup event detection ---
    GPIO.add_event_detect(ENCODER_PHASE_A, GPIO.RISING, callback=encoder_callback, bouncetime=5)
    GPIO.add_event_detect(ENCODER_PHASE_B, GPIO.RISING, callback=encoder_callback, bouncetime=5)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_callback, bouncetime=200)
    
    print("Monitoring rotary encoder, button, and controlling RGB LED (with PWM) and CRT Power (GPIO 6).")
    print("Turn the encoder to mix colors over 24 steps; press the button to turn off LEDs and toggle CRT Power.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        pwm_red.stop()
        pwm_green.stop()
        pwm_blue.stop()
        GPIO.cleanup()

if __name__ == '__main__':
    main()
