"""
Module for reading microSWIFT short burst data (SBD) files.

TODO:
- support for sensor type 50
"""

import struct
import warnings
from datetime import datetime, timezone
from typing import Tuple

import numpy as np

from microSWIFTtelemetry.sbd.definitions import get_sensor_type_definition
from microSWIFTtelemetry.sbd.definitions import get_variable_definitions


PAYLOAD_TYPE = '7'
PAYLOAD_START = 0  # (no header) otherwise it is: = payload_data.index(b':')


def read_sbd(sbd_file: str) -> Tuple:
    """
    Read microSWIFT short burst data (SBD) messages into a dictonary.

    Args:
        sbd_file (str): path to .sbd file

    Returns:
        Tuple[dict, dict] : microSWIFT data and errors
    """
    file_name = sbd_file.name
    file_content = sbd_file.read()
    return unpack_sbd(file_name, file_content)


def unpack_sbd(file_name: str, file_content: bytes) -> Tuple:
    """
    Unpack short burst data messages using formats defined in the sensor
    type payload definitions.

    Args:
        file_name (str): SBD filename
        file_content (bytes): binary SBD message

    Returns:
        Tuple[dict, dict] : microSWIFT data and errors
    """
    data = None
    error_message = {'file_name': file_name, 'error': None}
    sensor_type = get_sensor_type(file_content)

    if sensor_type:
        payload_struct = get_sensor_type_definition(sensor_type)
        file_size = len(file_content)
        expected_file_size = struct.calcsize(payload_struct)
        if file_size == expected_file_size:
            data = struct.unpack(payload_struct, file_content)
        elif len(_rstrip_null(file_content)) == expected_file_size:
            data = struct.unpack(payload_struct, _rstrip_null(file_content))
        else:
            error_message['error'] = (f'Unexpected message size ({file_size}B)'
                                      f': {file_content}')
            warnings.warn(f'The short burst data message size ({file_size}B)\n'
                          f'does not match the expected size of sensor type '
                          f'{sensor_type} ({expected_file_size}B).',
                          BytesWarning)
    else:
        error_message['error'] = _rstrip_null(file_content)  # decode('ascii')

    if data:
        if sensor_type == 51:
            swift = unpack_sensor_type_51(data)
        elif sensor_type == 52:
            swift = unpack_sensor_type_52(data)
        else:
            raise NotImplementedError(f'The specified sensor type '
                                      f'({sensor_type}) is not supported.')
    else:
        swift = {}

    return swift, error_message


def get_sensor_type(file_content: bytes) -> int:
    """
    Determine sensor type from an SBD message.

    Note:
        If the payload type does not match the expected value,
        `sensor_type` is returned as None. This indicates the message
        contains error in ASCII text or is otherwise invalid.

    Args:
        file_content (bytes): binary SBD message

    Returns:
        (int): int corresponding to sensor type
    """
    payload_type = \
        file_content[PAYLOAD_START:PAYLOAD_START+1].decode(errors='replace')

    if payload_type == PAYLOAD_TYPE:
        sensor_type = ord(file_content[PAYLOAD_START+1:PAYLOAD_START+2])
    else:
        sensor_type = None

    return sensor_type


def unpack_sensor_type_51(data):
    """Unpack microSWIFT sensor type 51 into a dictionary.

    Args:
        data (list): decoded SBD message

    Returns:
        dict: microSWIFT variables stored in a temporary dictionary
    """
    swift = {var[0]: None for var in get_variable_definitions()}

    swift['sensor_type'] = data[1]
    swift['com_port'] = data[2]
    swift['payload_size'] = data[3]
    swift['significant_height'] = data[4]
    swift['peak_period'] = data[5]
    swift['peak_direction'] = data[6]
    swift['energy_density'] = np.asarray(data[7:49])
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
    return swift


def unpack_sensor_type_52(data):
    """Unpack microSWIFT sensor type 52 into a dictionary.

    Args:
        data (list): decoded SBD message

    Returns:
        dict: microSWIFT variables stored in a temporary dictionary
    """
    swift = {var[0]: None for var in get_variable_definitions()}
    swift['sensor_type'] = data[1]
    swift['com_port'] = data[2]
    swift['payload_size'] = data[3]
    swift['significant_height'] = data[4]
    swift['peak_period'] = data[5]
    swift['peak_direction'] = data[6]
    swift['energy_density'] = np.asarray(data[7:49])
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
    return swift


def _rstrip_null(bytestring):
    return bytestring.rstrip(b'\x00')
