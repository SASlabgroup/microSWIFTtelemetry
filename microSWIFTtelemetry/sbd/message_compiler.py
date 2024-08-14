"""
Module for compiling microSWIFT short burst data (SBD) files.

TODO:
- to_netcdf function with nc compliance
"""

__all__ = [
    "compile_sbd",
]

import warnings
from collections import defaultdict
from collections.abc import KeysView
from typing import Any, Union, Dict, Literal, List, IO
from zipfile import ZipFile

import numpy as np
import pandas
import xarray
from pandas import DataFrame, to_datetime

from microSWIFTtelemetry.sbd.message_handler import SbdMessage
from microSWIFTtelemetry.sbd.definitions import VARIABLE_DEFINITIONS

# Type hint aliases
SbdDict = tuple[dict, dict]
SbdPandas = tuple[pandas.DataFrame, pandas.DataFrame]
SbdXarray = tuple[xarray.Dataset, dict]


def compile_sbd(
    sbd_dict: Dict[str, IO[bytes]],
    var_type: Literal['dict', 'pandas', 'xarray'],
    use_multi_index: bool = False,  # TODO: could be **kwargs
) -> Union[SbdDict, SbdPandas, SbdXarray]:
    """
    Compile a zip folder of short burst data files into a variable of the type
    specified by `var_type`.

    Args:
        sbd_dict (Dict[str, IO[bytes]]): Dictionary containing filenames and
            SBD content.
        var_type (Literal['dict', 'pandas', 'xarray']): The variable type to
            return. Defaults to 'dict'.
        use_multi_index (bool, optional): If True and var_type == 'pandas',
            return a DataFrame which is multi-indexed by ID and datetime.
            Defaults to False.

    Raises:
        ValueError: `var_type` can only be 'dict', 'pandas', or 'xarray'.

    Returns:
        (Union[SbdDict, SbdPandas, SbdXarray]):
            - If var_type == 'dict': data and errors (dict, dict)
            - If var_type == 'pandas': data and errors (DataFrame, DataFrame)
            - If var_type == 'xarray': data and errors (Dataset, dict).
    """
    data_list, error_list = _read_sbd(sbd_dict)

    error_dict = _combine_dict_list(error_list)

    if var_type == 'dict':
        return _compile_dict(data_list, error_dict)
    elif var_type == 'pandas':
        return _compile_pandas(data_list, error_dict, use_multi_index)
    elif var_type == 'xarray':
        return _compile_xarray(data_list, error_dict)
    else:
        raise ValueError("var_type can only be 'dict', 'pandas', or 'xarray'")


def _read_sbd(
    sbd_dict: Dict[str, IO[bytes]],
) -> tuple[list, list]:
    """
    Read microSWIFT short burst data (SBD) messages into a list of
    data dictionaries and a list of error dictionaries.
    """
    data_list = []
    error_list = []
    for sbd_bytes in sbd_dict.values():
        sbd_message = SbdMessage(sbd_bytes)
        data, error_message = sbd_message.read()
        if data:
            data_list.append(data)
        error_list.append(error_message)
    return data_list, error_list


def _compile_dict(
    data_list: list[dict],
    error_dict: dict
) -> SbdDict:
    """ Compile microSWIFT data and errors into dictionaries. """
    data_dict = _combine_dict_list(data_list)

    if data_dict:
        data_dict = _sort_dict(data_dict)
    else:
        warnings.warn("Empty dictionary; if you expected data, make sure "
                        "the `buoy_id` is a valid microSWIFT ID and that "
                        "`start_date` and `end_date` are correct.")
    return data_dict, error_dict


def _compile_pandas(
    data_list: list[dict],
    error_dict: dict,
    use_multi_index: bool = False,
) -> SbdPandas:
    """ Compile microSWIFT data and errors into DataFrames. """
    data_df = pandas.DataFrame(data_list)
    error_df = pandas.DataFrame(error_dict)

    if not data_df.empty:
        if use_multi_index:
            data_df = _set_pandas_multi_index(data_df)
        else:
            data_df = _set_pandas_datetime_index(data_df)
    else:
        warnings.warn("Empty DataFrame; if you expected data, make sure "
                        "the `buoy_id` is a valid microSWIFT ID and that "
                        "`start_date` and `end_date` are correct.")

    if not error_df.empty:
        error_df = error_df.sort_values(by='file_name')
        error_df.reset_index(drop=True, inplace=True)

    return data_df, error_df


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

    # Build the dictionary of data variables based on the array shapes.
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


def _combine_dict_list(dict_list: list[dict[Any, Any]]) -> Dict[Any, Any]:
    """ Combine a list of dictionaries with equivalent keys. """
    # Defaultdict doesn't raise a KeyError
    combined_dict = defaultdict(list)
    for d in dict_list:
        for key, value in d.items():
            combined_dict[key].append(value)
    return combined_dict


def _sort_dict(
    d: dict,
) -> dict:
    """
    Sort each key of a dictionary containing microSWIFT data based on
    the key containing datetime information.  The unsorted dictionary
    must contain a 'datetime' key with a list of datetimes.
    """
    sort_index = np.argsort(d['datetime'])
    d_sorted = {}
    for key, val in d.items():
        d_sorted[key] = np.array(val)[sort_index]

    return d_sorted


def _key_difference(keys_a: KeysView, keys_b: KeysView) -> List:
    """
    Return values in `keys_a` that are not in `keys_b` while maintaining order.
    """
    return [x for x in keys_a if x not in keys_b]


def _set_pandas_datetime_index(
    df: DataFrame,
    datetime_column: str = 'datetime',
) -> DataFrame:
    """ Set `datetime_column` of a DataFrame as a pandas.DatetimeIndex."""
    df[datetime_column] = to_datetime(df[datetime_column], utc=True)
    return df.set_index(datetime_column).sort_index()


def _set_pandas_multi_index(
    df: DataFrame,
    datetime_column: str = 'datetime',
    id_column: str = 'id',
) -> DataFrame:
    """
    Set a DataFrame's `id_column` and `datetime_column` as a pandas.MultiIndex.
    """
    df[datetime_column] = to_datetime(df[datetime_column], utc=True)
    return (df
            .set_index([id_column, datetime_column])
            .sort_index(level=[id_column, datetime_column], ascending=True))


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
