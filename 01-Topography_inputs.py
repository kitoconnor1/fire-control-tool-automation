import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

##### Set inputs ##########
arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
SA = u'Tonto_study_area.shp' # Polygon defining study landscape #
###########################

arcpy.env.overwriteOutput = True

# Mask downloaded DEM to study area #
DEM = ExtractByMask(r'LFdata/US_DEM2010/us_dem2010', SA)
DEM.save("dem.tif")
DEM = Raster('dem.tif')

if not os.path.isdir("BRTinputs"):
    os.makedirs("BRTinputs")

arcpy.gp.Slope_sa(DEM, "BRTinputs/slope.tif", "PERCENT_RISE", "1") # slope input
arcpy.gp.Aspect_sa(DEM, "BRTinputs/aspect.tif") # topographic aspect

###################### Topographic position input ####################################
DEM_200 = arcpy.gp.FocalStatistics_sa("DEM.tif", "DEM_200m.tif", "Circle 200 MAP", "MEAN", "NODATA") # 200m neighborhood DEM mean
tpi = DEM - DEM_200
slope = arcpy.gp.Slope_sa(DEM, "slope_deg.tif", "DEGREE", "1") # slope input
steep = Raster(slope) > 6
tpi_1 = tpi < (-12)
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save("BRTinputs/Dist_canyon.tif")
del(tpi_1, tpi_dist)

tpi_1 = ((tpi <= 12) & (tpi >= (-12))) * (1 - steep)
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save("BRTinputs/Dist_flat.tif")
del(tpi_1, tpi_dist)

tpi_1 = ((tpi <= 12) & (tpi >= (-12))) * steep
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save("BRTinputs/Dist_steep.tif")
del(tpi_1, tpi_dist)

tpi_1 = tpi > 12
tpi_1 = Reclassify(tpi_1, "Value", RemapValue([[0, "NODATA"], [1, 1]]))
tpi_dist = EucDistance(tpi_1, cell_size = 30)
tpi_dist = ExtractByMask(tpi_dist, SA)
tpi_dist.save("BRTinputs/Dist_ridge.tif")
del(tpi_1, tpi_dist)

arcpy.Delete_management("slope_deg.tif")
arcpy.Delete_management("DEM_200m.tif")
del(steep, tpi, slope, DEM_200)
######################################################################################
