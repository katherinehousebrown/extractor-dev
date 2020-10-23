# Python imports
import unittest
import json

# Application imports
from extractor.GdalExtractor import Generic
import extractor

GDAL_CONFIG = {
    'LOGLEVEL': 'DEBUG'
}


class TestNitfExtractor(unittest.TestCase):
    def test_extract(self):
        test_uri = (
            "s3://ele-gv-o2/16694214/SFN00000/HRTE5/37N070E/373300N0701200E_20121101000000_BKEYE_100_QCS_00_0_UFO.tif")

        extractor = Generic.GdalExtractor(test_uri)

        resp = extractor.extract()
        self.assertIsNotNone(resp)
        print(json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')))

    def setUp(self):
        extractor.create_app(GDAL_CONFIG)


if __name__ == '__main__':
    unittest.main()
