#-------------------------------------------------------------------------------
# Name:        Suppression Difficulty Index (SDI)
# Purpose:     Automate the creation of an sdi raster given study area shapefile
#
# Authors:      mpanunto, qlatif
#
# Acquired (mpanunto):     04/11/2017
# Revised and annotated for generalization (qlatif): 
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
CoordSys_ID = 102039   # Set to WKID for desired coordinate system defined by ESRI
CoordSys = arcpy.SpatialReference(CoordSys_ID)
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("USA Contiguous Albers Equal Area Conic")

####################################################################################################################################################################################
#  SET INPUT PATHS

#Base Directory
base = "E:/GISData/fire_control_modl_proj" #This is the base directory where outputs will be saved

#Fuels
fuels_file = base + "/fuels.tif" #A raster of fuels (this script was written assuming LANDFIRE FBFM40 is used)

##### Process disturbance layer (FDIST) from LANDFIRE to eliminate small patches unlikely to affect fire spread #####
#***Note: can be skipped if using custom disturbance history layer***
print "Perform clump and eliminate on fuelTreat layer representing potential fire breaks"
FDIST = base + "/LFdata/US_DIST2014/us_dist2014" # Identify FDIST layer for processing
    # Process: Region Group
regionout = arcpy.gp.RegionGroup_sa(FDIST, base + "regionout.tif", "FOUR", "WITHIN", "NO_LINK", "")
    # Process: Single Output Map Algebra
reg_select = Con(Lookup(regionout, "Count") >= 100, regionout) #Threshold currently set at 100 pixels
    # Process: Nibble
arcpy.gp.Nibble_sa(FDIST, reg_select, base + "/LFdata/US_DIST2014/FDIST_CE.tif", "DATA_ONLY")
del(regionout, reg_select)
######################################################################################################################

fuelTreat = base + "/LFdata/US_DIST2014/FDIST_CE.tif" #Used to generate fire breaks polygon for mobility index

#Flammap
flamlen_file = base + "/Tonto90pct/FL90.asc" #This is the path to the flame length raster output from Flammap model, this script assumes units are in meters
hua_file = base + "/Tonto90pct/HuAkj.asc" #This is the path to the heat per unit area raster output from Flammap model, this script assumes units are in kj/m2
 #Provide projection of flammap layers here (default is NAD83 Albers).
prj_in = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-96.0],PARAMETER['Standard_Parallel_1',29.5],PARAMETER['Standard_Parallel_2',45.5],PARAMETER['Latitude_Of_Origin',23.0],UNIT['Meter',1.0]]"

#Vector Inputs
streets_file = base + "/streets.shp" #A polyline of trail locations, if user does not have this, just insert path to roads polyline layer again
trails = base + "/trails.shp" #A polyline of trail locations, if user does not have this, just insert path to roads polyline layer again

#Topographic Inputs
dem_file = base + "/dem.tif" #This is the path to a ditigal elevation model (meters)
aspect_file = base + "/BRTinputs/aspect.tif" #This is the path to a LANDFIRE aspect raster (degrees)

#RTC Lookup table - Converts fuel categories to Round((hours / m)*10000). Need to divide by 10000 to get hours / m.
rtc_lookup = base + "/RTC_lookup_SDIwt_westernUS.txt"

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
arcpy.env.extent = Raster(dem_file).extent

# Convert FLAMMAP .asc files to .tif (may want to include conditional statement here to only apply if needed)
prj_out = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-96.0],PARAMETER['Standard_Parallel_1',29.5],PARAMETER['Standard_Parallel_2',45.5],PARAMETER['Latitude_Of_Origin',23.0],UNIT['Meter',1.0]]"
arcpy.ProjectRaster_management(flamlen_file, "FL.tif", out_coor_system = prj_out, in_coor_system = prj_in)
arcpy.gp.ExtractByMask_sa("FL.tif", dem_file, "FL_mask.tif")
flamlen_file = "FL_mask.tif"

arcpy.ProjectRaster_management(hua_file, "HuA.tif", out_coor_system = prj_out, in_coor_system = prj_in)
arcpy.gp.ExtractByMask_sa("HuA.tif", dem_file, "HuA_mask.tif")
hua_file = "HuA_mask.tif"

#####################################################################################################

#ENERGY BEHAVIOR SUB-INDEX

#####################################################################################################

#Create SDI folder
SDI_path = base + "/SDI"
checkPath(SDI_path)

#Create EnergyBehavior subfolder in the SDI dir
eb_dir = SDI_path + "/EnergyBehavior"
checkPath(eb_dir)

print "Calculate Energy Behavior Sub Index"

# Generates proportion fuel layer 
fuelGrid = Raster(fuels_file)
propFuel = Raster(fuels_file)
fuelGrid_M = arcpy.RasterToNumPyArray(fuelGrid, '', '', '', -32768)
fuel_unique = numpy.unique(fuelGrid_M).tolist()
del fuel_unique[0] # Removes NoData value (-32768) from list
for fuel in fuel_unique:
    R = Con((fuelGrid == fuel), 1, 0)
    R = arcpy.gp.FocalStatistics_sa(R, "fuel" + str(fuel) + "_Prp900m.tif", "Circle 56.41896 MAP", "MEAN", "DATA")
    propFuel = Con((propFuel == fuel), R, propFuel)
    del(R)

#The following code requires flame lengths and heat per unit area outputs from Flammap

###Reclassify Flammap flamelength raster values based on Table 2 of Rodriguez y Silva et al
#Ensure that units are first converted to meters before reclassifying, if necessary.
print "Reclassifying flame lengths to assigned index values"
flamlen_rast = Raster(flamlen_file)
flamelen_rast_recl_out = eb_dir + "/flamlen_recl.tif"
flamlen_rast_recl = Con((flamlen_rast<=0.5),1,
                        Con((flamlen_rast>0.5) & (flamlen_rast<=1),2,
                        Con((flamlen_rast>1)   & (flamlen_rast<=1.5),3,
                        Con((flamlen_rast>1.5) & (flamlen_rast<=2),4,
                        Con((flamlen_rast>2)   & (flamlen_rast<=2.5),5,
                        Con((flamlen_rast>2.5) & (flamlen_rast<=3),6,
                        Con((flamlen_rast>3)   & (flamlen_rast<=3.5),7,
                        Con((flamlen_rast>3.5) & (flamlen_rast<=4),8,
                        Con((flamlen_rast>4)   & (flamlen_rast<=4.5),9,
                        Con((flamlen_rast>4.5), 10))))))))))
flamlen_rast_recl.save(flamelen_rast_recl_out)

###Reclassify Flammap heat per unit area raster values based on Table 2 of Rodriguez y Silva et al
#Convert heat per unit area raster from kJ/m2 to kcal/m2
print "Reclassifying heat per unit area values to assigned index values"
hua_rast = Raster(hua_file)
hua_kcal_rast_out = eb_dir + "/hua_kcal"
hua_kcal_rast = hua_rast * 0.2388459
hua_kcal_rast.save(hua_kcal_rast_out)
hua_kcal_rast_recl_out = eb_dir + "/hua_kcal_recl"
hua_kcal_rast_recl = Con( (hua_kcal_rast<=380),1,
                        Con((hua_kcal_rast>380)  & (hua_kcal_rast<=1265),2,
                        Con((hua_kcal_rast>1265) & (hua_kcal_rast<=1415),3,
                        Con((hua_kcal_rast>1415) & (hua_kcal_rast<=1610),4,
                        Con((hua_kcal_rast>1610) & (hua_kcal_rast<=1905),5,
                        Con((hua_kcal_rast>1905) & (hua_kcal_rast<=2190),6,
                        Con((hua_kcal_rast>2190) & (hua_kcal_rast<=4500),7,
                        Con((hua_kcal_rast>4500) & (hua_kcal_rast<=6630),8,
                        Con((hua_kcal_rast>6630) & (hua_kcal_rast<=8000),9,
                        Con((hua_kcal_rast>8000), 10))))))))))
hua_kcal_rast_recl.save(hua_kcal_rast_recl_out)

#Calculate Energy Behavior raster
print "Creating energy behavior raster"
eb_rast_out = eb_dir + "/Energy_behave.tif"
eb_rast = (2 * Float(flamlen_rast_recl) * Float(hua_kcal_rast_recl) / (Float(flamlen_rast_recl) + Float(hua_kcal_rast_recl))) * (propFuel)
eb_rast.save(eb_rast_out)

#####################################################################################################

#ACCESSIBILITY SUB INDEX

#####################################################################################################


#Create Accessibility subfolder in the SDI dir
acc_dir = SDI_path + "/Accessibility"
checkPath(acc_dir)

print " "
print "Calculating Accessibility sub index for SDI:"

streets_lyr = arcpy.MakeFeatureLayer_management(streets_file, "streets_lyr")
arcpy.SelectLayerByAttribute_management(streets_lyr, "NEW_SELECTION", where_clause=""""SPEED_CAT" <> '7' AND "SPEED_CAT" <> '8'""")
roadlen_rast = arcpy.gp.LineStatistics_sa(streets_lyr, "NONE", "roads_length_900m.tif", "30", "56.41896", "LENGTH")

# Reclassify according to table 3 in Rodriguez y Silva et al. 2014
print "Reclassify road length raster to assigned accessibility index value"
roadlen_rast = Raster(roadlen_rast)
accessibility = Con((roadlen_rast<=100),1,
                Con((roadlen_rast>100)&(roadlen_rast<=200),2,
                Con((roadlen_rast>200)&(roadlen_rast<=300),3,
                Con((roadlen_rast>300)&(roadlen_rast<=400),4,
                Con((roadlen_rast>400)&(roadlen_rast<=500),5,
                Con((roadlen_rast>500)&(roadlen_rast<=600),6,
                Con((roadlen_rast>600)&(roadlen_rast<=700),7,
                Con((roadlen_rast>700)&(roadlen_rast<=800),8,
                Con((roadlen_rast>800)&(roadlen_rast<=900),9,
                10)))))))))
accessibility.save(acc_dir + "/accessibility.tif")

###############################################################################################################

#MOBILITY SUB-INDEX

###############################################################################################################

#Create Mobility subfolder in the SDI dir
mob_dir = SDI_path + "/Mobility"
checkPath(mob_dir)

print " "
print "Calculating Mobility sub index for SDI:"

#Convert LF FDIST raster --> firebreaks polygon --> polyline
print "Convert firebreaks polygon to polyline"

fuelTreat_rast = Raster(fuelTreat)
fuelTreat_ModHigh = arcpy.gp.Reclassify_sa(fuelTreat, "Value", "0 113 NoData;121 121;122 122;123 123;131 131;132 132;133 133;211 313 0;321 321;322 322;323 323;331 331;332 332;333 333", "DATA")
fuelTreat_poly = arcpy.RasterToPolygon_conversion(fuelTreat_ModHigh, simplify="SIMPLIFY", raster_field="VALUE")
firebreaks_line = arcpy.PolygonToLine_management(fuelTreat_poly, mob_dir + "/firebreaks_line.shp", "IGNORE_NEIGHBORS")

# Convert fire break polyline to neighborhood length raster
firebreaks_length = arcpy.gp.LineStatistics_sa(firebreaks_line, "NONE", "FBlength_900m.tif", "30", "56.41896", "LENGTH")
firebreaks_length = arcpy.gp.ExtractByMask_sa(firebreaks_length, dem_file, mob_dir + "/FBlength_900m.tif")

# Reclassify according to table 3 in Rodriguez y Silva et al. 2014
print "Reclassify firebreak length raster to assigned mobility index value"
firebreaks_length = Raster(mob_dir + "/FBlength_900m.tif")
mobility = Con((firebreaks_length<=100),1,
                Con((firebreaks_length>100)&(firebreaks_length<=200),2,
                Con((firebreaks_length>200)&(firebreaks_length<=300),3,
                Con((firebreaks_length>300)&(firebreaks_length<=400),4,
                Con((firebreaks_length>400)&(firebreaks_length<=500),5,
                Con((firebreaks_length>500)&(firebreaks_length<=600),6,
                Con((firebreaks_length>600)&(firebreaks_length<=700),7,
                Con((firebreaks_length>700)&(firebreaks_length<=800),8,
                Con((firebreaks_length>800)&(firebreaks_length<=900),9,
                    10)))))))))
mobility.save(mob_dir + "/mobility.tif")




#################################################################################################################

#PENETRABILITY SUB-INDEX

#################################################################################################################


#Create Penetrability subfolder in the SDI dir
pen_dir = SDI_path + "/Penetrability"
checkPath(pen_dir)

print " "
print "Calculating Penetrability Sub-Index"

#Create raster variables
dem_rast = Raster(dem_file)
aspect_rast = Raster(aspect_file)

#Convert Aspect Raster (degrees) into assigned values
print "Converting aspect raster into assinged values"
aspect_out = pen_dir + "/asp_class.tif"
aspect_class_rast = Con((aspect_rast >= 337.5), 10, #North Facing
                            Con((aspect_rast >= -1) & (aspect_rast < 22.5), 10, #North Facing
                            Con((aspect_rast >= 22.5) & (aspect_rast < 67.5), 8, #Northeast Facing
                            Con((aspect_rast >= 292.5) & (aspect_rast < 337.5), 7, #Northwest Facing
                            Con((aspect_rast >= 67.5) & (aspect_rast < 112.5), 6, #East Facing
                            Con((aspect_rast >= 247.5) & (aspect_rast < 292.5), 5, #West Facing
                            Con((aspect_rast >= 112.5) & (aspect_rast < 157.5), 4, #Southeast Facing
                            Con((aspect_rast >= 202.5) & (aspect_rast < 247.5), 3, #Southwest Facing
                            Con((aspect_rast >= 157.5) & (aspect_rast < 202.5), 2))))))))) #South Facing
aspect_class_rast.save(aspect_out)

#Calculate Percent Slope
print "Calculating percent slope"
slope_out = pen_dir + "/slp.tif"
slope_rast = Slope(dem_rast, "PERCENT_RISE")
slope_rast.save(slope_out)

#Convert Percent Slope Raster into assigned values
print "Converting percent slope into assigned values"
slope_class_out = pen_dir + "/slp_class.tif"
slope_class_rast = Con((slope_rast >= 0) & (slope_rast < 6), 10,
                            Con((slope_rast >= 6) & (slope_rast < 11), 9,
                            Con((slope_rast >= 11) & (slope_rast < 16), 8,
                            Con((slope_rast >= 16) & (slope_rast < 21), 7,
                            Con((slope_rast >= 21) & (slope_rast < 26), 6,
                            Con((slope_rast >= 26) & (slope_rast < 31), 5,
                            Con((slope_rast >= 31) & (slope_rast < 36), 4,
                            Con((slope_rast >= 36) & (slope_rast < 41), 3,
                            Con((slope_rast >= 41) & (slope_rast < 46), 2,
                            Con((slope_rast >= 46), 1))))))))))
slope_class_rast.save(slope_class_out)

#Calculate raster that averages the Slope and Aspect assigned values for each pixel
print "Calculating Slope/Aspect average raster"
slope_aspect_out = pen_dir + "/slp_asp_avg.tif"
slope_aspect_average = Float(slope_class_rast + aspect_class_rast) / 2
slope_aspect_average.save(slope_aspect_out)

#Reclassify fuels into assigned values using reclass table
#This will convert the fuel types into hours per meter of fire line implementation difficulty values assuming a 20-person crew according
#to table 1 of Rodriguez y Silva et al 2014
print "Reclassifying fuels into assigned values"
fuel_Cntrl_out = pen_dir + "/RTC_class.tif"
arcpy.gp.ReclassByASCIIFile_sa(fuels_file, rtc_lookup, fuel_Cntrl_out, "NODATA")
fuel_Cntrl_rast = Raster(fuel_Cntrl_out)

#Extract trails layer from Streets file and calculate length of trails within 1 ha (56.41896m radius) moving window.
#streets_lyr = arcpy.MakeFeatureLayer_management(streets_file, "streets_lyr")
#arcpy.SelectLayerByAttribute_management(streets_lyr, "NEW_SELECTION", where_clause=""""SPEED_CAT" = '7' OR "SPEED_CAT" = '8'""")
#arcpy.gp.LineStatistics_sa(streets_lyr, "NONE", "trails_length_900m.tif", "30", "56.41896", "LENGTH")
#trail_rast = Raster("trails_length_900m.tif")

#Temporary work around
#Extract trails layer from Streets file and calculate length of trails within 1 ha (56.41896m radius) moving window.
#streets_lyr = arcpy.MakeFeatureLayer_management(streets_file, "streets_lyr")
#arcpy.SelectLayerByAttribute_management(streets_lyr, "NEW_SELECTION", where_clause=""""SPEED_CAT" = '7' OR "SPEED_CAT" = '8'""")
arcpy.gp.LineStatistics_sa(trails, "NONE", "trails_length_900m.tif", "30", "56.41896", "LENGTH")
trail_rast = Raster("trails_length_900m.tif")

#Merge streets Sp cat 7 & 8 with trails
#Extract trails layer from Streets file and calculate length of trails within 1 ha (56.41896m radius) moving window.
#streets_lyr = arcpy.MakeFeatureLayer_management(streets_file, "streets_lyr")
#arcpy.SelectLayerByAttribute_management(streets_lyr, "NEW_SELECTION", where_clause=""""SPEED_CAT" = '7' OR "SPEED_CAT" = '8'""")
#trails_lyr = arcpy.Merge_management([trails, streets_lyr], trails_st)
#arcpy.gp.LineStatistics_sa(trails_st, "NONE", "trails_length_900m.tif", "30", "56.41896", "LENGTH")
#trail_rast = Raster("trails_length_900m.tif")

#Convert pre-suppression trails raster into assigned values
print "Reclassifying road/trail lengths to assigned values"
trail_len_out = pen_dir + "/trail_length_class.tif"
trail_len_class = Con((trail_rast >= 0) & (trail_rast < 6), 10,
                                Con((trail_rast >= 6) & (trail_rast < 11), 9,
                                Con((trail_rast >= 11) & (trail_rast < 16), 8,
                                Con((trail_rast >= 16) & (trail_rast < 21), 7,
                                Con((trail_rast >= 21) & (trail_rast < 26), 6,
                                Con((trail_rast >= 26) & (trail_rast < 31), 5,
                                Con((trail_rast >= 31) & (trail_rast < 36), 4,
                                Con((trail_rast >= 36) & (trail_rast < 41), 3,
                                Con((trail_rast >= 41) & (trail_rast < 46), 2,
                                Con((trail_rast >= 46), 1))))))))))
arcpy.gp.Reclassify_sa(trail_len_class, "Value", "1 1;2 2;3 3;4 4;5 5;6 6;7 7;8 8;9 9;10 10;NoData 10", "DATA") #In case there are NoData values, replace with 10 #
trail_len_class.save(trail_len_out)

#Create raster for Penetrability Sub Index
print "Creating Penetrability Sub Index Raster"
penetrability_out = pen_dir + "/penetrability.tif"
penetrability = ((Float(slope_class_rast) + Float(fuel_Cntrl_rast) + Float(slope_class_rast) + Float(slope_aspect_average)) / Float(trail_len_class)) * propFuel
penetrability.save(penetrability_out)

#######################################################################################################################

#FIRELINE OPENING / FIRELINE CREATION SUB-INDEX

#######################################################################################################################


#Create Fire line subfolder in the SDI dir
flo_dir = SDI_path + "/FirelineOpening"
checkPath(flo_dir)

print " "
print "Calculating Fireline Opening sub index for SDI:"

#Create Slope Adjustment Raster
print "Calculate slope adjustment raster"
slope_adj_out = flo_dir + "/slp_adj.tif"
slope_adjust_rast = Con((slope_rast >= 0) & (slope_rast < 16), 1,
                            Con((slope_rast >= 16) & (slope_rast < 31), 0.8,
                            Con((slope_rast >= 31) & (slope_rast < 46), 0.6,
                            Con((slope_rast >= 46), 0.5))))
slope_adjust_rast.save(slope_adj_out)

#Calculate Fireline Opening Sub Index
print "Calculate Fireline Opening Sub Index"
flo_rast_out = flo_dir + "/flo.tif"
flo_rast = (2 * Float(fuel_Cntrl_rast)) * slope_adjust_rast
flo_rast.save(flo_rast_out)


#######################################################################################################################

#SDI CALCULATION

#######################################################################################################################



SDI_path = base + "/SDI"


#Create SDI raster
print "Creating SDI raster"
sdi_rast_out = SDI_path + "/sdi_pre.tif"
sdi_rast = Float(eb_rast) / (Float(accessibility) + Float(mobility) + Float(penetrability) + Float(flo_rast))
sdi_rast.save(sdi_rast_out)

#Non-burnable fuels will be NoData, change these to zero
print "Setting non-burnable fuels to zero"
sdi_final_out = base + "/BRTinputs/sdi.tif"
sdi_final_rast = Con( (IsNull(sdi_rast) & (fuelGrid > 0)), 0, sdi_rast)
sdi_final_rast.save(sdi_final_out)

####*** Cleaning of _scratch and _workspace folders can be done by hand if satisfactory SDI layer is produced ***####
