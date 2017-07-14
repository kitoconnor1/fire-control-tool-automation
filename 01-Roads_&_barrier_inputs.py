#-------------------------------------------------------------------------------
# Name:                Distance to roads and barriers
#
# Schematic component: Physical landscape characteristics II: distance from major roads and barriers
#
# Purpose:             Generate the distance to major road and barrier input layers
#                      for BRT analysis
#
# Authors:             Matt Penunto, Quresh Latif
#-------------------------------------------------------------------------------


import os, arcpy, numpy
from arcpy.sa import *

# function(s)
def checkPath(path):
    try: os.makedirs(path)
    except: pass

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Set environmental settings for projection
CoordSys_ID = 102039  # Set to WKID for desired coordinate system defined by ESRI
CoordSys = arcpy.SpatialReference(CoordSys_ID)
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("USA Contiguous Albers Equal Area Conic")

####################################################################################################################################################################################
#  SET INPUT PATHS

#Base Directory
base = "E:/GISData/fire_control_modl_proj/" #This is the base directory where inputs/predictor outputs will be located

#Vector Inputs
streets = base + "streets.shp" #A polyline of trail locations
rivers = base + "NHD/NHDFlowline.shp" #A polyline of all linear hydrological features from USGS NHD
river_codes = [46000, 46006] # User must define NHD FCodes that could function as barriers.
    # Possible choices are:
        #46000 = 'Stream/River'
        #46003 = 'Intermittent Stream/River'
        #46006 = 'Perennial Stream/River'
        #46007 = 'Ephemeral Stream/River'
        #33600-33603 = 'canal/ditch'
lakes = base + "NHD/NHDWaterBodies.shp" #A polygon of lakes/waterbodies (from USGS NHD)
lake_codes = [39004] + range(43600, 43626) + [46602]
    # Possible additional choices:
        #39004 = perennial waterbody
        #39001 = 'intermittent lake/pond'
        #range(43600, 43626) = 'reservoirs'
        #46601 = 'intermittent swamp/marsh'
        #46602 = 'perennial swamp/marsh'

#FuelModel Inputs
fuelGrid = base + "fuels.tif" #LANDFIRE FBFM40 fuels

# Identify DEM file (for snapping)
dem_file = base + "/dem.tif" #This is the path to a ditigal elevation model (meters)
####################################################################################################################################################################################

#Set workspace and scratch workspace for temp outputs/calculations
arcpy.env.workspace = base + "/_workspace"
arcpy.env.scratchWorkspace = base + "/_scratch"

#Create workspace path
checkPath(arcpy.env.workspace)

#Create scratch path
checkPath(arcpy.env.scratchWorkspace)

# Set snap raster
arcpy.env.snapRaster = dem_file

##### ROAD DISTANCE SURFACE #####

print "Calculate distance to major roads"
rdist_dir = base + "BRTinputs/RoadDistance/"
checkPath(rdist_dir)

#Create selection of only MAJOR roads (NAVTEQ Speed Category 1-5)
roads_major_selection = rdist_dir + "roads_major.shp"
arcpy.Select_analysis(streets, roads_major_selection, """"SPEED_CAT" <= '5'""")

#Create selection of only MINOR/DIRT roads (NAVTEQ Speed Category 6-8)
roads_minor_selection = rdist_dir + "roads_minor.shp"
arcpy.Select_analysis(streets, roads_minor_selection, """"SPEED_CAT" > '5'""")

#Convert MAJOR roads to raster
rd_maj_rast = rdist_dir + "rd_maj.tif"
arcpy.PolylineToRaster_conversion(roads_major_selection, "FID", rd_maj_rast, "MAXIMUM_LENGTH", "#", 30)
rd_maj_rast= Raster(rd_maj_rast)

#Reclass MAJOR roads raster cell values to 1
rd_rast_recl = Con(rd_maj_rast >= 0, 1)
rd_rast_recl.save(rdist_dir + "rd_maj_recl.tif")

#Perform MAJOR roads euclidean distance calculation
rd_dist = EucDistance(rd_rast_recl)
arcpy.gp.ExtractByMask_sa(rd_dist, dem_file, base + "BRTinputs/rd_maj_dist.tif")


##### BARRIER DISTANCE SURFACE #####
#Barriers are 1) perrenial rivers, 2) lakes, and 3) Non-Burnable Fuels

barrier_dir = base + "BRTinputs/Barrier"
checkPath(barrier_dir)

print "Convert linear hydrological barriers to raster"
#Create selection of all potential linear hydrological barriers
rivers_selection = barrier_dir + "/rivers.shp"
arcpy.Select_analysis(rivers, rivers_selection, '"FCode" = ' + ' OR "FCode" = '.join(map(str,river_codes)))

#Convert hydrological barriers to raster
arcpy.PolylineToRaster_conversion(rivers_selection, "FID", barrier_dir + "/riv.tif", "MAXIMUM_LENGTH", "#", 30)
rivers_rast = Raster(barrier_dir + "/riv.tif")

#Reclass hydrological barrier values to 1
rivers_recl = Con(rivers_rast >= 0, 1)
rivers_recl.save(barrier_dir + "/riv_recl.tif")


print "Compile lakes raster"
#Create selection of lakes
lake_selection = barrier_dir + "/lakes.shp"
arcpy.Select_analysis(lakes, lake_selection, '"FCode" = ' + ' OR "FCode" = '.join(map(str,lake_codes)))

#Convert lake polygons to raster
arcpy.PolygonToRaster_conversion(lake_selection, "FID", barrier_dir + "/lakes.tif", "CELL_CENTER", "#", 30)
lakes_rast = Raster(barrier_dir + "/lakes.tif")

#Reclass Lakes raster cell values to 1
lakes_recl = Con(lakes_rast >= 0, 1)
lakes_recl.save(barrier_dir + "/lake_recl.tif")

print "Compile non-burnable fuels raster"
# Create nonburnable raster from FBFM40 fuels #
fuelGrid = Raster(fuelGrid)
nonburn_fuels = Con(fuelGrid < 100, 1, 0)

# Clump and Eliminate #
regionout = arcpy.gp.RegionGroup_sa(nonburn_fuels, barrier_dir + "/regionout.tif", "FOUR", "WITHIN", "NO_LINK", "")
reg_select = Con(Lookup(regionout, "Count") >= 100, regionout) #Threshold = 100 pixels
nonburn_CE = arcpy.gp.Nibble_sa(nonburn_fuels, reg_select, barrier_dir + "/nonburn_CE.tif", "DATA_ONLY")

print "Mosaic all barriers"
#Mosaic nonburnable raster with major roads, major rivers, and lakes to create barrier raster
mosaic_list = [rivers_recl, lakes_recl, nonburn_CE]
arcpy.MosaicToNewRaster_management(mosaic_list, barrier_dir, "barrier0.tif", "#", "#", "30", "1", "MAXIMUM", "#")
barrier_rast = Raster(barrier_dir + "/barrier0.tif")
barrier_rast = Con(barrier_rast == 1, 1)
barrier_rast.save(barrier_dir + "/barrier.tif")

print "Calculate distance to barrier input"
#Perform Barrier euclidean distance calculation
barrier_dist = EucDistance(barrier_rast)
arcpy.gp.ExtractByMask_sa(barrier_dist, dem_file, base + "BRTinputs/barrier_dist.tif")
