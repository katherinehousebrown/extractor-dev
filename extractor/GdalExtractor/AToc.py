import logging

import boto3

from extractor.GdalExtractor import wrapper
from osgeo import gdal, ogr, osr


class ATocExtractor(object):
    def __init__(self, uri, log):
        self.uri = uri
        self.log = log
        self.xml_uri = self.uri.lstrip('s3://')
        self.extractor_version = '1.3'

    def extract(self):
        # log = logging.getLogger('extractor_run')
        # log.setLevel(logging.DEBUG)
        self.log.debug("Atoc extractor")

        resp = {
            'ExtractorVersion': self.extractor_version,
            'ExtractorType': 'atoc',
            'FileUri': self.uri
        }

        self.log.info('a.tocExtractor(%s)' % self.uri)

        bucket = self.xml_uri.split('/')[0]
        key = self.xml_uri.lstrip(bucket).lstrip('/')

        temp_filename = '/tmp/toc_file'
        s3 = boto3.resource('s3', region_name='us-east-1')
        s3.meta.client.download_file(bucket, key, temp_filename)

        wrap = wrapper.ParseFile(self.log)
        self.log.debug('after wrapper instantiation')
        wrapper_response = wrap.parse(temp_filename)
        if wrapper_response is None:
            return None

        resp['Bucket'] = bucket
        resp['Key'] = key
        resp['OverlayList'] = wrapper_response['ovrFiles']
        resp['FrameList'] = wrapper_response['frameFiles']

        return resp

    def build_info(self, extractor_response):
        # log = logging.getLogger('build_info')
        self.log.debug("build_info")

        return {
            'ExtractorType': extractor_response['ExtractorType'],
            'ExtractorVersion': extractor_response['ExtractorVersion'],
            # TODO return something for next condtioner
            # 'FootprintWKT': extractor_response['FootprintWKT']
        }
