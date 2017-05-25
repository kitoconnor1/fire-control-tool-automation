import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
import os, sys

arcpy.env.workspace = r"E:\GISData\fire_control_modl_proj" # Set workspace #
NED_source = "T:\\FS\\Reference\\RSImagery\\ProcessedData\\wo_nfs_rsac\\NED\\NED_30m_Seamless_USA\\"

########### Get DEM for study landscape ###########################
in_file = NED_source + "_NED30M_Footprints.shp"
in_layer = "in_layer"
arcpy.MakeFeatureLayer_management(in_file, in_layer)

sel_file = "Tonto_study_area.shp" # Polygon defining study landscape #
sel_layer = "sel_layer"
arcpy.MakeFeatureLayer_management(sel_file, sel_layer)

arcpy.SelectLayerByLocation_management(in_layer, "INTERSECT", sel_layer, "", "NEW_SELECTION") # Select DEM footprints that intersect study area
paths = list() # Store paths for DEMs that intersect study area
with arcpy.da.SearchCursor(in_layer, ['PATHNAME']) as cursor:
    for row in cursor:
        p = str(row[0])
        p = p[62:len(p)]
        paths = paths + [p]

in_mosaic = ""
for i in range(0,len(paths)):
    arcpy.gp.ExtractByMask_sa(NED_source + paths[i], sel_layer, str(arcpy.env.workspace) + "/dem" + str(i) + "_sa.tif")
    in_mosaic = in_mosaic + ";" + str(arcpy.env.workspace) + "/dem" + str(i) + "_sa.tif"

in_mosaic = in_mosaic[1:len(in_mosaic)] # drop ';' at beginning
arcpy.MosaicToNewRaster_management(in_mosaic, output_location = str(arcpy.env.workspace), raster_dataset_name_with_extension = "DEM_n83gcs.tif", pixel_type="32_BIT_FLOAT", number_of_bands="1")
arcpy.ProjectRaster_management(in_raster = "DEM_n83gcs.tif", out_raster = "DEM.tif", out_coor_system = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['central_meridian',-96.0],PARAMETER['Standard_Parallel_1',29.5],PARAMETER['Standard_Parallel_2',45.5],PARAMETER['latitude_of_origin',23.0],UNIT['Meter',1.0]]", resampling_type="NEAREST", cell_size="30 30", geographic_transform="", Registration_Point="", in_coor_system="GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],VERTCS['Unknown VCS',VDATUM['Unknown'],PARAMETER['Vertical_Shift',0.0],PARAMETER['Direction',1.0],UNIT['Meter',1.0]]")
arcpy.Delete_management("DEM_n83gcs.tif")

for i in range(0, len(paths)):
    arcpy.Delete_management(str(arcpy.env.workspace) + "/dem" + str(i) + "_sa.tif")
#####################################################################
    

