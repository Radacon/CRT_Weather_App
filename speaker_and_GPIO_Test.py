import RPi.GPIO as GPIO
import time
import subprocess
import threading
import colorsys
import json
import math


# --- Constants and Pin Definitions ---
SOMAFM_STREAM = "http://ice1.somafm.com/groovesalad-128-mp3"

# Encoder pins and button
ENCODER_PHASE_A = 23
ENCODER_PHASE_B = 24
BUTTON_PIN = 25  # encoder button

# LED pins
LED_BLUE = 17
LED_GREEN = 27
LED_RED = 22

# New Power control pin
POWER_PIN = 6

# JSON file to share state with the GUI
GPIO_STATES_FILE = "./gpio_states.json"

# --- Global Variables ---
half_steps = 0
last_printed_position = 0
current_volume = 0   # Start muted
saved_volume = 50    # Default saved volume for unmuting  
is_muted = True
mpg123_process = None

# For button press handling
button_press_start_time = None
power_off_countdown = None   # Holds current countdown value if active
power_off_thread = None      # Thread object for the countdown
button_lock = threading.Lock()  # To avoid concurrent button processing

# For detecting long press
long_press_triggered = False

# Track power state: 0 for LOW (off), 1 for HIGH (on).
# On first execution, we want POWER_PIN LOW (cold and dark).
power_state = 0

# --- Load Settings ---
def load_settings():
    try:
        with open("./settings.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading settings.json:", e)
        return {}

settings = load_settings()
SOMAFM_STREAM = settings.get("somastream_url", "http://ice1.somafm.com/groovesalad-128-mp3")
default_volume = settings.get("default_volume", 50)

# --- Utility: Write state to JSON ---
def write_gpio_state():
    """Write the current state to the JSON file."""
    state = {
        "volume": current_volume,
        "button": GPIO.input(BUTTON_PIN),  # 1 if pressed, 0 if released
        "power": power_state,              # 0 or 1
    }
    if power_off_countdown is not None:
        state["power_off_countdown"] = power_off_countdown
    try:
        with open(GPIO_STATES_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print("Error writing GPIO state:", e)

# --- Streaming Functions ---
def start_stream():
    global mpg123_process
    if mpg123_process is None:
        mpg123_process = subprocess.Popen(["mpg123", "-q", SOMAFM_STREAM],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
        print("Streaming started...")

def stop_stream():
    global mpg123_process
    if mpg123_process:
        mpg123_process.terminate()
        mpg123_process = None
        print("Streaming stopped.")

# --- Volume Control Thread ---
def volume_control_thread():
    global current_volume
    last_volume = None
    while True:
        time.sleep(0.01)
        if current_volume != last_volume:     
            subprocess.run(["sudo", "amixer", "set", "PCM", f"{current_volume}%"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
            last_volume = current_volume

# --- Request Volume Update ---
def request_volume_update(volume):
    global current_volume
    current_volume = volume
    write_gpio_state()
    print(f"🔊 Volume set to {current_volume}%")

# --- LED Update ---
def update_leds(full_position):
    global pwm_red, pwm_green, pwm_blue
    hue = (full_position % 24) / 24.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    pwm_red.ChangeDutyCycle(r * 100)
    pwm_green.ChangeDutyCycle(g * 100)
    pwm_blue.ChangeDutyCycle(b * 100)

def toggle_power_and_mute():
    global power_state, is_muted, saved_volume, long_press_triggered
    if power_state == 1:
        # Turn power off: update both variable and physical pin.
        power_state = 0
        GPIO.output(POWER_PIN, GPIO.LOW)  # Set physical pin LOW
        if not is_muted:
            saved_volume = current_volume
            is_muted = True
            request_volume_update(0)
        long_press_triggered = True
        try:
            pwm_red.ChangeDutyCycle(100)
            pwm_green.ChangeDutyCycle(0)
            pwm_blue.ChangeDutyCycle(0)
        except Exception as e:
            pass
        print("Long press: Power toggled to LOW and muted.")
    else:
        # Turn power on: update both variable and physical pin.
        power_state = 1
        GPIO.output(POWER_PIN, GPIO.HIGH)  # Set physical pin HIGH
        if is_muted:
            is_muted = False
            request_volume_update(saved_volume)
            half_steps = (saved_volume // 5) * 2
            last_printed_position = saved_volume
            update_leds(half_steps // 2)
        print("Short press: Power toggled to HIGH and unmuted.")
    write_gpio_state()



def toggle_mute():
    global is_muted, current_volume, saved_volume, pwm_red, pwm_green, pwm_blue
    if is_muted:
        # Unmute: restore saved volume.
        is_muted = False
        request_volume_update(saved_volume)
        # Update LEDs according to the current volume.
        full_position = saved_volume // 5  # or use update_leds(saved_volume // 5)
        update_leds(full_position)
        print("Unmuted.")
    else:
        # Mute: save current volume and set volume to 0.
        saved_volume = current_volume if current_volume > 0 else saved_volume
        is_muted = True
        request_volume_update(0)
        # Set LED to red.
        pwm_red.ChangeDutyCycle(100)
        pwm_green.ChangeDutyCycle(0)
        pwm_blue.ChangeDutyCycle(0)
        print("Muted.")


# --- Power-off Countdown Thread ---
def power_off_countdown_thread():
    global power_off_countdown
    countdown = 5
    while countdown > 0:
        # If button is released during countdown, cancel it.
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            power_off_countdown = None
            write_gpio_state()
            return
        power_off_countdown = countdown
        write_gpio_state()
        time.sleep(1)
        countdown -= 1
    # If countdown finishes and button is still pressed, perform long press action.
    if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        toggle_power_and_mute()

# --- Button Callback using BOTH edges ---
def button_callback(channel):
    global button_press_start_time, long_press_triggered, power_off_countdown, power_off_thread
    with button_lock:
        button_state = GPIO.input(BUTTON_PIN)
        if button_state == GPIO.HIGH:  # Button pressed
            button_press_start_time = time.time()
            long_press_triggered = False
            write_gpio_state()  # Update button state to pressed

            if power_state == 1:
                # Start a thread that waits 1 second, then begins countdown if still pressed.
                def delayed_long_press():
                    time.sleep(1)
                    if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                        global power_off_thread
                        power_off_thread = threading.Thread(target=power_off_countdown_thread, daemon=True)
                        power_off_thread.start()
                threading.Thread(target=delayed_long_press, daemon=True).start()
        else:  # Button released
            press_duration = time.time() - button_press_start_time if button_press_start_time else 0
            write_gpio_state()  # Update button state to released
            power_off_countdown = None
            write_gpio_state()
            # Process as short press only if long press was not triggered.
            if not long_press_triggered:
                if power_state == 1:
                    toggle_mute()  # Short press toggles mute when power is on.
                elif power_state == 0:
                    toggle_power_and_mute()  # Short press toggles power on when power is off.

# --- Encoder Callback (for volume control) ---
def encoder_callback(channel):
    global half_steps, last_printed_position
    if channel == ENCODER_PHASE_A:
        direction = 1 if GPIO.input(ENCODER_PHASE_B) == GPIO.LOW else -1
    else:
        direction = 1 if GPIO.input(ENCODER_PHASE_A) == GPIO.HIGH else -1

    if last_printed_position >= 100 and direction > 0:
        return
    if last_printed_position <= 0 and direction < 0:
        return

    half_steps += direction
    full_position = half_steps // 2
    volume = max(0, min(100, full_position * 5))

    if volume != last_printed_position:
        print(f"🎛️ Volume: {volume}% (Queued for update)")
        request_volume_update(volume)
        update_leds(full_position)
        last_printed_position = volume

def led_breathe():
    """Continuously update the red LED brightness with a breathing effect when power is off."""
    while True:
        if power_state == 0:
            # Use a period of 2 seconds; brightness varies between 10 and 100%
            t = time.time() % 5  
            brightness = (math.sin(t * math.pi) + 1) / 2 * 90 + 10  
            try:
                pwm_red.ChangeDutyCycle(brightness)
            except Exception as e:
                # In case pwm_red isn't initialized yet.
                pass
            time.sleep(0.05)
        else:
            # When power is on, let normal LED control take over.
            time.sleep(0.2)

# --- Setup GPIO and Start ---
def main():
    global pwm_red, pwm_green, pwm_blue, half_steps, last_printed_position
    global current_volume, saved_volume, power_state

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Setup encoder and button pins.
    GPIO.setup(ENCODER_PHASE_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_PHASE_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Setup LED pins.
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)

    # Setup power control pin and assert LOW by default.
    GPIO.setup(POWER_PIN, GPIO.OUT)
    GPIO.output(POWER_PIN, GPIO.LOW)
    power_state = 0  # Cold and dark at startup.

    pwm_red = GPIO.PWM(LED_RED, 1000)
    pwm_green = GPIO.PWM(LED_GREEN, 1000)
    pwm_blue = GPIO.PWM(LED_BLUE, 1000)
    pwm_red.start(0)
    pwm_green.start(0)
    pwm_blue.start(0)

    # Start the LED breathing thread.
    threading.Thread(target=led_breathe, daemon=True).start()

    # Use BOTH edges for the button.
    GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_callback, bouncetime=50)
    GPIO.add_event_detect(ENCODER_PHASE_A, GPIO.RISING, callback=encoder_callback, bouncetime=1)
    GPIO.add_event_detect(ENCODER_PHASE_B, GPIO.RISING, callback=encoder_callback, bouncetime=1)

    print("Starting SomaFM stream...")
    start_stream()

    # Initialize volume and encoder position for a muted startup.
    half_steps = 0           # 0 volume corresponds to 0 half-steps.
    last_printed_position = 0
    current_volume = 0
    saved_volume = 50         # Saved volume remains 50 for unmuting.
    request_volume_update(0)
    update_leds(0)

    # Start volume control thread.
    threading.Thread(target=volume_control_thread, daemon=True).start()

    try:
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected! Exiting...")
    finally:
        stop_stream()
        pwm_red.stop()
        pwm_green.stop()
        pwm_blue.stop()
        GPIO.cleanup()
        print("Cleanup complete. Goodbye!")

if __name__ == '__main__':
    main()
