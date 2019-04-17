/*
** This is free and unencumbered software released into the public domain.
**
** Anyone is free to copy, modify, publish, use, compile, sell, or
** distribute this software, either in source code form or as a compiled
** binary, for any purpose, commercial or non-commercial, and by any
** means.
**
** In jurisdictions that recognize copyright laws, the author or authors
** of this software dedicate any and all copyright interest in the
** software to the public domain. We make this dedication for the benefit
** of the public at large and to the detriment of our heirs and
** successors. We intend this dedication to be an overt act of
** relinquishment in perpetuity of all present and future rights to this
** software under copyright law.
**
** THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
** EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
** MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
** IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
** OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
** ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
** OTHER DEALINGS IN THE SOFTWARE.
**
** For more information, please refer to <http://unlicense.org>
*/

#include "cpl_string.h"
#include "gdal.h"
#include "ogr_srs_api.h"

const char *apszDrivers[] = {"netCDF", NULL};

/*
** The Lambert Conformal Conic with 2 standard parallels for wrfout files.  The
** order of the metadata items for the %lf calls is:
** NC_GLOBAL#STAND_LON
** NC_GLOBAL#MOAD_CEN_LAT
** NC_GLOBAL#TRUELAT1
** NC_GLOBAL#TRUELAT2
*/
const char *pszWrfLCC =
    "PROJCS[\"WGC 84 / WRF Lambert\","
    "   GEOGCS[\"WGS 84\","
    "       DATUM[\"World Geodetic System 1984\","
    "           SPHEROID[\"WGS 84\",6378137.0,298.257223563,"
    "               AUTHORITY[\"EPSG\",\"7030\"]],"
    "           AUTHORITY[\"EPSG\",\"6326\"]],"
    "       PRIMEM[\"Greenwich\",0.0,"
    "       AUTHORITY[\"EPSG\",\"8901\"]],"
    "       UNIT[\"degree\",0.017453292519943295],"
    "       AXIS[\"Geodetic longitude\",EAST],"
    "       AXIS[\"Geodetic latitude\",NORTH],"
    "       AUTHORITY[\"EPSG\",\"4326\"]],"
    "   PROJECTION[\"Lambert_Conformal_Conic_2SP\"],"
    "   PARAMETER[\"central_meridian\",%s],"
    "   PARAMETER[\"latitude_of_origin\",%s],"
    "   PARAMETER[\"standard_parallel_1\",%s],"
    "   PARAMETER[\"false_easting\",0.0],"
    "   PARAMETER[\"false_northing\",0.0],"
    "   PARAMETER[\"standard_parallel_2\",%s],"
    "   UNIT[\"m\",1.0],"
    "   AXIS[\"Easting\",EAST],"
    "   AXIS[\"Northing\",NORTH]]";

const char *pszWrfMercator = "PROJCS[\"World_Mercator\","
                            "GEOGCS[\"GCS_WGS_1984\","
                            "DATUM[\"WGS_1984\","
                            "SPHEROID[\"WGS_1984\",6378137,298.257223563]],"
                            "PRIMEM[\"Greenwich\",0],"
                            "UNIT[\"Degree\",0.017453292519943295]],"
                            "PROJECTION[\"Mercator_1SP\"],"
                            "PARAMETER[\"False_Easting\",0],"
                            "PARAMETER[\"False_Northing\",0],"
                            "PARAMETER[\"Central_Meridian\",%s],"
                            "PARAMETER[\"latitude_of_origin\",%s],"
                              "UNIT[\"Meter\",1]]";

const char *apszRequiredMetadata[] = {
    "NC_GLOBAL#STAND_LON", "NC_GLOBAL#MOAD_CEN_LAT",
    "NC_GLOBAL#TRUELAT1",  "NC_GLOBAL#TRUELAT2",
    "NC_GLOBAL#CEN_LON",   "NC_GLOBAL#CEN_LAT",
    "NC_GLOBAL#DX",        "NC_GLOBAL#DY",
    "NC_GLOBAL#MAP_PROJ",  NULL};

int main(int argc, char *argv[]) {
  const char *pszWrf = NULL;
  const char *pszOut = NULL;
  const char *pszFrmt = "GTiff";
  const char *pszMapProj = NULL;
  GDALDatasetH hWrfDS, hOutDS;
  GDALDriverH hDrv = NULL;
  char *pszWkt = NULL;
  OGRSpatialReferenceH hSrcSRS, hTargetSRS;
  OGRCoordinateTransformationH hCT = NULL;
  char **papszSubDatasets = NULL;
  const char *pszMetadata;
  int nXSize, nYSize;
  double dfX, dfY;
  double dfDeltaX, dfDeltaY;
  double adfGeoTransform[6];
  int rc = 0;
  int i = 1;
  while (i < argc) {
    if (EQUAL(argv[i], "-of") && i < argc - 2) {
      pszFrmt = argv[++i];
    } else if (pszWrf == NULL) {
      pszWrf = argv[i];
    } else if (pszOut == NULL) {
      pszOut = argv[i];
    }
    i++;
  }
  if (pszWrf == NULL) {
    fprintf(stderr, "no wrf subdataset provided\n");
    exit(1);
  }
  if (pszWrf == NULL) {
    fprintf(stderr, "no output subdataset provided\n");
    exit(1);
  }

  GDALAllRegister();

  hDrv = GDALGetDriverByName(pszFrmt);
  if (hDrv == NULL) {
    fprintf(stderr, "invalid output format");
    exit(1);
  }

  hWrfDS = GDALOpenEx(pszWrf, GDAL_OF_RASTER | GDAL_OF_READONLY, apszDrivers,
                      NULL, NULL);
  if (hWrfDS == NULL) {
    exit(1);
  }
  papszSubDatasets = GDALGetMetadata(hWrfDS, "SUBDATASETS");
  if (CSLCount(papszSubDatasets) > 0) {
    fprintf(stderr, "please specify a subdataset\n");
    exit(1);
  }

  for (i = 0; apszRequiredMetadata[i] != NULL; i++) {
    pszMetadata = GDALGetMetadataItem(hWrfDS, apszRequiredMetadata[i], NULL);
    if (pszMetadata == NULL) {
      fprintf(stderr, "failed to get required metadata: %s\n",
              apszRequiredMetadata[i]);
      exit(1);
    }
  }
  pszMapProj = GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#MAP_PROJ", NULL);
  if (EQUALN(pszMapProj, "1", 1)) {
    pszWkt = CPLStrdup(CPLSPrintf(
        pszWrfLCC, GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#STAND_LON", NULL),
        GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#MOAD_CEN_LAT", NULL),
        GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#TRUELAT1", NULL),
        GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#TRUELAT2", NULL)));
  } else if(EQUALN(pszMapProj, "3", 1)) {
    pszWkt = CPLStrdup(CPLSPrintf(
        pszWrfMercator,
        GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#STAND_LON", NULL),
        GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#MOAD_CEN_LAT", NULL)));
    } else {
    fprintf(stderr, "invalid projection: %s", pszMapProj);
    exit(2);
			}
    hTargetSRS = OSRNewSpatialReference(pszWkt);
    if (hTargetSRS == NULL) {
    CPLFree(pszWkt);
    GDALClose(hWrfDS);
    fprintf(stderr, "failed to create target spatial reference");
    exit(1);
    }

    hSrcSRS = OSRNewSpatialReference(NULL);
    OSRImportFromEPSG(hSrcSRS, 4326);

    hCT = OCTNewCoordinateTransformation(hSrcSRS, hTargetSRS);
    if (hCT == NULL) {
    CPLFree(pszWkt);
    GDALClose(hWrfDS);
    OSRDestroySpatialReference(hSrcSRS);
    OSRDestroySpatialReference(hTargetSRS);
    fprintf(stderr, "failed to created coordinate tranform\n");
    exit(1);
    }

    dfX = CPLAtof(GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#CEN_LON", NULL));
    dfY = CPLAtof(GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#CEN_LAT", NULL));

    rc = OCTTransform(hCT, 1, &dfX, &dfY, NULL);
    OSRDestroySpatialReference(hSrcSRS);
    OSRDestroySpatialReference(hTargetSRS);
    OCTDestroyCoordinateTransformation(hCT);
    if (rc == 0) {
    CPLFree(pszWkt);
    GDALClose(hWrfDS);
    fprintf(stderr, "failed to transform coordinates\n");
    exit(1);
    }

    dfDeltaX = CPLAtof(GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#DX", NULL));
    dfDeltaY = CPLAtof(GDALGetMetadataItem(hWrfDS, "NC_GLOBAL#DY", NULL));
    nXSize = GDALGetRasterXSize(hWrfDS);
    nYSize = GDALGetRasterYSize(hWrfDS);
    adfGeoTransform[0] = dfX - ((nXSize / 2) * dfDeltaX);
    adfGeoTransform[1] = dfDeltaX;
    adfGeoTransform[2] = 0.0;
    adfGeoTransform[3] = dfY + ((nYSize / 2) * dfDeltaY);
    adfGeoTransform[4] = 0.0;
    adfGeoTransform[5] = -dfDeltaY;

    /* Shift 1/2 pixel.  Unkown if needed */
    /*
    adfGeoTransform[0] -= dfDeltaX / 2.0;
    adfGeoTransform[3] += dfDeltaY / 2.0;
    */

    hOutDS = GDALCreateCopy(hDrv, pszOut, hWrfDS, FALSE, NULL, GDALTermProgress,
                            NULL);
    if (hOutDS == NULL) {
    CPLFree(pszWkt);
    GDALClose(hWrfDS);
    fprintf(stderr, "failed to created target dataset\n");
    exit(1);
    }
    GDALSetProjection(hOutDS, pszWkt);
    GDALSetGeoTransform(hOutDS, adfGeoTransform);
    GDALClose(hWrfDS);
    GDALClose(hOutDS);
    CPLFree(pszWkt);
    return 0;
}
