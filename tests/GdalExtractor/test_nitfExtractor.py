# Python imports
import json
import unittest

import extractor
# Application imports
from extractor.GdalExtractor import Nitf

GDAL_CONFIG = {
    'LOGLEVEL': 'DEBUG'
}


class TestNitfExtractor(unittest.TestCase):
    def test_extract(self):
        test_uri = (
            "s3://img-cm-o2/16694632/NCL00000/Original/00000150/FVEY/UNC/"
            "NL_5100000_13JAN10WV011100010JAN13144213-P1BS-052062683010_05_P004_________AAE_0AAAAABIABE0.NTF")

        nitf_extractor = Nitf.NitfExtractor(test_uri)

        resp = nitf_extractor.extract()
        self.assertIsNotNone(resp)
        print(json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')))

    def setUp(self):
        extractor.create_app(GDAL_CONFIG)


if __name__ == '__main__':
    unittest.main()
