import datetime
import json
import pytz
from osgeo import gdal, ogr, osr


class GdalExtractor(object):
    def __init__(self, uri, log):
        self.uri = uri
        self.log = log
        self.gdal_uri = '/vsis3/' + self.uri.lstrip('s3://')
        self.extractor_version = '1.3'

    @staticmethod
    def utm_getZonePretty(crs):
        zone = crs.GetUTMZone()
        if zone >= 0:
            zone = str(zone) + 'N'
        else:
            zone = str(-zone) + 'S'

        return zone

    @staticmethod
    def utm_getZone(geom):
        centroid = geom.Centroid()
        zone = int(1 + (centroid.GetX() + 180.0) / 6.0)
        if centroid.GetY() >= 0:
            zone = str(zone) + 'N'
        else:
            zone = str(zone) + 'S'

        return zone

    @staticmethod
    def now():
        return datetime.datetime.now(pytz.timezone('UTC')).isoformat()

    def version(self):
        return self.extractor_version

    def gdalinfo(self):
        self.log.warning(
            "Shell call to 'gdalinfo', can we just pull the values of interest out in python to prevent "
            "fetching the data from s3 twice?")
        os_cmd = "gdalinfo -json --config AWS_ACCESS_KEY_ID '%s'" % gdal.GetConfigOption('AWS_ACCESS_KEY_ID') \
            + " --config AWS_SECRET_ACCESS_KEY '%s'" % gdal.GetConfigOption('AWS_SECRET_ACCESS_KEY') \
            + " --config NITF_OPEN_UNDERLYING_DS NO %s" % self.gdal_uri

        # log.debug(f"GDALINFO IS: {os_cmd}")
        #raw_gdal_info = subprocess.check_output(os_cmd, shell=True)
        # gdalinfo bug on TC - need to override EP
        raw_gdal_info = "{}"
        return json.loads(raw_gdal_info)

    @staticmethod
    def footprint_from_transform(rows, cols, transform):
        # NOTE: Transform from image space (col, row) to Geo space Xp,Yp
        # Xp = padfTransform[0] + col * padfTransform[1] + row * padfTransform[2];
        # Yp = padfTransform[3] + col * padfTransform[4] + row * padfTransform[5];
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

        return footprint

    @staticmethod
    def footprint_from_gcp(ul, ur, lr, ll):
        footprint_ring = ogr.Geometry(ogr.wkbLinearRing)

        # Upper Left
        footprint_ring.AddPoint(ul.GCPX, ul.GCPY)
        # Lower Left
        footprint_ring.AddPoint(ll.GCPX, ll.GCPY)
        # Lower Right
        footprint_ring.AddPoint(lr.GCPX, lr.GCPY)
        # Upper Right
        footprint_ring.AddPoint(ur.GCPX, ur.GCPY)
        # Upper Left
        footprint_ring.AddPoint(ul.GCPX, ul.GCPY)

        footprint = ogr.Geometry(ogr.wkbPolygon)
        footprint.AddGeometry(footprint_ring)

        return footprint

    @staticmethod
    def parse_metadata(dataset):
        metadata = {}
        metadata_domains = dataset.GetMetadataDomainList()

        for domain in metadata_domains:
            if domain == '':
                metadata['default'] = dataset.GetMetadata(domain)
            else:
                metadata[domain] = dataset.GetMetadata(domain)

        return metadata

    def extract(self):
        self.log.debug("Generic extractor")

        resp = {
            'ExtractorVersion': self.version(),
            'ExtractorType' : 'generic',
            'FileUri': self.uri
        }

        self.log.info('GenericExtractor(%s)' % self.uri)

        # TODO: Performance testing to determine optimal chunk size
        gdal.SetConfigOption('CPL_VSIL_CURL_CHUNK_SIZE ', '65536')
        dataset = gdal.Open(self.gdal_uri)

        if dataset is None:
            self.log.error('Error reading object file %s' % self.gdal_uri)
            return None

        ncols = dataset.RasterXSize
        nrows = dataset.RasterYSize
        nbands = dataset.RasterCount

        proj = dataset.GetProjection()

        self.log.debug('cols: %d rows: %d bands: %d projection: %s'
                  % (ncols, nrows, nbands, proj))

        transform = dataset.GetGeoTransform()
        footprint = self.footprint_from_transform(nrows, ncols, transform)

        resp['NativeFootprintWKT'] = footprint.ExportToWkt()
        resp['NativeProjection'] = proj

        if proj is not None and proj != '':
            native_crs = osr.SpatialReference()
            native_crs.ImportFromWkt(proj)

            epsg4326_crs = osr.SpatialReference()
            epsg4326_crs.ImportFromEPSG(4326)
            footprint.Transform(osr.CoordinateTransformation(native_crs, epsg4326_crs))
            if 'UTM zone' in proj:
                resp['UTMZone'] = self.utm_getZonePretty(native_crs)
            else:
                resp['UTMZone'] = self.utm_getZone(footprint)

        else:
            self.log.warning("Unable to determine projection of dataset %s" % self.uri)

        self.log.debug('Image: %s - Footprint: %s'
                  % (self.uri, footprint.ExportToWkt()))

        metadata = {'dataset': self.parse_metadata(dataset)}

        subdatasets = dataset.GetSubDatasets()

        if subdatasets is not None:
            for i in range(len(subdatasets)):
                key = ('subdataset%02d' % i)
                sds = gdal.Open(subdatasets[i][0])
                metadata[key] = self.parse_metadata(sds)
                sds = None

        classification = ''

        dataset = None

        #resp['GdalInfoOutput'] = self.gdalinfo()
        resp['Metadata'] = metadata
        resp['DerivedNITFClass'] = classification
        resp['FootprintWKT'] = footprint.ExportToWkt()
        # TODO WTH was for elastic
        resp['FootprintJSON'] = json.loads(footprint.ExportToJson())
        resp['ExtractionDT'] = self.now()
        return resp

    def build_info(self, extractor_response):
        self.log.debug("build_info")

        return {
            'ExtractorType': extractor_response['ExtractorType'],
            'ExtractorVersion': extractor_response['ExtractorVersion'],
            'FootprintWKT': extractor_response['FootprintWKT']
        }
