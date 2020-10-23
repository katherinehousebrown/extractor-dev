import logging

from . import ArcticDEM, AToc, Generic, Nitf, Pdf, Word, Excel


def factory(uri, log):
    log.error(uri)
    l_uri = uri.lower()
    if '.ntf' in l_uri or '.nitf' in l_uri:
        return Nitf.NitfExtractor(uri, log)
    elif l_uri.endswith('/a.toc'):
        log.debug('factory: returning AToc.ATocExtractor')
        return AToc.ATocExtractor(uri, log)
    elif l_uri.endswith('.pdf'):
        log.debug('factory: returning Pdf.pdfExtractor')
        return Pdf.pdfExtractor(uri, log)
    elif l_uri.endswith('.xlsx') or l_uri.endswith('.xlsm') or l_uri.endswith('.xls') or l_uri.endswith('.csv'):
        return Excel.SpreadsheetExtractor(uri, log)
    elif l_uri.endswith('.doc') or l_uri.endswith('.docx'):
        log.debug('factory: returning Word.WordExtractor')  
        return Word.WordExtractor(uri, log)
    elif l_uri.endswith('arcticps_nga_dsm_3m_01_meta.xml') or l_uri.endswith('arcticps_nga_dsm_12m_01_meta.xml'):
        return ArcticDEM.ArcticDEMExtractor(uri, log)

    return Generic.GdalExtractor(uri, log)



def gdal_config(config):
    try:
        from osgeo import gdal, ogr
        gdal.SetConfigOption('AWS_REGION', config['AR'])
        gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config['ASAK'])
        gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config['AKID'])
        gdal.SetConfigOption('AWS_S3_ENDPOINT', config['AS3EP'])
        gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'YES')
        gdal.SetConfigOption('GDAL_HTTP_UNSAFESSL', 'YES')
        gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
        gdal.SetConfigOption('GDAL_HTTP_USERAGENT ', 'ods.extractor')

        return gdal.__version__
    except ImportError:
        return None
