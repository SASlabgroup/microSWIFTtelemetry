"""
Testing of pull_telemetry.py module

Helpful links:
https://realpython.com/testing-third-party-apis-with-mocks/#your-first-mock
https://semaphoreci.com/community/tutorials/getting-started-with-mocking-in-python
https://stackoverflow.com/questions/70098351/how-to-mock-a-http-request-post-in-python-unittest

"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

import microSWIFTtelemetry as telemetry
import microSWIFTtelemetry.sbd as sbd
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
            'sensor_type': 52},
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
            'sensor_type': 52}
            ]


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

        response = telemetry.pull_telemetry_as_var(
            buoy_id='019',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22),
            var_type='dict'
        )

        # expected_response = self.sample_dictionary_data
        data = self.sample_data
        expected_response = {k: [d.get(k) for d in data]
                                                   for k in set().union(*data)}

        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertEqual(response.keys(),expected_response.keys())
    
        for variable in get_variable_definitions():
            np.array_equal(response[variable[0]], expected_response[variable[0]])


    @patch('microSWIFTtelemetry.pull_telemetry.urlopen')
    def test_pull_telemetry_as_var_pandas(self, mock_urlopen):
        """ Test pull_telemetry_as_var with var_type='pandas' """

        mock_urlopen.return_value.read.return_value = self.sample_zipped_sbd_file

        response = telemetry.pull_telemetry_as_var(
            buoy_id='019',
            start_date=datetime(2022,9,26,21),
            end_date=datetime(2022,9,26,22),
            var_type='pandas'
        )

        expected_response = pd.DataFrame(self.sample_data)
        sbd.to_pandas_datetime_index(expected_response)
        pd.testing.assert_frame_equal(response, expected_response)


if __name__ == '__main__':
    unittest.main()





    # def test_correct_length(self):
    #     """ 
    #     Smoke test that checks for runtime errors and proper output length.
    #     """
    #     data = np.array([[0, 1, 2, 3],
    #                      [0, 1, 2, 3],
    #                      [0, 1, 2, 3],
    #                      [0, 1, 2, 3],
    #                      [0, 1, 2, 3]])

    #     query = np.array([0, 0, 0, 0])
        
    #     self.assertEqual(
    #         len(euclidean_distance(data, query)), 
    #         data.shape[0],
    #     )



 # Run examples:
#  start = datetime(2022,9,26,0,0,0)
#  end = datetime.utcnow()
#  buoyID = '019'

 # SWIFT_json = pull_telemetry_as_json(buoyID = buoyID, startDate = start, endDate= end)
 # print(SWIFT_json)

 # SWIFT_dict = pull_telemetry_as_var(buoyID = buoyID, startDate = start, endDate= end, varType = 'dict')
 # print(SWIFT_dict.keys())

 # SWIFT_df = pull_telemetry_as_var(buoyID, datetime(2022,9,26), varType = 'pandas')

 # SWIFT_df = pull_telemetry_as_var(buoyID = buoyID, startDate = start, endDate= end, varType = 'pandas')
 # print(SWIFT_df.info())

 # TODO:
 # SWIFT_ds = pull_telemetry_as_var(buoyID = buoyID, startDate = start, endDate= end, varType = 'xarray')
 # print(SWIFT_ds)

#  pull_telemetry_as_zip(buoyID = buoyID, startDate = start, endDate= end)

#  pull_telemetry_as_kml(buoyID = buoyID, startDate = start, endDate= end)

        # # Sample dictionary representing the expected response from
        # # pull_telemetry_as_var() when microSWIFT 019 is queried from
        # # datetime(2022,9,26,21) to datetime(2022,9,26,22) with var_type
        # # = 'dict'.
        # self.sample_dictionary_data = {
        #     'peak_direction': np.array([134.375, 134.875]),
        #     'longitude': np.array([-83.82427979, -83.82427979]),
        #     'b1': np.array([
        #         [0.1 , -0.1 , -0.01, -0.04, -0.02, -0.1 , -0.2 ,  0.11, -0.13,
        #          -0.2 , -0.18, -0.1 , -0.08, -0.11, -0.12, -0.06,  0.09,  0.07,
        #          0.21,  0.3 ,  0.23,  0.33,  0.41,  0.12,  0.27,  0.24,  0.15,
        #          0.25,  0.13,  0.23,  0.1 ,  0.23,  0.28,  0.15,  0.04,  0.13,
        #          0.13,  0.09, -0.15, -0.02,  0.09, -0.05],
        #         [0.08,  0.03, -0.03, -0.13, -0.1 ,  0.06, -0.14, -0.06,  0.02,
        #          0.02,  0.04,  0.12,  0.28,  0.  ,  0.12,  0.32,  0.19,  0.38,
        #          0.47,  0.56,  0.52,  0.44,  0.52,  0.41,  0.32,  0.38,  0.37,
        #          0.49,  0.26,  0.45,  0.29,  0.46,  0.38,  0.37,  0.31,  0.38,
        #          0.47,  0.41,  0.45,  0.41,  0.32,  0.43]
        #         ]),
        #     'u_mean': np.array([None, None]),
        #     'peak_period': np.array([3.73632812, 3.73632812]),
        #     'check': np.array([
        #         [2.4, 11. , 25.5, 22.3, 24. , 16.4, 15.1, 15.6, 21.2, 13.7, 18.1,
        #          15.3,  7.1,  5.7,  6.4,  4.1,  5.1,  5.4,  3.3,  2.7,  1.8,  2.6,
        #          2.7,  2.6,  2. ,  2.5,  2.6,  2.6,  3.2,  1.4,  3.6,  1.4,  2.4,
        #          1.8,  1.6,  1.9,  2.4,  2.6,  1.6,  1.5,  1.4,  2.5],
        #         [0. ,  0.1,  0.2,  0.1,  0.1,  0.1,  0.1,  0.2,  0.1,  0.1,  0.2,
        #          0.1,  0.2,  0.2,  0.2,  0.3,  0.3,  0.4,  0.5,  0.4,  0.5,  0.6,
        #          0.6,  0.6,  0.4,  0.5,  0.5,  0.6,  0.5,  0.6,  0.4,  0.5,  0.5,
        #          0.6,  0.3,  0.2,  0.3,  0.4,  0.5,  0.2,  0.3,  0.5]
        #         ]),
        #     'temperature': np.array([0., 0.]),
        #     'datetime': np.array([
        #         datetime(2022, 9, 26, 21, 41, 20, tzinfo=timezone.utc),
        #         datetime(2022, 9, 26, 21, 41, 20, tzinfo=timezone.utc)
        #         ]),
        #     'a1': np.array([
        #         [-0.11,  0.03,  0.04, -0.07,  0.05,  0.14,  0.25, -0.04,  0.19,
        #          0.19,  0.02,  0.08,  0.09,  0.04, -0.03,  0.  ,  0.03,  0.01,
        #          -0.16, -0.28, -0.22, -0.35, -0.42, -0.31, -0.18, -0.18, -0.26,
        #          -0.22, -0.19, -0.23, -0.13, -0.04, -0.12, -0.14,  0.05, -0.1 ,
        #          -0.14, -0.02,  0.08,  0.1 , -0.04,  0.08],
        #         [-0.19, -0.06, -0.07,  0.08, -0.01,  0.05, -0.04, -0.07, -0.02,
        #          -0.08, -0.14, -0.19, -0.39, -0.11, -0.37, -0.26, -0.37, -0.38,
        #          -0.45, -0.55, -0.42, -0.43, -0.52, -0.51, -0.39, -0.37, -0.42,
        #          -0.42, -0.38, -0.47, -0.3 , -0.41, -0.45, -0.47, -0.26, -0.36,
        #          -0.32, -0.39, -0.34, -0.25, -0.32, -0.24]
        #         ]),
        #     'significant_height': np.array([2.43164062, 0.91650391]),
        #     'latitude': np.array([26.19651985, 26.19651985]),
        #     'salinity': np.array([0., 0.]),
        #     'b2': np.array([
        #         [-0.26, -0.03, -0.2 , -0.1 , -0.22, -0.27, -0.15, -0.11, -0.08,
        #          -0.2 , -0.09,  0.02, -0.47, -0.19, -0.18, -0.42, -0.21, -0.27,
        #          -0.61, -0.71, -0.53, -0.42, -0.58, -0.39, -0.19, -0.29, -0.22,
        #          -0.32, -0.15, -0.36, -0.23, -0.41, -0.27, -0.36, -0.15, -0.23,
        #          -0.23, -0.29, -0.3 , -0.29, -0.03, -0.16],
        #         [-0.24,  0.06, -0.22, -0.1 , -0.23, -0.26, -0.16, -0.11, -0.07,
        #          -0.21, -0.13,  0.  , -0.5 , -0.14, -0.19, -0.43, -0.18, -0.29,
        #          -0.62, -0.71, -0.56, -0.45, -0.56, -0.39, -0.22, -0.29, -0.21,
        #          -0.35, -0.17, -0.35, -0.17, -0.41, -0.26, -0.37, -0.16, -0.23,
        #          -0.25, -0.3 , -0.3 , -0.29, -0.03, -0.15]
        #         ]),
        #     'a2': np.array([
        #         [-0.33, -0.11,  0.14, -0.04, -0.03, -0.13, -0.1 , -0.24,  0.28,
        #          -0.15, -0.03,  0.17, -0.02, -0.01, -0.02, -0.15,  0.14, -0.16,
        #          -0.08, -0.03, -0.29,  0.01, -0.07,  0.02, -0.2 , -0.28,  0.01,
        #          -0.14, -0.02,  0.04, -0.09,  0.05,  0.06,  0.04,  0.  , -0.03,
        #          -0.03,  0.01, -0.08, -0.01, -0.03,  0.04],
        #         [ 0.07,  0.  ,  0.15, -0.06, -0.02, -0.14, -0.12, -0.27,  0.25,
        #          -0.09, -0.04,  0.15, -0.05, -0.03, -0.02, -0.14,  0.15, -0.17,
        #          -0.08, -0.03, -0.29,  0.01, -0.09,  0.  , -0.2 , -0.28,  0.  ,
        #          -0.13, -0.01,  0.02, -0.05,  0.  ,  0.06,  0.01,  0.05,  0.  ,
        #          -0.01,  0.  , -0.1 ,  0.01, -0.04,  0.03]]),
        #     'voltage': np.array([0., 1.]),
        #     'sensor_type': np.array([52, 52]),
        #     'energy_density': np.array([
        #         [0.04992676, 0.58105469, 2.63476562, 3.390625  , 3.80664062,
        #          3.75195312, 3.58789062, 3.078125  , 3.86328125, 3.00585938,
        #          2.3125    , 2.03125   , 0.8671875 , 0.55175781, 0.57226562,
        #          0.31054688, 0.33251953, 0.38989258, 0.27685547, 0.33056641,
        #          0.22412109, 0.27929688, 0.32739258, 0.2109375 , 0.14111328,
        #          0.11859131, 0.12054443, 0.11486816, 0.10961914, 0.0501709 ,
        #          0.0914917 , 0.04434204, 0.06414795, 0.04150391, 0.03863525,
        #          0.04629517, 0.05792236, 0.05090332, 0.0256958 , 0.03022766,
        #          0.02279663, 0.0262146 ],
        #         [0.        , 0.        , 0.        , 0.        , 0.36962891,
        #          0.58984375, 0.50341797, 0.33666992, 0.24499512, 0.26049805,
        #          0.1418457 , 0.13793945, 0.13305664, 0.0949707 , 0.08721924,
        #          0.07489014, 0.06591797, 0.07305908, 0.08312988, 0.12890625,
        #          0.13171387, 0.11724854, 0.1239624 , 0.08288574, 0.07470703,
        #          0.0486145 , 0.04595947, 0.04507446, 0.03485107, 0.03594971,
        #          0.02735901, 0.03369141, 0.02764893, 0.02488708, 0.02560425,
        #          0.0255127 , 0.02476501, 0.02027893, 0.01643372, 0.02157593,
        #          0.01753235, 0.01135254]
        #         ]),
        #     'frequency': np.array([
        #         [0.00976562, 0.02148438, 0.03320312, 0.04492188, 0.05664062,
        #          0.06835938, 0.08007812, 0.09179688, 0.10351562, 0.11523438,
        #          0.12695312, 0.13867188, 0.15039062, 0.16210938, 0.17382812,
        #          0.18554688, 0.19726562, 0.20898438, 0.22070312, 0.23242188,
        #          0.24414062, 0.25585938, 0.26757812, 0.27929688, 0.29101562,
        #          0.30273438, 0.31445312, 0.32617188, 0.33789062, 0.34960938,
        #          0.36132812, 0.37304688, 0.38476562, 0.39648438, 0.40820312,
        #          0.41992188, 0.43164062, 0.44335938, 0.45507812, 0.46679688,
        #          0.47851562, 0.49023438],
        #         [0.00976562, 0.02148438, 0.03320312, 0.04492188, 0.05664062,
        #          0.06835938, 0.08007812, 0.09179688, 0.10351562, 0.11523438,
        #          0.12695312, 0.13867188, 0.15039062, 0.16210938, 0.17382812,
        #          0.18554688, 0.19726562, 0.20898438, 0.22070312, 0.23242188,
        #          0.24414062, 0.25585938, 0.26757812, 0.27929688, 0.29101562,
        #          0.30273438, 0.31445312, 0.32617188, 0.33789062, 0.34960938,
        #          0.36132812, 0.37304688, 0.38476562, 0.39648438, 0.40820312,
        #          0.41992188, 0.43164062, 0.44335938, 0.45507812, 0.46679688,
        #          0.47851562, 0.49023438]]),
        #     'z_mean': np.array([None, None]),
        #     'v_mean': np.array([None, None])
        # }