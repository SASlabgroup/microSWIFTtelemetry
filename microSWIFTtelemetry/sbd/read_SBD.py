"""
Author: @jacobrdavis

A collection of python functions for reading microSWIFT short burst data (SBD) files.

Contents:
    - get_sensor_type()
    - unpack_SBD()
    - read_SBD()

Log:
    - 2022-09-06, J.Davis: created
    - 2022-09-12, J.Davis: updated doc strs
    - 2022-10-27, J.Davis: moved sensor type and payload def to definitions.py
"""
import struct
import numpy as np
from datetime import datetime, timezone
from microSWIFTtelemetry.sbd.definitions import get_sensor_type_definition, get_variable_definitions



def get_sensor_type(fileContent: bytes) -> int:
    """
    Helper function to determine sensor type from an SBD message.

    Arguments:
        - fileContent (bytes), binary SBD message

    Returns:
        - (int), int corresponding to sensor type
    """
    payloadStartIdx = 0 # (no header) otherwise it is: = payload_data.index(b':') 
    sensorType = ord(fileContent[payloadStartIdx+1:payloadStartIdx+2]) # sensor type is stored 1 byte after the header
    return sensorType

def unpack_SBD(fileContent: bytes) -> dict:
    """
    Unpack short burst data messages using formats defined in the sensor type
    payload definitions.

    Arguments:
        - fileContent (bytes), binary SBD message

    Returns:
        - (dict), microSWIFT variables stored in a temporary dictionary
    """
    sensorType = get_sensor_type(fileContent)

    payloadStruct = get_sensor_type_definition(sensorType) #['struct']
   
    data = struct.unpack(payloadStruct, fileContent)

    SWIFT = {var[0] : None for var in get_variable_definitions()}
    
    if sensorType == 50:
        #TODO:
        print('sensorType 50 is not yet supported')

    elif sensorType == 51:
        payload_size = data[3]
        SWIFT['Hs'] = data[4]
        SWIFT['Tp'] = data[5]
        SWIFT['Dp'] = data[6]
        SWIFT['E']  = np.asarray(data[7:49])
        fmin = data[49]
        fmax = data[50]
        fstep = data[51]
        if fmin != 999 and fmax != 999:
            SWIFT['f'] = np.arange(fmin, fmax + fstep, fstep)
        else:
            SWIFT['f'] = 999*np.ones(np.shape(SWIFT['E']))
        SWIFT['lat'] = data[52]
        SWIFT['lon'] = data[53]
        SWIFT['temp'] = data[54]
        SWIFT['volt'] = data[55]
        SWIFT['uMean'] = data[56]
        SWIFT['vMean'] = data[57]
        SWIFT['zMean'] = data[58]
        year = data[59]
        month = data[60]
        day = data[61]
        hour = data[62]
        min = data[63]
        sec = data[64]
        SWIFT['datetime'] = datetime(year, month, day, hour, min, sec, tzinfo=timezone.utc)  
        SWIFT['sensorType'] = sensorType

    elif sensorType == 52:
        payload_size = data[3]
        SWIFT['Hs'] = data[4]
        SWIFT['Tp'] = data[5]
        SWIFT['Dp'] = data[6]
        SWIFT['E']  = np.asarray(data[7:49])
        fmin = data[49]
        fmax = data[50]
        if fmin != 999 and fmax != 999:
            fstep = (fmax - fmin)/(len(SWIFT['E'])-1)
            SWIFT['f'] = np.arange(fmin, fmax + fstep, fstep)
        else:
            SWIFT['f'] = 999*np.ones(np.shape(SWIFT['E']))
        SWIFT['a1'] = np.asarray(data[51:93])/100
        SWIFT['b1'] = np.asarray(data[93:135])/100
        SWIFT['a2'] = np.asarray(data[135:177])/100
        SWIFT['b2'] = np.asarray(data[177:219])/100
        SWIFT['check'] = np.asarray(data[219:261])/10
        SWIFT['lat'] = data[261]
        SWIFT['lon'] = data[262]
        SWIFT['temp'] = data[263]
        SWIFT['salinity'] = data[264]
        SWIFT['volt'] = data[265]
        nowEpoch = data[266]
        SWIFT['datetime'] = datetime.fromtimestamp(nowEpoch, tz=timezone.utc)  
        SWIFT['sensorType'] = sensorType

    return SWIFT

def read_SBD(SBDfile: str) -> dict: #, fromMemory: bool = False):
    """
    Read microSWIFT short burst data messages.

    Arguments:
        - SBDfile (str), path to .sbd file

    Returns:
        - (dict), microSWIFT variables stored in a temporary dictionary
    """

    fileContent = SBDfile.read()

    return unpack_SBD(fileContent)


