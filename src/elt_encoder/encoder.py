#!/usr/bin/python
import argparse
import sys,os

from .definitions import *
from .helpers import *

class ProtectedDataField():
    def __init__(self):
        self.data = ''
        self.bch = ''
        self.nonprotectd = ''
        self.bch_poly = ''
        self.bch_lenght = 0

    def compute_bch_tests(self):
        field = "1001000000010010011110111001001010010010001010111100000000101"
        self.bch = calcbch(field, "1001101101100111100011", 0, len(field), len(field) + 21)
        if (self.bch) == '011010010010110100011':
            print('match')

    def compute_bch(self):
        self.bch = calcbch(self.data, self.bch_poly, 0, len(self.data), len(self.data) + self.bch_lenght)

    def __len__(self):
        return len(self.data) + len(self.bch) + len(self.nonprotectd)

    @property
    def bitstring(self):
        #self.compute_bch()
        return self.data + self.bch + self.nonprotectd

    def __str__(self):
        return self.data + self.bch + self.nonprotectd


class PDF1(ProtectedDataField):
    def __init__(self, format, protocol, **kwargs):
        super().__init__()
        self.bch_poly = "1001101101100111100011"
        self.bch_lenght = 21
        self.format = format
        self.protocol = protocol
        self.__hexid = '2024F72524FFBFF'
        self.data = ''
        self.__country = '0100000001' # Norway

    # @property
    # def format(self):
    #     return self.__format
    #
    # @format.setter
    # def format(self, v):
    #     self.__format = v
    #
    # @property
    # def protocol(self):
    #     return self.__protocol
    #
    # @protocol.setter
    # def protocol(self, v):
    #     self.__protocol = v

    @property
    def hexid(self):
        self.__hexid = bin2hex2(self.data[1:])
        return self.__hexid

    @hexid.setter
    def hexid(self, v):
        self.__hexid = v
        bits = hextobin(self.hexid)
        self.protocol = bits[0]
        self.data = str(self.format) + bits

    @property
    def country(self):
        return self.__country

    @country.setter
    def country(self, v):
        try:
            code=([k for k, ccode in countrydic.items() if v == ccode])
            self.__country = dec2bin(code[0], 10) # France has 3 numbers ?
        except IndexError:
            raise ValueError('Country Code not found')

def decdeg2dms(dd):
    is_positive = dd >= 0
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees
    return (degrees, minutes, seconds)

class PDF2(ProtectedDataField):
    def __init__(self):
        super().__init__()
        self.bch_poly = "1010100111001"
        self.bch_lenght = 12

class STANDARD_LOCATION():
    PDF1_DEFAULT_LAT = '0111111111'
    PDF1_DEFAULT_LON = '01111111111'
    PDF2_DEFAULT_LAT = '1000001111'
    PDF2_DEFAULT_LON = '1000001111'

    def __init__(self):
        self.pdf1 = PDF1(format = '1', protocol = '0')
        self.pdf2 = PDF2()

        self.country = 'France'
        self.protocol_code = '0010' # EPIRB-MMSI # bits 37-39
        self.serialid = 2
        self.identification = '01111011100100101001'
        self.supplementary = '1101' # bits 107-112 fixed
        self.latitude = None
        self.longitude = None
        self.internal_source = '1'
        self.has_homing = '1'

    def build(self):
        self.pdf1.country = self.country
        self.pdf1.data = str(self.pdf1.format) + str(self.pdf1.protocol) + str(self.pdf1.country) + self.protocol_code + self.identification + "{0:04b}".format(self.serialid)
        self.pdf2.data = self.supplementary + self.internal_source + self.has_homing
        if self.latitude == None or self.longitude == None:
            self.pdf1.data+= self.PDF1_DEFAULT_LAT + self.PDF1_DEFAULT_LON
            self.pdf2.data += self.PDF2_DEFAULT_LAT + self.PDF2_DEFAULT_LON
        else:
            #print(self.latitude, self.longitude)
            # Latitude
            if self.latitude > 0:
                self.pdf1.data+='0'
            else:
                self.pdf1.data+='1'
            deg_latitude = round(self.latitude*4)
            delta_latitude = self.latitude - deg_latitude /4
            d, m, s = decdeg2dms(delta_latitude)
            deg= dec2bin(deg_latitude, 9 )
            self.pdf1.data+=deg
            if delta_latitude < 0:
                self.pdf2.data+='0'
            else:
                self.pdf2.data+='1'
            mins = dec2bin(m, 5)
            secs = dec2bin(round(s/4), 4)
            self.pdf2.data += (mins+secs)
            # Longitude
            if self.longitude > 0:
                self.pdf1.data+='0'
            else:
                self.pdf1.data+='1'
            deg_longitude = round(self.longitude*4)
            delta_longitude = self.longitude - deg_longitude / 4
            d, m, s = decdeg2dms(delta_longitude)
            deg = dec2bin(deg_longitude, 10)
            self.pdf1.data += deg
            if delta_longitude < 0:
                self.pdf2.data += '0'
            else:
                self.pdf2.data += '1'
            mins = dec2bin(m, 5)
            secs = dec2bin(round(s / 4), 4)
            self.pdf2.data += (mins + secs)
        # BCH
        self.pdf1.compute_bch()
        self.pdf2.compute_bch()

class DigitalMessage():
    FORMAT_LONG = '1'
    FORMAT_SHORT = '0'
    BIT_SYNC = '111111111111111'
    FRAME_NORMAL = '000101111'
    FRAME_TEST = '011010000'

    def __init__(self, mode, protocol):
        self.__bitstring = ''
        self.message = None
        if mode == 'emergency':
            self.frame = self.FRAME_NORMAL
        else:
            self.frame = self.FRAME_TEST
        if protocol == 'standard':
            self.message = STANDARD_LOCATION()
            if mode == 'test': # 4.5.4 Beacon Self-Test Mode
                self.message.longitude = None
                self.message.latitude = None
        else:
            raise ValueError("Unsupported Sarsat Protocol")

    def update(self):
        self.message.build()
        self.__bitstring = self.BIT_SYNC + self.frame + self.message.pdf1.bitstring + self.message.pdf2.bitstring

    @property
    def bitstring(self):
        self.update()
        return self.__bitstring

    @property
    def bitlist(self):
        self.update()
        bits = []
        for b in self.__bitstring:
            bits.append(int(b))
        return bits

    @property
    def hexstring(self):
        self.update()
        return hex(int(self.__bitstring,2))

    @property
    def hexidstring(self):
        self.update()
        return self.message.pdf1.hexid

    def __len__(self):
        return len(self.__bitstring)


def main(argv):
    frame = 'test'
    protocol = 'standard'
    identification = '01111011100100101001'
    serial = 1
    latitude = None
    longitude = None
    homing = 0
    country = 'Belgium'
    output_t = None

    parser = argparse.ArgumentParser()
    parser.add_argument('--frame', choices=['test', 'emergency'], help='Mode')
    parser.add_argument('--protocol', choices=['standard', 'national', 'userlong', 'usershort'],
                        help='Location Protocol')
    parser.add_argument('--country', type=str, help='Country')
    parser.add_argument('--mmsi', type=str, help="MMSI Id 20 bit string")
    parser.add_argument('--serial', type=int, help='MMSI s/n 0 to 15')
    parser.add_argument('--coordinates', type=float, nargs=2, help='Lat Lon as dd.ddddd')
    parser.add_argument('--longitude', type=float, help='Longitude dd.ddddd')
    parser.add_argument('--homing', action='store_const', const=1, help='specify if Homing')
    parser.add_argument('--output', choices=['bitstring', 'bitlist', 'hexstring', 'hexid], help='Output format')
    args = parser.parse_args()

    if args.frame:
        frame = args.frame
    if args.protocol:
        protocol = args.protocol
    if args.country:
        country = args.country
    if args.mmsi:
        if (len(args.mmsi == 20)):
            identification = args.mmsi
        else:
            raise ValueError('mmsi should be 20 bits')
    if args.serial:
        if (args.serial >= 1) and (args.serial < 15):
            serial = args.serial
        else:
            raise  ValueError('serial should be between 1 et 15')
    if args.coordinates:
        latitude = args.coordinates[0]
        longitude = args.coordinates[1]

    if args.homing:
        homing = 1

    if args.output:
        output_t = args.output

    digital_msg = DigitalMessage( frame, protocol)
    digital_msg.message.country = country
    digital_msg.message.identification = identification
    digital_msg.message.serialid = serial
    digital_msg.message.latitude = latitude
    digital_msg.message.longitude = longitude
    digital_msg.message.has_homing = str(homing)

    if output_t == 'bitstring':
        print(digital_msg.bitstring)
    elif output_t == 'bitlist':
        print(digital_msg.bitlist)
    elif output_t == 'hexstring':
        print(digital_msg.hexstring)
    elif output_t == 'hexid':
        print(digital_msg.hexidstring)
    else:
        digital_msg.update()
        print("PDF1={} bits - Data={} - BCH={}".format(len(digital_msg.message.pdf1), digital_msg.message.pdf1.data, digital_msg.message.pdf1.bch))
        print("PDF2={} bits - Data={} - BCH={}".format(len(digital_msg.message.pdf2), digital_msg.message.pdf2.data, digital_msg.message.pdf2.bch))
        print("PDF1={} bits - PDF2={} bits - Total {} bits".format(len(digital_msg.message.pdf1),
                                                                   len(digital_msg.message.pdf2), len(digital_msg)))

if __name__ == "__main__":
    main(sys.argv[1:])

