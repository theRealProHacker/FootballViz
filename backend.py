import pandas as pd
import json

def get_data(table_name:str):
    """Gets the dataframe from the given string"""
    path=f"./database/{table_name}.csv"
    df=pd.read_csv(path)
    assert (not df.empty)
    return df
 
def goal_per_money(goals,money): 
    if 0 == money: 
        return float("inf")
    else:
        return (goals / money) * 1_000_000

def points_per_goal(points, goals):	
    if goals == 0:
        return float("inf")
    else:
        return points/goals 

def points_per_money(points,money):
    if money == 0:
        return float("inf")  
    else:
        return (points/money) *  1_000_000

def goals_against_per_point(goals_against,points):
    if 0 in (goals_against,points) :
        return 0
    else:
        return goals_against/points  
 

MATCHES=get_data("Match")
TEAMS=get_data("Team")[["team_id","logo","color","description","wiki_source","homepage","founded","members","german_name"]]
ATTRIBUTES=get_data("Team_Attributes")
TRANSFERS=get_data("Transfers")

def find_in_df(df,**kwargs):
    """Finds the first row where the key equals the corresponding value"""
    for k,v in kwargs.items():
        df=df[df[k]==v]
    try:
        return df.iloc[0]
    except IndexError:
        return None

def rgb_to_hex(rgb):
    """Converts an rgb color as list or tuple to a hex string for html"""
    #https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '#%02x%02x%02x' % tuple(rgb)

def make_seasons():
    """Returns a list of seasons ordered from oldest to latest"""
    for season in range (2008,2016):
        yield f"{season}/{season+1}"

def get_all_teams():
    """Makes the data for all teams"""
    CAT_NAMES = [f"cat{i+1}" for i in range(4)]
    data=[]
    teams=[]

    for season in make_seasons():
        season_df=ATTRIBUTES[ATTRIBUTES["season"]==season]       
        data_appension={"x":season} #initialize season data with current season
        calc_maxes=[0]*4

        #calculate cats for each team
        for team_id in TEAMS["team_id"]:
            calc_vals=[0]*4
            attributes = find_in_df(season_df,team_id=team_id)
            if attributes is not None:
                _,assertion_team_id,season,points,goals,goals_against,perfect_games,money_spent = tuple(attributes) 
                if not assertion_team_id==team_id:return f"Actual team_id: {team_id}. Found: {assertion_team_id}"
                calc_vals=[
                    goal_per_money(goals,money_spent),
                    points_per_goal(points,goals),
                    average_goals_per_win(team_id, season),
                    int(perfect_games)
                ]
                for i,x in enumerate(calc_vals):calc_maxes[i] = max(calc_maxes[i],x)
            data_appension[team_id]=dict(zip(CAT_NAMES,calc_vals))
        #normalize data 
        for team_id,team_data in data_appension.items():
            if team_id=="x":continue #skip season
            tmp_data = team_data.copy() 
            for catname,catmax in zip(CAT_NAMES,calc_maxes):
                if(tmp_data[catname] == float("inf")):
                    tmp_data[catname] = 1 
                else: 
                    tmp_data[catname]/=catmax
            data_appension[team_id] = tmp_data 
        data.append(data_appension)

    for team in TEAMS.itertuples(index=False):
        team_id, logo, colors, description, wiki_source, homepage, founded, members, german_name = team
        colors=json.loads(colors)
        teams.append({
            "dataKey":team_id,
            "selected":True,
            "logo_src":logo.split("/")[-1],
            "color":rgb_to_hex(colors[0])
        })
    result={
        "data":data,
        "teams":teams
        }
    return json.dumps(result,ensure_ascii=False)

def average_goals_per_win(team_id, season):
    matches = getSeasonalData(team_id, season)
    vicotory, goals, goal_against = 0, 0, 0
    for match in matches:  
        home= getHomeTeam(team_id, match)
        if(match["home_goals"] > match["away_goals"] and home):
            vicotory += 1
            goals += match["home_goals"]
            goal_against += match["away_goals"]
        elif(match["home_goals"] < match["away_goals"] and not home):
            vicotory += 1
            goals += match["away_goals"]
            goal_against += match["home_goals"]
    return  vicotory / (goals - goal_against)


def get_average_goals_per_win(team_id, season):
    matches = getSeasonalData(team_id, season)
    vicotory, goals, goal_against = 0, 0, 0
    out = []
    for match in matches: 
        match_out = {}
        home= getHomeTeam(team_id, match)
        if(match["home_goals"] > match["away_goals"] and home):
            vicotory += 1
            goals += match["home_goals"]
            goal_against += match["away_goals"]
        elif(match["home_goals"] < match["away_goals"] and not home):
            vicotory += 1
            goals += match["away_goals"]
            goal_against += match["home_goals"]
        match_out["vicSum"] = vicotory
        match_out["goalSum"] = goals
        match_out = fillJson(match_out, match, home)
        out.append(match_out)
    return  {"matches" : out}


def getSeasonalData(team_id: int, season: str):
    season_df=MATCHES[MATCHES["season"]==season]
    home_df = season_df[season_df["home_id"] == team_id]
    away_df = season_df[season_df["away_id"] == team_id]
    matches = pd.concat([home_df, away_df] , ignore_index=True)
    matches["date"] = pd.to_datetime(matches["date"])
    matches = matches.sort_values(by="date")
    matches["date"] = matches["date"].dt.strftime("%d.%m.%Y").astype(str)
    matches = json.loads(matches.to_json(orient="records"))
    return matches 

def getSeasonalDataTransfer(team_id: int, season: str): 
    season_df = TRANSFERS[TRANSFERS["season"] == season]
    transfers = json.loads(season_df[season_df["team_id"] == team_id].to_json(orient="records"))
    tranfersIncomingSum = 0 
    transfersOutgoingSum = 0 
    out = []
    for transfer in transfers: 
        if(transfer["ingoing"]):
            tranfersIncomingSum += transfer["money"]
        else:
            transfersOutgoingSum += transfer["money"]
    out.append({"name" : "ingoing" ,"value" : (tranfersIncomingSum / 1_000_000) })
    out.append({"name" : "outgoing" ,"value" :(transfersOutgoingSum / 1_000_000) })
    return out

def fillJson(jsonToFill: dict , dataJson : dict , home: bool):
    jsonToFill["date"] = dataJson["date"]
    jsonToFill["goalHome"] = dataJson["home_goals"] if home else dataJson["away_goals"]
    jsonToFill["goalAgainst"] = dataJson["home_goals"] if not home else dataJson["away_goals"]
    jsonToFill["teamHome"] = find_in_df(TEAMS,team_id=dataJson["home_id"])["german_name"] if home else find_in_df(TEAMS,team_id=dataJson["away_id"])["german_name"] 
    jsonToFill["teamAgainst"] = find_in_df(TEAMS,team_id=dataJson["home_id"])["german_name"] if not home else find_in_df(TEAMS,team_id=dataJson["away_id"])["german_name"] 
    return jsonToFill

def getHomeTeam(team_id : int, match: dict ):
    if(team_id == match["home_id"]):
        home = True
    else:
        home = False
    return home

def getMoneyDayData(team_id : int, season: str):
    matches = getSeasonalData(team_id, season)
    goals = 0
    out = []
    home = True
    transferData = getSeasonalDataTransfer(team_id, season)
    for match in matches:
        match_out = {}
        home = getHomeTeam(team_id, match)
        if(home):
            goals += match["home_goals"]
        else:
            goals += match["away_goals"]

        match_out["goalSum"] = goals
        match_out = fillJson(match_out, match, home)
        out.append(match_out)
    return { "matches" : out , "transfers" : transferData }

def getPointGoalData(team_id : int, season: str):
    matches = getSeasonalData(team_id, season)
    points = 0
    out = []
    home = True
    goals = 0
    for match in matches:
        match_out = {}
        home= getHomeTeam(team_id, match)
        if(home):
            goals += match["home_goals"]
        else:
            goals += match["away_goals"]
        if(match["home_goals"] == match["away_goals"]): 
            points += 1 
        elif(match["home_goals"] > match["away_goals"] and home):
            points += 3
        elif(match["home_goals"] < match["away_goals"] and not home):
            points += 3
        match_out["pointSum"] = points
        match_out["goalSum"] = goals
        match_out = fillJson(match_out, match, home)
        out.append(match_out)
    return {"matches": out}

def getPefectGameData(team_id : int, season: str):
    matches = getSeasonalData(team_id, season)
    perfectGames = 0
    out = []
    home = True
    for match in matches:
        match_out = {}
        home= getHomeTeam(team_id, match)
        if(match["home_goals"] > 0 and home and match["away_goals"] == 0 ): 
            perfectGames += 1 
        elif(match["home_goals"] == 0 and not home and match["away_goals"] > 0 ): 
            perfectGames += 1 
        match_out["perfectGames"] = perfectGames
        match_out = fillJson(match_out, match, home)
        out.append(match_out)
    return {"matches": out}

def getPointsPerMoneyData(team_id : int, season: str):
    matches = getSeasonalData(team_id, season)
    transferData = getSeasonalDataTransfer(team_id, season)
    points = 0
    out = []
    home = True
    for match in matches:
        match_out = {}
        home= getHomeTeam(team_id, match)
        if(match["home_goals"] == match["away_goals"]): 
            points += 1 
        elif(match["home_goals"] > match["away_goals"] and home):
            points += 3
        elif(match["home_goals"] < match["away_goals"] and not home):
            points += 3
        match_out["pointSum"] = points
        match_out = fillJson(match_out, match, home)
        out.append(match_out)
    return { "matches" : out , "transfers" : transferData }

def calc_mean(l):
    length = len(l)
    assert (length>0)
    return sum(l)/length

def get_team_and_comp(main_team_id,comp_team_id):
    CAT_NAMES = [f"cat{i+1}" for i in range(4)]
    team=find_in_df(TEAMS,team_id=main_team_id)
    team_id_for_assertion, logo, colors, description, wiki_source, homepage, founded, members, german_name = team
    colorsC = find_in_df(TEAMS, team_id=comp_team_id)[2] if comp_team_id else colors
    if not team_id_for_assertion==main_team_id:return f"Actual team_id: {main_team_id}. Found: {team_id_for_assertion}"
    team_dict={
        "name":german_name,
        "description":description,
        "color": rgb_to_hex(json.loads(colors)[0]),
        "colorC": rgb_to_hex(json.loads(colorsC)[0]),
        "wiki_source":wiki_source,
        "founded":founded,
        "url":homepage,
        "members":members
    }
    data=[]
    for season in make_seasons():
        season_df=ATTRIBUTES[ATTRIBUTES["season"]==season]    
        data_appension={"x":season} #initialize season data with current season
        calc_sums=[[],[],[],[]]
        calc_maxes=[0]*4
        btween_save={}
        for team_id in TEAMS["team_id"]:
            calc_vals=[0]*4
            attributes = find_in_df(season_df,team_id=team_id)
            if attributes is not None: 
                _,assertion_team_id,season,points,goals,goals_against,perfect_games,money_spent = tuple(attributes)
                if not assertion_team_id==team_id:return f"Actual team_id: {team_id}. Found: {assertion_team_id}"
                calc_vals=[
                    goal_per_money(goals,money_spent),
                    points_per_goal(points,goals),
                    average_goals_per_win(team_id, season), 
                    int(perfect_games  )
                ]
                #make calc_maxes contain max values for each cat
                for i,x in enumerate(calc_vals):
                    calc_maxes[i] = max(calc_maxes[i],x)
                    calc_sums[i].append(x)
                if team_id==main_team_id:btween_save[""]=calc_vals
                if team_id==comp_team_id:btween_save["c"]=calc_vals
        if comp_team_id is None: btween_save["c"]=[calc_mean(v) for v in calc_sums] 
        for appendix,cats in btween_save.items():
            for i,v in enumerate(cats):
                name=CAT_NAMES[i]
                v = 1 if v == float("inf") else v 
                data_appension[name+appendix]=v
        data.append(data_appension)
    team_dict["data"] = data 
    return json.dumps(team_dict,ensure_ascii=False)
 

if(__name__ == "__main__"):
    get_team_and_comp(9823, None )

