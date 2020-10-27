import io
import os
import json
from io import BytesIO

import boto3
from docx import Document


class WordExtractor:
    def __init__(self, uri, log):
        self.log = log
        self.uri = uri
        self.word_uri = self.uri.lstrip('s3://')
        self.extractor_version = '1.0'

    def extract(self):
        self.log.info('WordExtractor(%s)' % self.uri)
        bucket = self.word_uri.split('/')[0]
        key = self.word_uri.lstrip(bucket).lstrip('/')

        extractor_info = {
            'ExtractorType': 'word_extractor',
            'ExtractorVersion': self.extractor_version,
            'FileUri': self.uri,
            'Bucket': bucket,
            'Key': key
        }

        s3client = boto3.client(
            's3',
            region_name=os.environ.get('AWS_REG'),
            # endpoint_url='http://s3.amazonaws.com',
            config=boto3.session.Config(signature_version='s3v4')
        )

        obj = s3client.get_object(
            Bucket=bucket,
            Key=key
        )

        # Using python-docx library pull all metadata and put in metadata dictionary
        doc = Document(io.BytesIO(obj['Body'].read()))
        metadata = {}
        
        for attr in dir(doc.core_properties):
            if not attr.startswith('_'):
                metadata[attr] = getattr(doc.core_properties, attr)

        # Merge extractor info and metadata dictionaries        
        resp = { **extractor_info, **metadata }            
       
        return  json.loads(json.dumps(resp, default=str))

    def build_info(self, extractor_response):
        self.log.debug('word doc extractor build_info')

        return {
            #extractor_response = {}
            'ExtractorType': extractor_response['ExtractorType'],
            'ExtractorVersion': extractor_response['ExtractorVersion'],
        }
