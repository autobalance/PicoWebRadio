# (Micro)Python implementation of an interface to the Si4730 AM/FM receiver.
# Still a WIP, but major functionality is mostly complete.
#
# Derived from the Si47xx Programming Guide (AN332).
#

from machine import I2C, Pin
import time

# status bits defined here
STATUS_CTS                  = const(1 << 7)
STATUS_ERR                  = const(1 << 6)
STATUS_STCINT               = const(1 << 0)

# most used commands and their associated argument/response bits defined here
POWER_UP_CMD                = const(0x01)
POWER_UP_ARG1_CTSIEN        = const(1 << 7)
POWER_UP_ARG1_GPO2OEN       = const(1 << 6)
POWER_UP_ARG1_PATCH         = const(1 << 5)
POWER_UP_ARG1_XOSCEN        = const(1 << 4)
POWER_UP_ARG1_FUNC          = const(15 << 0)
POWER_UP_ARG1_FUNC_FM       = const(0 << 0)
POWER_UP_ARG1_FUNC_AM       = const(1 << 0)
POWER_UP_ARG2_OPMODE_ANALOG = const(0x05 << 0)

POWER_DOWN_CMD              = const(0x11)

SET_PROPERTY_CMD            = const(0x12)
SET_PROPERTY_ARG1           = const(0 << 0)
GET_PROPERTY_CMD            = const(0x13)
GET_PROPERTY_ARG1           = const(0 << 0)

GET_INT_STATUS_CMD          = const(0x14)

FM_TUNE_FREQ_CMD            = const(0x20)
FM_TUNE_FREQ_ARG1_FREEZE    = const(1 << 1)
FM_TUNE_FREQ_ARG1_FAST      = const(1 << 0)

FM_SEEK_START_CMD           = const(0x21)
FM_SEEK_START_ARG1_SEEKUP   = const(1 << 3)
FM_SEEK_START_ARG1_WRAP     = const(1 << 2)

FM_TUNE_STATUS_CMD          = const(0x22)
FM_TUNE_STATUS_ARG1_CANCEL  = const(1 << 1)
FM_TUNE_STATUS_ARG1_INTACK  = const(1 << 0)
FM_TUNE_STATUS_RESP1_VALID  = const(1 << 0)
FM_TUNE_STATUS_RESP1_BLTF   = const(1 << 7)

FM_RSQ_STATUS_CMD           = const(0x23)
FM_RSQ_STATUS_ARG1_INTACK   = const(1 << 0)

AM_TUNE_FREQ_CMD            = const(0x40)
AM_TUNE_FREQ_ARG1_FAST      = const(1 << 0)

AM_SEEK_START_CMD           = const(0x41)
AM_SEEK_START_ARG1_SEEKUP   = const(1 << 3)
AM_SEEK_START_ARG1_WRAP     = const(1 << 2)

AM_TUNE_STATUS_CMD          = const(0x42)
AM_TUNE_STATUS_ARG1_CANCEL  = const(1 << 1)
AM_TUNE_STATUS_ARG1_INTACK  = const(1 << 0)
AM_TUNE_STATUS_RESP1_VALID  = const(1 << 0)
AM_TUNE_STATUS_RESP1_BLTF   = const(1 << 7)

AM_RSQ_STATUS_CMD           = const(0x43)
AM_RSQ_STATUS_ARG1_INTACK   = const(1 << 0)

AM_AGC_STATUS_CMD           = const(0x47)


# common properties and associated arguments defined here
FM_DEEMPHASIS_PROP          = const(0x1100)
FM_DEEMPHASIS_DEEMPH_75US   = const(0b10 << 0)
FM_DEEMPHASIS_DEEMPH_50US   = const(0b01 << 0)

FM_CHANNEL_FILTER_PROP      = const(0x1102)
FM_CHANNEL_FILTER_AUTO      = const(0 << 0)
FM_CHANNEL_FILTER_110KHZ    = const(1 << 0)
FM_CHANNEL_FILTER_84KHZ     = const(2 << 0)
FM_CHANNEL_FILTER_60KHZ     = const(3 << 0)
FM_CHANNEL_FILTER_40KHZ     = const(4 << 0)

FM_BLEND_STEREO_THRESHOLD_PROP   = const(0x1105)
FM_BLEND_STEREO_THRESHOLD_STEREO = const(0 << 0)
FM_BLEND_STEREO_THRESHOLD_MONO   = const(127 << 0)

FM_BLEND_MONO_THRESHOLD_PROP   = const(0x1106)
FM_BLEND_MONO_THRESHOLD_STEREO = const(0 << 0)
FM_BLEND_MONO_THRESHOLD_MONO   = const(127 << 0)

FM_ANTENNA_INPUT_PROP          = const(0x1107)
FM_ANTENNA_INPUT_FMTXO_FMI     = const(0 << 0)
FM_ANTENNA_INPUT_FMTXO_LPI     = const(1 << 0)

FM_SEEK_BAND_BOTTOM_PROP       = const(0x1400)
FM_SEEK_BAND_BOTTOM_ITU_2      = const(8800 << 0) # Americas
FM_SEEK_BAND_BOTTOM_ITU_1_3    = const(8750 << 0) # Asia, Europe and others
FM_SEEK_BAND_BOTTOM_OTHER      = const(7600 << 0) # set lowest for FMRX<=2.0 compatibility

FM_SEEK_BAND_TOP_PROP          = const(0x1401)
FM_SEEK_BAND_TOP_ITU_2         = const(10800 << 0)
FM_SEEK_BAND_TOP_ITU_1_3       = const(10800 << 0)
FM_SEEK_BAND_TOP_OTHER         = const(10800 << 0)

FM_SEEK_FREQ_SPACING_PROP      = const(0x1402)
FM_SEEK_FREQ_SPACING_ITU_2     = const(10 << 0) # 100KHz spacing for Americas
FM_SEEK_FREQ_SPACING_ITU_1_3   = const(5 << 0) # 50KHz spacing should cover most other places

AM_DEEMPHASIS_PROP             = const(0x3100)
AM_DEEMPHASIS_50US             = const(1 << 0)
AM_DEEMPHASIS_NONE             = const(0 << 0)

AM_CHANNEL_FILTER_PROP         = const(0x3102)
AM_CHANNEL_FILTER_AMPLFLT      = const(1 << 8)
AM_CHANNEL_FILTER_6KHZ         = const(0 << 0)
AM_CHANNEL_FILTER_4KHZ         = const(1 << 0)
AM_CHANNEL_FILTER_3KHZ         = const(2 << 0)
AM_CHANNEL_FILTER_2KHZ         = const(3 << 0)
AM_CHANNEL_FILTER_1KHZ         = const(4 << 0)
AM_CHANNEL_FILTER_1_8KHZ       = const(5 << 0)
AM_CHANNEL_FILTER_2_5KHZ       = const(6 << 0)

# calculated as AVC_MAX_GAIN = desired_gain(dB) * 340.2 as per datasheet
AM_AVC_MAX_GAIN_PROP           = const(0x3103)
AM_AVC_MAX_GAIN_MAX            = const(0x7800 << 0)
AM_AVC_MAX_GAIN_MIN            = const(0 << 0)

# disabling soft mute when using a crappy antenna seems to improve audio (stable volume?)
AM_SOFT_MUTE_MAX_ATTEN_PROP    = const(0x3302)
AM_SOFT_MUTE_MAX_ATTEN_MAX     = const(63 << 0)
AM_SOFT_MUTE_MAX_ATTEN_MIN     = const(0 << 0) # use this to disable soft mute

AM_SEEK_BAND_BOTTOM_PROP       = const(0x3400)
AM_SEEK_BAND_BOTTOM_ITU_2      = const(520 << 0)
AM_SEEK_BAND_BOTTOM_ITU_1_3    = const(522 << 0)
AM_SEEK_BAND_BOTTOM_OTHER      = const(520 << 0)

AM_SEEK_BAND_TOP_PROP          = const(0x3401)
AM_SEEK_BAND_TOP_ITU_2         = const(1710 << 0)
AM_SEEK_BAND_TOP_ITU_1_3       = const(1710 << 0)
AM_SEEK_BAND_TOP_OTHER         = const(1710 << 0)

AM_SEEK_FREQ_SPACING_PROP      = const(0x3402)
AM_SEEK_FREQ_SPACING_ITU_2     = const(10 << 0)
AM_SEEK_FREQ_SPACING_ITU_1_3   = const(9 << 0)

AM_SEEK_TUNE_SNR_THRESHOLD_PROP  = const(0x3403)

AM_SEEK_TUNE_RSSI_THRESHOLD_PROP = const(0x3404)

RX_VOLUME_PROP                 = const(0x4000)
RX_VOLUME_MAX                  = const(63 << 0)
RX_VOLUME_MIN                  = const(0 << 0)

RX_HARD_MUTE                   = const(0x4001)
RX_HARD_MUTE_LMUTE             = const(1 << 1)
RX_HARD_MUTE_RMUTE             = const(1 << 0)

class Si4730:
    def __init__(self, i2c=None, rst_pin=22, addr=0x63):
        if (i2c is None):
            self.__i2c = I2C(0, freq=400000)
        else:
            self.__i2c = i2c

        self.__rst_pin = Pin(rst_pin, Pin.OUT)
        self.__addr = addr

        # state to store currently selected band
        self.__band = ''

        # maintain a list of channels detected via the scan function on the Si4730
        # store in units of 10KHz (e.g. fm_channel[0] == 8810 ---> real freq. = 88.1MHz)
        self.__channels = {'FM': [], 'AM': []}

        self.reset()

    # use this to initialize the device but also to get out of an unknown state (e.g. bad config.)
    def reset(self):
        # reset should be pulsed for at least 100us, so 10ms is somewhat arbitrary
        self.__rst_pin.off()
        time.sleep_ms(10)
        self.__rst_pin.on()

        # probably not needed after a cycle of the reset pin, but eh, why not
        self.send_cmd(POWER_DOWN_CMD)

        # start by default in FM mode, to be able to send other commands
        self.__set_band('FM')

        if ((self.__get_status() & STATUS_ERR) != 0):
            raise OSError(errno.EIO, 'Error status from Si4730')

    def __get_status(self):
        return self.__i2c.readfrom(self.__addr, 1)[0]

    # status byte appears to be first byte of response to any command
    # so let's just read from the device to see if it's clear to send
    def __wait_for_CTS(self, timeout=1000):
        while ((self.__get_status() & STATUS_CTS) == 0):
            time.sleep_ms(1)
            timeout -= 1

            if (timeout < 0):
                raise OSError(errno.ETIMEDOUT, 'Timeout waiting for CTS')

    # default timeout of 60s, seeking for valid channels can take a while
    def __wait_for_STC(self, timeout=60000):
        while ((self.send_cmd(GET_INT_STATUS_CMD)[0] & STATUS_STCINT) == 0):
            time.sleep_ms(1)
            timeout -= 1

            if (timeout < 0):
                raise OSError(errno.ETIMEDOUT, 'Timeout waiting for STC (try longer)')

    # cmd and args are treated as integers (to allow bitwise ops before calling)
    def send_cmd(self, cmd, *args):
        self.__wait_for_CTS()
        self.__i2c.writeto(self.__addr, bytes([cmd]) + bytes(args))

        # TODO: optimize this to not return max length response each time
        resp = self.__i2c.readfrom(self.__addr, 16)

        if ((resp[0] & STATUS_ERR) != 0):
            raise OSError(errno.EIO, 'Error status from Si4730')

        return resp

    # prop and val are treated as length-2 array of ints
    def set_property(self, prop, val):
        self.send_cmd(SET_PROPERTY_CMD, SET_PROPERTY_ARG1,
                                        prop >> 8, prop & 0xff,
                                        val >> 8, val & 0xff)

    def get_property(self, prop):
        resp = self.send_cmd(GET_PROPERTY_CMD, GET_PROPERTY_ARG1,
                                               prop >> 8, prop & 0xff)

        return resp[2]*256 + resp[3]


    # loosely follows example flowchart in datasheet for setting up AM/FM receiver
    # TODO: allow for setting up selected band based on region provided
    #       as it currently sets up assuming Americas
    def __set_band(self, band):
        band = band.upper()

        # don't needlessly power down/power up device if band is already selected
        if (band == self.__band):
            return

        if (band == 'FM'):
            self.__band = band

            self.send_cmd(POWER_DOWN_CMD)

            self.send_cmd(POWER_UP_CMD, POWER_UP_ARG1_XOSCEN | POWER_UP_ARG1_FUNC_FM,
                                        POWER_UP_ARG2_OPMODE_ANALOG)

            self.set_property(FM_ANTENNA_INPUT_PROP, FM_ANTENNA_INPUT_FMTXO_FMI)
            self.set_property(FM_DEEMPHASIS_PROP, FM_DEEMPHASIS_DEEMPH_75US)
            self.set_property(FM_BLEND_MONO_THRESHOLD_PROP, FM_BLEND_MONO_THRESHOLD_MONO)
            self.set_property(FM_BLEND_STEREO_THRESHOLD_PROP, FM_BLEND_STEREO_THRESHOLD_MONO)

            self.set_property(FM_CHANNEL_FILTER_PROP, FM_CHANNEL_FILTER_AUTO)
            self.set_property(FM_SEEK_BAND_BOTTOM_PROP, FM_SEEK_BAND_BOTTOM_ITU_2)
            self.set_property(FM_SEEK_BAND_TOP_PROP, FM_SEEK_BAND_TOP_ITU_2)
            self.set_property(FM_SEEK_FREQ_SPACING_PROP, FM_SEEK_FREQ_SPACING_ITU_2)
        elif (band == 'AM'):
            self.__band = band

            self.send_cmd(POWER_DOWN_CMD)

            self.send_cmd(POWER_UP_CMD, POWER_UP_ARG1_XOSCEN | POWER_UP_ARG1_FUNC_AM,
                                        POWER_UP_ARG2_OPMODE_ANALOG)

            self.set_property(AM_DEEMPHASIS_PROP, AM_DEEMPHASIS_50US)
            self.set_property(AM_SOFT_MUTE_MAX_ATTEN_PROP, AM_SOFT_MUTE_MAX_ATTEN_MIN)

            self.set_property(AM_CHANNEL_FILTER_PROP, AM_CHANNEL_FILTER_6KHZ)
                                                      # | AM_CHANNEL_FILTER_AMPLFLT) too much supression
            self.set_property(AM_SEEK_BAND_BOTTOM_PROP, AM_SEEK_BAND_BOTTOM_ITU_2)
            self.set_property(AM_SEEK_BAND_TOP_PROP, AM_SEEK_BAND_TOP_ITU_2)
            self.set_property(AM_SEEK_FREQ_SPACING_PROP, AM_SEEK_FREQ_SPACING_ITU_2)

            # default thresholds seem to miss signals that sound as good as AM gets
            self.set_property(AM_SEEK_TUNE_SNR_THRESHOLD_PROP, 0)
            self.set_property(AM_SEEK_TUNE_RSSI_THRESHOLD_PROP, 20)
        else:
            raise ValueError('Invalid band selected')

        self.set_property(RX_VOLUME_PROP, RX_VOLUME_MAX)
        self.set_property(RX_HARD_MUTE, 0)

    def get_channels(self):
        return self.__channels

    def scan(self, band):
        band = band.upper()

        if (band == 'FM'):
            # device may be tuned or otherwise configured in an unknown way
            # so let's force the band to be selected and configured
            self.__band = ''
            self.__set_band('FM')

            self.__channels['FM'].clear()
            seek_halt = False
            while (not seek_halt):
                self.send_cmd(FM_SEEK_START_CMD, FM_SEEK_START_ARG1_SEEKUP)
                self.__wait_for_STC()

                resp = self.send_cmd(FM_TUNE_STATUS_CMD, FM_TUNE_STATUS_ARG1_INTACK)
                if (resp[1] & FM_TUNE_STATUS_RESP1_VALID):
                    self.__channels['FM'].append(resp[2]*256 + resp[3])

                if (resp[1] & FM_TUNE_STATUS_RESP1_BLTF):
                    seek_halt = True

                # TODO: seek to first valid channel or mute here
        elif (band == 'AM'):
            self.__band = ''
            self.__set_band('AM')

            seek_halt = False
            self.__channels['AM'].clear()
            while (not seek_halt):
                self.send_cmd(AM_SEEK_START_CMD, AM_SEEK_START_ARG1_SEEKUP)
                self.__wait_for_STC()

                resp = self.send_cmd(AM_TUNE_STATUS_CMD, AM_TUNE_STATUS_ARG1_INTACK)
                if (resp[1] & AM_TUNE_STATUS_RESP1_VALID):
                    self.__channels['AM'].append(resp[2]*256 + resp[3])

                if (resp[1] & AM_TUNE_STATUS_RESP1_BLTF):
                    seek_halt = True

                # TODO: seek to first valid channel or mute here
        else:
            raise ValueError('Invalid band selected')

        return self.get_channels()[band]

    # expects freq in the units of 10KHz
    def tune(self, band, freq):
        band = band.upper()

        if (band == 'FM'):
            # this won't perform a power cycle if band is already selected
            self.__set_band('FM')

            if (freq < FM_SEEK_BAND_BOTTOM_ITU_2 or freq > FM_SEEK_BAND_TOP_ITU_2):
                raise ValueError('Frequency out of range')

            self.send_cmd(FM_TUNE_FREQ_CMD, 0, freq >> 8, freq & 0xff, 0)
            self.__wait_for_STC()

            resp = self.send_cmd(FM_TUNE_STATUS_CMD, FM_TUNE_STATUS_ARG1_INTACK)
        elif (band == 'AM'):
            self.__set_band('AM')

            if (freq < AM_SEEK_BAND_BOTTOM_ITU_2 or freq > AM_SEEK_BAND_TOP_ITU_2):
                raise ValueError('Frequency out of range')

            self.send_cmd(AM_TUNE_FREQ_CMD, 0, freq >> 8, freq & 0xff, 0, 0)
            self.__wait_for_STC()

            resp = self.send_cmd(AM_TUNE_STATUS_CMD, AM_TUNE_STATUS_ARG1_INTACK)
        else:
            raise ValueError('Invalid band selected')

        # return whether station is valid, and the RSSI and SNR
        return [resp[1] & 1, resp[4], resp[5]]
