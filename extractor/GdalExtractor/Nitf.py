# Standard Python
import json
import logging

# osgeo import
from osgeo import gdal, osr

# application imports
from . import Generic


class NitfExtractor (Generic.GdalExtractor):
    type = 'nitf'
    jpeg2000 = False

    def __init__(self, uri, log):
        super(NitfExtractor, self).__init__(uri, log)
        # check to see if we have the OpenJPEG driver
        if gdal.GetDriverByName('JP2OpenJPEG'):
            gdal.SetConfigOption('NITF_OPEN_UNDERLYING_DS', 'YES')
            self.jpeg2000 = True
        else:
            gdal.SetConfigOption('NITF_OPEN_UNDERLYING_DS', 'NO')
            self.jpeg2000 = False

    def extract(self):
        # log = logging.getLogger('extractor_run')
        # log.setLevel(logging.DEBUG)
        self.log.debug("Nitf extractor")
        resp = {
            'ExtractorVersion': self.version(),
            'ExtractorType': 'nitf',
            'FileUri': self.uri
        }

        self.log.info('NitfExtractor(%s)' % self.uri)
        if not self.jpeg2000:
            self.log.warning("Unable to find JPEG2000 driver, will not attempt to access underlying J2K codestream")

        # TODO: Performance testing to determine optimal chunk size
        gdal.SetConfigOption('CPL_VSIL_CURL_CHUNK_SIZE', '65536')
        nitf = gdal.Open(self.gdal_uri)

        if nitf is None:
            self.log.error('Error reading NITF file %s' % self.gdal_uri)
            return None

        ncols = nitf.RasterXSize
        nrows = nitf.RasterYSize
        nbands = nitf.RasterCount

        proj = nitf.GetProjection()

        self.log.debug('cols: %d rows: %d bands: %d projection: %s'
                  % (ncols, nrows, nbands, proj))

        gcp = nitf.GetGCPs()
        transform = nitf.GetGeoTransform()
        footprint = self.footprint_from_transform(nrows, ncols, transform)

        resp['NativeFootprintWKT'] = footprint.ExportToWkt()
        resp['NativeProjection'] = proj

        if proj is None or proj == '':
            self.log.debug('No projection present')
            # this is most likely an un-ortho'd image try to get the footprint from GCPs
            if len(gcp) == 4:
                self.log.debug('gcp == 4')
                footprint = self.footprint_from_gcp(gcp[0], gcp[1], gcp[2], gcp[3])

        else:
            self.log.debug('Has Projection')
            native_crs = osr.SpatialReference()
            native_crs.ImportFromWkt(proj)

            epsg4326_crs = osr.SpatialReference()
            epsg4326_crs.ImportFromEPSG(4326)
            footprint.Transform(osr.CoordinateTransformation(native_crs, epsg4326_crs))
            if 'UTM zone' in proj:
                self.log.debug('UTM zone in projection')
                resp['UTMZone'] = self.utm_getZonePretty(native_crs)
            else:
                self.log.debug('UTM zone NOT in projection')
                centroid = footprint.Centroid()
                self.log.debug(centroid)
                # resp['UTMZone'] = self.utm_getZone(centroid.GetX(), centroid.GetY())
                resp['UTMZone'] = self.utm_getZone(centroid)

        if footprint is None:
            self.log.error('Unable to extract footprint for %s' % self.uri)
            resp['FootprintWKT'] = ''
            resp['FootprintJSON'] = ''
        else:
            self.log.debug('Image: %s - Footprint: %s'
                      % (self.uri, footprint.ExportToWkt()))
            resp['FootprintWKT'] = footprint.ExportToWkt()
            resp['FootprintJSON'] = json.loads(footprint.ExportToJson())
            self.log.debug('footprint befor UTM zone else')
            resp['UTMZone'] =  self.utm_getZone(footprint)

        metadata = {'dataset': self.parse_metadata(nitf)}

        subdatasets = nitf.GetSubDatasets()

        if subdatasets is not None:
            for i in range(len(subdatasets)):
                key = ('subdataset%02d' % i)
                sds = gdal.Open(subdatasets[i][0])
                metadata[key] = self.parse_metadata(sds)
                sds = None

        resp['Metadata'] = metadata
        resp['DerivedNITFClass'] = metadata['dataset']['default']['NITF_FSCLAS']

        nitf = None

        # resp['GdalInfoOutput'] = self.gdalinfo()
        resp['ExtractionDT'] = self.now()
        return resp
