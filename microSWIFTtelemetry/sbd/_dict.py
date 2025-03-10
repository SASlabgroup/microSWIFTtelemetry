"""
Module for compiling microSWIFT SBD files into a dictionary.
"""

__all__ = [
    "_compile_dict",
    "_combine_dict_list",
]

import warnings
from collections import defaultdict
from typing import Any, Dict

import numpy as np

# Type hint alias
SbdDict = tuple[dict, dict]


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
