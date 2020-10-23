# flask imports
import logging
# standard python
import os
import time

from flask import Flask, Blueprint, make_response, jsonify, request
from flask_restplus import Resource, Api, Namespace

# application
from . import GdalExtractor

DEFAULT_CONFIG = {
    'FLASK_DEBUG': False,
    'PORT': 8080,
    'AR': 'us-west-2',
    'AS3EP': 's3.amazonaws.com',
    'ASAK': None,
    'AKID': None,
    'HAILSTORM_BUCKET': 'NOT AVAILABLE',
    'LOG_LEVEL': 'INFO'
}


def to_bool(value):
    if isinstance(value, str):
        if value.lower() in ('f', 'false', 'n', 'no', '0'):
            return False
        else:
            return True
    elif isinstance(value, int):
        return bool(value)
    else:
        return bool(value)


def configure(config, override_config):
    log = logging.getLogger('extractor_run')

    config.update(DEFAULT_CONFIG)
    config_file = os.environ.get('EXTRACTOR_CONFIG_FILE', 'env.cfg')

    try:
        log.info("Loading configuration from '%s'" % config_file)
        config.from_pyfile(config_file)
    except IOError:
        log.warning("Unable to find config file '%s'" % config_file)

    # Override config with environment variables
    flask_debug = os.environ.get("FLASK_DEBUG")
    if flask_debug is not None:
        config['FLASK_DEBUG'] = to_bool(flask_debug)

    port = os.environ.get("PORT", 8080)
    if port is not None:
        config['PORT'] = int(port)

    aws_region = os.environ.get('AR')
    if aws_region is not None:
        config['AR'] = aws_region

    s3_endpoint = os.environ.get('AS3EP')
    if s3_endpoint is not None:
        config['AS3EP'] = s3_endpoint

    aws_secret_key = os.environ.get('ASAK')
    if aws_secret_key is not None:
        config['ASAK'] = aws_secret_key

    aws_key_id = os.environ.get('AKID')
    if aws_key_id is not None:
        config['AKID'] = aws_key_id

    hailstorm_bucket = os.environ.get('HAILSTORM_BUCKET')
    if hailstorm_bucket is not None:
        config['HAILSTORM_BUCKET'] = hailstorm_bucket

    loglevel = os.environ.get('LOG_LEVEL')
    if loglevel is not None:
        config['LOG_LEVEL'] = str(loglevel).upper()

    if override_config is not None:
        config.update(override_config)


def create_app(config=None):
    app = Flask(__name__)

    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s %(name)s:%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z')
    logging.Formatter.converter = time.gmtime

    log = logging.getLogger('extractor_run')
    log.addFilter(logging.Filter('extractor_run'))

    configure(app.config, config)

    log.setLevel(logging.getLevelName(app.config['LOG_LEVEL']))

    gdal_version = GdalExtractor.gdal_config(app.config)
    if gdal_version is None:
        log.error('Unable to load GDAL')
        return None

    log.info('Found GDAL Version %s' % gdal_version)

    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api = Api(blueprint, doc='/swagger/')
    app.register_blueprint(blueprint)
    app.config['SWAGGER_UI_JSONEDITOR'] = True

    extractor_api = Namespace('extractor')
    api.add_namespace(extractor_api)

    @extractor_api.route('/health')
    class HealthCheckService(Resource):
        def get(self):
            """
            Health Check
            This endpoint will return the Health of the Service.
            ---
            """
            return make_response(jsonify({'Status': 'Oh I, oh, I\'m still alive!'}), 200)

    parser = api.parser()
    parser.add_argument('file_uri', help='fileuri', location='args')
    parser.add_argument('fingerprint', help='fingerprint', location='args')
    parser.add_argument('version', help='version', location='args')

    @extractor_api.route('/extract')
    class ExtractAPIService(Resource):
        # decorators = [jsonp, jwt_user, event_logging]
        @api.expect(parser)
        def get(self):
            """
            Geospatial Extent Extraction (and additional metadata)
            This endpoint extracts the metadata associated with a given fileUri and fingerprint.
            ---
            """
            fileuri = request.args.get('file_uri')
            fingerprint = request.args.get('fingerprint')
            version = request.args.get('version')
            log.info("file_uri %s - fingerprint: %s - version: %s",
                     fileuri, fingerprint, version)

            if fileuri is None:
                log.warning('Missing required request parameter file_uri')
                return make_response(jsonify({'Bad Request': 'file_uri was not provided'}), 400)
            if fingerprint is None:
                return make_response(jsonify({'Bad Request': 'fingerprint was not provided'}), 400)

            extractor = GdalExtractor.factory(fileuri, log)

            resp = extractor.extract()

            if resp is None:
                return make_response(jsonify({'Unsupported Object-type': 'No Metadata Found'}), 204)
            else:

                return make_response(jsonify(resp))

    @app.route('/extractor')
    def base():
        return "This is the root for the conditioning service!"

    @app.route('/extractor/batch')
    def proc_batch():
        return "This a stub for batch processing!"

    @app.after_request
    def apply_caching(response):
        response.headers["server"] = "ipf.extractor"
        # response.headers["X-Message Of The Day"] = (
        #     "Every normal man must be tempted, at times, to spit on his hands, "
        #     "hoist the black flag, and begin slitting throats")
        response.headers["X-PoweredBy"] = "A Bunch of Fools"
        return response

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    return app
