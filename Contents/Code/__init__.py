import sports_streams_core as core
import datetime
from dateutil import tz
import locale

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

	ObjectContainer.title1 = core.NAME
	
	Log.Debug("Plugin Start")

def MainMenu():
	dir = ObjectContainer(title2 = L("MainMenuTitle"), art=R(core.ART), view_group = "List")
	
	core.BuildMainMenu(dir, ScheduleMenu, ArchiveMenu)
	
	return dir
	 	
def ScheduleMenu(date, title):	
	dir = ObjectContainer(title2 = title, art=R(core.ART), view_group = "List")
	
	try:
		core.BuildScheduleMenu(dir, date, GameMenu, MainMenu)
	except core.NoGamesException:
		dir.add(DirectoryObject(
			key = Callback(ScheduleMenu, date=date), # call back to itself makes it go nowhere - in some clients anyway.
			title = L("ErrorNoGames")
		))
		
	
	return dir
	
def ArchiveMenu():
	dir = ObjectContainer(title2 = "Archive", art=R(core.ART))
	# this should allow users to select older dates than the main menu shows.
	dir.add(DirectoryObject(
		key = Callback(ArchiveMenu), # call back to itself makes it go nowhere - in some clients anyway.
		title = "Archive coming soon"
	))
	
	return dir
	 
def GameMenu(gameId, title):
	dir = ObjectContainer(title2 = title, art=R(core.ART), view_group = "List")
	
	core.BuildGameMenu(dir, gameId, HighlightsMenu, SelectQualityMenu) 
	
	if len(dir) == 0:		
		dir.add(DirectoryObject(
			key = Callback(GameMenu, gameId=gameId, title=title), # call back to itself makes it go nowhere - in some clients anyway.
			title = L("ErrorNoStreams")
		))
	
	return dir
	
def HighlightsMenu(gameId, title, forHomeTeam):
	dir = ObjectContainer(title2 = title, art=R(core.ART), view_group = "List")
	
	core.BuildHighlightsMenu(dir, gameId, forHomeTeam, title, SelectQualityMenu)
	
	return dir
	
def SelectQualityMenu(url, title, logo, available, isHighlight):
	dir = ObjectContainer(title2 = title, art=R(core.ART))
	
	if available == False:
		#show error message instead
		message = str(L("ErrorStreamsNotReady"))
		return ObjectContainer(header=L("MainMenuTitle"), message=message)	
	else:
		core.BuildQualitySelectionMenu(dir, url, logo, isHighlight)
	
	return dir
	
	