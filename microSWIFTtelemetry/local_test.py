# %%
import xarray as xr
from datetime import datetime
from microSWIFTtelemetry import pull_telemetry_as_var, pull_telemetry_as_zip, pull_telemetry_as_kml, pull_telemetry_as_json

# %%
response, errors = pull_telemetry_as_var(
    buoy_ids=['079'],
    # buoy_ids=['079', '087', '104', '105', '106'],
    start_date=datetime(2024, 7, 23, 19, 0, 0),
    end_date=datetime(2024, 7, 23, 20, 0, 0),
    var_type='pandas',
    return_errors=True,
    use_multi_index=True,
)

# %%
pull_telemetry_as_zip(
    buoy_ids=['079', '087', '104', '105', '106'],
    start_date=datetime(2024, 7, 20, 0, 0, 0),
    end_date=datetime(2024, 7, 30, 0, 0, 0),
)

#%%

pull_telemetry_as_json(
    buoy_ids=['079'],
    # buoy_ids=['079', '087', '104', '105', '106'],
    start_date=datetime(2024, 7, 20, 0, 0, 0),
    end_date=datetime(2024, 7, 30, 0, 0, 0),
)


 #%%

pull_telemetry_as_kml(
    buoy_ids=['079', '087', '104', '105', '106'],
    start_date=datetime(2024, 7, 20, 0, 0, 0),
    end_date=datetime(2024, 7, 30, 0, 0, 0),
)

# %%

from datetime import datetime
import json
swift_json = pull_telemetry_as_json(
        buoy_ids=['104', '105'],
        start_date=datetime(2024, 7, 20)
    )
with open('swift.json', 'w') as file:
    json.dump(swift_json, file)