import gpiod
import time
import threading

# --- Configuration ---
GPIO_PWM = 14  # Pin8 (BCM GPIO14), PWM-fähig
TEMP_FILE_PATH = "/sys/block/nvme0n1/device/hwmon1/temp1_input"
READ_INTERVAL = 10  # seconds
LOWER_TEMP = 40  # degrees Celsius
UPPER_TEMP = 65  # degrees Celsius
MIN_FAN_SPEED = 20  # percent
MAX_FAN_SPEED = 100 # percent

class SoftwarePWM:
    def __init__(self, chip, pin, frequency):
        self.chip = chip
        self.pin = pin
        self.frequency = frequency
        self.period = 1.0 / frequency
        self.duty_cycle = 0
        self.running = False
        self.thread = None
        
        # Request the GPIO line for output
        self.line = chip.get_line(pin)
        self.line.request(consumer="PWM", type=gpiod.LINE_REQ_DIR_OUT)
    
    def start(self, duty_cycle=0):
        """Start PWM with given duty cycle (0-100)"""
        self.duty_cycle = duty_cycle / 100.0
        self.running = True
        self.thread = threading.Thread(target=self._pwm_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def change_duty_cycle(self, duty_cycle):
        """Change duty cycle (0-100)"""
        self.duty_cycle = duty_cycle / 100.0
    
    def stop(self):
        """Stop PWM"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.line.set_value(0)
    
    def cleanup(self):
        """Release GPIO resources"""
        self.stop()
        self.line.release()
    
    def _pwm_loop(self):
        """Internal PWM loop"""
        while self.running:
            if self.duty_cycle > 0:
                # High period
                self.line.set_value(1)
                time.sleep(self.period * self.duty_cycle)
                
                # Low period
                if self.duty_cycle < 1.0:
                    self.line.set_value(0)
                    time.sleep(self.period * (1.0 - self.duty_cycle))
            else:
                # 0% duty cycle - stay low
                self.line.set_value(0)
                time.sleep(self.period)

def read_temp():
    """Reads temperature from the specified file."""
    try:
        with open(TEMP_FILE_PATH, 'r') as f:
            temp_str = f.read()
        # The value is in millidegrees Celsius, convert to Celsius
        return float(temp_str) / 1000.0
    except FileNotFoundError:
        print(f"Error: Temperature file not found at {TEMP_FILE_PATH}")
        return None
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None

def calculate_fan_speed(temp):
    """Calculates fan speed based on temperature."""
    if temp is None:
        # Turn off fan if temperature reading fails
        return 0

    if temp < LOWER_TEMP:
        return 0
    elif temp >= UPPER_TEMP:
        return MAX_FAN_SPEED
    else:
        # Linearly scale fan speed between MIN_FAN_SPEED and MAX_FAN_SPEED
        temp_range = float(UPPER_TEMP - LOWER_TEMP)
        speed_range = float(MAX_FAN_SPEED - MIN_FAN_SPEED)
        temp_delta = float(temp - LOWER_TEMP)
        
        speed = MIN_FAN_SPEED + (temp_delta / temp_range) * speed_range
        return int(speed)

# Main code
chip = gpiod.Chip('gpiochip4')  # Pi 5 uses gpiochip4 for main GPIO
pwm = SoftwarePWM(chip, GPIO_PWM, 25000)  # 25 kHz as per Noctua spec

def set_fan_speed(percent):
    """Set fan speed as percentage (0-100)"""
    pwm.change_duty_cycle(percent)

try:
    print("Starting temperature-based fan control...")
    pwm.start(0)  # Start PWM with 0% duty cycle

    while True:
        current_temp = read_temp()
        if current_temp is not None:
            fan_speed = calculate_fan_speed(current_temp)
            set_fan_speed(fan_speed)
            print(f"Current Temp: {current_temp:.2f}°C -> Fan Speed: {fan_speed}%")
        
        time.sleep(READ_INTERVAL)
    
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Cleanup
    pwm.cleanup()
    chip.close()
    print("GPIO resources cleaned up")