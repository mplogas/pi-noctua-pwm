#!/usr/bin/env python3
import time
from gpiozero import PWMOutputDevice

# --- Configuration ---
GPIO_PWM = 14            # BCM pin (physical pin 8)
PWM_FREQ_HZ = 1_000      # Software PWM via gpiozero/lgpio; 1 kHz is a good Pi-friendly default
TEMP_FILE_PATH = "/sys/block/nvme0n1/device/hwmon1/temp1_input"
READ_INTERVAL = 10       # seconds
LOWER_TEMP = 40          # degrees Celsius
UPPER_TEMP = 65          # degrees Celsius
MIN_FAN_SPEED = 20       # percent
MAX_FAN_SPEED = 100      # percent


def read_temp() -> float | None:
    try:
        with open(TEMP_FILE_PATH) as f:
            return int(f.read()) / 1000.0
    except FileNotFoundError:
        print(f"Error: Temperature file not found at {TEMP_FILE_PATH}")
        return None
    except (OSError, ValueError) as e:
        print(f"Error reading temperature: {e}")
        return None


def calculate_fan_speed(temp: float | None) -> int:
    if temp is None:
        return 0
    if temp < LOWER_TEMP:
        return 0
    if temp >= UPPER_TEMP:
        return MAX_FAN_SPEED
    span = (temp - LOWER_TEMP) / (UPPER_TEMP - LOWER_TEMP)
    return int(MIN_FAN_SPEED + span * (MAX_FAN_SPEED - MIN_FAN_SPEED))


def main() -> None:
    fan = PWMOutputDevice(GPIO_PWM, frequency=PWM_FREQ_HZ, initial_value=0)
    print("Starting temperature-based fan control...")
    try:
        while True:
            current_temp = read_temp()
            fan_speed = calculate_fan_speed(current_temp)
            fan.value = fan_speed / 100.0
            if current_temp is not None:
                print(f"Current Temp: {current_temp:.2f}°C -> Fan Speed: {fan_speed}%")
            time.sleep(READ_INTERVAL)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        fan.off()
        fan.close()
        print("Fan control stopped")


if __name__ == "__main__":
    main()
