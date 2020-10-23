# Python imports
import json
import unittest

import extractor
# Application imports
from extractor.GdalExtractor import ArcticDEM

GDAL_CONFIG = {
    'LOGLEVEL': 'DEBUG'
}


class TestArcticDEMExtractor(unittest.TestCase):
    def test_extract(self):
        test_uri = ''

        arcticDEM_extractor = ArcticDEM.ArcticDEMExtractor(test_uri)

        resp = arcticDEM_extractor.extract()
        self.assertIsNotNone(resp)
        print(json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')))

    def setUp(self):
        extractor.create_app(GDAL_CONFIG)


if __name__ == '__main__':
    unittest.main()
