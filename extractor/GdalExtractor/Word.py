import io
import os
from io import BytesIO

import boto3
from docx import Document 
#import textract

class WordExtractor:
    def __init__(self, uri, log):
        self.log = log 
        self.uri = uri
        self.xml_uri = self.uri.lstrip('s3://')
        self.extractor_version = '1.0'

    def extract(self):
        self.log.info('WordExtractor(%s)' % self.uri)
        bucket = self.xml_uri.split('/')[0]
        key = self.xml_uri.lstrip(bucket).lstrip('/')

        extractor_info = {
            'ExtractorType': 'wordExtractor',
            'ExtractorVersion': self.extractor_version,
            'FileUri': self.uri,
            'Bucket': bucket,
            'Key': key
        }

        s3client = boto3.client(
            's3',
#Hayley            
            region_name='us-east-1',                          
            # endpoint_url='http://s3.amazonaws.com',
            config=boto3.session.Config(signature_version='s3v4')
        )

        obj = s3client.get_object(
            Bucket=bucket,
            Key=key
        )
        
        # would like iterate through a list 
        # list = [author, category, comments]
        # prop = doc.core_properties
        # metadata = {}
        # for i in list:
        #     metadata.append(metadata[str = list] = prop.list)
        # return metadata

        #Using python-docx library pull all metadata and put in metadata dictionary
        doc = Document(io.BytesIO(obj['Body'].read()))

        metadata = {}
        prop = doc.core_properties
        metadata["author"] = prop.author
        metadata["category"] = prop.category
        metadata["comments"] = prop.comments
        metadata["content status"] = prop.content_status
        metadata["created"] = prop.created
        metadata["identifier"] = prop.identifier
        metadata["keywords"] = prop.keywords
        metadata["language"] = prop.language
        metadata["modified modified by"] = prop.last_modified_by
        metadata["last printed"] = prop.last_printed
        metadata["modified"] = prop.modified
        metadata["revision"] = prop.revision
        metadata["subject"] = prop.subject
        metadata["title"] = prop.title
        metadata["version"] = prop.version

        #content_dict = {}
        #content = { docx2txt.process(doc): contend_dict }

    
        resp = {}
        resp['metadata'] = metadata
        #resp['page content'] = content_dict
        resp['extractor_info'] = extractor_info

        return resp

        



       
        