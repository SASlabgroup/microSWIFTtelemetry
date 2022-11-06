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

import os
from urllib.request import urlopen
from urllib.parse import urlencode, quote_plus
from io import BytesIO
from zipfile import ZipFile
import json
from datetime import datetime
from typing import Union, List, BinaryIO, TextIO
from pandas import DataFrame
from xarray import DataArray
from microSWIFTtelemetry.sbd.compile_SBD import compile_SBD


def create_request(
    buoyID: str, 
    startDate: datetime, 
    endDate: datetime, 
    formatOut: str
)-> dict:
    """
    Create a URL-encoded request.

    Arguments:
        - buoyID (str), microSWIFT ID including leading zero (e.g. '043')
        - startDate (datetime), query start date in UTC (e.g. datetime(2022,9,26,0,0,0))
        - endDate (datetime), query end date in UTC
        - formatOut (str), format to query the SWIFT server for:
            * 'zip', return a `.zip` file of SBD messages
            * 'json', JSON-formatted text
            * 'kml', kml of drift tracks

    Returns:
        - (dict), URL-enoded (utf8) request to be sent to the server
    """

    # Convert dates to strings:
    startDateStr  = startDate.strftime('%Y-%m-%dT%H:%M:%S')
    endDateStr = endDate.strftime('%Y-%m-%dT%H:%M:%S')

    # Pack into a payload dictionary:
    payload = {
        'buoy_name' : f'microSWIFT {buoyID}'.encode('utf8'),
        'start' : startDateStr.encode('utf8'),
        'end' : endDateStr.encode('utf8'),
        'format' : formatOut.encode('utf8')
    }

    return urlencode(payload, quote_via=quote_plus)

def pull_telemetry_as_var(
    buoyID: str,
    startDate: datetime,
    endDate: datetime = datetime.utcnow(),
    varType: str = 'dict',
)-> Union[List[dict], DataFrame, DataArray]:
    """
    Query the SWIFT server for microSWIFT data over a specified date range and 
    return an object in memory. Note the `.zip` file of short burst data (SBD) messages
    is handled in memory and not saved to the local machine. Use pull_telemetry_as_zip
    for this purpose.

    Arguments:
        - buoyID (str), microSWIFT ID including leading zero (e.g. '043')
        - startDate (datetime), query start date in UTC (e.g. datetime(2022,9,26,0,0,0))
        - endDate (datetime, optional), query end date in UTC; defaults to datetime.utcnow().
        - varType (str, optional), variable type to be returned; defaults to 'dict'
            Possible values include:
            * 'dict', a dictionary with key-value pairs corresponding to vars
            * 'pandas', returns a pandas DataFrame object
            * 'xarray', returns an xarray DataArray object

    Returns:
        - (List[dict]), if varType == 'dict' 
        - (DataFrame), if varType == 'pandas' 
        - (DataArray), if varType == 'xarray' 

    Example:

    Return SWIFT as a pandas dataframe; by leaving the endDate empty, the 
    function will default to the present time (in UTC):

        >>> from datetime import datetime
        >>> import pandas
        >>> SWIFT_df = pull_telemetry_as_var('019', datetime(2022,9,26), varType = 'pandas')
    """
    # Create the payload request:
    formatOut = 'zip'
    request = create_request(buoyID, startDate, endDate, formatOut)

    # Define the base URL:
    baseURL = 'http://swiftserver.apl.washington.edu/services/buoy?action=get_data&'

    # Get the response:
    response = urlopen(baseURL + request)

    # Read the response into memory as a virtual zip file:
    zippedFile = ZipFile(BytesIO(response.read())) # virtual zip file
    response.close()

    # Compile SBD messages into specified variable and return:
    return compile_SBD(zippedFile, varType, fromMemory = True)

def pull_telemetry_as_zip(
    buoyID: str,
    startDate: datetime,
    endDate: datetime = datetime.utcnow(),
    localPath: str = None,
)-> BinaryIO:
    """
    Query the SWIFT server for microSWIFT data over a specified date range and 
    download a `.zip` file of individual short burst data (SBD) messages.

    Arguments:
        - buoyID (str), microSWIFT ID including leading zero (e.g. '043')
        - startDate (datetime), query start date in UTC (e.g. datetime(2022,9,26,0,0,0))
        - endDate (datetime, optional), query end date in UTC; defaults to datetime.utcnow().
        - localPath (str, optional), path to local file destination including folder 
            and filename; defaults to the current directory as './microSWIFT{buoyID}.zip'

    Returns:
        - (BinaryIO), compressed `.zip` file at localPath

    Example:

    Download zipped file of SBD messages; by leaving the endDate empty, the 
    function will default to the present time (in UTC):

        >>> from datetime import datetime
        >>> pull_telemetry_as_zip(buoyID = '019', startDate = datetime(2022,9,26))
    """
    # Create the payload request:
    formatOut = 'zip'
    request = create_request(buoyID, startDate, endDate, formatOut)

    # Define the base URL:
    baseURL = 'http://swiftserver.apl.washington.edu/services/buoy?action=get_data&'

    # Get the response:
    response = urlopen(baseURL + request)

    # Write the response to a local .zip file:
    zippedFile = response.read()
    response.close() 
    
    if localPath is None:
        localPath = os.path.join(os.getcwd(), f'microSWIFT{buoyID}.zip')
        
    with open(localPath, 'wb') as local:
        local.write(zippedFile)
        local.close()  
    return

def pull_telemetry_as_json(
    buoyID: str,
    startDate: datetime,
    endDate: datetime = datetime.utcnow(),
)-> dict:
    """
    Query the SWIFT server for microSWIFT data over a specified date range and 
    download a `.zip` file of individual short burst data (SBD) messages.

    Arguments:
        - buoyID (str), microSWIFT ID including leading zero (e.g. '043')
        - startDate (datetime), query start date in UTC (e.g. datetime(2022,9,26,0,0,0))
        - endDate (datetime, optional), query end date in UTC; defaults to datetime.utcnow().

    Returns:
        - (dict), JSON-formatted Python dictionary 

    Example:

    Query the SWIFT server and return a variable containing JSON-formatted text. Save to a .json file.

        >>> from datetime import datetime
        >>> import json
        >>> SWIFT_json = pull_telemetry_as_json(buoyID = '019', startDate = datetime(2022,9,26), endDate = datetime(2022,9,30))
        >>> with open('SWIFT.json', 'w') as f:
        >>>     json.dump(SWIFT_json, f)
    """
    # Create the payload request:
    formatOut = 'json'
    request = create_request(buoyID, startDate, endDate, formatOut)

    # Define the base URL:
    baseURL = 'http://swiftserver.apl.washington.edu/kml?action=kml&'   

    # Get the response:
    response = urlopen(baseURL + request)

    # Return as json
    jsonData = response.read()
    response.close()

    return json.loads(jsonData)

def pull_telemetry_as_kml(
    buoyID: str,
    startDate: datetime,
    endDate: datetime = datetime.utcnow(),
    localPath: str = None,
)-> TextIO:
    """
    Query the SWIFT server for microSWIFT data over a specified date range and 
    download a `.kml` file containing the buoy's GPS coordinates.

    Arguments:
        - buoyID (str), microSWIFT ID including leading zero (e.g. '043')
        - startDate (datetime), query start date in UTC (e.g. datetime(2022,9,26,0,0,0))
        - endDate (datetime, optional), query end date in UTC; defaults to datetime.utcnow().
        - localPath (str, optional), path to local file destination including folder 
            and filename; defaults to the current directory as 
            ./microSWIFT{buoyID}_{'%Y-%m-%dT%H%M%S'}_to_{'%Y-%m-%dT%H%M%S'}.kml

    Returns:
        - (TextIO), .kml file at localPath

    Example:

    Download a KML file of buoy drift tracks; by leaving the endDate empty, the 
    function will default to the present time (in UTC):

        >>> from datetime import datetime
        >>> pull_telemetry_as_kml(buoyID = '019', startDate = datetime(2022,9,26))
    """
    # Create the payload request:
    formatOut = 'kml'
    request = create_request(buoyID, startDate, endDate, formatOut)

    # Define the base URL:
    baseURL = 'http://swiftserver.apl.washington.edu/kml?action=kml&'

    # Get the response:
    response = urlopen(baseURL + request)

    # Write the response to a local .kml geographic file:
    kmlFile = response.read()
    response.close()
    if localPath is None:
        startDateStr  = startDate.strftime('%Y-%m-%dT%H%M%S')
        endDateStr = endDate.strftime('%Y-%m-%dT%H%M%S')
        localPath = os.path.join(os.getcwd(), f'microSWIFT{buoyID}_{startDateStr}_to_{endDateStr}.kml')
    with open(localPath, 'wb') as local:
            local.write(kmlFile)
    return


