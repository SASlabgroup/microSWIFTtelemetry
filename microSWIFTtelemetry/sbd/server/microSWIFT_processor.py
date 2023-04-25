#! /usr/bin/env python3
"""
Created on May 16, 2014
Updated Aug 22, 2022 for python 3

@author: adioso
"""

import codecs
import datetime
import struct
from struct import unpack_from

# Payload version
_4_0 = '7'


def _checkSize(size, expected, name, p_id):
    if size != expected:
        raise Exception("Payload {} {} size {} expected {}".format(p_id,
                                                                   name,
                                                                   size,
                                                                   expected))


def _float_from_unsigned16(n):
    """
    Read IEEE 754 half-precision float
    source: https://gist.github.com/zed/59a413ae2ed4141d2037
    """
    assert 0 <= n < 2 ** 16
    sign = n >> 15
    exp = (n >> 10) & 0b011111
    fraction = n & (2 ** 10 - 1)
    if exp == 0:
        if fraction == 0:
            return -0.0 if sign else 0.0
        else:
            return (-1) ** sign * fraction / 2 ** 10 * 2 ** (-14)  # subnormal
    elif exp == 0b11111:
        if fraction == 0:
            return float('-inf') if sign else float('inf')
        else:
            return float('nan')
    return (-1) ** sign * (1 + fraction / 2 ** 10) * 2 ** (exp - 15)


def _getDouble(data, index):
    end = index + 8
    return unpack_from('d', data[index:end])[0], end


def _getFloat(data, index):
    end = index + 4
    if end > len(data):
        print('Reached end of data unexpectedly')
    return unpack_from('f', data[index:end])[0], end


def _getFloat2(data, index):
    end = index + 2
    u16 = struct.unpack('<H', data[index:end])[0]
    return _float_from_unsigned16(u16), end


def _getInt1(data, index):
    end = index + 1
    return ord(data[index:end]), end


def _getInt2(data, index):
    end = index + 2
    return unpack_from('h', data[index:end])[0], end


def _getInt4(data, index):
    end = index + 4
    return unpack_from('i', data[index:end])[0], end


# Get Payload type, current valid types are 2 or 3
def _getPayloadType(data):
    (data_type,) = unpack_from('c', memoryview(data[0:1]))
    return data_type.decode('UTF-8'), 1


def processData(p_id, data):
    # Get Payload type, current valid types are 2 or 3
    (data_type, index) = _getPayloadType(data)
    print("payload type: {}".format(data_type))

    index = 1
    if data_type != _4_0:
        print("Invalid payload type: 0x{}".format(codecs.encode(data_type, 
                                                                "hex")))
        sys.exit(1)

    data_len = len(data)
    while index < data_len:
        print("Index: {}".format(index))
        (sensor_type, index) = _getInt1(data, index)
        (com_port, index) = _getInt1(data, index)
        print("Sensor: {}\tCom Port: {}".format(sensor_type, com_port))

        (size, index) = _getInt2(data, index)
        print("Size: {}".format(size))

        if sensor_type == 50:
            index = _processMicroSWIFT(p_id, data, index, size)

        elif sensor_type == 52:
            index = process_micro_swift_52(p_id, data, index, size)

        else:
            raise Exception(
                "Payload {} has unknown sensor type {} at index {}".format(
                    p_id, sensor_type, index))


def _processMicroSWIFT(p_id, data, index, size):
    if size == 0:
        print("MicroSWIFT empty")
        return index

    (hs, index) = _getFloat(data, index)
    print("hs {}".format(hs))
    (tp, index) = _getFloat(data, index)
    print("tp {}".format(tp))
    (dp, index) = _getFloat(data, index)
    print("dp {}".format(dp))

    arrays = ['e', 'f', 'a1', 'b1', 'a2', 'b2', 'cf']

    for array in arrays:
        # 0 - 41
        for a_index in range(0, 42):
            (val, index) = _getFloat(data, index)
            print("{}{} {}".format(array, a_index, val))

    (lat, index) = _getFloat(data, index)
    print("lat {}".format(lat))
    (lon, index) = _getFloat(data, index)
    print("lon {}".format(lon))
    (mean_temp, index) = _getFloat(data, index)
    print("mean_temp {}".format(mean_temp))
    (mean_voltage, index) = _getFloat(data, index)
    print("mean_voltage {}".format(mean_voltage))
    (mean_u, index) = _getFloat(data, index)
    print("mean_u {}".format(mean_u))
    (mean_v, index) = _getFloat(data, index)
    print("mean_v {}".format(mean_v))
    (mean_z, index) = _getFloat(data, index)
    print("mean_z {}".format(mean_z))
    (year, index) = _getInt4(data, index)
    print("year {}".format(year))
    (month, index) = _getInt4(data, index)
    print("month {}".format(month))
    (day, index) = _getInt4(data, index)
    print("day {}".format(day))
    (hour, index) = _getInt4(data, index)
    print("hour {}".format(hour))
    (_min, index) = _getInt4(data, index)
    print("min {}".format(_min))
    (sec, index) = _getInt4(data, index)
    print("sec {}".format(sec))

    return index


def process_micro_swift_52(p_id, data, index, size):
    if size == 0:
        print("MicroSWIFT52 empty")
        return index

    (hs, index) = _getFloat2(data, index)
    print("hs {}".format(hs))
    (tp, index) = _getFloat2(data, index)
    print("tp {}".format(tp))
    (dp, index) = _getFloat2(data, index)
    print("dp {}".format(dp))

    arrays = ['e']

    for array in arrays:
        # 0 - 41
        for a_index in range(0, 42):
            (val, index) = _getFloat2(data, index)
            print("{}{} {}".format(array, a_index, val))

    (f_min, index) = _getFloat2(data, index)
    print("f_min {}".format(f_min))
    (f_max, index) = _getFloat2(data, index)
    print("f_max {}".format(f_max))

    arrays = [{'label': 'a1', 'signed': True},
              {'label': 'b1', 'signed': True},
              {'label': 'a2', 'signed': True},
              {'label': 'b2', 'signed': True},
              {'label': 'cf', 'signed': False}]
    for array in arrays:
        # 0 - 41
        array_label = array['label']
        signed = array['signed']
        for a_index in range(0, 42):
            (val, index) = _getInt1(data, index)
            if signed and val > 127:
                val = val - 256
            print("{}{} {}".format(array, a_index, val))

    (lat, index) = _getFloat(data, index)
    print("lat {}".format(lat))
    (lon, index) = _getFloat(data, index)
    print("lon {}".format(lon))
    (mean_temp, index) = _getFloat2(data, index)
    print("mean_temp {}".format(mean_temp))
    (mean_salinity, index) = _getFloat2(data, index)
    print("mean_salinity {}".format(mean_salinity))
    (mean_voltage, index) = _getFloat2(data, index)
    print("mean_voltage {}".format(mean_voltage))
    (timestamp, index) = _getFloat(data, index)
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    min = dt.minute
    sec = dt.second
    print("timestamp {} ({}-{}-{}T{}:{}:{})".format(timestamp, year, month, day, hour, min, sec))

    return index


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Provide the path to the payload file.")
        sys.exit(1)

    with open(sys.argv[1], "rb") as binfile:
        payload_data = bytearray(binfile.read())

    processData(0, payload_data)
