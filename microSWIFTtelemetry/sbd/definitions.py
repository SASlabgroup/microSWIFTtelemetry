"""
MicroSWIFT variable and sensor type definitions.

TODO: add note to update SENSOR_TYPES in _sbd.py when adding new types.
TODO: map definitions to ncdf convention
"""

__all__ = [
    "VARIABLE_DEFINITIONS",
    "SensorType52",
    "SensorType51",
    "SensorType50",
]

import re
import struct
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Type, Optional

import numpy as np


# {variable name: (description, units)}
VARIABLE_DEFINITIONS = {
    'id': ("3-digit microSWIFT ID", "(-)"),
    'datetime': ("native Python datetime.datetime", "(datetime)"),
    'significant_height': ("significant wave height", "(m)"),
    'peak_period': ("peak wave period", "(s) "),
    'peak_direction': ("peak wave direction", "(deg)"),
    'energy_density': ("wave energy density spectrum", "(m^2/Hz)"),
    'frequency': ("spectral frequency bins", "(Hz)"),
    'a1': ("first directional moment, positive E", "(-)"),
    'b1': ("second directional moment, positive N", "(-)"),
    'a2': ("third directional moment, positive E-W", "(-)"),
    'b2': ("fourth directional moment, positive NE-SW", "(-)"),
    'check': ("check factor", "(-)"),
    'u_mean': ("mean GPS E-W velocity, positive E", "(m/s)"),
    'v_mean': ("mean GPS N-S velocity, positive N", "(m/s)"),
    'z_mean': ("mean GPS altitude, positive up", "(m)"),
    'latitude': ("mean GPS latitude", "(decimal degrees)"),
    'longitude': ("mean GPS longitude", "(decimal degrees)"),
    'temperature': ("mean temperature", "(C)"),
    'salinity': ("mean salinity", "(PSU)"),
    'voltage': ("mean battery voltage", "(V)"),
    'sensor_type': ("Iridium sensor type definition", "(-)"),
    'com_port': ("Iridium com port or # of replaced values", "(-)"),
    'payload_size': ("Iridium message size", "(bytes)"),
}


def init_swift_dict() -> dict:
    """ Initialize an empty SWIFT data dictionary. """
    return {var: None for var in VARIABLE_DEFINITIONS.keys()}


def id_from_filename(filename: str) -> Optional[str]:
    id_match = re.search(r'(microSWIFT \d{3})', filename)
    if id_match:
        full_id = id_match.group(0)
        return full_id.split(' ')[-1]
    else:
        return None


class SensorType(ABC):
    """ TODO: """
    @abstractmethod
    def __init__(self, sbd_content: bytes, sbd_filename: str):
        pass

    @property
    @abstractmethod
    def expected_file_size(self) -> int:
        pass

    @abstractmethod
    def unpack(self) -> dict[str, Any]:
        pass


class SensorType52(SensorType):
    # Sensor type 52 modified early 2025 ("Post" has 4 extra bytes.)
    definition_pre_2025 = '<sbBheee42eee42b42b42b42b42Bffeeef'  # original v1 has `b` in third pos
    definition_post_2025 = '<sbbheee42eee42b42b42b42b42BffeeefI'

    def __init__(self, sbd_content: bytes, sbd_filename: str):
        self.sbd_content = sbd_content
        self.sbd_filename = sbd_filename

    @property
    def definition(self) -> str:
        """ Return sensor type definition based on file size. """
        if len(self.sbd_content) == struct.calcsize(self.definition_post_2025):
            return self.definition_post_2025
        else:
            return self.definition_pre_2025

    @property
    def expected_file_size(self) -> int:
        return struct.calcsize(self.definition)

    def unpack(self) -> dict[str, Any]:
        """ Unpack microSWIFT sensor type 52 into a dictionary. """
        data = struct.unpack(self.definition, self.sbd_content)

        swift = init_swift_dict()
        swift['id'] = id_from_filename(self.sbd_filename)
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
            fnum = len(swift['energy_density'])
            swift['frequency'] = np.linspace(fmin, fmax, fnum)
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


class SensorType51(SensorType):
    definition = '<sbbhfff42fffffffffffiiiiii'

    def __init__(self, sbd_content: bytes, sbd_filename: str):
        self.sbd_content = sbd_content
        self.sbd_filename = sbd_filename

    @property
    def expected_file_size(self):
        return struct.calcsize(self.definition)

    def unpack(self) -> dict[str, Any]:
        """ Unpack microSWIFT sensor type 51 into a dictionary. """
        data = struct.unpack(self.definition, self.sbd_content)

        swift = init_swift_dict()
        swift['id'] = id_from_filename(self.sbd_filename)
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


class SensorType50(SensorType):
    definition = '<sbbhfff42f42f42f42f42f42f42ffffffffiiiiii'

    def __init__(self, sbd_content: bytes, sbd_filename: str):
        self.sbd_content = sbd_content
        self.sbd_filename = sbd_filename

    @property
    def expected_file_size(self):
        return struct.calcsize(self.definition)

    def unpack(self) -> dict[str, Any]:
        """ Unpack microSWIFT sensor type 50 into a dictionary. """
        raise NotImplementedError
