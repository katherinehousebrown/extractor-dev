import io
import json
import logging
import os
import re
from io import BytesIO

import boto3
import xmltodict
from flask import Blueprint, Flask, abort, jsonify, make_response, request
from PyPDF2 import PdfFileReader


class pdfExtractor:
    def __init__(self, uri, log):
        self.uri = uri  
        self.xml_uri = self.uri.lstrip('s3://')
        self.extractor_version = '1.0'
        self.log = log
    
    # this turns the byte string into a regular string, and then cleans up its format for readbility by removing new lines and returns
    def parseKeywords(self, byteString):
        parsedByteString = byteString.decode("utf-8")
        return list(filter(None, parsedByteString.replace("\r","").replace("\n", ";").replace("; ", ";").split(';')))

    def extract(self):
        app = Flask(__name__)
        app.config.from_pyfile('/extractor/env.cfg')
        self.log.debug("Pdf extractor")
        self.log.info('pdfExtractor(%s)' % self.uri)

        bucket = self.xml_uri.split('/')[0]
        key = self.xml_uri.lstrip(bucket).lstrip('/')

        s3client = boto3.client(
            's3',
            region_name=app.config['AR'],
            # endpoint_url='http://s3.amazonaws.com',
            config=boto3.session.Config(signature_version='s3v4')
        )
        obj = s3client.get_object(
            Bucket=bucket,
            Key=key
        )

        extractorInfo = {
            'ExtractorVersion': self.extractor_version,
            'ExtractorType' : 'pdf',
            'FileUri': self.uri,
            'Bucket': bucket,
            'Key': key
        }

        numberOfPagesToReturn = 20
        
        data = obj['Body'].read()
        pdf = PdfFileReader(BytesIO(data))
        info = pdf.getDocumentInfo()
        # parse info into json object to capture all present metadata, the info response adds a leading / so this was removed for
        # readability the replace call should be able to be removed if necessary, appears to be a function of getDocumentInfo, 
        # not the underlying PDF 
        jsonStr = json.dumps(info, default=lambda o: o.__dict__).replace('"/', '"')
        metadata = {}
        #this either grabs all present metadata, or defaults to null if none present 
        if (info is not None):
            metadata = eval(jsonStr)
            if '/Keywords' in info:
                #for some reason the keywords info comes back as a byte string which needs special handling to convert to json
               metadata['Keywords'] = self.parseKeywords(info['/Keywords'])
        else:
            metadata = {}

        # builds separate object for page information and content
        dicts = {}
        keys = range(pdf.getNumPages())
        for x in keys:
            if (x > numberOfPagesToReturn):
                break
            tempText = pdf.getPage(x).extractText()
            tempText = ' '.join(tempText.split())
            dicts[x] = tempText
        pageContent = {'page_content': dicts}
        pageContent['num_pages'] = pdf.getNumPages()

        #builds complete response object 
        resp = {}
        resp['metadata'] = metadata
        resp['page content'] = pageContent
        resp['extractorInfo'] = extractorInfo

        return resp
