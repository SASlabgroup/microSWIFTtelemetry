"""
Module for reading microSWIFT short burst data (SBD) files.
"""

import struct
from datetime import datetime, timezone

import numpy as np

from microSWIFTtelemetry.sbd.definitions import get_sensor_type_definition
from microSWIFTtelemetry.sbd.definitions import get_variable_definitions


def get_sensor_type(file_content: bytes) -> int:
    """
    Helper function to determine sensor type from an SBD message.

    Arguments:
        - file_content (bytes), binary SBD message

    Returns:
        - (int), int corresponding to sensor type
    """
    payload_start= 0 # (no header) otherwise it is: = payload_data.index(b':')
    sensor_type = ord(file_content[payload_start+1:payload_start+2])
    return sensor_type

def unpack_sbd(file_content: bytes) -> dict:
    """
    Unpack short burst data messages using formats defined in the sensor
    type payload definitions.

    Arguments:
        - file_content (bytes), binary SBD message

    Returns:
        - (dict), microSWIFT variables stored in a temporary dictionary
    """
    sensor_type = get_sensor_type(file_content)
    payload_struct = get_sensor_type_definition(sensor_type) #['struct']
    data = struct.unpack(payload_struct, file_content)

    swift = {var[0] : None for var in get_variable_definitions()}

    if sensor_type == 50:
        #TODO:
        print('sensor_type 50 is not yet supported')

    elif sensor_type == 51:
        payload_size = data[3]
        swift['significant_height'] = data[4]
        swift['peak_period'] = data[5]
        swift['peak_direction'] = data[6]
        swift['energy_density']  = np.asarray(data[7:49])
        fmin = data[49]
        fmax = data[50]
        fstep = data[51]
        if fmin != 999 and fmax != 999:
            swift['frequency'] = np.arange(fmin, fmax + fstep, fstep)
        else:
            swift['frequency'] = 999*np.ones(np.shape(swift['energy_density']))
        swift['latitude'] = data[52]
        swift['longitude'] = data[53]
        swift['temperature'] = data[54]
        swift['voltage'] = data[55]
        swift['u_mean'] = data[56]
        swift['v_mean'] = data[57]
        swift['z_mean'] = data[58]
        swift['datetime'] = datetime(year=data[59],
                                     month=data[60],
                                     day=data[61],
                                     hour=data[62],
                                     minute=data[63],
                                     second=data[64],
                                     tzinfo=timezone.utc)
        swift['sensor_type'] = sensor_type

    elif sensor_type == 52:
        payload_size = data[3]
        swift['significant_height'] = data[4]
        swift['peak_period'] = data[5]
        swift['peak_direction'] = data[6]
        swift['energy_density']  = np.asarray(data[7:49])
        fmin = data[49]
        fmax = data[50]
        if fmin != 999 and fmax != 999:
            fstep = (fmax - fmin)/(len(swift['energy_density'])-1)
            swift['frequency'] = np.arange(fmin, fmax + fstep, fstep)
        else:
            swift['frequency'] = 999*np.ones(np.shape(swift['energy_density']))
        swift['a1'] = np.asarray(data[51:93])/100
        swift['b1'] = np.asarray(data[93:135])/100
        swift['a2'] = np.asarray(data[135:177])/100
        swift['b2'] = np.asarray(data[177:219])/100
        swift['check'] = np.asarray(data[219:261])/10
        swift['latitude'] = data[261]
        swift['longitude'] = data[262]
        swift['temperature'] = data[263]
        swift['salinity'] = data[264]
        swift['voltage'] = data[265]
        now_epoch = data[266]
        swift['datetime'] = datetime.fromtimestamp(now_epoch, tz=timezone.utc)
        swift['sensor_type'] = sensor_type

    return swift

def read_sbd(sbd_file: str) -> dict:
    """
    Read microSWIFT short burst data messages.

    Arguments:
        - sbd_file (str), path to .sbd file

    Returns:
        - (dict), microSWIFT variables stored in a temporary dictionary
    """
    file_content = sbd_file.read()
    return unpack_sbd(file_content)
