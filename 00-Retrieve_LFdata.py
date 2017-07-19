import arcpy, os, sys, urllib2
import json
import xml.dom.minidom as DOM
import time

# function(s)
def checkPath(path):
    try: os.makedirs(path)
    except: pass

################ Script inputs #######################
home = "E:/GISData/fire_control_modl_proj/"
SA = home + "Tonto_SA_WGS84.shp"
LFproduct = ["F0A", "F0F", "F0R", "F0E", "F0D", "F0C", "F0K", "F0T", "FA9"] # List desired LANDFIRE products for study area
LFformat = ["01XZ", "01XZ", "01XZ", "08XZ", "08XZ", "08XZ", "08XZ", "08XZ", "08XZ"] # Layers without thematic attribute information (topography) are 01XZ and the rest are 08XZ
# Products, respectively, are aspect, elevation, slope, canopy cover, canopy bulk density, canopy base height, fuels (Scott/Burgan), canopy height, and Disturbance 2014
######################################################

arcpy.env.overwriteOutput = True

# Project to WGS84
arcpy.Project_management(in_dataset = SA, out_dataset=home + "SA_WGS84.shp", out_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", max_deviation="")
SA_WGS84 = u'' + home + "SA_WGS84.shp"

# Get extent of study area
desc = arcpy.Describe(SA_WGS84)
BOTTOM = desc.extent.YMin
TOP = desc.extent.YMax
LEFT = desc.extent.XMin
RIGHT = desc.extent.XMax
arcpy.Delete_management(SA_WGS84)

# Create destination folder for LF data #
arcpy.env.workspace = home + "LFdata"
checkPath(arcpy.env.workspace)

for i in range(0, len(LFproduct)):
    # Get download URL using REST
    post_data = ""
    headers = {}
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    serviceURL = "https://landfire.cr.usgs.gov/requestValidationServiceClient/sampleRequestValidationServiceProxy/processAOI2.jsp?TOP=" + str(TOP) + "&BOTTOM=" + str(BOTTOM) + "&LEFT=" + str(LEFT) + "&RIGHT=" + str(RIGHT) + "&SPATIALREFERENCE_WKID=4326&CHUNK_SIZE=250&ORIGINATOR=RMRS&JSON=true&LAYER_IDS=" + LFproduct[i] + LFformat[i]
    req = urllib2.Request(serviceURL, post_data, headers)
    response_stream = urllib2.urlopen(req)
    response = response_stream.read()
    jsondict = json.loads(response)

    #  submit a job to the Download Service
    chunkUrl = str(jsondict['REQUEST_SERVICE_RESPONSE']['PIECE'][0]['DOWNLOAD_URL'])

    page = urllib2.urlopen(chunkUrl)
    result = page.read()
    doc = DOM.parseString(result)
    requestIDelement = doc.getElementsByTagName("ns:return")[0]
    requestID = requestIDelement.firstChild.data
    print requestID
                    
# call Download service with request id to get status
    downloadStatusUrl = "https://landfire.cr.usgs.gov/axis2/services/DownloadService/getData?downloadID=" + requestID

    filelocation = "start";

## Tries every 30 seconds until zip file name is returned ##
    while "zip" not in filelocation:
        page2 = urllib2.urlopen(downloadStatusUrl)
        result = page2.read()
        print result
        doc = DOM.parseString(result)
        requestIDelement = doc.getElementsByTagName("ns:return")[0]
        filelocation = requestIDelement.firstChild.data
        print filelocation
        time.sleep(30) # sleep for 30 seconds before checking again

    print "broke out of while"

    try:
        page = urllib2.urlopen(filelocation)
        downloadFile = open(requestID + '.zip', 'wb')
        while True:
            data = page.read(8192)
            if data == "":
                break
            downloadFile.write(data)
        downloadFile.close()
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
        else:
            downloadFile = open(requestID + '.zip', 'wb')
            while True:
                data = page.read(8192)
                if data == "":
                    break
                downloadFile.write(data)
            downloadFile.close()
    finally:
        page.close()

    #  send complete message back to server so it can cleanup the job (courtesy to LANDFIRE) #
    setStatusUrl = "https://landfire.cr.usgs.gov/axis2/services/DownloadService/setDownloadComplete?downloadID=" + requestID

    try:
        page = urllib2.urlopen(setStatusUrl)
        result = page.read()
        result = result.replace("&#xd;\n"," ")
        startPos = result.find("<ns:return>") + 11
        endPos = result.find("</ns:return>")
        status = result[startPos:endPos]
        print status
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
        else:
            result = page.read()
            result = result.replace("&#xd;\n"," ")
            startPos = result.find("<ns:return>") + 11
            endPos = result.find("</ns:return>")
            status = result[startPos:endPos]
            print status
    finally:
        page.close()

    # Unzip layer #
    import zipfile
    zip_ref = zipfile.ZipFile(str(requestID) + ".zip", 'r')
    zip_ref.extractall(arcpy.env.workspace)
    zip_ref.close()
    os.remove(str(requestID) + ".zip")
