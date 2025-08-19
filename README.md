# pi-noctua-pwm

Controls a 4-pin (PWM) 5V Noctua fan using a Raspberry Pi 5's GPIO pins. The fan speed is automatically adjusted based on the temperature readings from an NVMe drive, making it ideal for cooling solutions like the Pimoroni NVMe Base.

## Wiring

This guide is for 5V PWM fans (e.g., Noctua NF-A4x10 5V PWM or NF-A4x20 5V PWM) which can be powered directly from the Pi's 5V GPIO pins.

Connect the fan's 4-pin connector to the Raspberry Pi 5 GPIO header as follows:

```
Raspberry Pi 5 GPIO Header
+------------------+
| 3V3  (1) (2) 5V  |
| SDA  (3) (4) 5V  | <--- Fan +5V (Pin 2)
| SCL  (5) (6) GND | <--- Fan GND (Pin 1)
| GP4  (7) (8) GP14| <--- Fan PWM (Pin 4)
| ...              |
+------------------+
```

-   **Fan Pin 1 (GND):** Connect to a Pi Ground pin (e.g., Pin 6).
-   **Fan Pin 2 (+5V):** Connect to a Pi 5V pin (e.g., Pin 4).
-   **Fan Pin 3 (Tacho):** Leave disconnected (unused by this script).
-   **Fan Pin 4 (PWM):** Connect to Pi Pin 8 (GPIO14).

## Prerequisites

This script requires the `gpiod` library. Install it and its dependencies with:

```bash
sudo apt update
sudo apt install gpiod
```

## Configuration

All user-configurable parameters are located at the top of the `fan-control.py` script.

```python
# --- Configuration ---
GPIO_PWM = 14  # BCM pin number for the PWM signal. Default is 14 (physical pin 8).
TEMP_FILE_PATH = "/sys/block/nvme0n1/device/hwmon1/temp1_input" # Path to temperature sensor file.
READ_INTERVAL = 10  # Seconds between temperature checks.
LOWER_TEMP = 40  # Temp (C) below which the fan turns off.
UPPER_TEMP = 65  # Temp (C) at which the fan reaches 100% speed.
MIN_FAN_SPEED = 20  # Minimum fan speed (percent) when temp is above LOWER_TEMP.
MAX_FAN_SPEED = 100 # Maximum fan speed (percent).
```

## Running as a Systemd Service

To have the script start automatically on boot, you can run it as a `systemd` service.

### 1. Create the Service File

Create a new service file using a text editor of your choice:

```bash
sudo joe /etc/systemd/system/fan-control.service
```

Paste the following content into the file. **You must modify the `ExecStart` and `User` lines to match your system.**

```ini
[Unit]
Description=Temperature-based Fan Control Service
After=multi-user.target

[Service]
Type=simple
# Replace '/home/pi/Github/pi-noctua-pwm/fan-control.py' with the full path to your script
ExecStart=/usr/bin/python3 /home/pi/Github/pi-noctua-pwm/fan-control.py
Restart=on-failure
# Replace 'pi' with your username
User=pi
Group=gpio

[Install]
WantedBy=multi-user.target
```

### 2. Add User to GPIO Group

The service needs permission to access GPIO. Add your user to the `gpio` group (if not already done) and reboot or log out/in for the change to take effect.

```bash
sudo usermod -aG gpio <your_username>
```

### 3. Enable and Start the Service

-   Reload the systemd daemon to recognize the new service:
    ```bash
    sudo systemctl daemon-reload
    ```

-   Enable the service to start automatically on boot:
    ```bash
    sudo systemctl enable fan-control.service
    ```

-   Start the service immediately:
    ```bash
    sudo systemctl start fan-control.service
    ```

### 4. Check the Service Status

You can check if the service is running correctly and view its log output.

-   **Check status:**
    ```bash
    sudo systemctl status fan-control.service
    ```

-   **View live logs:**
    ```bash
    journalctl -u fan-control.service -f
    ```
    Press `Ctrl+C` to exit the log view.