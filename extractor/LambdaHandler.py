import fnmatch
import glob
import json
import logging
import os

import boto3
import requests

from osgeo import gdal

from . import GdalExtractor

log = logging.getLogger('lambda handler')
log_level = os.environ.get('LOG_LEVEL')
if log_level is not None:
    log.setLevel(log_level)
else:
    log.setLevel(logging.INFO)


def handler(event, context):
    handle_event(event, context)


def handle_event(event, context):
    log.info(event)
    gdal_config_lambda()

    try:
        records = event['Records']
        for record in records:
            message = json.loads(record['body'])
            process_message(message)

        return 1

    except Exception as inst:
        log.error("Error: {0}".format(inst))


def process_message(message):
    # TODO Add version update keys, bucket - s3key
    fileuri = "s3://" + message['bucket'] + "/" + message['s3Key']
    log.info(fileuri)

    extractor = GdalExtractor.factory(fileuri, log)
    log.debug('Extractor selected: {0}'.format(extractor))
    extract_info = extractor.extract()

    if extract_info is None:
        log.warning("No response returned")
        # TODO unsupported file types end up here - process info only or nothing?
        return

    create_extractinfo_in_c3po(message, extract_info, 'success')
    send_result_message(message, extractor.build_info(extract_info))

    log.info('Complete')


def create_extractinfo_in_c3po(message, extract_info, status):
    log.debug("c3po, guid: {}, url: {}".format(message['guid'], os.environ.get('C3PO_DNSNAME')))

    c3po_payload = {
        'rawHeader': extract_info
    }

    header = create_header(message, extract_info, status)

    # TODO http should be a param
    response = requests.put('http://' + os.environ.get('C3PO_DNSNAME') + '/c3po/extracts/' + message['guid'],
                            headers=header,
                            json=c3po_payload)
    log.debug("c3po response: %s" % response)


def send_result_message(incoming_message, extract):
    sqs_client = boto3.client('sqs', endpoint_url=os.environ.get('SQS_ENDPOINT'))

    if extract['ExtractorType'] == 'atoc':
        log.debug('Sending message to Product queue');
        queue_product_msg = sqs_client.send_message(
            QueueUrl=os.environ.get('PRODUCT_QUEUE'),
            MessageBody=json.dumps({
                'inventory': incoming_message,
                'extract': extract
            })
        )
        log.info("product queue send: %s" % queue_product_msg)

    log.debug('Sending message to extractor result queue');
    queue_extract_result = sqs_client.send_message(
        QueueUrl=os.environ.get('RESULT_QUEUE'),
        MessageBody=json.dumps({
            'inventory': incoming_message,
            'extract': extract
        })
    )
    log.info("result queue send: %s" % queue_extract_result)


def gdal_config_lambda():
    try:
        from osgeo import gdal, ogr
        gdal.SetConfigOption('AWS_REGION', os.environ.get('AWS_REGION'))
        gdal.SetConfigOption('AWS_SECRET_ACY_ID', os.environ.get('AWS_ACCESS_KEY_ID'))
        gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY'))

        gdal.SetConfigOption('AWS_S3_ENDPOINT', 's3.amazonaws.com')

        gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'YES')
        gdal.SetConfigOption('GDAL_HTTP_UNSAFESSL', 'YES')
        gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
        # TODO params for debug
        # gdal.SetConfigOption('CPL_DEBUG', 'ON')
        # gdal.SetConfigOption('CPL_LOG_ERRORS', 'ON')

        # gdal.SetConfigOption('CPL_CURL_VERBOSE', 'YES')

        return gdal.__version__
    except ImportError:
        return None


def create_header(message, extract_info, status):
    processInfo = {
        'inventoryId': message['inventoryId'],
        'processName': 'extractor',
        'version': extract_info['ExtractorVersion'],
        'status': status
    }
    header = {'x-processinfo': json.dumps(processInfo)}
    log.debug('header: {0}'.format(header))
    return header
