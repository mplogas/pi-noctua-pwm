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

The script uses `gpiozero` with the `lgpio` backend (default on Raspberry Pi OS Bookworm/Trixie). Both are pre-installed on a stock image; if you need to install them manually:

```bash
sudo apt update
sudo apt install python3-gpiozero python3-lgpio
```

Your user must be in the `gpio` group to access GPIO without root:

```bash
sudo usermod -aG gpio <your_username>
```

Log out and back in (or reboot) for the group change to take effect.

## Configuration

All user-configurable parameters are located at the top of the `fan-control.py` script.

```python
# --- Configuration ---
GPIO_PWM = 14            # BCM pin number (physical pin 8)
PWM_FREQ_HZ = 1_000      # Software PWM frequency
TEMP_FILE_PATH = "/sys/block/nvme0n1/device/hwmon1/temp1_input"
READ_INTERVAL = 10       # Seconds between temperature checks.
LOWER_TEMP = 40          # Temp (C) below which the fan turns off.
UPPER_TEMP = 65          # Temp (C) at which the fan reaches 100% speed.
MIN_FAN_SPEED = 20       # Minimum fan speed (percent) when temp is above LOWER_TEMP.
MAX_FAN_SPEED = 100      # Maximum fan speed (percent).
```

Noctua's PWM specification calls for ~25 kHz, but the fan tested for this project was unresponsive at that rate, so `PWM_FREQ_HZ` defaults to 1 kHz. If you hear an audible whine from the fan windings, drop it to `100`.

## Running as a Systemd Service

To have the script start automatically on boot, you can run it as a `systemd` service.

### 1. Install the Service File

A ready-to-use unit file ships in the repo. Copy it into place and edit the `ExecStart` path and `User` to match your setup:

```bash
sudo cp fan-control.service /etc/systemd/system/fan-control.service
sudoedit /etc/systemd/system/fan-control.service
```

The file content, with the two lines you will need to change marked:

```ini
[Unit]
Description=Temperature-based Fan Control Service
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/pi-noctua-pwm/fan-control.py   # edit this
Restart=on-failure
User=<your_username>                                               # edit this
Group=gpio
Environment=PYTHONUNBUFFERED=1
# lgpio creates a notification pipe in CWD; give it a managed runtime dir.
RuntimeDirectory=fan-control
WorkingDirectory=/run/fan-control

[Install]
WantedBy=multi-user.target
```

`RuntimeDirectory` plus `WorkingDirectory` are not optional: lgpio writes a notification pipe to the current working directory on startup, and the default systemd CWD (`/`) is not writable by an unprivileged user, so without them the service fails to start even though manual invocations from a shell work. `PYTHONUNBUFFERED=1` makes the script's prints reach `journalctl` live instead of buffering until the process exits.

### 2. Enable and Start the Service

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

### 3. Check the Service Status

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