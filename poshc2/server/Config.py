import os, yaml
from poshc2.server.UrlConfig import UrlConfig

with open('./config.yml', 'r') as fileio:
    try:
        config = yaml.safe_load(fileio)
    except yaml.YAMLError as e:
        print("Error parsing config.yml: ", e)

BindIP = config["BindIP"]
BindPort = config["BindPort"]
PoshInstallDirectory = config["PoshInstallDirectory"]
PoshProjectDirectory = config["PoshProjectDirectory"]
ResourcesDirectory = "%sresources%s" % (PoshInstallDirectory, os.sep)
PayloadTemplatesDirectory = "%spayload-templates%s" % (ResourcesDirectory, os.sep)
BeaconDataDirectory = "%sbeacon-data%s" % (ResourcesDirectory, os.sep)
ModulesDirectory = "%smodules%s" % (ResourcesDirectory, os.sep)
DownloadsDirectory = "%sdownloads%s" % (PoshProjectDirectory, os.sep)
ReportsDirectory = "%sreports%s" % (PoshProjectDirectory, os.sep)
PayloadsDirectory = "%spayloads%s" % (PoshProjectDirectory, os.sep)
Database = "%s%sPowershellC2.SQLite" % (PoshProjectDirectory, os.sep)

PayloadCommsHost = config["PayloadCommsHost"]
DomainFrontHeader = config["DomainFrontHeader"]
UserAgent = config["UserAgent"]
DefaultSleep = config["DefaultSleep"]
Jitter = config["Jitter"]
KillDate = config["KillDate"]
Sounds = config["Sounds"]
PayloadCommsPort = config["PayloadCommsPort"]
NotificationsProjectName = config["NotificationsProjectName"]
EnableNotifications = config["EnableNotifications"]
DefaultMigrationProcess = config["DefaultMigrationProcess"]
ClockworkSMS_APIKEY = config["ClockworkSMS_APIKEY"]
ClockworkSMS_MobileNumbers = config["ClockworkSMS_MobileNumbers"]
Pushover_APIToken = config["Pushover_APIToken"]
Pushover_APIUser = config["Pushover_APIUser"]
SocksHost = config["SocksHost"]
Referrer = config["Referrer"]

HTTPResponse = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
<hr>
<address>Apache (Debian) Server</address>
</body></html>
"""
HTTPResponses = [
    "STATUS 200",
    "OK",
    "<html><head></head><body>#RANDOMDATA#</body></html>",
    "<html><body>#RANDOMDATA#</body></html>",
    """<?xml version="1.0" encoding="UTF-8"?>
<heading>#RANDOMDATA#</heading>
<body>#RANDOMDATA#</body>""",
    "<html><head>#RANDOMDATA#</head><body><div>#RANDOMDATA#</div></body></html>"
]
ServerHeader = config["ServerHeader"]
Insecure = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback: {$true}"

if config["UrlConfig"] == "urls":
    urlConfig = UrlConfig("%surls.txt" % ResourcesDirectory)  
elif config["UrlConfig"] == "wordlist":
    urlConfig = UrlConfig(wordList="%swordlist.txt" % ResourcesDirectory)
else:
    raise Exception(f"Invalid configuration: urlConfig must be urls/wordlist but was: {config['urlConfig']}")

QuickCommand = urlConfig.fetchQCUrl()
DownloadURI = urlConfig.fetchConnUrl()
URLS = urlConfig.fetchUrls()
SocksURLS = urlConfig.fetchSocks()
HTTPResponse = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
<hr>
<address>Apache (Debian) Server</address>
</body></html>
"""
HTTPResponses = [
    "STATUS 200",
    "OK",
    "<html><head></head><body>#RANDOMDATA#</body></html>",
    "<html><body>#RANDOMDATA#</body></html>",
    """<?xml version="1.0" encoding="UTF-8"?>
<heading>#RANDOMDATA#</heading>
<body>#RANDOMDATA#</body>""",
    "<html><head>#RANDOMDATA#</head><body><div>#RANDOMDATA#</div></body></html>"
]

