##### Clips street layer from NAVTEQ source file for use in various inputs #####

import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

######################### Inputs #################################
arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
SA = "Tonto_study_area.shp" # Polygon defining study landscape #
source = "T:\\FS\\RD\\RMRS\\Science\\HD\\MySpace\\Oconnor\\NorthAmerica_SDC\\Navteq_Q32011\\"
##################################################################

SA_WGS = arcpy.Project_management(in_dataset = SA, out_dataset = "SA_WGS.shp", out_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]")
Streets = source + "streets.sdc\\streets"
streets_WGS = arcpy.Clip_analysis(in_features = Streets, clip_features = SA_WGS, out_feature_class = "streets_WGS.shp")
arcpy.Project_management(in_dataset = streets_WGS, out_dataset = "streets.shp", out_coor_system="GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]")
arcpy.Delete_management(streets_WGS)
arcpy.Delete_management(SA_WGS)
