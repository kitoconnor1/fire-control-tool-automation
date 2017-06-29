############################################################################################################################
# Consolidates FDIST from LANDFIRE or comparable layer to eliminate small fire breaks unlikely to influence fire behavior, #
# leaving only larger breaks (>/= 100 30-m pixels) for calculation of the Mobility sub-index of SDI.                       #
############################################################################################################################

# Import arcpy module
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

####### Inputs#####
base = "E:/GISData/fire_control_modl_proj/Coronado_AZ/Frye0619/SDI_inputs/" #Set workspace here
Input_Raster = "FDIST.tif"
###################

#### Clump and eliminate fuelTreat_rast ####
print "Perform clump and eliminate on fuelTreat layer representing potential fire breaks"

# Process: Region Group
regionout = arcpy.gp.RegionGroup_sa(base + Input_Raster, base + "regionout.tif", "FOUR", "WITHIN", "NO_LINK", "")

# Process: Single Output Map Algebra
reg_select = Con(Lookup(regionout, "Count") >= 100, regionout) #Threshold currently set at 100 pixels

# Process: Nibble
fuelTreat_rast = arcpy.gp.Nibble_sa(base + Input_Raster, reg_select, base + "FDIST_CE.tif", "DATA_ONLY")
del(regionout, reg_select)
