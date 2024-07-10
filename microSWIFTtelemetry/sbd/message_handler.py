"""
Module for reading microSWIFT short burst data (SBD) files.

TODO:
- support for sensor type 50
"""

#TODO: rename?

from typing import IO, Union, Type

from microSWIFTtelemetry.sbd import definitions
from microSWIFTtelemetry.sbd.definitions import SensorType

#TODO: move to definitions.py?  but needs to go at end
SENSOR_TYPES: dict[int, Type[SensorType]] = {
    50: definitions.SensorType50,
    51: definitions.SensorType51,
    52: definitions.SensorType52,
}


class SbdMessage:
    """ TODO: """
    PAYLOAD_START: int = 0  # (no header) otherwise it is: = payload_data.index(b':')

    def __init__(self, file: IO[bytes]):
        self.file = file
        self.file_content = _rstrip_null(self.file.read())
        self.file_size = len(self.file_content)
        self._payload_type_id: Union[str, None] = None  # TODO: are these types needed?
        self._sensor_type_id: Union[int, None] = None
        self._sensor_type: Union[SensorType, None] = None

    @property
    def payload_type_id(self) -> Union[str, None]:
        """ TODO: """
        if self._payload_type_id is None:
            payload_type_id_slice = slice(self.PAYLOAD_START,
                                          self.PAYLOAD_START + 1)
            payload_type_id_str = self.file_content[payload_type_id_slice]
            self._payload_type_id = payload_type_id_str.decode(errors='replace')
        return self._payload_type_id

    @property
    def sensor_type_id(self) -> Union[int, None]:
        """ Determine sensor type id from an SBD message. """
        if self._sensor_type_id is None:
            if self.payload_type_id == '7':
                sensor_type_slice = slice(self.PAYLOAD_START + 1,
                                          self.PAYLOAD_START + 2)
                self._sensor_type_id = ord(self.file_content[sensor_type_slice])
        return self._sensor_type_id

    @property
    def sensor_type(self) -> SensorType:
        """ Get sensor type class. """
        if self._sensor_type is None:
            sensor_type = self.get_sensor_type_by_id()
            self._sensor_type = sensor_type(self.file_content)
        return self._sensor_type

    def get_sensor_type_by_id(self) -> Type[SensorType]:
        """ Return sensor type class based on sensor type id. """
        if self.sensor_type_id is None:
            raise ValueError('Sensor type ID cannot be `None`.')
        else:
            return SENSOR_TYPES[self.sensor_type_id]

    def validate_file_size(self) -> None:
        """ Validate file size against the sensor type's expected size ."""
        if self.file_size != self.sensor_type.expected_file_size:
            raise ValueError(
                f'Expected {self.sensor_type.expected_file_size} bytes, '
                f'but received {self.file_size} bytes.'
            )

    def read(self) -> tuple[dict, dict]:
        """
        Read microSWIFT short burst data (SBD) messages into dictonaries
        containing data and errors.

        Note:
            If the `_payload_type_id` does not match any of the expected
            values then `sensor_type` is returned as None. This indicates the
            file content contains an error message (ASCII text) or is otherwise
            invalid.

        Returns:
            tuple[dict, dict] : microSWIFT data and errors
        """
        error_message = {'file_name': self.file.name, 'error': None}

        if self.sensor_type_id is not None:
            self.validate_file_size()
            swift = self.sensor_type.unpack()
        else:
            swift = {}
            error_message['error'] = self.file_content
        return swift, error_message


def _rstrip_null(bytestring):
    return bytestring.rstrip(b'\x00')
