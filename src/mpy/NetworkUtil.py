import rp2
import network
import time

ssid = 'CHANGEME'
password = 'ORELSE'

# Function to connect to a WLAN network. Fill in the 'ssid' and 'password' fields.
# This runs indefinitely until either a successful connection is made or an error otherwise occurs.
def connect():
    rp2.country('CA')

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # If you need to disable powersaving mode
    # wlan.config(pm = 0xa11140)

    wlan.connect(ssid, password)

    print('Connecting', end='')
    while (wlan.status() != network.STAT_GOT_IP):
        print('.', end='')

        if (wlan.status() == network.STAT_WRONG_PASSWORD):
            raise Exception('Wrong network password')
        elif (wlan.status() == network.STAT_NO_AP_FOUND):
            raise Exception('No AP named ' + ssid + ' found')
        elif (wlan.status() == network.STAT_CONNECT_FAIL):
            raise Exception('Unforeseen consequences while connecting to network')

        time.sleep(1)
    print('')

    print('Connected with IP: ' +  wlan.ifconfig()[0])
