#-------------------------------------------------------------------------------
# Name:                Topographic inputs
#
# Schematic component: Physical landscape characteristics I: topography
#
# Purpose:             Generate the distance to major road and barrier input layers
#                      for BRT analysis
#
# Author:              Quresh Latif
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

# function(s)
def checkPath(path):
    try: os.makedirs(path)
    except: pass

##### Set inputs ##########
base = "E:/GISData/fire_control_modl_proj" # Set workspace #
arcpy.env.workspace = base
SA = u'Tonto_study_area.shp' # Polygon defining study landscape #
###########################

arcpy.env.overwriteOutput = True

# Mask downloaded DEM to study area #
DEM = ExtractByMask(r'LFdata/US_DEM2010/us_dem2010', SA)
DEM.save("dem.tif")
DEM = Raster('dem.tif')

out_dir = base + "/BRTinputs/"
checkPath(out_dir)

arcpy.gp.Slope_sa(DEM, out_dir + "slope.tif", "PERCENT_RISE", "1") # slope input
arcpy.gp.Aspect_sa(DEM, out_dir + "aspect.tif") # topographic aspect

###################### Topographic position input ####################################
DEM_200 = arcpy.gp.FocalStatistics_sa("DEM.tif", "DEM_200m.tif", "Circle 200 MAP", "MEAN", "NODATA") # 200m neighborhood DEM mean
tpi = DEM - DEM_200
slope = arcpy.gp.Slope_sa(DEM, "slope_deg.tif", "DEGREE", "1") # slope input
steep = Raster(slope) > 6
tpi_1 = tpi < (-12)
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save(out_dir + "Dist_canyon.tif")
del(tpi_1, tpi_dist)

tpi_1 = ((tpi <= 12) & (tpi >= (-12))) * (1 - steep)
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save(out_dir + "Dist_flat.tif")
del(tpi_1, tpi_dist)

tpi_1 = ((tpi <= 12) & (tpi >= (-12))) * steep
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save(out_dir + "Dist_steep.tif")
del(tpi_1, tpi_dist)

tpi_1 = tpi > 12
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save(out_dir + "Dist_ridge.tif")
del(tpi_1, tpi_dist)

arcpy.Delete_management("slope_deg.tif")
arcpy.Delete_management("DEM_200m.tif")
del(steep, tpi, slope, DEM_200)
######################################################################################
