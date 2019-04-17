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
wrf_wkt_lcc = '''
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

wrf_wkt_mercator = '''
PROJCS["World_Mercator",
   GEOGCS["GCS_WGS_1984",
      DATUM["WGS_1984",
         SPHEROID["WGS_1984",6378137,298.257223563]],
      PRIMEM["Greenwich",0],
      UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_1SP"],
      PARAMETER["False_Easting",0],
      PARAMETER["False_Northing",0],
      PARAMETER["Central_Meridian","{}"],
      PARAMETER["latitude_of_origin","{}"],
      UNIT["Meter",1]]
'''

req_meta = ["NC_GLOBAL#STAND_LON",
            "NC_GLOBAL#MOAD_CEN_LAT",
            "NC_GLOBAL#TRUELAT1",
            "NC_GLOBAL#TRUELAT2",
            "NC_GLOBAL#CEN_LON",
            "NC_GLOBAL#CEN_LAT",
            "NC_GLOBAL#DX",
            "NC_GLOBAL#DY",
            "NC_GLOBAL#MAP_PROJ",
           ]

gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
gdal.PushErrorHandler(None)

ds = gdal.Open(sys.argv[1])
if ds is None:
    os.exit(1)


for md in req_meta:
    mdi = ds.GetMetadataItem(md)
    if md is None:
        print("missing required metadata: %s", md)
        os.Exit(1)
proj = ds.GetMetadataItem("NC_GLOBAL#MAP_PROJ")

if proj is "1":
    wkt = wrf_wkt_lcc.format(ds.GetMetadataItem("NC_GLOBAL#STAND_LON"),
                         ds.GetMetadataItem("NC_GLOBAL#MOAD_CEN_LAT"),
                         ds.GetMetadataItem("NC_GLOBAL#TRUELAT1"),
                         ds.GetMetadataItem("NC_GLOBAL#TRUELAT2"))
elif proj is "3":
    wkt = wrf_wkt_mercator.format(ds.GetMetadataItem("NC_GLOBAL#STAND_LON"),
                                ds.GetMetadataItem("NC_GLOBAL#MOAD_CEN_LAT"))

wrf_srs = osr.SpatialReference(wkt)
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
ct = osr.CoordinateTransformation(srs, wrf_srs)

x = float(ds.GetMetadataItem("NC_GLOBAL#CEN_LON"))
y = float(ds.GetMetadataItem("NC_GLOBAL#CEN_LAT"))

x, y, z = ct.TransformPoint(x, y)

dx = float(ds.GetMetadataItem("NC_GLOBAL#DX"))
dy =  float(ds.GetMetadataItem("NC_GLOBAL#DY"))
sds = gdal.Open(ds.GetSubDatasets()[0][0])
if sds is None:
    print("invalid subdataset")
    os.Exit(1)
nx = sds.RasterXSize
ny = sds.RasterYSize
gt = [x - ((nx / 2) * dx), dx, 0.0, dy + ((ny / 2) * dy), 0.0,  -dy]
# Shift 1/2 pixel.  Unkown if needed
gt[0] -= dx / 2.0;
gt[3] -= dy / 2.0;

drv = gdal.GetDriverByName("VRT")
for sds in ds.GetSubDatasets():
    tag, file, var = sds[0].split(":")
    if var in ("Times", "XLAT", "XLONG"):
        continue
    ds = gdal.Open(sds[0])
    vrt = drv.CreateCopy("/vsimem/{}.vrt".format(var), ds)
    vrt.SetProjection(wkt)
    vrt.SetGeoTransform(gt)
    vds = drv.CreateCopy("{}.vrt".format(var), vrt)
    vds = None

ds = None
