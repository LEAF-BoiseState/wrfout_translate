#!/usr/bin/env python
# Copyright (c) 2018, Boise State University All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.import os, sys

import os, sys
from osgeo import gdal, osr

# The Lambert Conformal Conic with 2 standard parallels for wrfout files.  The
# order of the metadata items for the %lf calls is:
# NC_GLOBAL#STAND_LON
# NC_GLOBAL#MOAD_CEN_LAT
# NC_GLOBAL#TRUELAT1
# NC_GLOBAL#TRUELAT2
wrf_wkt = '''
PROJCS["WGC 84 / WRF Lambert",
   GEOGCS["WGS 84",
       DATUM["World Geodetic System 1984",
           SPHEROID["WGS 84",6378137.0,298.257223563,
               AUTHORITY["EPSG","7030"]],
           AUTHORITY["EPSG","6326"]],
       PRIMEM["Greenwich",0.0,
       AUTHORITY["EPSG","8901"]],
       UNIT["degree",0.017453292519943295],
       AXIS["Geodetic longitude",EAST],
       AXIS["Geodetic latitude",NORTH],
       AUTHORITY["EPSG","4326"]],
   PROJECTION["Lambert_Conformal_Conic_2SP"],
   PARAMETER["central_meridian",{}],
   PARAMETER["latitude_of_origin",{}],
   PARAMETER["standard_parallel_1",{}],
   PARAMETER["false_easting",0.0],
   PARAMETER["false_northing",0.0],
   PARAMETER["standard_parallel_2",{}],
   UNIT["m",1.0],
   AXIS["Easting",EAST],
   AXIS["Northing",NORTH]];
'''

req_meta = ["NC_GLOBAL#STAND_LON",
            "NC_GLOBAL#MOAD_CEN_LAT",
            "NC_GLOBAL#TRUELAT1",
            "NC_GLOBAL#TRUELAT2",
            "NC_GLOBAL#CEN_LON",
            "NC_GLOBAL#CEN_LAT",
            "NC_GLOBAL#DX",
            "NC_GLOBAL#DY",
           ]

# Supress PAM generation
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

ncdf = None
fmt = "wkt"

argv = gdal.GeneralCmdLineProcessor(sys.argv)
if argv is None:
    sys.exit(0)

# Parse command line arguments.
i = 1
while i < len(argv):
    arg = argv[i]
    if arg == '-f':
        i += 1
        fmt = sys.argv[i]
    elif ncdf is None:
        ncdf = sys.argv[i]
    i += 1

ds = gdal.Open(ncdf)
if ds is None:
    os.exit(1)

# Make sure all the required metadata exists
for md in req_meta:
    mdi = ds.GetMetadataItem(md)
    if md is None:
        print("missing required metadata: %s", md)
        os.Exit(1)

wkt = wrf_wkt.format(ds.GetMetadataItem("NC_GLOBAL#STAND_LON"),
                     ds.GetMetadataItem("NC_GLOBAL#MOAD_CEN_LAT"),
                     ds.GetMetadataItem("NC_GLOBAL#TRUELAT1"),
                     ds.GetMetadataItem("NC_GLOBAL#TRUELAT2"))

wrf_srs = osr.SpatialReference(wkt)
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
ct = osr.CoordinateTransformation(srs, wrf_srs)

x = float(ds.GetMetadataItem("NC_GLOBAL#CEN_LON"))
y = float(ds.GetMetadataItem("NC_GLOBAL#CEN_LAT"))

x, y, z = ct.TransformPoint(x, y)

dx = float(ds.GetMetadataItem("NC_GLOBAL#DX"))
dy =  float(ds.GetMetadataItem("NC_GLOBAL#DY"))
nx = ds.RasterXSize
ny = ds.RasterYSize
gt = [x - ((nx / 2) * dx), dx, 0.0, dy + ((ny / 2) * dy), 0.0,  -dy]
# Shift 1/2 pixel.  Unkown if needed
gt[0] -= dx / 2.0;
gt[3] -= dy / 2.0;

if fmt == "wkt":
    print(wkt)
elif fmt == "proj":
    print(wrf_srs.ExportToProj4())
else:
    print("invalid output format: %s" % fmt)
    os.exit(1)

