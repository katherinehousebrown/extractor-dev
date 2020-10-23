import json
import logging
import os

import boto3
import xmltodict

# import pprint


class ArcticDEMExtractor:
    def __init__(self, uri, log):
        self.uri = uri
        self.log = log
        self.xml_uri = self.uri.lstrip('s3://')

    def extract(self):
        self.log.debug("Arctic extractor")
        self.log.info('ArcticDEMExtractor(%s)' % self.uri)

        bucket = self.xml_uri.split('/')[0]
        key = self.xml_uri.lstrip(bucket).lstrip('/')

        s3client = boto3.client(
            's3',
            region_name='us-east-1',
            # endpoint_url='http://s3.amazonaws.com',
            config=boto3.session.Config(signature_version='s3v4')
        )

        obj = s3client.get_object(
            Bucket=bucket,
            Key=key
        )

        data = obj['Body'].read().decode('utf-8')
        res = xmltodict.parse(data, encoding='utf-8')
        return res
