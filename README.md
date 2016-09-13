# wrfout_translate
Translate specific subdatasets in wrfout files to GDAL supported rasters.

wrfout files are missing some geotransform data that needs to be derived from
header data.  It is not CF compliant, so the normal GDAL driver doesn't handle
them correctly.  This tool sets the missing data in the geotransform so it can
be viewed in a GIS.

