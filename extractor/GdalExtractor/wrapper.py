#! /usr/bin/env python3​

import argparse
import ctypes
import logging
import re
import string

_gdal = None

try:
    _gdal = ctypes.CDLL('libgdal.so')
except:
    pass

if _gdal is None:
    try:
        _gdal = ctypes.CDLL(
            '/Users/acurtis/workspace/gdal-osx/gdal-base/lib/libgdal.dylib')
    except:
        pass

if _gdal is None:
    print("Unable to load libgdal")
    exit(-1)


class RPFTocFrameEntry(ctypes.Structure):
    _fields_ = [
        ('exists', ctypes.c_int),
        ('fileExists', ctypes.c_int),
        ('frameRow', ctypes.c_ushort),
        ('frameCol', ctypes.c_ushort),
        ('directory', ctypes.c_char_p),
        ('filename', ctypes.c_char * 13),
        ('georef', ctypes.c_char * 7),
        ('fullFilePath', ctypes.c_char_p)
    ]

    def __repr__(self):
        return "Filename: %s" % self.filename


class RPFTocEntry(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_char * 6),
        ('compression', ctypes.c_char * 6),
        ('scale', ctypes.c_char * 13),
        ('zone', ctypes.c_char * 2),
        ('producer', ctypes.c_char * 6),
        ('nwLat', ctypes.c_double),
        ('nwLong', ctypes.c_double),
        ('swLat', ctypes.c_double),
        ('swLong', ctypes.c_double),
        ('neLat', ctypes.c_double),
        ('neLong', ctypes.c_double),
        ('seLat', ctypes.c_double),
        ('seLong', ctypes.c_double),
        ('vertResolution', ctypes.c_double),
        ('horizResolution', ctypes.c_double),
        ('vertInterval', ctypes.c_double),
        ('horizInterval', ctypes.c_double),
        ('nVertFrames', ctypes.c_uint),
        ('nHorizFrames', ctypes.c_uint),
        ('boundaryId', ctypes.c_int),
        ('isOverviewOrLegend', ctypes.c_int),
        ('seriesAbbreviation', ctypes.c_char_p),
        ('seriesName', ctypes.c_char_p),
        ('RPFTocFrameEntry', ctypes.POINTER(RPFTocFrameEntry))
    ]

    def __repr__(self):
        return "type: %s, frames: %d" % (self.type, self.nHorizFrames * self.nVertFrames)


class RPFToc(ctypes.Structure):
    _fields_ = [
        ("nEntries", ctypes.c_int),
        ("RPFTocEntry", ctypes.POINTER(RPFTocEntry))
    ]


# Function declarations
_gdal.NITFOpen.restype = ctypes.c_void_p
_gdal.NITFOpen.argtypes = [ctypes.c_char_p, ctypes.c_int]
_gdal.NITFClose.restype = None
_gdal.NITFClose.argtypes = [ctypes.c_void_p]
_gdal.RPFTOCRead.restype = ctypes.POINTER(RPFToc)
_gdal.RPFTOCRead.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
_gdal.RPFTOCFree.resType = None
_gdal.RPFTOCFree.argtypes = [ctypes.c_void_p]


class ParseFile:
    def __init__(self, log):
        self.log = log

    def parse(self, obj):
        try:
            self.log.debug('before cstrFile')
            cstrFile = ctypes.c_char_p(bytes(obj, 'utf8'))
            self.log.debug('before nitfFile')
            nitfFile = _gdal.NITFOpen(cstrFile, ctypes.c_int(0))
            self.log.debug('before RPFTOCRead')
            rpftoc = _gdal.RPFTOCRead(cstrFile, nitfFile)
            self.log.debug('after RPFTOCRead')

            # TODO: Does filename always match these patterns? Can we get more specific with letter v number?
            # .i41 files with directory (frame files)
            i41Regex = re.compile('[a-z0-9]{7}/[a-z0-9]{8}\\.i41$', re.IGNORECASE)
            # .orv files
            ovrRegex = re.compile('[a-z0-9]{8}\\.ovr$', re.IGNORECASE)
            frameFiles = []
            ovrFiles = []

            for tocIdx in range(rpftoc.contents.nEntries):
                tocEntry = rpftoc.contents.RPFTocEntry[tocIdx]
                for frmIdx in range(tocEntry.nHorizFrames * tocEntry.nVertFrames):
                    filePath = tocEntry.RPFTocFrameEntry[frmIdx].fullFilePath.decode(
                        'UTF-8')

                    i41 = re.search(i41Regex, filePath)
                    ovr = re.search(ovrRegex, filePath)
                    if (i41):
                        frameFiles.append(i41.group(0))
                    elif (ovr):
                        ovrFiles.append(ovr.group(0))
                    else:
                        self.log.error(
                            'File name found but does not match .ovr or .i41 patterns')
            resp = {
                'ovrFiles': ovrFiles,
                'frameFiles': frameFiles
            }
            _gdal.RPFTOCFree(rpftoc)
            _gdal.NITFClose(nitfFile)
            return resp
        except Exception as e:
            self.log.error('exception in atoc wrapper {0}'.format(e))
            return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("files", metavar='N', type=str, nargs='+',
                        help='list of files to try and parse')
    args = parser.parse_args()
    for f in args.files:
        cstrFile = ctypes.c_char_p(bytes(f, 'utf8'))
        print('cstrFile: {0}'.format(cstrFile.value))
        nitfFile = _gdal.NITFOpen(cstrFile, ctypes.c_int(0))

        rpftoc = _gdal.RPFTOCRead(cstrFile, nitfFile)
        print("Number of Entries: ", rpftoc.contents.nEntries)

        for tocIdx in range(rpftoc.contents.nEntries):
            print('before tocEntry')
            tocEntry = rpftoc.contents.RPFTocEntry[tocIdx]
            print("toc item: ", tocEntry)
            for frmIdx in range(tocEntry.nHorizFrames * tocEntry.nVertFrames):
                print("frame: ", tocEntry.RPFTocFrameEntry[frmIdx])

        _gdal.RPFTOCFree(rpftoc)
        _gdal.NITFClose(nitfFile)
