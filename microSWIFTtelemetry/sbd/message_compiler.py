"""
Module for compiling microSWIFT short burst data (SBD) files.

TODO:
- support for xarray
- to_netcdf function with nccompliance
"""

__all__ = [
    "to_pandas_datetime_index",
    "sort_dict",
    "compile_sbd",
]

import os
import warnings
from collections import defaultdict
from typing import Any, Union, Dict, Literal
from zipfile import ZipFile

import numpy as np
import pandas
import xarray
from pandas import DataFrame, to_datetime

from microSWIFTtelemetry.sbd.message_handler import SbdMessage

# Type hint aliases
# CompiledSbd = Union[dict, pandas.DataFrame, xarray.Dataset]
SbdDict = tuple[dict, dict]
SbdPandas = tuple[pandas.DataFrame, pandas.DataFrame]
SbdXarray = tuple[xarray.Dataset, xarray.Dataset]


def compile_sbd(
    sbd_folder: ZipFile,  # Union[ZipFile, os.PathLike],
    var_type: Literal['dict', 'pandas', 'xarray'],
    from_memory: bool = False
) -> Union[SbdDict, SbdPandas, SbdXarray]:
    """
    #TODO: update:
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
    data_list = []
    error_list = []

    #TODO: split into two functions
    if from_memory:
        data_list, error_list = _read_sbd_from_memory(sbd_folder)
        # for file in sbd_folder.namelist():
        #     sbd_message = SbdMessage(sbd_folder.open(file))
        #     data, error_message = sbd_message.read()
        #     if data:
        #         data_list.append(data)
        #     error_list.append(error_message)

    # else:
    #     for file in os.listdir(sbd_folder):
    #         with open(os.path.join(sbd_folder, file), 'rb') as open_file:
    #             sbd_message = SbdMessage(open_file)
    #             data, error_message = sbd_message.read()
    #         if data:
    #             data_list.append(data)
    #         error_list.append(error_message)

    error_dict = _combine_dict_list(error_list)

    #TODO: function
    if var_type == 'dict':
        data_dict = _combine_dict_list(data_list)
        if data_dict:
            data_dict = sort_dict(data_dict)
        else:
            warnings.warn("Empty dictionary; if you expected data, make sure "
                          "the `buoy_id` is a valid microSWIFT ID and that "
                          "`start_date` and `end_date` are correct.")
        return data_dict, error_dict

    #TODO: function
    elif var_type == 'pandas':
        data_df = pandas.DataFrame(data_list)
        error_df = pandas.DataFrame(error_dict)

        if not data_df.empty:
            to_pandas_datetime_index(data_df)
        else:
            warnings.warn("Empty DataFrame; if you expected data, make sure "
                          "the `buoy_id` is a valid microSWIFT ID and that "
                          "`start_date` and `end_date` are correct.")

        if not error_df.empty:
            error_df = error_df.sort_values(by='file_name')
            error_df.reset_index(drop=True, inplace=True)

        #TODO: concatenate dfs?
        return data_df, error_df

    elif var_type == 'xarray':  # TODO: support for xarray
        # TODO: use VARIABLE_DEFINTIONS for description and units
        raise NotImplementedError('xarray is not supported yet')

    else:
        raise ValueError("var_type can only be 'dict', 'pandas', or 'xarray'")


def _read_sbd_from_memory(
    sbd_folder: ZipFile,
):
    data_list = []
    error_list = []

    for file in sbd_folder.namelist():
        sbd_message = SbdMessage(sbd_folder.open(file))
        data, error_message = sbd_message.read()
        if data:
            data_list.append(data)
        error_list.append(error_message)

    return data_list, error_list


def _read_sbd_from_local():


#TODO: update to remove inplace
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


def _combine_dict_list(dict_list: list[dict[Any, Any]]) -> Dict[Any, Any]:
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

