"""
Module for reading microSWIFT short burst data (SBD) files.

TODO:
- support for sensor type 50
"""

#TODO: combine with another module?

from typing import IO, Union, Type

from microSWIFTtelemetry.sbd import definitions
from microSWIFTtelemetry.sbd.definitions import SensorType


SENSOR_TYPES: dict[int, Type[SensorType]] = {
    50: definitions.SensorType50,
    51: definitions.SensorType51,
    52: definitions.SensorType52,
}


class SbdMessage:
    PAYLOAD_START: int = 0  # (no header) otherwise it is: = payload_data.index(b':')

    def __init__(self, file: IO[bytes]):
        self.file = file
        self.file_content = _rstrip_null(self.file.read())
        self.file_size = len(self.file_content)
        self._payload_type_id: Union[str, None] = None
        self._sensor_type_id: Union[int, None] = None
        self._sensor_type: Union[SensorType, None] = None

    @property
    def payload_type_id(self) -> Union[str, None]:
        # try:
        if self._payload_type_id is None:
            payload_type_id_slice = slice(self.PAYLOAD_START,
                                          self.PAYLOAD_START + 1)
            payload_type_id_str = self.file_content[payload_type_id_slice]
            self._payload_type_id = payload_type_id_str.decode(errors='replace')
        # except UnicodeDecodeError:
        # else:
        #     self._payload_type_id = None
        return self._payload_type_id

    @property
    def sensor_type_id(self) -> Union[int, None]:
        """ Determine sensor type id from an SBD message.

        Note:
            If the payload type id does not match the expected value,
            `sensor_type` is returned as None. This indicates the message
            contains error in ASCII text or is otherwise invalid.

        Returns:
            Union[int, None]: int corresponding to sensor type or `None`
        """
        if self._sensor_type_id is None:
            if self.payload_type_id == '7':
                sensor_type_slice = slice(self.PAYLOAD_START + 1,
                                          self.PAYLOAD_START + 2)
                self._sensor_type_id = ord(self.file_content[sensor_type_slice])
            # else:
            #     self._sensor_type_id = None
        return self._sensor_type_id

    # @property
    # def sensor_type(self) -> SensorType:
    #     return self._sensor_type

    # @sensor_type.setter
    # def sensor_type(self, sensor_type):
    #     self._age = sensor_type

    @property
    def sensor_type(self) -> SensorType:
        if self._sensor_type is None:
            sensor_type = self.get_sensor_type_by_id()
            self._sensor_type = sensor_type(self.file_content)
        return self._sensor_type

    # def get_sensor_type(self) -> SensorType:
    #     sensor_type = SENSOR_TYPES[self.sensor_type_id]
    #     return sensor_type(self.file_content)

        # if self.sensor_type_id == 50:
        #     return SensorType50(self.file_content)
        # elif self.sensor_type_id == 51:
        #     return SensorType51(self.file_content)
        # elif self.sensor_type_id == 52:
        #     return SensorType52(self.file_content)
        # else:

        #TODO: check using keys?
        #     raise NotImplementedError(
        #         f'The specified sensor type ({self.sensor_type_id}) '
        #         f'is not supported.'
        #     )

    def get_sensor_type_by_id(self) -> Type[SensorType]:
        if self.sensor_type_id is None:
            raise ValueError('Sensor type ID cannot be `None`.')
        else:
            return SENSOR_TYPES[self.sensor_type_id]

    def validate_file_size(self) -> None:
        if self.file_size != self.sensor_type.expected_file_size:
            raise ValueError(
                f'Expected {self.sensor_type.expected_file_size} bytes, '
                f'but received {self.file_size} bytes.'
            )

    def read(self) -> tuple[dict, dict]:
        """
        Read microSWIFT short burst data (SBD) messages into a dictonary.

        Args:
            sbd_file (str): path to .sbd file

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
