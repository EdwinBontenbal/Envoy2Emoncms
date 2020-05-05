# This utility sends envoy (enphase) data to emoncms
#  
# coded by:
# author : Edwin Bontenbal
# Email : Edwin.Bontenbal@Gmail.COM 
version = "v1.00"


# If you experience errors while executing this script, make sure you installed python and the required modules/libraries
import ConfigParser
import datetime
import logging
import json
import urllib2
import urllib
import time

TimeStampList = { }
DataJson_inv  = { }
DataJson_sum  = { }

TranslationList = { }

LogFile              = "/var/log/Envoy2Emoncms.log"
LogFileLastMessage   = "/tmp/Envoy2Emoncms.log"
WatchdogFile         = "/tmp/Envoy2Emoncms_Watchdog"

# Set logging params
logging.basicConfig(filename=LogFile,format='%(asctime)s %(message)s',level=logging.DEBUG)

###############################################################################################################
# Procedures 
###############################################################################################################

Config = ConfigParser.ConfigParser()
Config.read("/etc/Envoy2Emoncms/Envoy2Emoncms.cfg")

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            logging.debug("Reading config file : " + section + "," + option + " = " +  dict1[option] )
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

print Config.sections()

emon_privateKey = ConfigSectionMap("emoncms")['privatekey'] 
emon_node_panel = ConfigSectionMap("emoncms")['node_panel'] 
emon_node_sum   = ConfigSectionMap("emoncms")['node_sum'] 
emon_host       = ConfigSectionMap("emoncms")['host'] 
emon_protocol   = ConfigSectionMap("emoncms")['protocol'] 
emon_url        = ConfigSectionMap("emoncms")['url'] 

envoy_url_inv   = ConfigSectionMap("envoy")['url_inv'] 
envoy_url_sum   = ConfigSectionMap("envoy")['url_sum'] 
envoy_host      = ConfigSectionMap("envoy")['host'] 
envoy_protocol  = ConfigSectionMap("envoy")['protocol'] 
envoy_realm     = ConfigSectionMap("envoy")['realm'] 
envoy_username  = ConfigSectionMap("envoy")['username'] 
envoy_password  = ConfigSectionMap("envoy")['password'] 

options = Config.options('translationlist')
for option in options:
        try:
            TranslationList[option] = Config.get('translationlist', option)
            logging.debug("Reading config file : translationlist," + option + " = " +  TranslationList[option]  )
        except:
            print("exception on %s!" % option)

###############################################################################################################
# Main program
###############################################################################################################

# Construct urls 
url_envoy_inv  = envoy_protocol + envoy_host + envoy_url_inv 
url_envoy_sum  = envoy_protocol + envoy_host + envoy_url_sum 

# Set passwordlist for Envoy URL 
authhandler  = urllib2.HTTPDigestAuthHandler()
authhandler.add_password(envoy_realm, envoy_protocol + envoy_host, envoy_username, envoy_password)
opener       = urllib2.build_opener(authhandler)
urllib2.install_opener(opener)

# Do forever ....

while True:
 # Write time to watchdog file, as a sign of life  
 f3=open(WatchdogFile, "w")
 timestamp = int(time.time())
 f3.write (str(timestamp))
 f3.close()

 # Fetch page with ENVOY inverter data
 page_content_inv = urllib2.urlopen(url_envoy_inv)
 the_page_inv     = page_content_inv.read()
 logging.debug(the_page_inv)
 data_inv = json.loads(the_page_inv)

 # Fetch page with ENVOY general data
 page_content_sum = urllib2.urlopen(url_envoy_sum)
 the_page_sum     = page_content_sum.read()
 logging.debug(the_page_sum)
 data_sum = json.loads(the_page_sum)

 # Write raw output from envoy to file 
 f1=open(LogFileLastMessage, "w")
 f1.write (the_page_inv)
 f1.write (the_page_sum)
 f1.close()

 # Build up timestamp collection 
 for x in range(len(data_inv)):
   # Check if Inverter Device is in dictionary list
   if TimeStampList.has_key(data_inv[x]['serialNumber']):
     # Time Stamp Already in list 
     logging.debug(data_inv[x]['serialNumber'] + " - not add serialnumber to list")
   else: 
     # Time Stamp Not In List
     TimeStampList[data_inv[x]['serialNumber']] = data_inv[x]['lastReportDate'] 
     logging.debug(data_inv[x]['serialNumber'] + " -     add serialnumber to list")

 DataJson_inv.clear()
 DataJson_sum.clear()

 # Determine panel and array according to translation list, based on naming 
 for x in range(len(data_inv)):
   if TranslationList.has_key(data_inv[x]['serialNumber']):
     # Serial in list use alias 
     PanelID = TranslationList[data_inv[x]['serialNumber']]
     logging.debug("Inverter     found in list : " + data_inv[x]['serialNumber'] + " -> " + TranslationList[data_inv[x]['serialNumber']])
   else:
     # Serial not In List use serial
     PanelID = data_inv[x]['serialNumber']  
     logging.debug("Inverter not found in list : " + data_inv[x]['serialNumber'])

   logging.debug("Serial          : " + data_inv[x]['serialNumber'])
   logging.debug("LastReportDate  : " + str(data_inv[x]['lastReportDate']))
   logging.debug("TimeStampList   : " + str(TimeStampList[data_inv[x]['serialNumber']]))
   logging.debug("lastReportWatts : " + str(data_inv[x]['lastReportWatts']))
 
   if      (data_inv[x]['lastReportDate'] > TimeStampList[data_inv[x]['serialNumber']])  and (data_inv[x]['lastReportWatts']>0):
    # String contains a newer report  
    logging.debug("Update, newer timestamp found")
    DataJson_inv[PanelID + '_LRW'] = data_inv[x]['lastReportWatts']
    DataJson_inv[PanelID + '_MRW'] = data_inv[x]['maxReportWatts']
    DataJson_inv[PanelID + '_IVO'] = 1 
    logging.debug("Update time inverter : " + str(data_inv[x]['lastReportDate']) + "  LastKnowUpdate : " + str(TimeStampList[data_inv[x]['serialNumber']]))
    TimeStampList[data_inv[x]['serialNumber']]     = data_inv[x]['lastReportDate']
   elif    (data_inv[x]['lastReportDate'] == TimeStampList[data_inv[x]['serialNumber']]) and data_sum['wattsNow'] == 0:
    # Since more than 300 sec and no new data recieved, this means inverts are off 
    logging.debug("stop, set everything to zero, no new data comming in")
    DataJson_inv[PanelID + '_LRW'] = 0 
    DataJson_inv[PanelID + '_MRW'] = data_inv[x]['maxReportWatts']
    DataJson_inv[PanelID + '_IVO'] = 0

 if DataJson_inv == {}:
  logging.debug("No new inverter data found, so nothing to push to emoncms")
 else:
  logging.debug("   new inverter data found, so push to emoncms")
  logging.debug(json.dumps(DataJson_inv, separators=(',', ':')))
  url_inv  = emon_protocol + emon_host + emon_url + "&node=" + emon_node_panel + "&apikey=" + emon_privateKey + "&json=" + str( json.dumps(DataJson_inv, separators=(',', ':')))
  logging.debug(url_inv)
  HTTPresult_inv = urllib2.urlopen(url_inv)
  logging.debug("Response code : " + str(HTTPresult_inv.getcode()))

 DataJson_sum['wattHoursToday']    = data_sum['wattHoursToday']
 DataJson_sum['wattHoursLifetime'] = data_sum['wattHoursLifetime']
 DataJson_sum['wattsNow']          = data_sum['wattsNow']

 logging.debug(json.dumps(DataJson_sum, separators=(',', ':')))
 url_sum  = emon_protocol + emon_host + emon_url + "&node=" + emon_node_sum   + "&apikey=" + emon_privateKey + "&json=" + str( json.dumps(DataJson_sum, separators=(',', ':')))
 logging.debug(url_sum)
 HTTPresult_sum = urllib2.urlopen(url_sum)
 logging.debug("Response code : " +  str(HTTPresult_sum.getcode()))

 time.sleep(15) 
