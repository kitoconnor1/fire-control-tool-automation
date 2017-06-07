####### Generates response variable for boosted regression tree from MTBS fire perimeter polygons ######

import os,urllib2,urllib
import arcpy
arcpy.CheckOutExtension("Spatial")

#################################### Inputs ###################################
arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
arcpy.env.extent = "dem.tif"
arcpy.env.snapRaster = "dem.tif"
arcpy.env.overwriteOutput = True
base_dir = 'E:/GISData/fire_control_modl_proj/' # for trying my own list
SA = "Tonto_study_area.shp" # Polygon defining study landscape #
###############################################################################

# Set up inputs (not working yet; download gets interrupted) #
#url = 'http://www.mtbs.gov/MTBS_Uploads/data/composite_data/burned_area_extent_shapefile/mtbs_perimeter_data.zip'
#urllib.urlretrieve(url, base_dir + "mtbs_perim_data.zip")

# Project source layer to NAD83 albers as necessary #
#arcpy.Project_management(in_dataset = base_dir + "mtbs/mtbs_perims_1984-2015_DD_20170501.shp", out_dataset = base_dir + "mtbs/mtbs_perims_n83alb.shp", out_coor_system="PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['false_easting',0.0],PARAMETER['false_northing',0.0],PARAMETER['central_meridian',-96.0],PARAMETER['standard_parallel_1',29.5],PARAMETER['standard_parallel_2',45.5],PARAMETER['latitude_of_origin',23.0],UNIT['Meter',1.0]]", preserve_shape="NO_PRESERVE_SHAPE")

# Extract perimeters completely contained within study area #
in_file = base_dir + "mtbs/mtbs_perims_n83alb.shp"
in_layer = "in_layer"
arcpy.MakeFeatureLayer_management(in_file, in_layer)

sel_file = "Tonto_study_area.shp" # Polygon defining study landscape #
sel_layer = "sel_layer"
arcpy.MakeFeatureLayer_management(sel_file, sel_layer)

arcpy.SelectLayerByLocation_management(in_layer, "COMPLETELY_WITHIN", sel_layer, "", "NEW_SELECTION") # Select DEM footprints that intersect study area
arcpy.FeatureClassToFeatureClass_conversion(in_layer, base_dir, 'fire_perims.shp')

# Convert perimeter shapefile to 0-1 raster #
arcpy.CalculateField_management(in_table = "fire_perims.shp", field = "Id", expression = "0")
arcpy.PolygonToRaster_conversion(in_features="fire_perims.shp", value_field = "Id", out_rasterdataset = "perims0.tif", cellsize="30")
arcpy.FeatureToLine_management(in_features="fire_perims.shp", out_feature_class = "fire_lines.shp", attributes="NO_ATTRIBUTES")
arcpy.Buffer_analysis(in_features="fire_lines.shp", out_feature_class="fire_lines_90m_buff.shp", buffer_distance_or_field="90 Meters", dissolve_option="ALL")
arcpy.CalculateField_management(in_table = "fire_lines_90m_buff.shp", field = "Id", expression = "1")
arcpy.PolygonToRaster_conversion(in_features = "fire_lines_90m_buff.shp", value_field = "Id", out_rasterdataset = "fire_lines.tif", cellsize="30")
arcpy.gp.Reclassify_sa("fire_lines.tif", "Value", "1 1;NODATA 0", "fire_lines_fill0.tif")
Obs = arcpy.Raster("fire_lines_fill0.tif") + arcpy.Raster("perims0.tif")
Obs.save("BRT_obs.tif")
arcpy.Delete_management("fire_lines.tif")
arcpy.Delete_management("fire_lines.shp")
arcpy.Delete_management("fire_lines_fill0.tif")
arcpy.Delete_management("fire_lines_90m_buffer.shp")
arcpy.Delete_management("perims0.tif")
