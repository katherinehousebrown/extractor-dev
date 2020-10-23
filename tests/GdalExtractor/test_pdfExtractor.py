# Python imports
import json
import unittest

import extractor
# Application imports
from extractor.GdalExtractor import Pdf

GDAL_CONFIG = {
    'LOG_LEVEL': 'DEBUG'
}


class TestPdfExtractor(unittest.TestCase):
    def test_extract(self):
        test_uri = (
            "s3://maw-gv-o1/16694153/SFN00000/GEOPOS/1999/VAFB-99-15/VAFB-99-15_46-60.pdf")
            
        pdf_extractor = Pdf.pdfExtractor(test_uri)

        resp = pdf_extractor.extract()
        self.assertIsNotNone(resp)
        print(json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')))

    def setUp(self):
        extractor.create_app(GDAL_CONFIG)


if __name__ == '__main__':
    unittest.main()
