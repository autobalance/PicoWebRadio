# PicoWebRadio main app including the associated server classes and run function.
#
# NOTE: Tried to run the web servers in a multi-threaded fashion on the Raspberry Pi Pico
# using MicroPython's _thread class, but it always crashes, so I opted for a simpler uasyncio
# approach. The uasyncio approach was guided by the great tutorial at:
#
#   https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md
#
# with the server code adapted from:
# 
#   https://github.com/peterhinch/micropython-async/tree/master/v3/as_drivers/client_server
#

from machine import I2C, Pin
import machine
import time
import usocket as socket
import uasyncio as asyncio
import os

import NetworkUtil
from Si4730 import Si4730
import WAVBuffer

# Set the desired channel for acquiring mono audio from the Si4730.
ADC_CHAN = const(2)

# Configure the Si4730 parameters here.
SI4730_I2C_DEV = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
SI4730_RESET_PIN = const(22)
SI4730_I2C_ADDR = const(0x63)
SI4730_RADIO = Si4730(i2c=SI4730_I2C_DEV, rst_pin=SI4730_RESET_PIN, addr=SI4730_I2C_ADDR)

# Audio server to stream the audio buffer (currently encoded as a WAV file).
# TODO: Note that iOS/Safari doesn't support WAV files, so look into some other
#       format (e.g. try to build an MP3Buffer encoder to run on core 1 of the RP2040).
#       This may require an external DSP to do the encoding...
class AudioServer:
    def __init__(self, host='0.0.0.0', port=1234, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    async def run(self):
        self.cid = -1
        self.server = await asyncio.start_server(self.audio_stream, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)

    async def audio_stream(self, sreader, swriter):
        self.cid += 1
        stream_id = self.cid

        try:
            # TODO: Look into properly reading and handling the entire HTTP request.
            #       For now, we just care about the first line (handling GET for 'audio.wav').
            r = await asyncio.wait_for(sreader.read(1024), self.timeout)
            if (r == b''):
                raise Exception('Invalid HTTP request?')

            r = r.decode().splitlines()[0].split(' ')

            req_method = r[0]
            req_data = r[1].strip('/')

            if (req_method != 'GET' or req_data != 'audio.wav'):
                swriter.write(b'HTTP/1.0 400 Bad Request\r\n\r\n')
                await swriter.drain()
                raise

            # if no more FIFOs, send 503 error and end stream early
            try:
                buf = WAVBuffer.fetch(stream_id)
            except ValueError:
                swriter.write(b'HTTP/1.0 503 Service Unavailable\r\n'  \
                              b'Access-Control-Allow-Origin: *\r\n\r\n')
                await swriter.drain()
                raise Exception('No more FIFOs available')

            swriter.write(b'HTTP/1.0 200 OK\r\n' \
                          b'Access-Control-Allow-Origin: *\r\n' \
                          b'Content-type: audio/wav\r\n\r\n')

            swriter.write(WAVBuffer.header())
            await swriter.drain()

            # repeatedly send audio buffer as it becomes available
            while True:
                while (buf := WAVBuffer.fetch(stream_id)) == b'':
                    await asyncio.sleep_ms(1)
                swriter.write(buf)
                await swriter.drain()

        except OSError as ose:
            if (ose.errno != errno.ECONNRESET):
                raise
        except Exception as e:
            print('ERROR in audio_stream: ' + str(e))

        self.cid -= 1
        await sreader.wait_closed()

    async def close(self):
        self.server.close()
        await self.server.wait_closed()


# HTML server to present the web radio app and allow scanning/tuning of the Si4730.
class HTMLServer:
    def __init__(self, host='0.0.0.0', port=80, backlog=5, timeout=20, radio=None):
        if (radio is None):
            radio = Si4730()

        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        self.__radio = radio

        try:
            os.stat('stations.xml')
        except OSError as ose:
            if (ose.errno == errno.ENOENT):
                self.__gen_stations_xml()
            else:
                raise

    def __gen_stations_xml(self):
        self.__radio.scan('AM')
        self.__radio.scan('FM')
        stations = self.__radio.get_channels()

        stations_xml = open('stations.xml', 'w')
        stations_xml.write('<?xml version="1.0" encoding="UTF-8"?>\r\n' \
                           '<station-list>\r\n')
        for station in stations['FM']:
            stations_xml.write('<station>\r\n' \
                               '<name>'+str(station/100)+' FM</name>\r\n' \
                               '<url>tune/fm/'+str(station)+'</url>\r\n' \
                               '</station>\r\n')
        for station in stations['AM']:
            stations_xml.write('<station>\r\n' \
                               '<name>'+str(station)+' AM</name>\r\n' \
                               '<url>tune/am/'+str(station)+'</url>\r\n' \
                               '</station>\r\n')
        stations_xml.write('</station-list>\r\n')
        stations_xml.close()

    async def run(self):
        self.server = await asyncio.start_server(self.html_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)

    async def html_client(self, sreader, swriter):
        try:
            # TODO: Look into properly reading and handling the entire HTTP request.
            #       For now, we just care about the first line (handling GET or PATCH).
            r = await asyncio.wait_for(sreader.read(1024), self.timeout)
            if (r == b''):
                raise Exception('Invalid HTTP request?')

            r = r.decode().splitlines()[0].split(' ')

            req_method = r[0]
            req_data = r[1].strip('/')

            if (req_method == 'GET'):
                if (req_data == ''):
                    req_data = 'index.html'
                elif (req_data == 'scan.xml'):
                    self.__gen_stations_xml()
                    req_data = 'stations.xml'

                req_data_ext = req_data.split('.')[-1].lower()
                if (req_data_ext == 'html'):
                    content_type = b'Content-type: text/html\r\n\r\n'
                elif (req_data_ext == 'js'):
                    content_type = b'Content-type: text/javascript\r\n\r\n'
                elif (req_data_ext == 'css'):
                    content_type = b'Content-type: text/css\r\n\r\n'
                elif (req_data_ext == 'svg'):
                    content_type = b'Content-type: image/svg+xml\r\n\r\n'
                elif (req_data_ext == 'xml'):
                    content_type = b'Content-type: text/xml\r\n\r\n'

                # TODO: read data from file incrementally (may run out of memory)
                try:
                    file = open(req_data, 'rb')
                    file_data = file.read()
                    file.close()

                    swriter.write(b'HTTP/1.0 200 OK\r\n')
                    swriter.write(content_type)
                    swriter.write(file_data)
                    await swriter.drain()
                except:
                    swriter.write(b'HTTP/1.0 400 Bad Request\r\n\r\n')
                    await swriter.drain()

            elif (req_method == 'PATCH'):
                valid_patch = False
                req_data_split = req_data.split('/')
                if (len(req_data_split) == 3):
                    if (req_data_split[0] == 'tune'):
                        if (req_data_split[1] == 'am'):
                            self.__radio.tune('AM', int(req_data_split[2]))
                            valid_patch = True
                        elif (req_data_split[1] == 'fm'):
                            self.__radio.tune('FM', int(req_data_split[2]))
                            valid_patch = True

                if (valid_patch):
                    swriter.write(b'HTTP/1.0 204 No Content\r\n')
                    swriter.write(b'Content-Location: /' + req_data + '\r\n\r\n')
                else:
                    swriter.write(b'HTTP/1.0 400 Bad Request\r\n\r\n')

                await swriter.drain()

            else:
                swriter.write(b'HTTP/1.0 400 Bad Request\r\n\r\n')
                await swriter.drain()

        except Exception as e:
            print('ERROR in html_client: ' + str(e))

        await sreader.wait_closed()

    async def close(self):
        self.server.close()
        await self.server.wait_closed()

async def heartbeat(led):
    while True:
        led.off()
        await asyncio.sleep_ms(800)
        led.on()
        await asyncio.sleep_ms(50)
        led.off()
        await asyncio.sleep_ms(50)
        led.on()
        await asyncio.sleep_ms(50)
        led.off()
        await asyncio.sleep_ms(50)

# Function to run the entire app.
# TODO: Look into why the ADC and DMA module can't be started until after
#       the network is connected (may have to do with DMA being used?)
def run():
    led = Pin('LED', Pin.OUT)

    NetworkUtil.connect()

    # start the ADC DMA acquisition after starting the network
    WAVBuffer.init(ADC_CHAN)
    WAVBuffer.start()

    audio_server = AudioServer()
    html_server = HTMLServer(radio=SI4730_RADIO)

    try:
        gather_run = asyncio.gather(audio_server.run(), html_server.run(), heartbeat(led))
        asyncio.run(gather_run)
    except:
        raise
    finally:
        gather_close = asyncio.gather(audio_server.close(), html_server.close())
        asyncio.run(gather_close)
        led.off()
        _ = asyncio.new_event_loop()
