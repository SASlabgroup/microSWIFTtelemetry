"""
Core module for accessing microSWIFT data from the UW-APL SWIFT server.
"""

__all__ = [
    "create_request",
    "pull_telemetry_as_var",
    "pull_telemetry_as_zip",
    "pull_telemetry_as_json",
    "pull_telemetry_as_kml",
]

import json
import os

from datetime import datetime, timezone
from typing import Any, Dict, IO, Union, Literal, List, Optional
from urllib.request import urlopen
from urllib.parse import urlencode, quote_plus
from zipfile import ZipFile

from io import BytesIO
from pandas import DataFrame
from xarray import Dataset
from microSWIFTtelemetry.sbd.message_compiler import compile_sbd

# Type aliases
CompiledData = Union[dict, DataFrame, Dataset]
CompiledErrors = Union[dict, DataFrame, Dataset]


def create_request(
    buoy_id: str,
    start_date: datetime,
    end_date: datetime,
    format_out: Literal['zip', 'json', 'kml'],
) -> str:
    """
    Create a URL-encoded request.

    Arguments:
        buoy_id (str): microSWIFT ID (e.g. '043')
        start_date (datetime): Query start date in UTC.
        end_date (datetime): Query end date in UTC.
        format_out (Literal['zip', 'json', 'kml']): Format to query the SWIFT
            server for: a .zip file of SBD messages, JSON-formatted text, or
            a KML of drift tracks.

    Returns:
        str: URL-encoded (utf8) request to be sent to the server.
    """

    # Convert dates to strings:
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')

    # Pack into a payload dictionary:
    payload = {
        'buoy_name': f'microSWIFT {buoy_id}'.encode('utf8'),
        'start': start_date_str.encode('utf8'),
        'end': end_date_str.encode('utf8'),
        'format': format_out.encode('utf8')
    }

    return urlencode(payload, quote_via=quote_plus)


def pull_telemetry_as_var(
    buoy_ids: List[str],
    start_date: datetime,
    end_date: Optional[datetime] = None,
    var_type: Literal['dict', 'pandas', 'xarray'] = 'dict',
    return_errors: bool = False,
    use_multi_index: bool = False,
) -> Union[CompiledData, tuple[CompiledData, CompiledErrors]]:
    """
    Query the SWIFT server for microSWIFT data over a specified date
    range and return an object in memory.

    Note: The .zip file of short burst data (SBD) messages is handled in
    memory and is not saved to the local machine. Use `pull_telemetry_as_zip`
    for this purpose.

    Args:
        buoy_id (List[str]): Three-digit microSWIFT ID(s) (e.g. ['043']).
        start_date (datetime): Query start date in UTC.
        end_date (datetime, optional): Query end date in UTC. Defaults to None
            which is replaced with the current UTC time.
        var_type (Literal['dict', 'pandas', 'xarray'], optional): The variable
            type to return. Defaults to 'dict'.
        return_errors (bool, optional): If True, return error messages.
            Defaults to False.
        use_multi_index (bool, optional): If True and var_type == 'pandas',
            return a DataFrame which is multi-indexed by ID and datetime.
            Defaults to False.

    Returns:
        (CompiledData | tuple[CompiledData, CompiledErrors]):
            - If var_type == 'dict': data (dict) or data and errors
            (dict, dict) if return_errors == True.
            - If var_type == 'pandas': data (DataFrame) or data and errors
            (DataFrame, DataFrame).
            - If var_type == 'xarray': data (Dataset) or data and errors
            (Dataset, dict).

    Examples:
        Get microSWIFT 104 and 105 data from 2024-07-20 to the present time
        (in UTC) as a Pandas DataFrame::

            from datetime import datetime
            import pandas
            from microSWIFTtelemetry import pull_telemetry_as_var

            swift_df = pull_telemetry_as_var(buoy_ids=['104', '105'],
                                             start_date=datetime(2024, 7, 20),
                                             var_type='pandas')

    """
    FORMAT_OUT: Literal['zip'] = 'zip'
    BASE_URL = 'http://swiftserver.apl.washington.edu/services/buoy?action=get_data&'

    # Handle inputs.
    buoy_ids = _handle_scalar_buoy_id(buoy_ids)
    end_date = _handle_empty_end_date(end_date)

    # Query the SWIFT server and collect the SBD messages for each ID.
    sbd_dict: Dict[str, IO[bytes]] = {}
    for buoy_id in buoy_ids:
        request = create_request(buoy_id, start_date, end_date, FORMAT_OUT)
        response = urlopen(BASE_URL + request)

        # The bytes in the response are a virtual zip file.
        virtual_sbd_zip = BytesIO(response.read())
        sbd_dict = _merge_dict(sbd_dict, _extract_zip(virtual_sbd_zip))

        response.close()

    # Compile SBD messages into the specified variable type
    data, errors = compile_sbd(sbd_dict, var_type, use_multi_index)

    if return_errors:
        return data, errors
    else:
        return data


def pull_telemetry_as_zip(
    buoy_ids: List[str],
    start_date: datetime,
    end_date: Optional[datetime] = None,
    local_path: Optional[str] = None,
) -> None:
    """
    Query the SWIFT server for microSWIFT data over a specified date
    range and download a .zip file of individual short burst data
    (SBD) messages.

    Args:
        buoy_id (List[str]): Three-digit microSWIFT ID(s) (e.g. ['043']).
        start_date (datetime): Query start date in UTC.
        end_date (datetime, optional): Query end date in UTC. Defaults to None
            which is replaced with the current UTC time.
        local_path (Optional[str], optional): Local directory to save files in.
            Defaults to None which is replaced with the working directory.

    Returns:
       None: Zip file(s) are saved at local_path.

    Examples:
        Download zipped file of SBD messages for microSWIFT 104 from 2024-07-20
        to the present time (in UTC)::

            from datetime import datetime
            from microSWIFTtelemetry import pull_telemetry_as_zip

            pull_telemetry_as_zip(buoy_ids=['104'],
                                  start_date=datetime(2024, 7, 20))

    """
    FORMAT_OUT: Literal['zip'] = 'zip'
    BASE_URL = 'http://swiftserver.apl.washington.edu/services/buoy?action=get_data&'
    DATE_STR_FORMAT = '%Y-%m-%dT%HZ'

    # Handle inputs.
    buoy_ids = _handle_scalar_buoy_id(buoy_ids)
    end_date = _handle_empty_end_date(end_date)
    local_path = _handle_empty_local_path(local_path)

    # Query the SWIFT server and write zip files to the local machine.
    for buoy_id in buoy_ids:
        request = create_request(buoy_id, start_date, end_date, FORMAT_OUT)
        response = urlopen(BASE_URL + request)
        zipped_file = response.read()
        response.close()

        file_name = (f'microSWIFT{buoy_id}_'
                     f'{start_date.strftime(DATE_STR_FORMAT)}_to_'
                     f'{end_date.strftime(DATE_STR_FORMAT)}.zip')

        full_path = os.path.join(local_path, file_name)
        with open(full_path, 'wb') as local:
            local.write(zipped_file)
            local.close()

    return None


def pull_telemetry_as_json(
    buoy_ids: List[str],
    start_date: datetime,
    end_date: Optional[datetime] = None,
) -> dict:
    """
    Query the SWIFT server for microSWIFT data over a specified date
    range and return a dict of JSON-formatted text.

    Args:
        buoy_id (List[str]): Three-digit microSWIFT ID(s) (e.g. ['043']).
        start_date (datetime): Query start date in UTC.
        end_date (datetime, optional): Query end date in UTC. Defaults to None
            which is replaced with the current UTC time.

    Returns:
        dict: JSON-formatted Python dictionary keyed by buoy ID.

    Examples:
        Get microSWIFT 104 and 105 data from 2024-07-20 to the present time
        (in UTC) as a dict of JSON-formatted text and save it to a .json file::

            from datetime import datetime
            import json
            from microSWIFTtelemetry import pull_telemetry_as_json

            swift_json = pull_telemetry_as_json(
                    buoy_ids=['104', '105'],
                    start_date=datetime(2024, 7, 20)
                )
            with open('swift.json', 'w') as file:
                json.dump(swift_json, file)

    """
    FORMAT_OUT: Literal['json'] = 'json'
    BASE_URL = 'http://swiftserver.apl.washington.edu/kml?action=kml&'

    # Handle inputs.
    buoy_ids = _handle_scalar_buoy_id(buoy_ids)
    end_date = _handle_empty_end_date(end_date)

    # Query the SWIFT server for json output and save it in a dict keyed by ID.
    json_dict: Dict[str, dict] = {}
    for buoy_id in buoy_ids:
        request = create_request(buoy_id, start_date, end_date, FORMAT_OUT)
        response = urlopen(BASE_URL + request)
        json_data = response.read()
        json_dict[buoy_id] = json.loads(json_data)
        response.close()

    return json_dict


def pull_telemetry_as_kml(
    buoy_ids: List[str],
    start_date: datetime,
    end_date: Optional[datetime] = None,
    local_path: Optional[str] = None,
) -> None:
    """
    Query the SWIFT server for microSWIFT data over a specified date
    range and download a .kml file containing the buoy's coordinates.


    Args:
        buoy_id (List[str]): Three-digit microSWIFT ID(s) (e.g. ['043']).
        start_date (datetime): Query start date in UTC.
        end_date (datetime, optional): Query end date in UTC. Defaults to None
            which is replaced with the current UTC time.
        local_path (Optional[str], optional): Local directory to save files in.
            Defaults to None which is replaced with the working directory.

    Returns:
       None: KML file(s) are saved at local_path.

    Example:
        Download KML files for microSWIFT 104 from 2024-07-20
        to the present time (in UTC)::

            from datetime import datetime
            from microSWIFTtelemetry import pull_telemetry_as_kml

            pull_telemetry_as_kml(buoy_ids=['104'],
                                  start_date=datetime(2024, 7, 20))

    """
    FORMAT_OUT: Literal['kml'] = 'kml'
    BASE_URL = 'http://swiftserver.apl.washington.edu/kml?action=kml&'
    DATE_STR_FORMAT = '%Y-%m-%dT%HZ'

    # Handle inputs.
    buoy_ids = _handle_scalar_buoy_id(buoy_ids)
    end_date = _handle_empty_end_date(end_date)
    local_path = _handle_empty_local_path(local_path)

    # Query the SWIFT server and write KML files to the local machine.
    for buoy_id in buoy_ids:
        request = create_request(buoy_id, start_date, end_date, FORMAT_OUT)
        response = urlopen(BASE_URL + request)
        kml_file = response.read()
        response.close()

        file_name = (f'microSWIFT{buoy_id}_'
                     f'{start_date.strftime(DATE_STR_FORMAT)}_to_'
                     f'{end_date.strftime(DATE_STR_FORMAT)}.kml')

        full_path = os.path.join(local_path, file_name)
        with open(full_path, 'wb') as local:
            local.write(kml_file)
            local.close()

    return None


def _extract_zip(zip_folder: IO[bytes]) -> Dict[str, IO[bytes]]:
    """
    Extract a virtual zip file into a dictionary of file names and bytes.
    """
    opened_zip = ZipFile(zip_folder)
    return {name: opened_zip.open(name) for name in opened_zip.namelist()}


def _merge_dict(d: dict, other: dict):
    """ Merge two dicts (this syntax only works with 3.9+). """
    return d | other


def _handle_scalar_buoy_id(buoy_ids: Any) -> List[str]:
    """ Catch any IDs provided as a string (which are also iterable) """
    if isinstance(buoy_ids, str):
        buoy_ids = [buoy_ids]
    return buoy_ids


def _handle_empty_end_date(end_date: Optional[datetime]) -> datetime:
    """ Replace empty end_date with the current UTC time. """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    return end_date


def _handle_empty_local_path(local_path: Optional[str]) -> str:
    """ Replace empty local_path with the current working directory. """
    if local_path is None:
        local_path = os.getcwd()
    return local_path

def read_telemetry_from_file():
    # TODO: implement
    raise NotImplementedError


    # Args:
    #     sbd_zip_folder (Union[os.PathLike, IO[bytes]]): local or virtual zip
    #         file of .sbd files.
    #     var_type (Literal['dict', 'pandas', 'xarray']): variable type to be
    #         returned.


    # def _read_sbd_from_local(
    #     sbd_folder: os.PathLike,
    # ):
    #     data_list = []
    #     error_list = []

    #     for file in os.listdir(sbd_folder):
    #         with open(os.path.join(sbd_folder, file), 'rb') as open_file:
    #             sbd_message = SbdMessage(open_file)
    #             data, error_message = sbd_message.read()
    #         if data:
    #             data_list.append(data)
    #         error_list.append(error_message)

    #     return data_list, error_list