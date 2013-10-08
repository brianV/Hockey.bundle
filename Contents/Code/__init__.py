import sports_streams_core as core
import datetime
from dateutil import tz

###############################################

VIDEO_PREFIX = "/video/hockey"

NAME = "Hockey"

ART = 'art-default.png'
ICON = 'icon-default.png'
DEFAULT_TEAM_ICON = "Team_DEFAULT.jpg"

SPORT_KEYWORD = "hockey"
#STREAM_FORMAT = "http://nlds{server}.cdnak.neulion.com/nlds/nhl/{streamName}/as/live/{streamName}_hd_{q}.m3u8?t={title}&l={logo}&d={desc}"
STREAM_FORMAT = "http://nlds{server}.cdnak.neulion.com/nlds/nhl/{streamName}/as/live/{streamName}_hd_{q}.m3u8"

# the logos here are also referenced in a different collection in ServiceCode.pys, ensure any changes to filenames are copied over there.
TEAMS = {
	"ANA": { "City": "Anaheim", "Name": "Ducks", "Logo": "Team_ANA.jpg"},
	"BOS": { "City": "Boston", "Name": "Bruins", "Logo": "Team_BOS.jpg"},
	"BUF": { "City": "Buffalo", "Name": "Sabres", "Logo": "Team_BUF.jpg"},
	"CAR": { "City": "Carolina", "Name": "Hurricanes", "Logo": "Team_CAR.jpg"},
	"CMB": { "City": "Columbus", "Name": "Blue Jackets", "Logo": "Team_CBS.jpg"},
	"CGY": { "City": "Calgary", "Name": "Flames", "Logo": "Team_CGY.jpg"},
	"CHI": { "City": "Chicago", "Name": "Blackhawks", "Logo": "Team_CHI.jpg"},
	"COL": { "City": "Colorado", "Name": "Avalanche", "Logo": "Team_COL.jpg"},
	"DAL": { "City": "Dallas", "Name": "Stars", "Logo": "Team_DAL.jpg"},
	"DET": { "City": "Detroit", "Name": "Red Wings", "Logo": "Team_DET.jpg"},
	"EDM": { "City": "Edmonton", "Name": "Oilers", "Logo": "Team_EDM.jpg"},
	"FLA": { "City": "Florida", "Name": "Panthers", "Logo": "Team_FLA.jpg"},
	"LOS": { "City": "Los Angeles", "Name": "Kings", "Logo": "Team_LOS.jpg"},
	"MIN": { "City": "Minnesota", "Name": "Wild", "Logo": "Team_MIN.jpg"},
	"MON": { "City": "Montreal", "Name": "Canadiens", "Logo": "Team_MON.jpg"},
	"NJD": { "City": "New Jersey", "Name": "Devils", "Logo": "Team_NJD.jpg"},
	"NSH": { "City": "Nashville", "Name": "Predators", "Logo": "Team_NSH.jpg"},
	"NYI": { "City": "NY", "Name": "Islanders", "Logo": "Team_NYI.jpg"},
	"NYR": { "City": "NY", "Name": "Rangers", "Logo": "Team_NYR.jpg"},
	"OTT": { "City": "Ottawa", "Name": "Senators", "Logo": "Team_OTT.jpg"},
	"PHI": { "City": "Philadelphia", "Name": "Flyers", "Logo": "Team_PHI.jpg"},
	"PHX": { "City": "Phoenix", "Name": "Coyotes", "Logo": "Team_PHX.jpg"},
	"PIT": { "City": "Pittsburgh", "Name": "Penguins", "Logo": "Team_PIT.jpg"},
	"SJS": { "City": "San Jose", "Name": "Sharks", "Logo": "Team_SAN.jpg"},
	"STL": { "City": "St. Louis", "Name": "Blues", "Logo": "Team_STL.jpg"},
	"TBL": { "City": "Tampa Bay", "Name": "Lightning", "Logo": "Team_TAM.jpg"},
	"TOR": { "City": "Toronto", "Name": "Maple Leafs", "Logo": "Team_TOR.jpg"},
	"VAN": { "City": "Vancouver", "Name": "Canucks", "Logo": "Team_VAN.jpg"},
	"WPG": { "City": "Winnipeg", "Name": "Jets", "Logo": "Team_WPG.jpg"},
	"WSH": { "City": "Washington", "Name": "Capitals", "Logo": "Team_WSH.jpg"}
}

###############################################

# This function is initially called by PMS to inialize the plugin

def Start():

	# Initialize the plugin
	Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("List", viewMode = "InfoList", mediaType = "items")
	
	ObjectContainer.title1 = NAME
	
	core.Init(NAME, SPORT_KEYWORD, STREAM_FORMAT, TEAMS, DEFAULT_TEAM_ICON)
	
	Log.Debug("Plugin Start")

def MainMenu():
	dir = ObjectContainer(title2 = L("MainMenuTitle"), art=R(ART), view_group = "List")
	
	#try:
	core.BuildMainMenu(dir, ScheduleMenu, ArchiveMenu)
	#except core.NoGamesException:
	#	Log.Debug("no games")
	#	return ObjectContainer(header=L("MainMenuTitle"), message=L("ErrorNoGames")) 
	
	Log.Debug("View Groups")
	
	for item in Plugin.ViewGroups:
		Log.Debug(str(item))
	
	return dir
	 	
def ScheduleMenu(date, title):	
	dir = ObjectContainer(title2 = title, art=R(ART), view_group = "List")
	
	try:
		core.BuildScheduleMenu(dir, date, GameMenu, MainMenu)
	except core.NoGamesException:
		dir.add(DirectoryObject(
			key = Callback(ScheduleMenu, date=date), # call back to itself makes it go nowhere - in some clients anyway.
			title = L("ErrorNoGames"),
			thumb = R(DEFAULT_TEAM_ICON)
		))
		
	
	return dir
	
def ArchiveMenu():
	dir = ObjectContainer(title2 = "TEMP", art=R(ART))
	
	return dir
	
def GameMenu(gameId, title):
	dir = ObjectContainer(title2 = title, art=R(ART))
	
	
	
	return dir
	
		 
def StreamMenu(gameId, title):
	dir = ObjectContainer(title2 = title, art=R(ART))
	
	try:
		core.BuildStreamMenu(dir, gameId)	
	#except core.NotAvailableException as ex:
	except core.NotAvailableException, ex:
		message = str(L("ErrorStreamsNotReady")).replace("{minutes}", str(ex.Minutes))
		return ObjectContainer(header=L("MainMenuTitle"), message=message)	
	
	return dir
	
	