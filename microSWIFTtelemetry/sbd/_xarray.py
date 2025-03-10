"""
Module for compiling microSWIFT SBD files into an Xarray Dataset.
"""

__all__ = [
    "_compile_xarray",
]

from collections.abc import KeysView
from typing import List

import xarray

from microSWIFTtelemetry.sbd.definitions import VARIABLE_DEFINITIONS
from microSWIFTtelemetry.sbd._dict import _compile_dict

# Type hint alias
SbdXarray = tuple[xarray.Dataset, dict]


def _compile_xarray(
    data_list: list[dict],
    error_dict: dict
) -> SbdXarray:
    """ Compile microSWIFT data and errors into a Dataset and a dict. """
    data_dict, error_dict = _compile_dict(data_list, error_dict)

    # Build the dictionary of Dataset coordinates.
    datetime_coord = data_dict['datetime']
    frequency_coord = _unify_frequency(data_dict['frequency'])
    coords = {
        'datetime': (
            ['datetime'],
            datetime_coord,
            _create_attributes('datetime')
        ),
        'frequency': (
            ['frequency'],
            frequency_coord,
            _create_attributes('frequency')
        ),
    }

    # Expected shapes for scalar and spectral variables.
    t = datetime_coord.shape[0]
    f = frequency_coord.shape[0]
    scalar_shape = (t,)
    spectral_shape = (t, f)

    # Build dictionary of data variables based on the array shapes.
    data_vars = {}
    variable_keys = _key_difference(VARIABLE_DEFINITIONS.keys(), coords.keys())
    for var in variable_keys:
        if data_dict[var].shape == scalar_shape:
            data_vars[var] = (
                ['datetime'],
                data_dict[var],
                _create_attributes(var)
            )
        elif data_dict[var].shape == spectral_shape:
            data_vars[var] = (
                ['datetime', 'frequency'],
                data_dict[var],
                _create_attributes(var)
            )
        else:
            raise ValueError
    data_ds = xarray.Dataset(data_vars=data_vars, coords=coords)
    return data_ds, error_dict


def _key_difference(keys_a: KeysView, keys_b: KeysView) -> List:
    """
    Return values in `keys_a` that are not in `keys_b` while maintaining order.
    """
    return [x for x in keys_a if x not in keys_b]


def _create_attributes(key):
    """ Create a Dataset attribute dictionary from variable definitions. """
    attributes = {
        'description': VARIABLE_DEFINITIONS[key][0],
        'units': VARIABLE_DEFINITIONS[key][1],
    }
    return attributes


def _unify_frequency(frequency_array):
    """ Convert an ndarray of frequency arrays to a single frequency array. """
    # The frequency array(s) should always be the same (within precision).
    return frequency_array.mean(axis=0)
