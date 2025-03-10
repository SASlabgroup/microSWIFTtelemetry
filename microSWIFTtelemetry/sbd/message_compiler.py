"""
Module for compiling microSWIFT short burst data (SBD) files into objects.

TODO: to_netcdf function with nc compliance
"""

__all__ = [
    "compile_sbd",
]

from typing import Union, Dict, Literal, IO

from microSWIFTtelemetry.sbd.sbd_message import SbdMessage
from microSWIFTtelemetry.sbd._dict import _compile_dict, _combine_dict_list, SbdDict
from microSWIFTtelemetry.sbd._pandas import _compile_pandas, SbdPandas
from microSWIFTtelemetry.sbd._xarray import _compile_xarray, SbdXarray


def compile_sbd(
    sbd_dict: Dict[str, IO[bytes]],
    var_type: Literal['dict', 'pandas', 'xarray'],
    use_multi_index: bool = False,  # TODO: could be **kwargs
) -> Union[SbdDict, SbdPandas, SbdXarray]:
    """
    Compile a zip folder of short burst data files into a variable of the type
    specified by `var_type`.

    Args:
        sbd_dict (Dict[str, IO[bytes]]): Dictionary of filenames and
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
