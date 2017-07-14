import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
SA = "Tonto_study_area.shp" # Polygon defining study landscape #
source = "T:\\FS\\RD\\RMRS\\Science\\HD\\MySpace\\Oconnor\\NorthAmerica_SDC\\Navteq_Q32011\\"

Roads = source + "mroads.sdc/mroads"
arcpy.Clip_analysis(in_features = Roads, clip_features = SA, out_feature_class = "roads.shp")

Streets = source + "streets.sdc\\streets"
arcpy.Clip_analysis(in_features = Streets, clip_features = SA, out_feature_class = "streets.shp")
