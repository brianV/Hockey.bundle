import sports_streams_core as core
import datetime
from dateutil import tz

###############################################



SPORT_KEYWORD = "hockey"
#STREAM_FORMAT = "http://nlds{server}.cdnak.neulion.com/nlds/nhl/{streamName}/as/live/{streamName}_hd_{q}.m3u8?t={title}&l={logo}&d={desc}"
STREAM_FORMAT = "http://nlds{server}.cdnak.neulion.com/nlds/nhl/{streamName}/as/live/{streamName}_hd_{q}.m3u8"


###############################################

# This function is initially called by PMS to inialize the plugin

def Start():

	# Initialize the plugin
	Plugin.AddPrefixHandler(core.VIDEO_PREFIX, MainMenu, core.NAME, core.ICON, core.ART)
	Plugin.AddViewGroup("List", viewMode = "InfoList", mediaType = "items")
	
	HTTP.SetHeader('User-agent', 'iPhone')
	
	ObjectContainer.title1 = core.NAME
	
	#core.Init(NAME, SPORT_KEYWORD, STREAM_FORMAT, TEAMS, DEFAULT_TEAM_ICON)
	
	Log.Debug("Plugin Start")

def MainMenu():
	dir = ObjectContainer(title2 = L("MainMenuTitle"), art=R(core.ART), view_group = "List")
	
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
	dir = ObjectContainer(title2 = title, art=R(core.ART), view_group = "List")
	
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
	dir = ObjectContainer(title2 = "Archive", art=R(core.ART))
	# this should allow users to select older dates than the main menu shows.
	return dir
	
def GameMenu(gameId, title):
	dir = ObjectContainer(title2 = title, art=R(core.ART))
	
	core.BuildGameMenu(dir, gameId, StreamMenu, HighlightsMenu)
	
	return dir
	
def HighlightsMenu(gameId, title):
	dir = ObjectContainer(title2 = "TEMP", art=R(core.ART))
	
	return dir
	
		 
def StreamMenu(gameId, title):
	dir = ObjectContainer(title2 = title, art=R(core.ART))
	
	try:
		core.BuildStreamMenu(dir, gameId)	
	#except core.NotAvailableException as ex:
	except core.NotAvailableException, ex:
		message = str(L("ErrorStreamsNotReady")).replace("{minutes}", str(ex.Minutes))
		return ObjectContainer(header=L("MainMenuTitle"), message=message)	
	
	return dir
	
	