## Retrieval of National Hydrological Data (NHD) ##
# Currently requires retrieval of raw geodatabase from online repository
# This script clips out the Flowline and Waterbody data for specified study area

import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

##### Inputs ######
arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
SA = "Tonto_study_area.shp" # Polygon defining study landscape #
# Note: this is currently set to draw from local geodatabase.
    # Will eventually need to setup a repository on the T drive or figure out how to download data directly from NHD web service
source = "NHD\\NHD_H_Arizona_GDB.gdb\\Hydrography\\"
###################

Rivers = source + "NHDFlowline"
arcpy.Clip_analysis(in_features = Rivers, clip_features = SA, out_feature_class = "rivers.shp")

Lakes = source + "NHDWaterbody"
arcpy.Clip_analysis(in_features = Lakes, clip_features = SA, out_feature_class = "lakes.shp")
