import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
arcpy.env.overwriteOutput = True
DEM = "DEM.tif"

if not os.path.isdir("BRTinputs"):
    os.makedirs("BRTinputs")

arcpy.gp.Slope_sa("DEM.tif", "BRTinputs/slope.tif", "PERCENT_RISE", "1") # slope input
arcpy.gp.Aspect_sa("DEM.tif", "BRTinputs/aspect.tif") # topographic aspect

###################### Topographic position input ####################################
arcpy.gp.FocalStatistics_sa("DEM.tif", "DEM_200m.tif", "Circle 200 MAP", "MEAN", "NODATA") # 200m neighborhood DEM mean
tpi = Raster("DEM.tif") - Raster("DEM_200m.tif")
tpi.save("tpi.tif")
arcpy.gp.Slope_sa("DEM.tif", "slope_deg.tif", "DEGREE", "1") # slope input
steep = Raster("slope_deg.tif") > 6
steep.save("steep.tif")
tpi_1 = (Raster("tpi.tif") < (-12))
tpi_1.save("tpi_1.tif")
tpi_2 = ((Raster("tpi.tif") <= 12) & (Raster("tpi.tif") >= (-12))) * (1 - Raster("steep.tif")) * 2
tpi_2.save("tpi_2.tif")
tpi_3 = ((Raster("tpi.tif") <= 12) & (Raster("tpi.tif") >= (-12))) * Raster("steep.tif") * 3
tpi_3.save("tpi_3.tif")
tpi_4 = (Raster("tpi.tif") > 12)*4
tpi_4.save("tpi_4.tif")
tpi_class = Raster("tpi_1.tif") + Raster("tpi_2.tif") + Raster("tpi_3.tif") + Raster("tpi_4.tif")
tpi_class.save("BRTinputs/tpi_class.tif")

arcpy.Delete_management("steep.tif")
arcpy.Delete_management("slope_deg.tif")
arcpy.Delete_management("tpi.tif")
arcpy.Delete_management("tpi_1.tif")
arcpy.Delete_management("tpi_2.tif")
arcpy.Delete_management("tpi_3.tif")
arcpy.Delete_management("tpi_4.tif")
arcpy.Delete_management("DEM_200m.tif")
######################################################################################
