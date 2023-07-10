"""
Testing of pull_telemetry.py module

Helpful links:
https://realpython.com/testing-third-party-apis-with-mocks/#your-first-mock
https://semaphoreci.com/community/tutorials/getting-started-with-mocking-in-python
https://stackoverflow.com/questions/70098351/how-to-mock-a-http-request-post-in-python-unittest

"""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np
import pandas as pd

import microSWIFTtelemetry as telemetry
from microSWIFTtelemetry import sbd
from microSWIFTtelemetry.sbd.definitions import get_variable_definitions

# import microSWIFTtelemetry.pull_telemetry as telemetry
# import microSWIFTtelemetry.sbd as sbd
# from microSWIFTtelemetry.sbd.definitions import get_variable_definitions


class TestPullTelemetry(unittest.TestCase):
    """ Unit tests for pull_telemetry.py """

    def setUp(self):
        """ Setup sample data to test on """

        # Sample json string representing the expected response from
        # the SWIFT server when microSWIFT 019 is queried from
        # datetime(2022,9,26,21) to datetime(2022,9,26,22).
        self.sample_json_text = (
            b'{"error_msg":[],"success":true,"buoys":[{"data":[{"wind_speed":0,'
            b'"timestamp":"2022-09-26T21:45:24Z","lon":-83.8242797851562,'
            b'"wave_height":2.431640625,"voltage":0.0,"lat":26.1965198516846},'
            b'{"wind_speed":0,"timestamp":"2022-09-26T21:50:54Z",'
            b'"lon":-83.8242797851562,"wave_height":0.91650390625,'
            b'"voltage":1.0,"lat":26.1965198516846}],"id":300434064043430,'
            b'"name":"microSWIFT 019"}]}'
        )

        # Sample json dict representing the expected response from
        # pull_telemetry_as_var() when microSWIFT 019 is queried from
        # datetime(2022,9,26,21) to datetime(2022,9,26,22) with var_type
        # = 'json'.
        self.sample_json_dict = {
            'error_msg': [],
            'success': True,
            'buoys': [
                {'data': [
                    {'wind_speed': 0,
                     'timestamp': '2022-09-26T21:45:24Z',
                     'lon': -83.8242797851562,
                     'wave_height': 2.431640625,
                     'voltage': 0.0,
                     'lat': 26.1965198516846},
                    {'wind_speed': 0,
                     'timestamp':'2022-09-26T21:50:54Z',
                     'lon': -83.8242797851562,
                     'wave_height': 0.91650390625,
                     'voltage': 1.0,
                     'lat': 26.1965198516846}
                ],
                'id': 300434064043430,
                'name': 'microSWIFT 019'}
            ]
        }

        # Sample .zip file binary representing the expected response
        # from the SWIFT server when microSWIFT 019 is queried from
        # datetime(2022,9,26,21) to datetime(2022,9,26,22).
        self.sample_zipped_sbd_file = (
            b"PK\x03\x04\x14\x00\x00\x00\x00\x00\xdbu\x84U%\xcc\xb0\xdaG\x01"
            b"\x00\x00G\x01\x00\x00n\x00\x00\x00buoy-microSWIFT 019-start-2022"
            b"-09-26T21:00:00-end-2022-09-26T22:00:00/buoy-microSWIFT 019-26Se"
            b"p2022 214524.sbd74\x06G\x01\xdd@yC3Xd*\xa68EA\xc8B\x9dC\x81C-C(B"
            b"\xbaC\x03B\xa0@\x10@\xf0:j8\x948\xf84R5=6n4J5,3x4=5\xc02\x840"
            b"\x97/\xb7/Z/\x04/l*\xdb-\xad)\x1b,P)\xf2(\xed)j+\x84*\x94&\xbd'"
            b"\xd6%\xb6&\x00!\xd87\xf5\x03\x04\xf9\x05\x0e\x19\xfc\x13\x13\x02"
            b"\x08\t\x04\xfd\x00\x03\x01\xf0\xe4\xea\xdd\xd6\xe1\xee\xee\xe6"
            b"\xea\xed\xe9\xf3\xfc\xf4\xf2\x05\xf6\xf2\xfe\x08\n\xfc\x08\n\xf6"
            b"\xff\xfc\xfe\xf6\xec\x0b\xf3\xec\xee\xf6\xf8\xf5\xf4\xfa\t\x07"
            b"\x15\x1e\x17!)\x0c\x1b\x18\x0f\x19\r\x17\n\x17\x1c\x0f\x04\r\r\t"
            b"\xf1\xfe\t\xfb\xdf\xf5\x0e\xfc\xfd\xf3\xf6\xe8\x1c\xf1\xfd\x11"
            b"\xfe\xff\xfe\xf1\x0e\xf0\xf8\xfd\xe3\x01\xf9\x02\xec\xe4\x01\xf2"
            b"\xfe\x04\xf7\x05\x06\x04\x00\xfd\xfd\x01\xf8\xff\xfd\x04\xe6\xfd"
            b"\xec\xf6\xea\xe5\xf1\xf5\xf8\xec\xf7\x02\xd1\xed\xee\xd6\xeb\xe5"
            b"\xc3\xb9\xcb\xd6\xc6\xd9\xed\xe3\xea\xe0\xf1\xdc\xe9\xd7\xe5\xdc"
            b"\xf1\xe9\xe9\xe3\xe2\xe3\xfd\xf0\x18n\xff\xdf\xf0\xa4\x97\x9c"
            b"\xd4\x89\xb5\x99G9@)36!\x1b\x12\x1a\x1b\x1a\x14\x19\x1a\x1a "
            b"\x0e$\x0e\x18\x12\x10\x13\x18\x1a\x10\x0f\x0e\x19y\x92\xd1A\x08"
            b"\xa6\xa7\xc2\x00\x00\x00\x00\x00\x009d\xc6NPK\x03\x04\x14\x00"
            b"\x00\x00\x00\x00\xdbu\x84U\x83!\xcbBG\x01\x00\x00G\x01\x00\x00n"
            b"\x00\x00\x00buoy-microSWIFT 019-start-2022-09-26T21:00:00-end-20"
            b"22-09-26T22:00:00/buoy-microSWIFT 019-26Sep2022 215054.sbd74"
            b"\x06G\x01U;yC7X\x00\x00\x00\x00\x00\x00\x00\x00\xea5\xb88\x078c5"
            b"\xd73+4\x8a0j0B0\x14.\x95-\xcb,8,\xad,R- 070\x81/\xef/N-\xc8,9*"
            b"\xe2)\xc5)v(\x9a(\x01'P(\x14'_&\x8e&\x88&W&1%5$\x86%}$\xd0!\x00!"
            b"\xd87\xed\xfa\xf9\x08\xff\x05\xfc\xf9\xfe\xf8\xf2\xed\xd9\xf5"
            b"\xdb\xe6\xdb\xda\xd3\xc9\xd6\xd5\xcc\xcd\xd9\xdb\xd6\xd6\xda\xd1"
            b"\xe2\xd7\xd3\xd1\xe6\xdc\xe0\xd9\xde\xe7\xe0\xe8\x08\x03\xfd\xf3"
            b"\xf6\x06\xf2\xfa\x02\x02\x04\x0c\x1c\x00\x0c \x13&/84,4) &%1"
            b"\x1a-\x1d.&%\x1f&/)-) +\x07\x00\x0f\xfa\xfe\xf2\xf4\xe5\x19\xf7"
            b"\xfc\x0f\xfb\xfd\xfe\xf2\x0f\xef\xf8\xfd\xe3\x01\xf7\x00\xec\xe4"
            b"\x00\xf3\xff\x02\xfb\x00\x06\x01\x05\x00\xff\x00\xf6\x01\xfc\x03"
            b"\xe8\x06\xea\xf6\xe9\xe6\xf0\xf5\xf9\xeb\xf3\x00\xce\xf2\xed\xd5"
            b"\xee\xe3\xc2\xb9\xc8\xd3\xc8\xd9\xea\xe3\xeb\xdd\xef\xdd\xef\xd7"
            b"\xe6\xdb\xf0\xe9\xe7\xe2\xe2\xe3\xfd\xf1\x00\x01\x02\x01\x01\x01"
            b"\x01\x02\x01\x01\x02\x01\x02\x02\x02\x03\x03\x04\x05\x04\x05\x06"
            b"\x06\x06\x04\x05\x05\x06\x05\x06\x04\x05\x05\x06\x03\x02\x03\x04"
            b"\x05\x02\x03\x05y\x92\xd1A\x08\xa6\xa7\xc2\x00\x00\x00\x00"
            b"\x00<9d\xc6NPK\x01\x02\x14\x03\x14\x00\x00\x00\x00\x00\xdbu"
            b"\x84U%\xcc\xb0\xdaG\x01\x00\x00G\x01\x00\x00n\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x80\x01\x00\x00\x00\x00buoy-microSW"
            b"IFT 019-start-2022-09-26T21:00:00-end-2022-09-26T22:00:00/buoy-m"
            b"icroSWIFT 019-26Sep2022 214524.sbdPK\x01\x02\x14\x03\x14\x00\x00"
            b"\x00\x00\x00\xdbu\x84U\x83!\xcbBG\x01\x00\x00G\x01\x00\x00n\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\xd3\x01\x00\x00"
            b"buoy-microSWIFT 019-start-2022-09-26T21:00:00-end-2022-09-26T22:"
            b"00:00/buoy-microSWIFT 019-26Sep2022 215054.sbdPK\x05\x06\x00\x00"
            b"\x00\x00\x02\x00\x02\x008\x01\x00\x00\xa6\x03\x00\x00\x00\x00"
        )

        # Sample .zip file binary representing the expected response
        # from the SWIFT server when microSWIFT 010 is queried from
        # datetime(2022,9,26,21) to datetime(2022,9,26,22); no data.
        self.sample_zipped_sbd_file_empty = (
            b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00"
        )

        # Sample .zip file binary representing the expected response
        # from the SWIFT server when microSWIFT 012 is queried from
        # datetime(2023,7,9,5) to datetime(2023,7,9,6).
        self.sample_zipped_sbd_file_2 = (
            b"PK\x03\x04\x14\x00\x00\x00\x00\x00\xb4\x80\xeaV\xeb4X\x8aG\x01"
            b"\x00\x00G\x01\x00\x00n\x00\x00\x00buoy-microSWIFT 012-start-2023"
            b"-07-09T05:00:00-end-2023-07-09T06:00:00/buoy-microSWIFT 012-09Ju"
            b"l2023 053512.sbd74\xffG\x01\x8b5WH!]\x0cE\xf1=#2\xf24P0\xdf-\x96"
            b"-q-\xea(\xaa(\xb7)%\x1f\x99\x1ey\x1f\xd0\x1e[%\x98\x1a^\x19\xf1"
            b"\x11\x95\x1ad\x17\x9c\x1ak\x1a\xa9\x19\x0f\x19N\x15\xf2\x1e\x98"
            b"\x1d*\x16\xac\x1a\xde\x11\xe4\x1a\xe0\x08^\x16:\x14\xf8\x16,\x14"
            b"=\x0e\xa0\x1a\x9c\x13\xc2\x1a\xe1\x18\x1f!\x008\x07!\xf2%\xca"
            b"\xe3\xce\xc2\xe1\x0b\x04&\xe3\r\xd3\xf4\xf2\xd8/\n\x05\xef\xe6"
            b'\xeb\xe2\x12\xf8\xf3\xdd\xc9\x1a\xee"\xc0\xd6\x04\xc6\x1c$\xc1.'
            b'\xcb\xf3\xb4\x08\xd3B#S7X\xef\x03\x0c\x1e\xb1= Z\xe9\x0e\x19\n'
            b'\x1aH/=\xd8KBQ4\xf6N\xc6@4\n\xe5\xf7Z\x014\x0e\xcd\xc6\x0f\xf1'
            b'\xee\x0f\xce\xf9\xc8\xeb\xe3@\xdd\xb2\xd2\x14\xa2\x02U\xbaQ\xf7'
            b'\xcc\xae\xe0\x14\xee\xb2\xde\xf9\x1c\xaf\x15\x01\xc8\xcbE\xf6'
            b'\xb8?\xe9\x00\xad\xb1\xa7\xa6\xa1\xa4\xaa\xa1\xcc\xa3\xa2\x1d'
            b'\xa4\xcf\xb7\xa6\xe4\x10$\xe80L\xd9\x0e\xf4"\xe7\xef\xc7\xbb\xcc'
            b'\xff\xd3\xb0\xba\xafG\xed?-\\ \x08\x04\x08\x02\x04\x03\x00\x02'
            b'\x02\x04\x03\x1d\x0e\t\t\x03\x08\x12f\x01\x1a\x04\x08\x05\x03'
            b'\x0b\x05\x0b\x16\x0c\x08\x0b\x13\x0b\x0b\x02\x01.\x03\x05\x06'
            b'\x04\xcd\xa0\x8bB\xe9\xee,\xc3\xb7D\xe2O3F\x8eT\xc9NPK\x01\x02'
            b'\x14\x03\x14\x00\x00\x00\x00\x00\xb4\x80\xeaV\xeb4X\x8aG\x01\x00'
            b'\x00G\x01\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x80\x01\x00\x00\x00\x00buoy-microSWIFT 012-start-2023-07-09T05:'
            b'00:00-end-2023-07-09T06:00:00/buoy-microSWIFT 012-09Jul2023 0535'
            b'12.sbdPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00\x9c\x00\x00\x00'
            b'\xd3\x01\x00\x00\x00\x00'
        )

        # Sample data representing the expected response from read_sbd()
        # when microSWIFT 019 is queried from datetime(2022,9,26,21) to
        # datetime(2022,9,26,22).
        self.sample_data = [
           {'datetime': datetime(2022, 9, 26, 21, 41, 20,
                                 tzinfo=timezone.utc),
            'significant_height': 2.431640625,
            'peak_period': 3.736328125,
            'peak_direction': 134.375,
            'energy_density': np.array([
                0.04992676, 0.58105469, 2.63476562, 3.390625  , 3.80664062,
                3.75195312, 3.58789062, 3.078125  , 3.86328125, 3.00585938,
                2.3125    , 2.03125   , 0.8671875 , 0.55175781, 0.57226562,
                0.31054688, 0.33251953, 0.38989258, 0.27685547, 0.33056641,
                0.22412109, 0.27929688, 0.32739258, 0.2109375 , 0.14111328,
                0.11859131, 0.12054443, 0.11486816, 0.10961914, 0.0501709 ,
                0.0914917 , 0.04434204, 0.06414795, 0.04150391, 0.03863525,
                0.04629517, 0.05792236, 0.05090332, 0.0256958 , 0.03022766,
                0.02279663, 0.0262146
                ]),
            'frequency': np.array([
                0.00976562, 0.02148438, 0.03320312, 0.04492188, 0.05664062,
                0.06835938, 0.08007812, 0.09179688, 0.10351562, 0.11523438,
                0.12695312, 0.13867188, 0.15039062, 0.16210938, 0.17382812,
                0.18554688, 0.19726562, 0.20898438, 0.22070312, 0.23242188,
                0.24414062, 0.25585938, 0.26757812, 0.27929688, 0.29101562,
                0.30273438, 0.31445312, 0.32617188, 0.33789062, 0.34960938,
                0.36132812, 0.37304688, 0.38476562, 0.39648438, 0.40820312,
                0.41992188, 0.43164062, 0.44335938, 0.45507812, 0.46679688,
                0.47851562, 0.49023438
                ]),
            'a1': np.array([
                -0.11,  0.03,  0.04, -0.07,  0.05,  0.14,  0.25, -0.04,  0.19,
                 0.19,  0.02,  0.08,  0.09,  0.04, -0.03,  0.  ,  0.03,  0.01,
                -0.16, -0.28, -0.22, -0.35, -0.42, -0.31, -0.18, -0.18, -0.26,
                -0.22, -0.19, -0.23, -0.13, -0.04, -0.12, -0.14,  0.05, -0.1 ,
                -0.14, -0.02,  0.08,  0.1 , -0.04,  0.08
                ]),
            'b1': np.array([
                 0.1 , -0.1 , -0.01, -0.04, -0.02, -0.1 , -0.2 ,  0.11, -0.13,
                -0.2 , -0.18, -0.1 , -0.08, -0.11, -0.12, -0.06,  0.09,  0.07,
                 0.21,  0.3 ,  0.23,  0.33,  0.41,  0.12,  0.27,  0.24,  0.15,
                 0.25,  0.13,  0.23,  0.1 ,  0.23,  0.28,  0.15,  0.04,  0.13,
                 0.13,  0.09, -0.15, -0.02,  0.09, -0.05
                ]),
            'a2': np.array([
                -0.33, -0.11,  0.14, -0.04, -0.03, -0.13, -0.1 , -0.24,  0.28,
                -0.15, -0.03,  0.17, -0.02, -0.01, -0.02, -0.15,  0.14, -0.16,
                -0.08, -0.03, -0.29,  0.01, -0.07,  0.02, -0.2 , -0.28,  0.01,
                -0.14, -0.02,  0.04, -0.09,  0.05,  0.06,  0.04,  0.  , -0.03,
                -0.03,  0.01, -0.08, -0.01, -0.03,  0.04
                ]),
            'b2': np.array([
                -0.26, -0.03, -0.2 , -0.1 , -0.22, -0.27, -0.15, -0.11, -0.08,
                -0.2 , -0.09,  0.02, -0.47, -0.19, -0.18, -0.42, -0.21, -0.27,
                -0.61, -0.71, -0.53, -0.42, -0.58, -0.39, -0.19, -0.29, -0.22,
                -0.32, -0.15, -0.36, -0.23, -0.41, -0.27, -0.36, -0.15, -0.23,
                -0.23, -0.29, -0.3 , -0.29, -0.03, -0.16
                ]),
            'check': np.array([
                2.4, 11. , 25.5, 22.3, 24. , 16.4, 15.1, 15.6, 21.2, 13.7, 18.1,
                15.3,  7.1,  5.7,  6.4,  4.1,  5.1,  5.4,  3.3,  2.7,  1.8,  2.6,
                2.7,  2.6,  2. ,  2.5,  2.6,  2.6,  3.2,  1.4,  3.6,  1.4,  2.4,
                1.8,  1.6,  1.9,  2.4,  2.6,  1.6,  1.5,  1.4,  2.5
                ]),
            'u_mean': None,
            'v_mean': None,
            'z_mean': None,
            'latitude': 26.19651985168457,
            'longitude': -83.82427978515625,
            'temperature': 0.0,
            'salinity': 0.0,
            'voltage': 0.0,
            'sensor_type': 52,
            'com_port': 6,
            'payload_size': 327},
           {'datetime': datetime(2022, 9, 26, 21, 41, 20,
                                 tzinfo=timezone.utc),
            'significant_height': 0.91650390625,
            'peak_period': 3.736328125,
            'peak_direction': 134.875,
            'energy_density': np.array([
                0.        , 0.        , 0.        , 0.        , 0.36962891,
                0.58984375, 0.50341797, 0.33666992, 0.24499512, 0.26049805,
                0.1418457 , 0.13793945, 0.13305664, 0.0949707 , 0.08721924,
                0.07489014, 0.06591797, 0.07305908, 0.08312988, 0.12890625,
                0.13171387, 0.11724854, 0.1239624 , 0.08288574, 0.07470703,
                0.0486145 , 0.04595947, 0.04507446, 0.03485107, 0.03594971,
                0.02735901, 0.03369141, 0.02764893, 0.02488708, 0.02560425,
                0.0255127 , 0.02476501, 0.02027893, 0.01643372, 0.02157593,
                0.01753235, 0.01135254
                ]),
            'frequency': np.array([
                0.00976562, 0.02148438, 0.03320312, 0.04492188, 0.05664062,
                0.06835938, 0.08007812, 0.09179688, 0.10351562, 0.11523438,
                0.12695312, 0.13867188, 0.15039062, 0.16210938, 0.17382812,
                0.18554688, 0.19726562, 0.20898438, 0.22070312, 0.23242188,
                0.24414062, 0.25585938, 0.26757812, 0.27929688, 0.29101562,
                0.30273438, 0.31445312, 0.32617188, 0.33789062, 0.34960938,
                0.36132812, 0.37304688, 0.38476562, 0.39648438, 0.40820312,
                0.41992188, 0.43164062, 0.44335938, 0.45507812, 0.46679688,
                0.47851562, 0.49023438
                ]),
            'a1': np.array([
                -0.19, -0.06, -0.07,  0.08, -0.01,  0.05, -0.04, -0.07, -0.02,
                -0.08, -0.14, -0.19, -0.39, -0.11, -0.37, -0.26, -0.37, -0.38,
                -0.45, -0.55, -0.42, -0.43, -0.52, -0.51, -0.39, -0.37, -0.42,
                -0.42, -0.38, -0.47, -0.3 , -0.41, -0.45, -0.47, -0.26, -0.36,
                -0.32, -0.39, -0.34, -0.25, -0.32, -0.24
                ]),
            'b1': np.array([
                0.08,  0.03, -0.03, -0.13, -0.1 ,  0.06, -0.14, -0.06,  0.02,
                0.02,  0.04,  0.12,  0.28,  0.  ,  0.12,  0.32,  0.19,  0.38,
                0.47,  0.56,  0.52,  0.44,  0.52,  0.41,  0.32,  0.38,  0.37,
                0.49,  0.26,  0.45,  0.29,  0.46,  0.38,  0.37,  0.31,  0.38,
                0.47,  0.41,  0.45,  0.41,  0.32,  0.43
                ]),
            'a2': np.array([
                 0.07,  0.  ,  0.15, -0.06, -0.02, -0.14, -0.12, -0.27,  0.25,
                -0.09, -0.04,  0.15, -0.05, -0.03, -0.02, -0.14,  0.15, -0.17,
                -0.08, -0.03, -0.29,  0.01, -0.09,  0.  , -0.2 , -0.28,  0.  ,
                -0.13, -0.01,  0.02, -0.05,  0.  ,  0.06,  0.01,  0.05,  0.  ,
                -0.01,  0.  , -0.1 ,  0.01, -0.04,  0.03
                ]),
            'b2': np.array([
                -0.24,  0.06, -0.22, -0.1 , -0.23, -0.26, -0.16, -0.11, -0.07,
                -0.21, -0.13,  0.  , -0.5 , -0.14, -0.19, -0.43, -0.18, -0.29,
                -0.62, -0.71, -0.56, -0.45, -0.56, -0.39, -0.22, -0.29, -0.21,
                -0.35, -0.17, -0.35, -0.17, -0.41, -0.26, -0.37, -0.16, -0.23,
                -0.25, -0.3 , -0.3 , -0.29, -0.03, -0.15
                ]),
            'check': np.array([
                0. , 0.1, 0.2, 0.1, 0.1, 0.1, 0.1, 0.2, 0.1, 0.1, 0.2, 0.1, 0.2,
                0.2, 0.2, 0.3, 0.3, 0.4, 0.5, 0.4, 0.5, 0.6, 0.6, 0.6, 0.4, 0.5,
                0.5, 0.6, 0.5, 0.6, 0.4, 0.5, 0.5, 0.6, 0.3, 0.2, 0.3, 0.4, 0.5,
                0.2, 0.3, 0.5
                ]),
            'u_mean': None,
            'v_mean': None,
            'z_mean': None,
            'latitude': 26.19651985168457,
            'longitude': -83.82427978515625,
            'temperature': 0.0,
            'salinity': 0.0,
            'voltage': 1.0,
            'sensor_type': 52,
            'com_port': 6,
            'payload_size': 327},
            ]
        self.sample_data_errors = {
            'file_name': [
                ('buoy-microSWIFT 019-start-2022-09-26T21:00:00-end-2022-09-'
                 '26T22:00:00/buoy-microSWIFT 019-26Sep2022 214524.sbd'),
                ('buoy-microSWIFT 019-start-2022-09-26T21:00:00-end-2022-09-'
                 '26T22:00:00/buoy-microSWIFT 019-26Sep2022 215054.sbd')
                 ],
            'error': [None, None]
        }

        # Sample data representing the expected response from read_sbd()
        # when microSWIFT 012 is queried from datetime(2023,7,9,5) to
        # datetime(2023,7,9,6).
        self.sample_data_2 = [{
            'datetime': datetime(2023, 7, 9, 5, 34, 56,
                                 tzinfo=timezone.utc),
            'significant_height': 0.346435546875,
            'peak_period': 8.6796875,
            'peak_direction': 328.25,
            'energy_density': np.array([
                5.04687500e+00, 1.48535156e+00, 1.91772461e-01, 3.09082031e-01,
                1.34765625e-01, 9.17358398e-02, 8.72802734e-02, 8.50219727e-02,
                3.83911133e-02, 3.64379883e-02, 4.46472168e-02, 6.97708130e-03,
                6.44302368e-03, 7.29751587e-03, 6.65283203e-03, 2.09197998e-02,
                3.21960449e-03, 2.62069702e-03, 7.25269318e-04, 3.21388245e-03,
                1.80435181e-03, 3.22723389e-03, 3.13377380e-03, 2.76374817e-03,
                2.47001648e-03, 1.29508972e-03, 6.78253174e-03, 5.46264648e-03,
                1.50489807e-03, 3.25775146e-03, 7.16209412e-04, 3.36456299e-03,
                1.48773193e-04, 1.55448914e-03, 1.03187561e-03, 1.70135498e-03,
                1.01852417e-03, 3.80754471e-04, 3.23486328e-03, 9.28878784e-04,
                3.29971313e-03, 2.38227844e-03]),
            'frequency': np.array([
                0.01000214, 0.0219533 , 0.03390447, 0.04585564, 0.05780681,
                0.06975797, 0.08170914, 0.09366031, 0.10561148, 0.11756264,
                0.12951381, 0.14146498, 0.15341615, 0.16536731, 0.17731848,
                0.18926965, 0.20122081, 0.21317198, 0.22512315, 0.23707432,
                0.24902548, 0.26097665, 0.27292782, 0.28487899, 0.29683015,
                0.30878132, 0.32073249, 0.33268366, 0.34463482, 0.35658599,
                0.36853716, 0.38048833, 0.39243949, 0.40439066, 0.41634183,
                0.428293  , 0.44024416, 0.45219533, 0.4641465 , 0.47609767,
                0.48804883, 0.5       ]),
            'a1': np.array([
                0.07,  0.33, -0.14,  0.37, -0.54, -0.29, -0.5 , -0.62, -0.31,
                0.11,  0.04,  0.38, -0.29,  0.13, -0.45, -0.12, -0.14, -0.4 ,
                0.47,  0.1 ,  0.05, -0.17, -0.26, -0.21, -0.3 ,  0.18, -0.08,
                -0.13, -0.35, -0.55,  0.26, -0.18,  0.34, -0.64, -0.42,  0.04,
                -0.58,  0.28,  0.36, -0.63,  0.46, -0.53]),
            'b1': np.array([
                -0.13, -0.76,  0.08, -0.45,  0.66,  0.35,  0.83,  0.55,  0.88,
                -0.17,  0.03,  0.12,  0.3 , -0.79,  0.61,  0.32,  0.9 , -0.23,
                0.14,  0.25,  0.1 ,  0.26,  0.72,  0.47,  0.61, -0.4 ,  0.75,
                0.66,  0.81,  0.52, -0.1 ,  0.78, -0.58,  0.64,  0.52,  0.1 ,
                -0.27, -0.09,  0.9 ,  0.01,  0.52,  0.14]),
            'a2': np.array([
                -0.51, -0.58,  0.15, -0.15, -0.18,  0.15, -0.5 , -0.07, -0.56,
                -0.21, -0.29,  0.64, -0.35, -0.78, -0.46,  0.2 , -0.94,  0.02,
                0.85, -0.7 ,  0.81, -0.09, -0.52, -0.82, -0.32,  0.2 , -0.18,
                -0.78, -0.34, -0.07,  0.28, -0.81,  0.21,  0.01, -0.56, -0.53,
                0.69, -0.1 , -0.72,  0.63, -0.23,  0.  ]),
            'b2': np.array([
                -0.83, -0.79, -0.89, -0.9 , -0.95, -0.92, -0.86, -0.95, -0.52,
                -0.93, -0.94,  0.29, -0.92, -0.49, -0.73, -0.9 , -0.28,  0.16,
                0.36, -0.24,  0.48,  0.76, -0.39,  0.14, -0.12,  0.34, -0.25,
                -0.17, -0.57, -0.69, -0.52, -0.01, -0.45, -0.8 , -0.7 , -0.81,
                0.71, -0.19,  0.63,  0.45,  0.92,  0.32]),
            'check': np.array([
                0.8,  0.4,  0.8,  0.2,  0.4,  0.3,  0. ,  0.2,  0.2,  0.4,  0.3,
                2.9,  1.4,  0.9,  0.9,  0.3,  0.8,  1.8, 10.2,  0.1,  2.6,  0.4,
                0.8,  0.5,  0.3,  1.1,  0.5,  1.1,  2.2,  1.2,  0.8,  1.1,  1.9,
                1.1,  1.1,  0.2,  0.1,  4.6,  0.3,  0.5,  0.6,  0.4]),
            'u_mean': None,
            'v_mean': None,
            'z_mean': None,
            'latitude': 69.8140640258789,
            'longitude': -172.93324279785156,
            'temperature': 4.71484375,
            'salinity': 31.53125,
            'voltage': 6.19921875,
            'sensor_type': 52,
            'com_port': 255,
            'payload_size': 327
        }]
        self.sample_data_errors_2 = {
            'file_name': [
                ('buoy-microSWIFT 012-start-2023-07-09T05:00:00-end-2023-07-'
                 '09T06:00:00/buoy-microSWIFT 012-09Jul2023 053512.sbd')
            ],
            'error': [None]
        }

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_json(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='json' """

        mock_urlopen.return_value.read.return_value = self.sample_json_text

        response = telemetry.pull_telemetry_as_json(
            buoy_id='019',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22)
        )

        expected_response = self.sample_json_dict

        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertDictEqual(response, expected_response)

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_dict(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='dict' """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='019',
            start_date=datetime(2022, 9, 26, 21),
            end_date=datetime(2022, 9, 26, 22),
            var_type='dict'
        )

        # expected_response = self.sample_dictionary_data
        data = self.sample_data
        expected_response = {k: [d.get(k) for d in data]
                                                   for k in set().union(*data)}
        expected_errors = self.sample_data_errors

        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertEqual(response.keys(), expected_response.keys())
        for variable in get_variable_definitions():
            np.array_equal(response[variable[0]], expected_response[variable[0]])

        self.assertIsInstance(expected_errors, dict)
        self.assertEqual(errors.keys(), expected_errors.keys())
        for key in ['file_name', 'error']:
            np.array_equal(errors[key], expected_errors[key])

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_dict_2(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='dict' """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file_2

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='012',
            start_date=datetime(2023, 7, 9, 5),
            end_date=datetime(2023, 7, 9, 6),
            var_type='dict'
        )

        data = self.sample_data_2
        expected_response = {k: [d.get(k) for d in data]
                                                   for k in set().union(*data)}
        expected_errors = self.sample_data_errors_2

        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertEqual(response.keys(), expected_response.keys())
        for variable in get_variable_definitions():
            np.array_equal(response[variable[0]], expected_response[variable[0]])

        self.assertIsInstance(expected_errors, dict)
        self.assertEqual(errors.keys(), expected_errors.keys())
        for key in ['file_name', 'error']:
            np.array_equal(errors[key], expected_errors[key])

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_pandas(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='pandas' """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='019',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22),
            var_type='pandas'
        )

        expected_response = pd.DataFrame(self.sample_data)
        expected_errors = pd.DataFrame(self.sample_data_errors)

        sbd.to_pandas_datetime_index(expected_response)
        pd.testing.assert_frame_equal(response, expected_response)
        pd.testing.assert_frame_equal(errors, expected_errors)

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_pandas_2(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='pandas' """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file_2

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='012',
            start_date=datetime(2023, 7, 9, 5),
            end_date=datetime(2023, 7, 9, 6),
            var_type='pandas'
        )

        expected_response = pd.DataFrame(self.sample_data_2)
        expected_errors = pd.DataFrame(self.sample_data_errors_2)

        sbd.to_pandas_datetime_index(expected_response)
        pd.testing.assert_frame_equal(response, expected_response)
        pd.testing.assert_frame_equal(errors, expected_errors)

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_dict_empty(self, mock_urlopen):
        """
        Test pull_telemetry_as_var with var_type='dict' when the
        response contains an empty file.
        """
        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file_empty

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='010',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22),
            var_type='dict'
        )

        expected_response = {}
        expected_errors = {}

        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertDictEqual(response, expected_response)
        self.assertDictEqual(errors, expected_errors)

    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_empty_pandas_empty(self, mock_urlopen):
        """
        Test pull_telemetry_as_var with var_type='pandas' when the
        response contains an empty file.
        """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file_empty

        response, errors = telemetry.pull_telemetry_as_var(
            buoy_id='010',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22),
            var_type='pandas'
        )

        expected_response = pd.DataFrame({})
        expected_errors = pd.DataFrame({})

        pd.testing.assert_frame_equal(response, expected_response)
        pd.testing.assert_frame_equal(errors, expected_errors)

if __name__ == '__main__':
    unittest.main()
