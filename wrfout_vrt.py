import os, sys


from osgeo import gdal, osr

gauges = [
 "13235000",
 "14158500",
 "13237920",
 "13240000",
 "13250600",
 "13288200",
 "13296500",
 "13308500",
 "13309220",
 "13310199",
 "13310700",
 "13313000",
 "13329500",
 "13331500",
 "13334450",
 "13334700",
 "13337000",
 "13338500",
 "13339500",
 "05014300",
 "13340000",
 "13340500",
 "13340600",
 "14010000",
 "14013500",
 "14020000",
 "14020300",
 "14036860",
 "14037500",
 "14046890",
 "14053000",
 "14054500",
 "14090350",
 "14090400",
 "14092750",
 "14092885",
 "14095500",
 "14096300",
 "14096850",
 "14101500",
 "14107000",
 "14121300",
 "14127000",
 "14128500",
 "14134000",
 "14136500",
 "14137000",
 "14138800",
 "14138870",
 "14138900",
 "14139700",
 "14139800",
 "14141500",
 "14144800",
 "14144900",
 "14146500",
 "14147500",
 "14150300",
 "14150800",
 "14152500",
 "14154500",
 "14156500",
 "14158790",
 "14159200",
 "14161100",
 "14161500",
 "14163000",
 "14166500",
 "14179000",
 "14180300",
 "14181750",
 "14181900",
 "14182500",
 "14185000",
 "14185900",
 "14187000",
 "14189500",
 "14193000",
 "14194300",
 "14197000",
 "14198400",
 "14198500",
 "14199704",
 "14208000",
 "14216000",
 "14216500",
 "14219000",
 "14219800",
 "14222500",
 "14231000",
 "14232500",
 "14235500",
 "14236200",
 "14237000",
 "14243500",
 "14245000",
 "14247500",
 "14249000",
 "14250500",
 "14299800",
 "14301000",
 "14301500",
 "14303200",
 "14305500",
 "14306100",
 "14306340",
 "14306400",
 "14306500",
 "14307580",
 "14307620",
 "14316495",
 "14316700",
 "14318000",
 "12010000",
 "14319830",
 "12013500",
 "14319835",
 "12017000",
 "14320934",
 "12020000",
 "14324500",
 "12020800",
 "12024000",
 "12025000",
 "12025700",
 "12032500",
 "12035000",
 "12035450",
 "12039000",
 "12039005",
 "12039300",
 "12040500",
 "06073500",
 "12041200",
 "06078500",
 "12041500",
 "06079000",
 "12043000",
 "12043300",
 "06092500",
 "12044900",
 "06102500",
 "12048000",
 "12050500",
 "12054000",
 "12056500",
 "12060500",
 "12065500",
 "12068500",
 "12073500",
 "12079000",
 "12082500",
 "12083000",
 "12092000",
 "12094000",
 "12095000",
 "12096500",
 "12097000",
 "12097500",
 "12097850",
 "12104000",
 "12105000",
 "12108500",
 "12114000",
 "12114500",
 "12115000",
 "12115500",
 "12115700",
 "12117000",
 "12135000",
 "12137290",
 "12141300",
 "12142000",
 "12143400",
 "12143600",
 "12144000",
 "12145500",
 "12147000",
 "12147500",
 "12147600",
 "12157250",
 "12161000",
 "12167000",
 "12168500",
 "12175500",
 "12177500",
 "12178100",
 "12179900",
 "12182500",
 "12186000",
 "12189500",
 "12196000",
 "12201500",
 "12201960",
 "12202300",
 "12202310",
 "12206900",
 "12207750",
 "12207850",
 "12209000",
 "12209490",
 "12209500",
 "12210000",
 "12210700",
 "12303100",
 "12305500",
 "12323670",
 "12323710",
 "12332000",
 "12347500",
 "12354000",
 "12358500",
 "12359800",
 "12361000",
 "12369200",
 "12374250",
 "12375900",
 "12377150",
 "12381400",
 "12383500",
 "12387450",
 "12388400",
 "12390700",
 "12392155",
 "12392300",
 "12411000",
 "12413000",
 "12413360",
 "12413875",
 "12414500",
 "12416000",
 "12433542",
 "12439300",
 "12447383",
 "12447390",
 "12448000",
 "12448500",
 "12451000",
 "12452800",
 "12452890",
 "12454000",
 "12456500",
 "12458000",
 "12483800",
 "12488500",
 "12500500",
 "12501000",
 "13185000",
 "13196500",
 "13200500",
 "13216500",
]
sql = "GAGE_ID IN("
for i, g in enumerate(gauges):
    sql += "'{}'".format(g)
    if i < len(gauges)-1:
        sql += ","

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

drv = gdal.GetDriverByName("VRT")
for sds in ds.GetSubDatasets():
    tag, file, var = sds[0].split(":")
    ds = gdal.Open(sds[0])
    vrt = drv.CreateCopy("/vsimem/{}.vrt".format(var), ds)
    vrt.SetProjection(wkt)
    vrt.SetGeoTransform(gt)
    vds = drv.CreateCopy("{}.vrt".format(var), vrt)
    vds = None

ds = None
