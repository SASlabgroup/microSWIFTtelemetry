"""
Module for compiling microSWIFT short burst data (SBD) files.
"""

__all__ = [
    "to_pandas_datetime_index",
    "sort_dict",
    "compile_sbd",
]

import warnings
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
)-> Any:
    """
    Compile contents of short burst data files into the specified
    variable type or output.

    Arguments:
        - sbd_folder (str), directory containing.sbd files
        - var_type (str), variable type to be returned
        - from_memory (bool, optional), flag to indicate whether
                sbd_folder was loaded from memory (True) or a local file
                (False); defaults to False.

    Raises:
        - ValueError, var_type can only be 'dict', 'pandas', or 'xarray'

    Returns:
        - (dict), if var_type == 'dict'
        - (DataFrame), if var_type == 'pandas'
        See pull_telemetry_as_var() for definitions

    """
    data = []

    if from_memory is True:

        for file in sbd_folder.namelist():
            data.append(read_sbd(sbd_folder.open(file)))

    else: #TODO: support reading from a folder of SBDs
        raise Exception(('Reading from a folder on the local machine is not'
                         'supported yet.'))
        # for SBDfile in sbd_folder:
        #     with open(SBDfile, mode='rb') as file: # b is important -> binary
        #         # fileContent = file.read()
        #         data.append(read_sbd(file))

    if var_type == 'dict':
        d = {k: [d.get(k) for d in data] for k in set().union(*data)}
        if d:
            d = sort_dict(d)
        else:
            warnings.warn("empty dict")
        return d

    elif var_type == 'pandas':
        df = pandas.DataFrame(data)
        if not df.empty:
            to_pandas_datetime_index(df)
        else:
            warnings.warn("empty DataFrame")
        return df

    elif var_type == 'xarray': #TODO: support for xarray
        raise Exception('xarray is not supported yet')

    else:
        raise ValueError("var_type can only be 'dict', 'pandas', or 'xarray'")


def to_pandas_datetime_index(
    df: DataFrame,
    datetime_column: str = 'datetime',
)-> DataFrame:
    """
    Convert a pandas.DataFrame integer index to a pandas.DatetimeIndex
    in place.

    Arguments:
        - df (DataFrame), DataFrame with integer index
        - datetime_column (str, optional), column name containing
                datetime objects to be converted to datetime index;
                defaults to 'datetime'.

    Returns:
        - (DataFrame), DataFrame with datetime index
    """
    df[datetime_column] = to_datetime(df['datetime'], utc=True)
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    # df.drop(['datetime'], axis=1, inplace=True)


def sort_dict(
    d: dict,
)-> dict:
    """
    Sort each key of a dictionary containing microSWIFT data based on
    the key containing datetime information.

    Arguments:
        - d (dict), unsorted dictionary
            * Must contain a 'datetime' key with a list of datetimes

    Returns:
        - (dict), sorted dictionary
    """
    sort_index = np.argsort(d['datetime'])
    d_sorted = {}
    for key, val in d.items():
        d_sorted[key] = np.array(val)[sort_index]

    return d_sorted
