import arcpy, os, sys, urllib2
import json
import xml.dom.minidom as DOM
import time

################ Script inputs #######################
home = "E:/GISData/fire_control_modl_proj/"
SA = home + "Tonto_study_area.shp"
######################################################

arcpy.env.workspace = home # Set workspace #
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

# Get download URL using REST
post_data = ""
headers = {}
headers["Content-Type"] = "application/x-www-form-urlencoded"
serviceURL = "https://landfire.cr.usgs.gov/requestValidationServiceClient/sampleRequestValidationServiceProxy/processAOI2.jsp?TOP=" + str(TOP) + "&BOTTOM=" + str(BOTTOM) + "&LEFT=" + str(LEFT) + "&RIGHT=" + str(RIGHT) + "&SPATIALREFERENCE_WKID=4326&CHUNK_SIZE=250&ORIGINATOR=RMRS&JSON=true&LAYER_IDS=F0F38HZ"
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
    downloadFile = open(home + requestID + '.zip', 'wb')
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
        downloadFile = open(home + requestID + '.zip', 'wb')
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

#  Unzip DEM
import zipfile
zip_ref = zipfile.ZipFile(home + str(requestID) + ".zip", 'r')
zip_ref.extractall(home)
zip_ref.close()
