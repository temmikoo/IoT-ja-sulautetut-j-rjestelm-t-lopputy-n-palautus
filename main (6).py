from machine import ADC, Pin, I2C
from time import sleep
from pico_i2c_lcd import I2cLcd
import network
import urequests
import socket
import json

# =============================
#   ADC SENSORS
# =============================

# Spoon temperature sensor
adc_spoon = ADC(Pin(27))  # GP27 / ADC1

# Foil leak sensor
adc_foil = ADC(Pin(26))  # GP26 / ADC0

# =============================
#   LEDs
# =============================

# Temperature LED bar (GP6..GP2)
leds_temp = [
    Pin(6, Pin.OUT),  # LED 1 – coldest
    Pin(5, Pin.OUT),  # LED 2
    Pin(4, Pin.OUT),  # LED 3
    Pin(3, Pin.OUT),  # LED 4
    Pin(2, Pin.OUT),  # LED 5 – hottest before warning
]

# Leak LEDs
led_ok = Pin(10, Pin.OUT)  # Green – dry
led_leak = Pin(11, Pin.OUT)  # Red – leak detected

# =============================
#   LCD
# =============================

# NOTE: using your current I2C0 + 0x3C setup
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
lcd = I2cLcd(i2c, addr=0x3C, cols=16, rows=2)
DEG = chr(223)

# =============================
#   CONSTANTS
# =============================

VCC = 3.3
SAMPLES = 20  # Increased for better noise rejection
DELAY = 2.0

# Leak sensor calibration (you measured these)
FOIL_DRY = 64000
FOIL_WET = 40000
FOIL_THRESH = (FOIL_DRY + FOIL_WET) // 2  # mid-point (modifiable at runtime)

# Leak detection debouncing (prevent false triggers from noise)
LEAK_DEBOUNCE_COUNT = 3  # Must detect leak this many times in a row
leak_counter = 0  # Tracks consecutive leak readings

# =============================
#   THINGSPEAK / WIFI SETTINGS
# =============================

SSID = ""
PASSWORD = ""

WRITE_API_KEY = "RDNRM48C5ODU3MSR"
CHANNEL_ID = "Y3190908"  # not used directly, but left here


# -----------------------------
# WIFI-YHTEYS
# -----------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("WiFi: Connecting", end="")
    while not wlan.isconnected():
        print(".", end="")
        sleep(0.3)

    ip = wlan.ifconfig()[0]
    print(f"\nWiFi Connected: {ip}")
    return ip


# -----------------------------
# THINGSPEAK-LÄHETYS
# -----------------------------
def send_to_thingspeak(temp, leak_value):
    url = (
        f"https://api.thingspeak.com/update?"
        f"api_key={WRITE_API_KEY}"
        f"&field1={temp}"
        f"&field2={leak_value}"
    )

    try:
        r = urequests.get(url)
        print("ThingSpeak:", r.text)
        r.close()
    except Exception as e:
        print("TS error:", e)


# -----------------------------
# HTTP CONTROL SERVER
# -----------------------------
def send_response(client, response_data):
    """Send HTTP response with proper headers and connection handling"""
    response_body = json.dumps(response_data)
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{response_body}"
    )
    client.sendall(response.encode("utf-8"))


def handle_request(client):
    global FOIL_THRESH, FOIL_DRY, FOIL_WET

    try:
        # Set client socket to blocking mode for receiving data
        client.setblocking(True)
        client.settimeout(2.0)  # 2 second timeout

        request = client.recv(1024).decode("utf-8")

        # Parse the request line
        lines = request.split("\r\n")
        if len(lines) > 0:
            parts = lines[0].split(" ")
            if len(parts) >= 2:
                method = parts[0]
                path = parts[1]

                # Handle OPTIONS preflight (CORS)
                if method == "OPTIONS":
                    response = (
                        "HTTP/1.1 204 No Content\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                        "Access-Control-Allow-Headers: Content-Type\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                    )
                    client.sendall(response.encode("utf-8"))
                    return

                # Handle GET /status
                if method == "GET" and path == "/status":
                    response_data = {
                        "foil_thresh": FOIL_THRESH,
                        "foil_dry": FOIL_DRY,
                        "foil_wet": FOIL_WET,
                        "temp_limit": 50,
                    }
                    send_response(client, response_data)
                    return

                # Handle POST /set_threshold
                elif method == "POST" and path.startswith("/set_threshold"):
                    # Extract value from query string
                    if "?" in path:
                        query = path.split("?")[1]
                        for param in query.split("&"):
                            if "=" in param:
                                key, value = param.split("=")
                                if key == "value":
                                    new_thresh = int(value)
                                    FOIL_THRESH = new_thresh
                                    print(f"Threshold updated to: {FOIL_THRESH}")

                    response_data = {"success": True, "new_threshold": FOIL_THRESH}
                    send_response(client, response_data)
                    return

                # Handle POST /reset_threshold
                elif method == "POST" and path == "/reset_threshold":
                    FOIL_THRESH = (FOIL_DRY + FOIL_WET) // 2
                    print(f"Threshold reset to default: {FOIL_THRESH}")

                    response_data = {"success": True, "new_threshold": FOIL_THRESH}
                    send_response(client, response_data)
                    return

                # Handle POST /calibrate_dry
                elif method == "POST" and path == "/calibrate_dry":
                    foil_raw = read_adc_avg(adc_foil)
                    FOIL_DRY = foil_raw
                    FOIL_THRESH = (FOIL_DRY + FOIL_WET) // 2
                    print(f"Dry calibration: {FOIL_DRY}, new threshold: {FOIL_THRESH}")

                    response_data = {
                        "success": True,
                        "foil_dry": FOIL_DRY,
                        "new_threshold": FOIL_THRESH,
                    }
                    send_response(client, response_data)
                    return

                # Handle POST /calibrate_wet
                elif method == "POST" and path == "/calibrate_wet":
                    foil_raw = read_adc_avg(adc_foil)
                    FOIL_WET = foil_raw
                    FOIL_THRESH = (FOIL_DRY + FOIL_WET) // 2
                    print(f"Wet calibration: {FOIL_WET}, new threshold: {FOIL_THRESH}")

                    response_data = {
                        "success": True,
                        "foil_wet": FOIL_WET,
                        "new_threshold": FOIL_THRESH,
                    }
                    send_response(client, response_data)
                    return

        # Default 404 response
        response = "HTTP/1.1 404 Not Found\r\n" "Connection: close\r\n" "\r\n"
        client.sendall(response.encode("utf-8"))

    except Exception as e:
        print(f"Request error: {e}")
        try:
            response = (
                "HTTP/1.1 500 Internal Server Error\r\n" "Connection: close\r\n" "\r\n"
            )
            client.sendall(response.encode("utf-8"))
        except:
            pass

    finally:
        try:
            client.close()
        except:
            pass


def start_server(port=80):
    """Start HTTP server in non-blocking mode"""
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.setblocking(False)  # Non-blocking mode
    print(f"HTTP server listening on port {port}")
    return s


def check_server(server_socket):
    """Check for incoming requests without blocking"""
    try:
        client, addr = server_socket.accept()
        print(f"Client connected from {addr}")
        handle_request(client)
    except OSError:
        # No connection pending
        pass


# =============================
#   FUNCTIONS
# =============================


def read_adc_avg(adc: ADC):
    """Read ADC with averaging and outlier rejection for noise immunity"""
    readings = []
    for _ in range(SAMPLES):
        readings.append(adc.read_u16())
        sleep(0.01)

    # Sort and discard top/bottom 10% to remove noise spikes
    readings.sort()
    trim = SAMPLES // 10 or 1
    trimmed = readings[trim:-trim] if trim < SAMPLES // 2 else readings

    return sum(trimmed) // len(trimmed)


def adc_to_voltage(raw):
    return raw * VCC / 65535.0


def light_leds(count: int):
    """Turn on the first `count` temperature LEDs (0–5)."""
    for i, led in enumerate(leds_temp):
        led.value(1 if i < count else 0)


def check_leak(raw_value: int) -> int:
    """
    Handle leak LEDs + debug print with debouncing.
    Wiring: 1M pull-up to 3.3V, other foil to GND.
    => Wet (leak) pulls node DOWN -> raw_value becomes SMALLER.
    Uses debouncing to ignore transient noise/interference.
    """
    global leak_counter

    # Check if reading indicates potential leak
    if raw_value < FOIL_THRESH:
        leak_counter += 1
    else:
        leak_counter = 0  # Reset if reading is normal

    # Only trigger leak alarm after consecutive detections
    if leak_counter >= LEAK_DEBOUNCE_COUNT:
        # Confirmed leak
        led_leak.value(1)
        led_ok.value(0)
        print(f"!! Vuoto havaittu !!  arvo: {raw_value} (confirmed)")
    else:
        # Dry or unconfirmed reading
        led_leak.value(0)
        led_ok.value(1)
        if leak_counter > 0:
            print(
                f"Vuotovahti: {raw_value} (checking {leak_counter}/{LEAK_DEBOUNCE_COUNT})"
            )
        else:
            print(f"Vuotovahti OK, arvo: {raw_value}")

    return raw_value


# =============================
#   MAIN
# =============================

pico_ip = connect_wifi()
print(f"\n>>> Control panel: http://{pico_ip}")
print(">>> Available endpoints:")
print("    GET  /status")
print("    POST /reset_threshold")
print("    POST /set_threshold?value=XXXXX")
print("    POST /calibrate_dry")
print("    POST /calibrate_wet\n")

# Start HTTP control server
server = start_server(80)

while True:
    # Check for control commands (non-blocking)
    check_server(server)
    # ---- Spoon temperature ----
    spoon_raw = read_adc_avg(adc_spoon)
    spoon_voltage = adc_to_voltage(spoon_raw)
    # Your current transfer function
    temperature = 48.65 * spoon_voltage - 7

    # ---- Foil leak sensor ----
    foil_raw = read_adc_avg(adc_foil)
    leak_value = check_leak(foil_raw)  # sets LEDs, returns same raw

    # Leak boolean just for printing
    leak = foil_raw < FOIL_THRESH

    # ---- Overheat branch (> 50 °C) ----
    if temperature > 50:
        # Debug print
        print(
            "!! YLIKUUMENEMINEN !!  "
            f"Temp: {temperature:.1f}C | "
            f"Spoon RAW {spoon_raw} | "
            f"Foil RAW {foil_raw} | "
            f"Leak: {'YES' if leak else 'NO'}"
        )

        # LCD warning
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("VAROITUS!")
        lcd.move_to(0, 1)
        lcd.putstr("{:.1f} {}C".format(temperature, DEG))

        # Blink all temp LEDs
        light_leds(5)
        sleep(0.5)
        light_leds(0)
        sleep(0.1)

        # Send to ThingSpeak even in overheat
        send_to_thingspeak(temperature, leak_value)

        # Fast loop so blinking + LCD feel responsive
        continue

    # ---- Normal temperature range behaviour ----

    # Temperature LED ranges like the original
    if temperature < 0:
        light_leds(0)
    elif 0 <= temperature <= 10:
        light_leds(1)
    elif 11 <= temperature <= 20:
        light_leds(2)
    elif 21 <= temperature <= 30:
        light_leds(3)
    elif 31 <= temperature <= 40:
        light_leds(4)
    elif 41 <= temperature <= 50:
        light_leds(5)

    # ---- Debug print ----
    print(
        f"Temp: {temperature:.1f}C | "
        f"Spoon RAW {spoon_raw} | "
        f"Foil RAW {foil_raw} | "
        f"Leak: {'YES' if leak else 'NO'}"
    )

    # ---- LCD normal display ----
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Lampotila:")
    lcd.move_to(0, 1)
    lcd.putstr("{:.1f} {}C".format(temperature, DEG))

    # ---- Send to ThingSpeak ----
    send_to_thingspeak(temperature, leak_value)

    sleep(DELAY)
