import re, urlparse, string, socket, sys, datetime
from dateutil import parser
from dateutil import tz

###############################################
VIDEO_PREFIX = "/video/hockey"
NAME = "Hockey"

ART = 'art-default.png'
ICON = 'icon-default.png'
DEFAULT_TEAM_ICON = "Team_DEFAULT.jpg"

SCHEDULE_URL = "https://raw.github.com/pudds/JsonData/master/h/{year}-{month}-{day}.json"
GAME_URL = "https://raw.github.com/pudds/JsonData/master/h/g/{gameid}.json"

STREAM_AVAILABLE_MINUTES_BEFORE = 20
STREAM_HIDDEN_AFTER = 360 # 6 hours oughta be plenty...
MAIN_MENU_EXTRA_DAYS = 3 # day count not including today and tomorrow
DATE_FORMAT = "%Y-%m-%d"

HERE = tz.tzlocal()
UTC = tz.tzutc()
EASTERN = tz.gettz("EST5EDT")


TEAMS = {
	"ANA": { "City": "Anaheim", "Name": "Ducks", "Logo": "Team_ANA.jpg", "LiveName":"ducks" },
	"BOS": { "City": "Boston", "Name": "Bruins", "Logo": "Team_BOS.jpg", "LiveName":"bruins" },
	"BUF": { "City": "Buffalo", "Name": "Sabres", "Logo": "Team_BUF.jpg", "LiveName":"sabres" },
	"CAR": { "City": "Carolina", "Name": "Hurricanes", "Logo": "Team_CAR.jpg", "LiveName":"hurricanes" },
	"CBJ": { "City": "Columbus", "Name": "Blue Jackets", "Logo": "Team_CBS.jpg", "LiveName":"bluejackets" },
	"CGY": { "City": "Calgary", "Name": "Flames", "Logo": "Team_CGY.jpg", "LiveName":"flames" },
	"CHI": { "City": "Chicago", "Name": "Blackhawks", "Logo": "Team_CHI.jpg", "LiveName":"blackhawks" },
	"COL": { "City": "Colorado", "Name": "Avalanche", "Logo": "Team_COL.jpg", "LiveName":"avalanche" },
	"DAL": { "City": "Dallas", "Name": "Stars", "Logo": "Team_DAL.jpg", "LiveName":"stars" },
	"DET": { "City": "Detroit", "Name": "Red Wings", "Logo": "Team_DET.jpg", "LiveName":"redwings" },
	"EDM": { "City": "Edmonton", "Name": "Oilers", "Logo": "Team_EDM.jpg", "LiveName":"oilers" },
	"FLA": { "City": "Florida", "Name": "Panthers", "Logo": "Team_FLA.jpg", "LiveName":"panthers" },
	"LAK": { "City": "Los Angeles", "Name": "Kings", "Logo": "Team_LOS.jpg", "LiveName":"kings" },
	"MIN": { "City": "Minnesota", "Name": "Wild", "Logo": "Team_MIN.jpg", "LiveName":"wild" },
	"MTL": { "City": "Montreal", "Name": "Canadiens", "Logo": "Team_MON.jpg", "LiveName":"canadiens" },
	"NJD": { "City": "New Jersey", "Name": "Devils", "Logo": "Team_NJD.jpg", "LiveName":"devils" },
	"NSH": { "City": "Nashville", "Name": "Predators", "Logo": "Team_NSH.jpg", "LiveName":"predators" },
	"NYI": { "City": "NY", "Name": "Islanders", "Logo": "Team_NYI.jpg", "LiveName":"islanders" },
	"NYR": { "City": "NY", "Name": "Rangers", "Logo": "Team_NYR.jpg", "LiveName":"rangers" },
	"OTT": { "City": "Ottawa", "Name": "Senators", "Logo": "Team_OTT.jpg", "LiveName":"senators" },
	"PHI": { "City": "Philadelphia", "Name": "Flyers", "Logo": "Team_PHI.jpg", "LiveName":"flyers" },
	"PHX": { "City": "Phoenix", "Name": "Coyotes", "Logo": "Team_PHX.jpg", "LiveName":"coyotes" },
	"PIT": { "City": "Pittsburgh", "Name": "Penguins", "Logo": "Team_PIT.jpg", "LiveName":"penguins" },
	"SJS": { "City": "San Jose", "Name": "Sharks", "Logo": "Team_SAN.jpg", "LiveName":"sharks" },
	"STL": { "City": "St. Louis", "Name": "Blues", "Logo": "Team_STL.jpg", "LiveName":"blues" },
	"TBL": { "City": "Tampa Bay", "Name": "Lightning", "Logo": "Team_TAM.jpg", "LiveName":"lightning" },
	"TOR": { "City": "Toronto", "Name": "Maple Leafs", "Logo": "Team_TOR.jpg", "LiveName":"mapleleafs" },
	"VAN": { "City": "Vancouver", "Name": "Canucks", "Logo": "Team_VAN.jpg", "LiveName":"canucks" },
	"WPG": { "City": "Winnipeg", "Name": "Jets", "Logo": "Team_WPG.jpg", "LiveName":"jets" },
	"WSH": { "City": "Washington", "Name": "Capitals", "Logo": "Team_WSH.jpg", "LiveName":"capitals" }
}

###############################################	

class NotAvailableException(Exception):
	pass
	
	Minutes = STREAM_AVAILABLE_MINUTES_BEFORE
	
class NoGamesException(Exception):
	pass
	

class Game:
	def __init__(self, id, seasonId, type, gameNumber, utcStart, summary, home, away): # pbp
		self.Id = id
		self.SeasonId = seasonId
		self.Type = type
		self.GameNumber = gameNumber
		self.UtcStart = utcStart
		self.Summary = summary
		self.Home = home
		self.Away = away
				
class Team:
	def __init__(self, ab, record, live, replayShort, replayFull):
		self.AB = ab
		self.Record = record
		self.Live = live
		self.ReplayShort = replayShort
		self.ReplayFull = replayFull
		
class GameSummary:
	def __init__(self, id, utcStart, summary, home, away): # pbp
		self.Id = id
		self.UtcStart = utcStart
		self.Summary = summary
		self.Home = home
		self.Away = away
		
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
	yesterdayDate = todayDate - datetime.timedelta(days = 1)
	
	today = datetime.datetime.strftime(todayDate, DATE_FORMAT)
	tomorrow = datetime.datetime.strftime(tomorrowDate, DATE_FORMAT)
	yesterday = datetime.datetime.strftime(yesterdayDate, DATE_FORMAT)
	
	#temp
	container.add(GetDirectoryItem("Yesterday", Callback(scheduleCallback, date = yesterday, title = "Yesterday")))
	container.add(GetDirectoryItem(L("TodayLabel"), Callback(scheduleCallback, date = today, title = L("TodayLabel"))))
	container.add(GetDirectoryItem(L("TomorrowLabel"), Callback(scheduleCallback, date = tomorrow, title = L("TomorrowLabel"))))
	
	dateFormat = str(L("ScheduleDateFormat")) # strftime can't take a localstring for some reason.	
	for x in range(1, MAIN_MENU_EXTRA_DAYS + 1):
		date = tomorrowDate + datetime.timedelta(days = x)
		dateString = datetime.datetime.strftime(date, DATE_FORMAT)
		Log.Debug("Main menu date string: " + dateString)
		title = datetime.datetime.strftime(date, dateFormat)
		container.add(GetDirectoryItem(title, Callback(scheduleCallback, date = dateString, title = title)))
		
	#archive
	container.add(GetDirectoryItem(L("ArchiveLabel"), Callback(archiveCallback)))
	
	
def GetDirectoryItem(title, callbackKey):
	return DirectoryObject(
		key = callbackKey,
		title = title,
		thumb = R(DEFAULT_TEAM_ICON)
	)
	
def BuildScheduleMenu(container, date, gameCallback, mainMenuCallback):
	# get games
	games = GetGameSummariesForDay(date)
	
	if len(games) == 0:
		# no games
		raise NoGamesException
		
	matchupFormat = GetStreamFormatString("MatchupFormat")
	summaryFormat = GetStreamFormatString("SummaryFormat")

	for game in games:
		title = GetStreamFormat(matchupFormat, game.Away, game.Home, game.UtcStart, game.Summary) 
		summary = GetStreamFormat(summaryFormat, game.Away, game.Home, game.UtcStart, game.Summary)
		container.add(DirectoryObject(
			key = Callback(gameCallback, gameId = game.Id, title = title),
			title = title,
			summary = summary,
			thumb = R(DEFAULT_TEAM_ICON) 
		))

		
def BuildGameMenu(container, gameId, highlightsCallback, selectQualityCallback):
		
	url = GAME_URL.replace("{gameid}", gameId)
	Log.Debug("Loading game from url: " + url)
	game = JSON.ObjectFromURL(url)
	
	utcStart = parser.parse(game["utcStart"])
	liveStreamsAvailable = GetMinutesToStart(utcStart) <= STREAM_AVAILABLE_MINUTES_BEFORE

	#replays are always available (assuming the menu item appears), but for clarity, I'll use a variable here too
	replaysAvailable = True
	
	hostname = socket.gethostname()
	
	if hostname in ["puddsPC", "Poseidon"]:
		liveStreamsAvailable = True
		
	Log.Debug("Live Streams Available? " + str(liveStreamsAvailable))
		
	# if there is a live away stream, add that
	if game["a"]["live"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "liveAway", game["a"]["ab"], L("AwayStreamLabelFormat"), liveStreamsAvailable))

	if game["h"]["live"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "liveHome", game["h"]["ab"], L("HomeStreamLabelFormat"), liveStreamsAvailable))
		
	# replays
	if game["a"]["replayShort"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "replayShortAway", game["a"]["ab"], L("AwayReplayCondensedFormat"), replaysAvailable))
	if game["a"]["replayFull"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "replayFullAway", game["a"]["ab"], L("AwayReplayFullFormat"), replaysAvailable))
	
	if game["h"]["replayShort"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "replayShortHome", game["h"]["ab"], L("HomeReplayCondensedFormat"), replaysAvailable))
	if game["h"]["replayFull"] != "":
		container.add(GetStreamDirectory(selectQualityCallback, url, "replayFullHome", game["h"]["ab"], L("HomeReplayFullFormat"), replaysAvailable))
		
	if len(game["pbp"]) > 0:
		container.add(GetDirectoryItem(L("HighlightsLabel"), Callback(highlightsCallback, gameId = gameId, title = L("HighlightsLabel"))))
	


def BuildQualitySelectionMenu(container, url, logo):
		
	container.add(VideoClipObject(url = url + "4500", title = "4500", thumb = R(logo)))
	container.add(VideoClipObject(url = url + "3000", title = "3000", thumb = R(logo)))
	container.add(VideoClipObject(url = url + "1600", title = "1600", thumb = R(logo)))
	container.add(VideoClipObject(url = url + "1200", title = "1200", thumb = R(logo)))
	container.add(VideoClipObject(url = url + "800", title = "800", thumb = R(logo)))
	container.add(VideoClipObject(url = url + "400", title = "400", thumb = R(logo)))


def GetStreamDirectory(selectQualityCallback, gameUrl, type, teamAb, titleFormat, available):
	#STREAM_FORMAT = "http://nlds{server}.cdnak.neulion.com/nlds/nhl/{streamName}/as/live/{streamName}_hd_{q}.m3u8"
	team = GetTeamConfig(teamAb)
	Log.Debug("Add clip for " + team["City"])
	
	url = gameUrl + "?type=" + type + "&name=" + team["LiveName"] + "&logo=" + team["Logo"] + "&q=" #appended in next menu
	title = str(titleFormat).replace("{name}", team["Name"])
	
	# tie to video prefix..
	return DirectoryObject(
		key = Callback(selectQualityCallback, url = url, title = title, logo = team["Logo"], available = available),
		title = title,
		thumb = R(team["Logo"])
	)
	

	
def GetEasternNow():
	#utcNow = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S")
	utcNow = datetime.datetime.utcnow()
	utcNow = utcNow.replace(tzinfo = UTC)
	Log.Debug("UTC Now: " + str(utcNow))
	
	easternNow = utcNow.astimezone(EASTERN)
	Log.Debug("Eastern Now: " + str(easternNow))
	
	return easternNow
	
def GetGameSummariesForDay(date):
	
	Log.Info("Get games for " + date)
	
	split = date.split("-")
	year = split[0]
	month = split[1]
	day = split[2]
	
	url = SCHEDULE_URL.replace("{year}", year).replace("{month}", month).replace("{day}", day)
	Log.Info("Schedule URL: " + url)
	
	games = []
	
	try:
		schedule = JSON.ObjectFromURL(url)	
	except:
		Log.Error("Unable to open schedule url")
		# couldn't load url, return no games
		return games
	
	Log.Info("Found " + str(len(schedule)) + " games")	
		
	for item in schedule["games"]:		
		gameId = item["id"]
		utcStart = parser.parse(item["utcStart"])
		summary = item["summary"]
		home = item["h"]
		away = item["a"]
				
		Log.Debug(away + " at " + home + " at " + str(utcStart) + "(utc)")		
		
		game = GameSummary(gameId, utcStart, summary, home, away)		
		games.append(game) 
		
	return games

def GetTeamFromJson(json):
	ab = json["ab"]
	record = json["record"]
	live = json["live"]
	replayShort = json["replayShort"]
	replayFull = json["replayFull"]
	
	return Team(ab, record, live, replayShort, replayFull)

	
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
	if team in TEAMS:
		return TEAMS[team]
	else:
		# create a new team so it's null safe 
		Log.Info("Could not find team configuration for '" + team + "'")
		return { "City": team, "Name": team, "Logo": DEFAULT_TEAM_ICON}
		
def FormatTeamName(team):
	teamConfig = GetTeamConfig(team)
	
	if teamConfig["City"] == teamConfig["Name"]:
		return teamConfig["City"]
	else:
		return teamConfig["City"] + " " + teamConfig["Name"]
	

def GetMinutesToStart(utcStart):
	#Python's date handling is horrifically bad.
	gameStart = utcStart.replace(tzinfo = None) - datetime.datetime.utcnow()
	# to get a logical representation of how long in the future or past the game was, I have to do all this ridiculous math...
	minutesToStart = ((gameStart.microseconds + (gameStart.seconds + gameStart.days * 24 * 3600) * 10**6) / 10.0**6) / 60
	
	return minutesToStart
	
	