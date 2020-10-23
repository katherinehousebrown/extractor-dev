#!flask/bin/python
# flask imports
from flask import Flask, make_response, abort, jsonify, request, Blueprint
from flask_restplus import Resource, Api, Namespace, fields
# standard python
import argparse
import glob
import datetime
import logging
import os.path
import pytz
import subprocess
import jsbeautifier
# osgeo
from osgeo import gdal
from osgeo import ogr

# END OF IMPORTS
app = Flask(__name__)
# blueprint = Blueprint('api', __name__, url_prefix='/api')
# api = Api(blueprint, doc='/swagger/')
# app.register_blueprint(blueprint)
# app.config['SWAGGER_UI_JSONEDITOR'] = True
#
# extractor_api = Namespace('extractor')
# api.add_namespace(extractor_api)


app.config.from_pyfile('/app/env.cfg')

gdal.SetConfigOption('AWS_S3_ENDPOINT', app.config['AS3EP'])
gdal.SetConfigOption('AWS_REGION', app.config['AR'])
gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', app.config['ASAK'])
gdal.SetConfigOption('AWS_ACCESS_KEY_ID', app.config['AKID'])
gdal.SetConfigOption('AWS_S3_ENDPOINT', app.config['AS3EP'])
gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'YES')
gdal.SetConfigOption('GDAL_HTTP_UNSAFESSL', 'YES')
gdal.SetConfigOption('CPL_CURL_VERBOSE', 'YES')

# DTED0
#fileuri = "s3://ele-gv-o2/16694069/SFN00000/dted0/dted00/dted/e000/n05.dt0"
# GeoEye
#fileuri = "s3://img-cm-o2/16740167/NCL00000/Original/00004950/FVEY/UNC/NL_5940000_08JUN10OV05010005V100608P0005673694B222000100872M_000516079_____AAE_0AAAAAEEABQ0.ntf"
# TERRAFORM_v4
#fileuri = "s3://ele-gv-o2/16753568/SFN00000/TERRAFORM/TERRAFORM_v4/e000_n045_e060_n090/e000/n45/e000n45_TFRM.dt2"
# WV
fileuri = "s3://img-cm-o2/16694632/NCL00000/Original/00000150/FVEY/UNC/NL_5100000_13JAN10WV011100010JAN13144213-P1BS-052062683010_05_P004_________AAE_0AAAAABIABE0.NTF"

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s %(name)s:%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %Z')

log = logging.getLogger('imagemosaic_load')
log.addFilter(logging.Filter('imagemosaic_load'))

str = fileuri.lstrip('s3://')
print str
granule = "/vsis3/" + str
print granule

if app.config['HAILSTORM_BUCKET'] in fileuri:
    gdal.SetConfigOption('NITF_OPEN_UNDERLYING_DS', 'NO')
    granule = "/vsis3_streaming/" + str
    osCmd='gdalinfo -json --config AWS_ACCESS_KEY_ID ' + app.config['AKID'] + ' --config AWS_SECRET_ACCESS_KEY ' + app.config['ASAK'] + ' --config NITF_OPEN_UNDERLYING_DS NO ' + granule
elif  '16740167' in fileuri: #GEOEYE ContentID
    gdal.SetConfigOption('NITF_OPEN_UNDERLYING_DS', 'NO')
    granule = "/vsis3/" + str
    osCmd='gdalinfo -json --config AWS_ACCESS_KEY_ID ' + app.config['AKID'] + ' --config AWS_SECRET_ACCESS_KEY ' + app.config['ASAK'] + ' --config NITF_OPEN_UNDERLYING_DS NO ' + granule
else:
    granule = "/vsis3/" + str
    osCmd='gdalinfo -json --config AWS_ACCESS_KEY_ID ' + app.config['AKID'] + ' --config AWS_SECRET_ACCESS_KEY ' + app.config['ASAK'] + ' ' + granule


log.info("GDALINFO IS:         %s", osCmd)
log.info("granule %s", granule)

rawGdalInfo = subprocess.check_output(osCmd, shell=True)
#convert json returned from gdal to a python dictionary so we don't do double encoding in jsonify
rawGdalInfo = json.loads(rawGdalInfo)
print rawGdalInfo

#rawGdalInfo = ' '.join(rawGdalInfo.split())
#rawGdalInfo =  rawGdalInfo.replace("\\", "")
#rawGdalInfo =  rawGdalInfo.replace("\"", '"')
#rawGdalInfo = jsbeautifier.beautify(rawGdalInfo)
#rawGdalInfo = rawGdalInfo.strip('\\"')
#print rawGdalInfo

img = gdal.Open(granule)
print img
# Get UTM Zone for HTRE
proj = img.GetProjection()
log.info("proj %s", proj)

        #If in UTM Zone make readable
if 'HRTE' or '16758538' in fileuri: #HRTE AND PLANET DATA
    utmzone = proj[26:29]
else:
    utmzone = proj

        # footPrint
transform = img.GetGeoTransform()
log.info("transform %s", transform)
cols = img.RasterXSize
rows = img.RasterYSize

footprint_ring = ogr.Geometry(ogr.wkbLinearRing)

        # Upper Left
footprint_ring.AddPoint(
    transform[0],
    transform[3])
        # Lower Left
footprint_ring.AddPoint(
    transform[0] + 0 * transform[1] + rows * transform[2],
    transform[3] + 0 * transform[4] + rows * transform[5])
        # Lower Right
footprint_ring.AddPoint(
    transform[0] + cols * transform[1] + rows * transform[2],
    transform[3] + cols * transform[4] + rows * transform[5])
        # Upper Right
footprint_ring.AddPoint(
    transform[0] + cols * transform[1] + 0 * transform[2],
    transform[3] + cols * transform[4] + 0 * transform[5])
        # Upper Left
footprint_ring.AddPoint(
    transform[0],
    transform[3])

footprint = ogr.Geometry(ogr.wkbPolygon)
footprint.AddGeometry(footprint_ring)

log.info("Image %s - Footprint: %s - fileuri %s", granule, footprint.ExportToWkt(), file)

metadata = img.GetMetadata()
classification = img.GetMetadataItem('NITF_FSCLAS')

now = datetime.datetime.now(pytz.timezone('UTC')).isoformat()
extractorVersion = '1.1'
fingerprint = 'none'
version = 'Test'

return make_response(jsonify({'ExtractionDT': now, 'ExtractorVersion': extractorVersion, 'DerivedNITFClass': classification, 'Footprint': footprint.ExportToWkt(), 'FileUri': fileuri, 'FingerPrint': fingerprint, 'UTMZone': utmzone, 'Metadata': metadata, 'Version': version, 'GdalInfoOutput': rawGdalInfo.replace("\\", "")}), 200)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', debug=True, port=80)