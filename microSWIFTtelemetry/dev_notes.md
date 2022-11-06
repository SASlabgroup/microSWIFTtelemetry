# Telemetry tools development

## TODO:
### pull_telemetry.py
- create fun to save to ncf and csv
- sort dictionary according to datetimes

### ReadSBD.py
- support for sensor types 50 and 51

### compileSBD.py
- this should probably be separated into multiple functions based on return type
- support functionality for reading from SBD files NOT in memory
Example notebook: `pull_telemetry_example.ipynb`

## Structure:

```
telemetry/
│   requirements.txt
│  
└───pull_telemetry.py
│       create_request()
│       pull_telemetry_as_var()
│       pull_telemetry_as_zip()
│       pull_telemetry_as_json()
│       pull_telemetry_as_kml()
│
└───read_SBD.py
│       read_SBD()
│       get_sensor_type()
│       unpack_SBD()
│
└───compile_SBD.py
│       compile_SBD()
│       to_pandas_datetime_index()
│        
└───definitions.py
│       get_sensor_type_definition()
│       get_variable_definitions()
│   
└───telemetry_analytics.py
```