""" Testing of core knn functions """
import unittest
import microSWIFTtelemetry as telemetry

class TestMicroSWIFTtelemetry(unittest.TestCase):

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
