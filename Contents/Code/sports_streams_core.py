import re, urlparse, string, socket, sys, datetime
from dateutil import parser
from dateutil import tz

###############################################

# NOTHING SPORT SPECIFIC SHOULD GO IN HERE.  
# THE CODE SHOULD BE REUSABLE REGARDLESS OF THE SPORT.

SEARCH_URL = "http://www.reddit.com/r/Sports_Streams/search.rss?q={sport}&sort=new&t=week&restrict_sr=on"
QUALITY_MARKER = "{q}" 

STREAM_AVAILABLE_MINUTES_BEFORE = 20
STREAM_HIDDEN_AFTER = 360 # 6 hours oughta be plenty...
MAIN_MENU_EXTRA_DAYS = 3 # day count not including today and tomorrow
DATE_FORMAT = "%Y-%m-%d"

HERE = tz.tzlocal()
UTC = tz.tzutc()
EASTERN = tz.gettz("EST5EDT")

CONFIG = None

###############################################

# This method should be called first by sport plugins.
def Init(title, sportKeyword, streamFormat, teamNames, defaultTeamIcon):
	Log.Debug("Core.Init()")
	global CONFIG
	CONFIG = Config(title, sportKeyword, streamFormat, teamNames, defaultTeamIcon)
	

class NotAvailableException(Exception):
	pass
	
	Minutes = STREAM_AVAILABLE_MINUTES_BEFORE
	
class NoGamesException(Exception):
	pass

	
class Config:
	def __init__(self, title, sportKeyword, streamFormat, teams, defaultTeamIcon):
		self.Title = title
		self.SportKeyword = sportKeyword
		self.StreamFormat = streamFormat
		self.Teams = teams
		self.DefaultTeamIcon = defaultTeamIcon
		

class Game:
	def __init__(self, id, utcStart, awayAbbreviation, homeAbbreviation, summary):
		self.ID = id
		self.UtcStart = utcStart
		self.AwayAbbreviation = awayAbbreviation
		self.HomeAbbreviation = homeAbbreviation
		self.Summary = summary
				
		
class Stream:
	def __init__(self, title, url, team, available, summary):
		self.Title = title
		self.Url = url
		self.Team = team
		self.Available = available
		self.Summary = summary
	
###############################################	

def BuildMainMenu(container, scheduleCallback, archiveCallback):	
	# log some details about the request	
	Log.Info("Hostname: " + socket.gethostname())
	Log.Info("Python Version: " + sys.version)
	Log.Info("Platform: " + sys.platform)
	Log.Info("Client: " + str(Client.Platform)) # cast as string in case it's a null

	# make sure these times, which are used to make calls to the nhl servers, are always in eastern time.
	todayDate = GetEasternNow()
	tomorrowDate = todayDate + datetime.timedelta(days = 1)
	
	today = datetime.datetime.strftime(todayDate, DATE_FORMAT)
	tomorrow = datetime.datetime.strftime(tomorrowDate, DATE_FORMAT)
	
	container.add(GetMainMenuItem(L("TodayLabel"), Callback(scheduleCallback, date = today, title = L("TodayLabel"))))
	container.add(GetMainMenuItem(L("TomorrowLabel"), Callback(scheduleCallback, date = tomorrow, title = L("TomorrowLabel"))))
	
	dateFormat = str(L("ScheduleDateFormat")) # strftime can't take a localstring for some reason.	
	for x in range(1, MAIN_MENU_EXTRA_DAYS + 1):
		date = tomorrowDate + datetime.timedelta(days = x)
		dateString = datetime.datetime.strftime(date, dateFormat)
		title = dateString
		container.add(GetMainMenuItem(title, Callback(scheduleCallback, date = dateString, title = title)))
		
	#archive
	container.add(GetMainMenuItem(L("ArchiveLabel"), Callback(archiveCallback)))
			
	if NeedsPreferencesItem():
		Log.Debug("Adding preferences menu item")
		container.add(PrefsObject(title="Preferences", summary="Change the stream bitrate.", thumb=R("icon-prefs.png")))
	
	
def GetMainMenuItem(title, callbackKey):
	return DirectoryObject(
		key = callbackKey,
		title = title,
		thumb = R(CONFIG.DefaultTeamIcon)
	)
	
def BuildScheduleMenu(container, date, gameCallback, mainMenuCallback):
	# get games
	games = GetGamesForDay(date)
	
	if len(games) == 0:
		# no games
		raise NoGamesException
		
	matchupFormat = GetStreamFormatString("MatchupFormat")
	summaryFormat = GetStreamFormatString("SummaryFormat")
		 
	for game in games:
		title = GetStreamFormat(matchupFormat, game.AwayAbbreviation, game.HomeAbbreviation, game.UtcStart, game.Summary)
		summary = GetStreamFormat(summaryFormat, game.AwayAbbreviation, game.HomeAbbreviation, game.UtcStart, game.Summary)
		container.add(DirectoryObject(
			key = Callback(gameCallback, gameId = game.ID, title = title),
			title = title,
			summary = summary,
			thumb = R(CONFIG.DefaultTeamIcon)
		))

		
def BuildGameMenu(container, date, streamCallback):
	# get streams for game		
	streams, available = GetGameStreams(gameId, CONFIG.StreamFormat)
	
	quality = Prefs["videoQuality"]
	
	if not available:
		raise NotAvailableException
	
	for stream in streams:
		stream.Url = stream.Url.replace(QUALITY_MARKER, quality)
		team = GetTeamConfig(stream.Team)
		Log.Debug("Logo: " + team["Logo"])
		container.add(VideoClipObject(
			url = stream.Url,
			title = str(stream.Title).replace("{city}", team["Name"]),
			thumb = R(team["Logo"])
		))
	
	
def GetEasternNow():
	#utcNow = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S")
	utcNow = datetime.datetime.utcnow()
	utcNow = utcNow.replace(tzinfo = UTC)
	Log.Debug("UTC Now: " + str(utcNow))
	
	easternNow = utcNow.astimezone(EASTERN)
	Log.Debug("Eastern Now: " + str(easternNow))
	
	return easternNow
	
def GetGamesForDay(date):
	
	Log.Info("Get games for " + date)
	split = date.split("-")
	year = split[0]
	month = split[1]
	day = split[2]
	
	#http://nhlwc.cdnak.neulion.com/fs1/nhl/league/schedule/2013/10/06/iphone/schedule.json
	url = SCHEDULE_URL.replace("{year}", year).replace("{month}", month).replace("{day}", day)
	
	Log.Info("Schedule URL: " + url)
	
	schedule = JSON.ObjectFromURL(url)	
	Log.Info("Found " + str(len(schedule["games"])) + " games")
	
	games = []
	
	for game in schedule["games"]:
		gameId = game["gameId"]
		# status = "" when unstarted, "FINAL" when complete, probably something else when in progress.
		easternStart = datetime.datetime.strptime(date + " " + game["startTime"], "%Y-%m-%d %H:%M:%S")
		easternStart = easternStart.replace(tzinfo = EASTERN)
		utcStart = easternStart.astimezone(UTC)
		awayAbbr = game["a"]["ab"]
		homeAbbr = game["h"]["ab"] 
		summary = game["gamePreview"] # gameRecap when completed
		#self.UtcStart = utcStart
		#self.HomeCity = homeCity
		#self.AwayCity = awayCity
		#self.Summary = summary
		Log.Debug(awayAbbr + " at " + homeAbbr + " at " + str(easternStart) + "(eastern)/" + str(utcStart) + "(utc)")
		games.append(Game(gameId, utcStart, awayAbbr, homeAbbr, summary)) 
		
	return games

	
def GetStreamFormatString(key):
	CLIENT_OS =  Client.Platform
	
	format = L(key + CLIENT_OS)
	if str(format) == key + CLIENT_OS:
		# No client specific MatchupFormat, fallback to default
		format = L(key)
		
	return format
	

def GetStreamFormat(format, awayTeam, homeTeam, utcStart, summary):
	#Log.Debug("utcStart: " + str(utcStart))
	localStart = utcStart.astimezone(HERE).strftime("%H:%M")
	#Log.Debug("localStart: " + str(localStart))
	
	#away = CONFIG.Teams[awayTeam]["City"] + " " + CONFIG.Teams[awayTeam]["Name"]
	#home = CONFIG.Teams[homeTeam]["City"] + " " + CONFIG.Teams[homeTeam]["Name"]
	away = FormatTeamName(awayTeam)
	home = FormatTeamName(homeTeam)
	
	return str(format).replace("{away}", away).replace("{home}", home).replace("{time}", localStart).replace("{summary}", summary)
	
def GetTeamConfig(team):
	if team in CONFIG.Teams:
		return CONFIG.Teams[team]
	else:
		# create a new team so it's null safe 
		Log.Info("Could not find team configuration for '" + team + "'")
		return { "City": team, "Name": team, "Logo": CONFIG.DefaultTeamIcon }
		
def FormatTeamName(team):
	teamConfig = GetTeamConfig(team)
	
	if teamConfig["City"] == teamConfig["Name"]:
		return teamConfig["City"]
	else:
		return teamConfig["City"] + " " + teamConfig["Name"]
	
def NeedsPreferencesItem():
	# Rather than only show it for some items, we'll show for all and hide for some.
	# The list of those that don't need it is probably shorter and doesn't include hard to predict ones like browers
	# Showing it for iOS now, so it works with plex connect
	if Client.Platform in [ClientPlatform.Android]:
		return False
	else:
		return True

def GetGameList():

	#Log.Debug("GetGameList()")
	
	# thedate = datetime.datetime.now()
	# year = thedate.strftime("%Y")
	# month = thedate.strftime("%m")
	# day = thedate.strftime("%d")
	#stupid osx doesn't have .format available....	
	Log.Debug("Searching for: " + CONFIG.SportKeyword)
	url = SEARCH_URL.replace("{sport}", CONFIG.SportKeyword)
	
	#Log.Debug(url)
	
	#try:
	threadList = XML.ElementFromURL(url, cacheTime=None)
	#except:
		# reddit down likely
	#	return itemList
	
	items = threadList.xpath("//item")
	
	if len(items) == 0:
		# no threads in past week
		return []
		
	# we're only concerned with the most recent game
	item = items[0]
	threadUrl = item.xpath("./link/text()")[0]
	
	#Log.Debug("Opening thread: " + threadUrl)
	
	thread = XML.ElementFromURL(threadUrl + ".rss")
	selfPost = thread.xpath("//item")[0]
	Log.Debug("selfPost: " + selfPost.xpath("./description/text()")[0])
	description = HTML.ElementFromString(selfPost.xpath("./description/text()")[0])
	
	gamesXml = XML.ElementFromString(description.xpath("//p/text()")[0])
	#cache xml
	#This gets cached so we don't need to reload the XML when we open the game menu
	#We reload it each time we open the main menu, to avoid an out of date game list
	#Should probably read from the cache for a certain time period as well, since the games only change once per day.
	Data.Save("games", XML.StringFromElement(gamesXml))
	
	return GamesXmlToList(gamesXml)
	
def GamesXmlToList(xml):	
	list = []
		  
	#I should cache this data for the next calls...
	for game in xml.xpath("//game"): 
		gameId = GetSingleXmlValue(game, "./@id") 
		summary = GetSingleXmlValue(game, "./summary/text()")
		utcStartString = GetSingleXmlValue(game, "./utcStart/text()") #2013-05-18 17:00:00+0000
		#Log.Debug("utc string: " + utcStartString)
		#utcStart = datetime.datetime.strptime(utcStartString, "%Y-%m-%d %H:%M:%S%z")
		utcStart = parser.parse(utcStartString)
		# set timezone
		#utcStart = utcStart.replace(tzinfo=UTC)
		#utcStart.tzinfo = UTC 
		#Log.Debug("utc date: " + str(utcStart))
		homeCity = GetSingleXmlValue(game, "./homeTeam/@city")
		homeStreamName = GetSingleXmlValue(game, "./homeTeam/@streamName")
		awayCity = GetSingleXmlValue(game, "./awayTeam/@city")
		awayStreamName = GetSingleXmlValue(game, "./awayTeam/@streamName")
		homeServer = GetSingleXmlValue(game, "./homeTeam/@server")
		awayServer = GetSingleXmlValue(game, "./awayTeam/@server")
		#Log.Debug("gameID: " + gameId)
		
		# only add if the start time is within a reasonable window
		minutesToStart = GetMinutesToStart(utcStart)
		if minutesToStart > STREAM_HIDDEN_AFTER * -1: # -1 in the past			
			list.append(Game(gameId, utcStart, homeCity, awayCity, homeServer, awayServer, homeStreamName, awayStreamName, summary))
	
	return list
	
	
def GetSingleXmlValue(element, xpath):
	match = element.xpath(xpath)
	
	if len(match) > 0:
		return match[0]
	elif len(match) > 1:
		raise Exception("found " + str(len(match)) + " elements where 1 was expected")
	else:
		return ""
		

def GetMinutesToStart(utcStart):
	#Python's date handling is horrifically bad.
	gameStart = utcStart.replace(tzinfo = None) - datetime.datetime.utcnow()
	# to get a logical representation of how long in the future or past the game was, I have to do all this ridiculous math...
	minutesToStart = ((gameStart.microseconds + (gameStart.seconds + gameStart.days * 24 * 3600) * 10**6) / 10.0**6) / 60
	
	return minutesToStart
	
		
def GetGameStreams(gameId, stream_format):
 
	xml = XML.ElementFromString(Data.Load("games"))
	games = GamesXmlToList(xml)
	 
	streams = []
	UTC = tz.gettz("UTC")
	
	matchupFormat = GetStreamFormatString("MatchupFormat")
	
	for game in filter(lambda g: g.ID == gameId, games):
		minutesToStart = GetMinutesToStart(game.UtcStart)
		Log.Debug("game starts in: " + str(minutesToStart))
		
		available = minutesToStart <= STREAM_AVAILABLE_MINUTES_BEFORE
				  
		if game.HomeServer != "":
			title = str(L("HomeStreamLabelFormat"))
			desc = GetStreamFormat(matchupFormat, game.AwayCity, game.HomeCity, game.UtcStart, game.Summary)
			homeTeam = GetTeamConfig(game.HomeCity)
			#Log.Debug("description: " + desc)
			url = stream_format.replace("{server}", game.HomeServer).replace("{streamName}", game.HomeStreamName).replace("{city}", game.HomeCity).replace("{desc}", desc).replace("{logo}", homeTeam["Logo"])
			Log.Info("url: " + url)
			streams.append(Stream(title, url, game.HomeCity, available, game.Summary))
			
		if game.AwayServer != "":
			title = str(L("AwayStreamLabelFormat"))
			desc = GetStreamFormat(matchupFormat, game.AwayCity, game.HomeCity, game.UtcStart, game.Summary)
			awayTeam = GetTeamConfig(game.AwayCity)
			url = stream_format.replace("{server}", game.AwayServer).replace("{streamName}", game.AwayStreamName).replace("{city}", game.AwayCity).replace("{desc}", desc).replace("{logo}", awayTeam["Logo"])
			Log.Info("url: " + url)
			streams.append(Stream(title, url, game.AwayCity, available, game.Summary))
		
	return streams, available

