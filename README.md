# microSWIFTtelemetry
microSWIFTtelemetry provides Python-based functionality for pulling telemetry from the microSWIFT wave buoy developed at the University of Washington Applied Physics Laboratory (UW-APL). 

It contains collection of python functions for accessing data from the UW-APL SWIFT server:\
[http://swiftserver.apl.washington.edu/](http://swiftserver.apl.washington.edu/) (base URL)\
[http://faculty.washington.edu/jmt3rd/SWIFTdata/DynamicDataLinks.html](http://faculty.washington.edu/jmt3rd/SWIFTdata/DynamicDataLinks.html) (HTML page)

See [examples/](https://github.com/jacobrdavis/microSWIFTtelemetry/tree/main/examples) for usage.

## Organization
```
microSWIFTtelemetry/
├── LICENSE
├── README.md
├── docs
├── examples/
│   ├── create_telemetry_report_example.ipynb
│   └── pull_telemetry_example.ipynb
├── microSWIFTtelemetry/
│   ├── __init__.py
│   ├── pull_telemetry.py
│   ├── sbd/
│   │   ├── __init__.py
│   │   ├── compile_SBD.py
│   │   ├── definitions.py
│   │   └── read_SBD.py
│   └── version.py
├── pyproject.toml
├── requirements.txt
├── setup.py
└── tests/
    └── test_microSWIFTtelemetry.py
```
## microSWIFT
Learn more about the microSWIFT wave buoy:
* [https://apl.uw.edu/project/projects/swift/pdfs/microSWIFTspecsheet.pdf](https://apl.uw.edu/project/projects/swift/pdfs/microSWIFTspecsheet.pdf) (spec sheet)

* [https://github.com/SASlabgroup/microSWIFT](https://github.com/SASlabgroup/microSWIFT) (microSWIFTv1 operational code)

Schematic depicting buoys telemetering wave data from the ocean to a scientist on land via satellite:
![schematic depicting buoys telemetering wave data from the ocean to a scientist on land via satellite](./docs/imgs/how_telemetry_works.png)

