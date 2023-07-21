"""
Module for compiling microSWIFT short burst data (SBD) files.

TODO:
- support for xarray
"""

__all__ = [
    "to_pandas_datetime_index",
    "sort_dict",
    "compile_sbd",
]

import os
import warnings
from collections import defaultdict
from typing import Any

import numpy as np
import pandas
import xarray
from pandas import DataFrame, to_datetime

from microSWIFTtelemetry.sbd.read_sbd import read_sbd


def compile_sbd(
    sbd_folder: str,
    var_type: str,
    from_memory: bool = False
) -> Any:
    """
    Compile contents of short burst data files into the specified
    variable type or output.

    Valid variable types: 'dict' or 'pandas'

    Args:
        sbd_folder (str): directory containing.sbd files
        var_type (str): variable type to be returned
        from_memory (bool, optional): flag to indicate whether
                sbd_folder was loaded from memory (True) or a local file
                (False); defaults to False.

    Raises:
        ValueError: var_type can only be 'dict', 'pandas', or 'xarray'

    Returns:
        (dict): if var_type == 'dict'
        (DataFrame): if var_type == 'pandas'
    """
    data = []
    errors = []

    if from_memory:
        for file in sbd_folder.namelist():
            swift_data, error_message = read_sbd(sbd_folder.open(file))
            if swift_data:
                data.append(swift_data)
            errors.append(error_message)

    else:
        for file in os.listdir(sbd_folder):
            with open(os.path.join(sbd_folder, file), 'rb') as file:
                swift_data, error_message = read_sbd(file)
            if swift_data:
                data.append(swift_data)
            errors.append(error_message)

    errors = _combine_dict_list(errors)

    if var_type == 'dict':
        d = _combine_dict_list(data)
        if d:
            d = sort_dict(d)
        else:
            warnings.warn("Empty dictionary; if you expected data, make sure "
                          "the `buoy_id` is a valid microSWIFT ID and that "
                          "`start_date` and `end_date` are correct.")
        return d, errors

    if var_type == 'pandas':
        df = pandas.DataFrame(data)
        errors = pandas.DataFrame(errors)
        if not df.empty:
            to_pandas_datetime_index(df)
        else:
            warnings.warn("Empty DataFrame; if you expected data, make sure "
                          "the `buoy_id` is a valid microSWIFT ID and that "
                          "`start_date` and `end_date` are correct.")
        return df, errors

    if var_type == 'xarray':  # TODO: support for xarray
        raise NotImplementedError('xarray is not supported yet')

    raise ValueError("var_type can only be 'dict', 'pandas', or 'xarray'")


def to_pandas_datetime_index(
    df: DataFrame,
    datetime_column: str = 'datetime',
) -> DataFrame:
    """
    Convert a pandas.DataFrame integer index to a pandas.DatetimeIndex
    in place.

    Args:
        df (DataFrame): DataFrame with integer index
        datetime_column (str, optional): column name containing
                datetime objects to be converted to datetime index;
                defaults to 'datetime'.

    Returns:
        (DataFrame): DataFrame with datetime index
    """
    df[datetime_column] = to_datetime(df['datetime'], utc=True)
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    # df.drop(['datetime'], axis=1, inplace=True)


def _combine_dict_list(dict_list):
    """Helper function to combine a list of dictionaries with equivalent keys.

    Args:
        dict_list (list): list containing dictonaries

    Returns:
        dict: unified dictionary
    """
    combined_dict = defaultdict(list)
    for d in dict_list:
        for key, value in d.items():
            combined_dict[key].append(value)

    return combined_dict
    # return {k: [d.get(k) for d in dict_list] for k in set().union(*dict_list)}


def sort_dict(
    d: dict,
) -> dict:
    """
    Sort each key of a dictionary containing microSWIFT data based on
    the key containing datetime information.

    Args:
        d (dict): unsorted dictionary
            * Must contain a 'datetime' key with a list of datetimes

    Returns:
        (dict): sorted dictionary
    """
    sort_index = np.argsort(d['datetime'])
    d_sorted = {}
    for key, val in d.items():
        d_sorted[key] = np.array(val)[sort_index]

    return d_sorted

