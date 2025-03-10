"""
Module for compiling microSWIFT SBD files into a Pandas DataFrame.
"""

__all__ = [
    "_compile_pandas",
    "_set_pandas_datetime_index",
]

import warnings

import pandas
from pandas import DataFrame, to_datetime

# Type hint alias
SbdPandas = tuple[pandas.DataFrame, pandas.DataFrame]


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
