"""
Module containing microSWIFT sensor type and variable definitions.
"""

__all__ = [
    "get_sensor_type_definition",
    "get_variable_definitions",
]

from typing import List, Tuple

def get_sensor_type_definition(sensor_type: int) -> str:
    """
    Dictionary of microSWIFT sensor type definitions;
    see https://github.com/alexdeklerk/microSWIFT.

    Arguments:
        - sensor_type (int), sensor type defintion to return

    Raises:
        - ValueError, raise error if the sensor type is not one of the
                types defined in microSWIFT.py and configured to be
                parsed on the sever.

    Returns:
        - (str), sensor type defintion in Python's struct module format
            * See: https://docs.python.org/3/library/struct.html
    """

    # Define the sensor type using Python's struct module format
    PAYLOAD_DEFINITIONS = {
        50 : '<sbbhfff42f42f42f42f42f42f42ffffffffiiiiii',
        51 : '<sbbhfff42fffffffffffiiiiii',
        52 : '<sbbheee42eee42b42b42b42b42Bffeeef',
    }

    if sensor_type not in PAYLOAD_DEFINITIONS.keys():
        raise ValueError((f'sensor_type not defined - can only be value in:'
                          f'{list(PAYLOAD_DEFINITIONS.keys())}'))

    return PAYLOAD_DEFINITIONS[sensor_type]

def get_variable_definitions() -> List[Tuple]:
    """
    microSWIFT variable definitions.

    Returns:
        - (List[Tuple]), microSWIFT variable definitions with format:
            [
            (variable name, description, units)
                :             :          :
            ]
    """
    VARIABLE_DEFINITIONS = [
        ('datetime', "native Python datetime.datetime", "(datetime)"),
        ('Hs', "significant wave height", "(m)"),
        ('Tp', "peak period", "(s) "),
        ('Dp', "wave direction", "(deg)"),
        ('E' , "energy density", "(m^2/Hz)"),
        ('f' , "frequency", "(Hz)"),
        ('a1', "first directional moment, positive E", "(-)"),
        ('b1', "second directional moment, positive N", "(-)"),
        ('a2', "third directional moment, positive E-W", "(-)"),
        ('b2', "fourth directional moment, positive NE-SW", "(-)"),
        ('check', "check factor", "(-)"),
        ('uMean', "mean GPS E-W velocity, positive E", "(m/s)"),
        ('vMean', "mean GPS N-S velocity, positive N", "(m/s)"),
        ('zMean', "mean GPS altitude, positive up", "(m)"),
        ('lat', "mean GPS latitude", "(decimal degrees)"),
        ('lon', "mean GPS longitude", "(decimal degrees)"),
        ('temp', "mean temperature", "(C)"),
        ('salinity', "mean salinity", "(psu)"),
        ('volt', "mean battery voltage", "(V)"),
        ('sensor_type', "Iridium sensor type definition", "(-)"),
    ]

    return VARIABLE_DEFINITIONS
