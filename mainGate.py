import requests
import json
import sqlite3
import time
import math
import sys
import os

class gateway:

    def __init__(self):
        self.dbArray = {}
        self.defaultDB = "Newgrounds.db"
        
        self.initDatabase(self.defaultDB)
        
        self.getScores = False # Export user scores
        self.getSaveFiles = False # Export user submitted data
        self.seperateData = False # Keeps saves and score entries in a seperate database
        self.exportJson = False
        
        print("Starting Newgrounds Gateway class...")
    
    
    # Handles initiating multible databases
    def initDatabase(self, databaseName, subDB = False):
        tables = ["movies", "medals", "scoreboards", "save_groups", "scores", "saves"]
        
        if databaseName in self.dbArray:
            print("- Database already initiated: " + databaseName)
            return

        self.dbArray[databaseName] = {}
        self.dbArray[databaseName]["con"] = sqlite3.connect(databaseName)
        self.dbArray[databaseName]["cur"] = self.dbArray[databaseName]["con"].cursor()
        
        if subDB:
            tables = ["scores", "saves"]
        
        for table in tables:
            with open(os.getcwd() + f"\\sql\\{table}.sql") as tableQuery:
                self.dbArray[databaseName]["cur"].execute(tableQuery.read())
        
        self.dbArray[databaseName]["con"].commit()
    
    def getSeperateDB(self, app_id):
        entriesDatabase = self.defaultDB
        
        if self.seperateData:
            entriesDatabase = str(app_id).replace(":","_") + ".db"
            self.initDatabase(entriesDatabase, True)
        
        return entriesDatabase
            
        
    
    # Make a url request, and be polite to request limits
    def urlReq(self, url, params):
        data = None
        while data == None:
            try:
                data = requests.post(url, params)

                if data.content.decode().strip()[0] != "{":
                    print("Error with response, likely timeout. Retrying")
                    data = None
                    time.sleep(10)
                
            except:
                print("! connection failed! retrtying")
                time.sleep(10)

        time.sleep(1)
        return data
    
    def urlGet(self, url):
        data = None
        while data == None:
            try:
                data = requests.get(url)
                
            except:
                print("! connection failed! retrtying")
                time.sleep(10)

        time.sleep(1)
        return data
        
    
    def dbReq(self, query, databaseName = "Newgrounds.db"):
        if databaseName not in self.dbArray:
            print("- Database not initiated: " + databaseName)
        
        self.dbArray[databaseName]["cur"].execute(query)
        self.dbArray[databaseName]["con"].commit()
        return self.dbArray[databaseName]["cur"].fetchall()
            
    
    def formatQuery(self, table, item):
        colToJson = ["ratings", "keys"]
        col = ""
        vals = ""
        i = 0
        for x in item:
            val = item[x]
            if x in colToJson:
                val = json.dumps(item[x])
   
            if i <= len(item) and i != 0 and val != 'null':
                col += ','
                vals += ','

            i = i + 1
            
            if val == 'null':
                continue
                
            col += x
            vals += '"' + str(val).replace('"','""') + '"'

        return f'INSERT INTO {table} ({col}) VALUES ({vals})'
    
    
    # Helps with guessing a mystery medal file name
    def filterMedalName(self, char):
        if char.isnumeric() or char.isalpha():
            return True
        else:
            return False
    
    
    def guessMysteryMedal(self, app_id, medal_id, medal_name):
        if ":" in app_id:
            app_id = int(app_id.split(":")[0])
        
        possibleExts = [".png", ".jpg", ".webp", ".gif"]
        guessedName = str(medal_id) + '_' + ''.join(filter(self.filterMedalName, medal_name)).lower()
        medalDir = math.floor(int(app_id) / 1000) * 1000
        
        for x in possibleExts:
            guessUrl = f"{medalDir}/{app_id}/" + guessedName + x
            urlStatus = self.urlGet("https://apifiles.ngfiles.com/medals/" + guessUrl).status_code
            if urlStatus == 200:
                print("! Found mystery medal: " + guessUrl)
                return guessUrl
        
        print("- Could not guess mystery medal img: " + medal_name)
        
        return None
    

    # Make an input parameter for gateway 3 requests
    def makeGatewayInput(self, app_id, components):
        input = {}
        input['app_id'] = app_id
        input['call'] = []

        for x in components:
            comp = {}
            comp['component'] = x[0]
            comp['parameters'] = {}
            
            if len(x) == 2:
                comp['parameters'] = x[1]
            
            input['call'].append(comp)
        
        return input
    
    
    def gateway3Req(self, param):
        url = "https://newgrounds.io/gateway_v3.php"
        data = self.urlReq(url, {"input": json.dumps(param)})
        responseJson = json.loads(data.content)
        return responseJson


    def gatewayReq(self, params):
        url = "https://www.ngads.com/gateway_v2.php"
        data = self.urlReq(url, params)
        responseJson = json.loads(data.content)
        
        if responseJson['success'] == 1:
            return responseJson
        
        elif responseJson['error_msg'] == params['tracker_id']:
            print("! tracker_id error")
            return []
        
        else:
            print("error: " + responseJson['error_msg'])
            
            return responseJson
    
    
    
    
    
    
    # Main function:
    
    def addScoreboads(self, app_id):
        print("Adding scoreboards")
        inputObj = base.makeGatewayInput(app_id, [["ScoreBoard.getBoards"]])
        boardResponse = base.gateway3Req(inputObj)
        totalBoards = 0
        
        if boardResponse['success']:
            for x in boardResponse['result']:
                if x['component'] ==  "ScoreBoard.getBoards":
                    for y in x['data']['scoreboards']:
                        totalBoards += 1
                        boardExists = len(self.dbReq('SELECT * FROM scoreboards WHERE board_id=' + str(y['id']))) != 0
                        if not boardExists:
                            boardObj = {}
                            boardObj['app_id'] = app_id
                            boardObj['board_id'] = y['id']
                            boardObj['board_name'] = y['name']
                            self.dbReq(self.formatQuery("scoreboards", boardObj))
                        else:
                            print("! Board already in database: " + str(y['id']))
                        
                        if self.getScores:
                            self.scrapeScoreboard(y['id'], app_id)
        
        print("! Found " + str(totalBoards) + " scoreboards")
    
    
    def addMovie(self, app_id):
        movieExists = len(self.dbReq('SELECT app_id FROM movies WHERE app_id="'+app_id+'"')) != 0
        
        if not movieExists:
            params = {}
            params['tracker_id'] = app_id
            params['command_id'] = "connectMovie"
            gameResponse = self.gatewayReq(params)
            
            if gameResponse == []:
                return False
            
            movieObj = {}
            movieObj['app_id'] = app_id
            movieObj['movie_name'] = gameResponse['movie_name']
            
            self.dbReq(self.formatQuery("movies", movieObj))

        else:
            print("- movie already exists in database: " + app_id)
        
        self.addSaveGroups(app_id)
        
        return True
    
    def scrapeSaveFiles(self, app_id, group_id, keys, ratings):
        print("Adding saves for group: " + str(group_id))
        
        entriesDatabase = self.getSeperateDB(app_id)
        
        page = 1
        moreExist = True
        totalSaves = 0
        
        # Make sub query
        subQuery = {}
        subQuery['num_results'] = 30
        
        if len(keys) > 0:
            keyArr = []
            for x in keys:
                keyArr.append(int(x['id']))
            subQuery['lookup_keys'] = keyArr
        
        if len(ratings) > 0:
            ratingArr = []
            for x in ratings:
                ratingArr.append(int(x['id']))
            subQuery['lookup_ratings'] = ratingArr
        
        # Iterate data
        while moreExist:
            subQuery['page'] = page

            saveQuery = {}
            saveQuery['group_id'] = group_id
            saveQuery['tracker_id'] = app_id
            saveQuery['command_id'] = "lookupSaveFiles"
            saveQuery['query'] = json.dumps(subQuery)
            
            saveData = self.gatewayReq(saveQuery)
            
            moreExist = len(saveData['files']) != 0
            
            for x in saveData['files']:
                totalSaves += 1
                saveExists = len(self.dbReq('SELECT save_id FROM saves WHERE save_id="'+str(x['save_id'])+'"', entriesDatabase)) != 0
                if not saveExists:
                    x.pop("file")
                    x['group_id'] = group_id
                    self.dbReq(self.formatQuery("saves", x), entriesDatabase)
            
            page += 1
            
        print("! Found " + str(totalSaves) + " save files")
        
    
    
    # Add save_group entries
    def addSaveGroups(self, app_id):
        print("Adding Save Groups")
        
        params = {}
        params['command_id'] = "preloadSettings"
        params['tracker_id'] = app_id
        settingsData = self.gatewayReq(params)
        
        totalGroups = 0
        
        if "save_groups" in settingsData:
            for x in settingsData['save_groups']:
                totalGroups += 1
                groupExists = len(self.dbReq('SELECT group_id FROM save_groups WHERE group_id="'+str(x['group_id'])+'" AND app_id="'+str(app_id)+'"')) != 0
                if not groupExists:
                    groupObj = {}
                    groupObj['app_id'] = app_id
                    groupObj['group_id'] = x['group_id']
                    groupObj['group_name'] = x['group_name']
                    groupObj['group_type'] = x['group_type']
                    groupObj['keys'] = x['keys']
                    groupObj['ratings'] = x['ratings']
                    
                    self.dbReq(self.formatQuery("save_groups", groupObj))

                if self.getSaveFiles:
                    self.scrapeSaveFiles(app_id, x['group_id'], x['keys'], x['ratings'])
            
        print("! Found " + str(totalGroups) + " groups")
        
    
    
    def getMedals(self, app_id):
        
        movieStatus = self.addMovie(app_id)
        
        if not movieStatus:
            print("- Movie does not exist with ID")
            return
        
        self.addScoreboads(app_id)
        
        params = {}
        params['command_id'] = "preloadSettings"
        params['tracker_id'] = app_id
        
        gatewayJson = self.gatewayReq(params)
        
        print("Adding medals: " + app_id)
        
        if 'medals' not in gatewayJson:
            print("- game_id has no badges: " + str(app_id))
            return
        
        totalMedals = 0
        
        for x in gatewayJson['medals']:
            totalMedals += 1
            medalExists = len(self.dbReq('SELECT medal_id FROM medals WHERE medal_id="'+str(x['medal_id'])+'"')) != 0
            
            if not medalExists:
                medalEntry = x
                
                if x['secret']:
                    medalEntry.pop("medal_icon")
                    guessTry = self.guessMysteryMedal(app_id, x['medal_id'], x['medal_name'])
                    if guessTry != None:
                        medalEntry['medal_icon'] = guessTry
                    
                else:
                    medalEntry['medal_icon'] = x['medal_icon'].split("ngfiles.com/medals/")[1]
                
                medalEntry['app_id'] = app_id
                medalEntry.pop("medal_unlocked")

                self.dbReq(self.formatQuery("medals", medalEntry))
            
            else:
                print("! Medal already in database: " + str(x['medal_id']))
        
        print("! Found " + str(totalMedals) + " medals!")
    
    
    # Download scoreboard entries
    def scrapeScoreboard(self, board_id, app_id):
        print("Adding scoreboard entries: " + str(board_id))
        entriesExist = True
        page = 1
        totalScores = 0
        entriesDatabase = self.getSeperateDB(app_id)
        
        while entriesExist:
            paramObj = {}
            paramObj['publisher_id'] = 1
            paramObj['board'] = board_id
            paramObj['page'] = page
            paramObj['num_results'] = 30
            paramObj['period'] = "All-Time"
            paramObj['tracker_id'] = app_id
            paramObj['command_id'] = "loadScores"
            
            scoreDat = self.gatewayReq(paramObj)
            

            if "scores" in scoreDat:
                entriesExist = len(scoreDat['scores']) > 0
                totalScores += len(scoreDat['scores'])
                for x in scoreDat['scores']:
                    scoreExists = len(self.dbReq('SELECT user_id FROM scores WHERE board_id="'+str(board_id)+'" AND user_id="'+str(x['user_id'])+'"', entriesDatabase)) != 0
                    
                    if not scoreExists:
                        scoreObj = {}
                        scoreObj['board_id'] = board_id
                        scoreObj['user_id'] = x['user_id']
                        scoreObj['username'] = x['username']
                        scoreObj['value'] = x['value']
                        scoreObj['numeric_value'] = x['numeric_value']
                        scoreObj['tag'] = x['tag']
                        
                        self.dbReq(self.formatQuery("scores", scoreObj), entriesDatabase)
                
                page += 1
            
            else:
                print("Error in scoreboard request, ending")
                entriesExist = False
        
        print("! Found " + str(totalScores) + " scores")
    
    
    def exportMovieJson(self, app_id):
        jsonPath = os.getcwd() + "\\exports\\"
        jsonFilename = str(app_id).replace(":","_") + ".json"
        exportObj = {}
        
        if not os.path.exists(jsonPath):
            os.makedirs(jsonPath)
        
        # Movie
        movieDat = self.dbReq('SELECT * FROM movies WHERE app_id="'+str(app_id)+'"')[0]
        exportObj['movies'] = {"app_id":movieDat[0], "movie_name": movieDat[1], "encryptionKey": movieDat[2]}
        
        # Medals
        medalDat = self.dbReq('SELECT * FROM medals WHERE app_id="'+str(app_id)+'"')
        exportObj['medals'] = []
        for x in medalDat:
            medalObj = {}
            medalObj['app_id'] = x[0]
            medalObj['medal_id'] = x[1]
            medalObj['medal_name'] = x[2]
            medalObj['medal_description'] = x[3]
            medalObj['medal_icon'] = x[4]
            medalObj['medal_difficulty'] = x[5]
            medalObj['medal_value'] = x[6]
            medalObj['secret'] = x[7]
            exportObj['medals'].append(medalObj)
        
        # save_groups
        groupDat = self.dbReq('SELECT * FROM save_groups WHERE app_id="'+str(app_id)+'"')
        exportObj['save_groups'] = []
        for x in groupDat:
            groupObj = {}
            groupObj['app_id'] = x[0]
            groupObj['group_id'] = x[1]
            groupObj['group_name'] = x[2]
            groupObj['group_type'] = x[3]
            groupObj['keys'] = x[4]
            groupObj['ratings'] = x[5]
            exportObj['save_groups'].append(groupObj)
        
        # Scoreboards
        boardDat = self.dbReq('SELECT * FROM scoreboards WHERE app_id="'+str(app_id)+'"')
        exportObj['scoreboards'] = []
        for x in boardDat:
            boardObj = {}
            boardObj['app_id'] = x[0]
            boardObj['board_id'] = x[1]
            boardObj['board_name'] = x[2]
            exportObj['scoreboards'].append(boardObj)
        
        with open(jsonPath + jsonFilename, "w") as writeFile:
            writeFile.write(json.dumps(exportObj))
        
        print("! Export json for: " + str(app_id))
      
      
    def mainFlow(self):
        if len(sys.argv) < 2:
            fileName = os.path.basename(__file__)
            print(f"Usage: python {fileName} [app_id] ['scoreboards','savefiles','split']")
            return
        
        # init extra commands
        if len(sys.argv) > 2:
            i = 2
            while i < len(sys.argv):
                match sys.argv[i]:
                    case "scoreboards":
                        print("[] Enabled getScores")
                        self.getScores = True
                    
                    case "savefiles":
                        print("[] Enabled getSaveFiles")
                        self.getSaveFiles = True
                    
                    case "seperateData":
                        print("[] Enabled seperateData")
                        self.seperateData = True
                    
                    case "exportJson":
                        print("[] Enabled exportJson")
                        self.exportJson = True
                
                i += 1
        
        app_id = sys.argv[1]

        base.getMedals(app_id)
        
        if self.exportJson:
            self.exportMovieJson(app_id)
    
    
        
        


base = gateway()
base.mainFlow()
