from machine import Pin, I2C
import time
import urequests
import network
import json
from ssd1306 import SSD1306_I2C
import sys

# Constants
BASE_URL = "http://iotcounter.northeurope.cloudapp.azure.com/"
PASSWORD = {"username": "iotcalc", "password": "secret"}
WLAN_ADDRESS = "Wokwi-GUEST"

STATUS = BASE_URL + "status"
UPDATE = BASE_URL + "update"
RESET = BASE_URL + "reset"

# Shortcuts
current = "currentVisitors"
total = "totalVisitors"

# Button configuration
plus_button = Pin(2, Pin.IN, Pin.PULL_UP)
quit_button = Pin(3, Pin.IN, Pin.PULL_UP)
minus_button = Pin(4, Pin.IN, Pin.PULL_UP)

# Screen configuration
resolution_x = 128
resolution_y = 64
i2c_dev = I2C(1, scl=Pin(27), sda=Pin(26), freq=2000)
oled = SSD1306_I2C(resolution_x, resolution_y, i2c_dev)


# Connect to wifi
def connectWifi():
    print("Connecting to Wifi", end="")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WLAN_ADDRESS, "")

    tries = 0
    while not wlan.isconnected() and tries < 120:
        print(".", end="")
        time.sleep(1)
        tries += 1

    if wlan.isconnected():
        print(" Wifi connected.")

    elif not wlan.isconnected():
        print(" Wifi not connected, restart simulation!")
        sys.exit()


# Empty screen and add text
def screen_text(oled, count, countMax):
    oled.fill(0)
    oled.text(f"Visitors now:", 0, 5)
    oled.text(f"{str(count)}", 0, 20)
    oled.text("Visitors today:", 0, 35)
    oled.text(f"{str(countMax)}", 0, 50)
    oled.show()


# plus count
def plus(count, countMax):
    count += 1
    countMax += 1
    screen_text(oled, count, countMax)
    print(f"\nVisitor added!\nVisitors now: {count}\nVisitors today: {countMax}")
    return count, countMax


# minus count
def minus(count, countMax):
    if count > 0:
        count -= 1
        screen_text(oled, count, countMax)
        print(f"\nVisitor removed!\nVisitors now: {count}\nVisitors today: {countMax}")
        return count
    else:
        print("Count is 0")
        return count


# Reset visitors
def reset(count, countMax):
    try:
        response = urequests.post(RESET, json=PASSWORD).json()
        count = int(response[current])
        countMax = int(response[total])
        screen_text(oled, count, countMax)
        print(f"\nReset succeeded!\nVisitors now: {count}\nVisitors today: {countMax}")
        return count, countMax
    except Exception:
        print("\nReset failed!")


# Update
def update(timer):
    try:
        print("\nUpdating....")
        PASSWORD["currentVisitors"] = count
        PASSWORD["totalVisitors"] = countMax
        print(PASSWORD)
        response = urequests.post(UPDATE, json=PASSWORD).json()
        return True
    except Exception:
        print("Update failed")
        return False


# Main program
def main():
    connectWifi()
    global count, countMax

    # Get request for visitorcounts.
    response = urequests.get(STATUS).json()
    count = int(response[current])
    countMax = int(response[total])

    PASSWORD["currentVisitors"] = count
    PASSWORD["totalVisitors"] = countMax

    print("\nAdd: green\nRemove: red\nReset: green & red for 5 sec\nQuit: black")

    # Text to screen
    screen_text(oled, count, countMax)

    # Timer for update
    timer = machine.Timer(-1)
    timer.init(period=30000, callback=update)

    # Check if button on hold
    hold = False
    resetTimer = 0

    # Check for pressed buttons
    while True:
        if quit_button.value() == 0:
            if update(timer) == True:
                break

        elif plus_button.value() == 0 and minus_button.value() == 1 and not hold:
            count, countMax = plus(count, countMax)
            hold = True
            resetTimer = 0

        elif plus_button.value() == 1 and minus_button.value() == 0 and not hold:
            count = minus(count, countMax)
            hold = True
            resetTimer = 0

        elif plus_button.value() == 0 and minus_button.value() == 0:
            time.sleep(1)
            resetTimer += 1
            if resetTimer == 5:
                print("\nResetting....")
                count, countMax = reset(count, countMax)
            hold = True

        elif plus_button.value() == 1 and minus_button.value() == 1:
            hold = False
            resetTimer = 0

    print("\nStopping program....")
    timer.deinit()


main()