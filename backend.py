import pandas as pd
import numpy as np
import json

def get_data(table_name:str):
    """Gets the dataframe from the given string"""
    path=f"./database/{table_name}.csv"
    df=pd.read_csv(path)
    assert (not df.empty)
    return df

def goal_per_money(goals,money):
    if 0 in (goals,money): 
        return 0
    else:
        return goals/money * 1000000 #goals per 1000000 € spent

def points_per_goal(points, goals):	
    if not points*goals:
        return 0
    else:
        return goals/points #goals per point

def points_per_money(points,money):
    if 0 in (points,money):
        return 0
    else:
        return points/money * 1000000 #points per 1000000 € spent

def goals_against_per_point(goals_against,points):
    if 0 in (goals_against,points):
        return 0
    else:
        return goals_against/points # goals_against per point

#MATCHES=get_data("Match")
TEAMS=get_data("Team")[["team_id","logo","color","description","wiki_source","german_name"]]
ATTRIBUTES=get_data("Team_Attributes")
#TRANSFERS=get_data("Transfers")

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

# def normalize_groups(df,groupby,normalize):
#     groups = df.groupby(groupby)
#     mean, std = groups.transform("mean"), groups.transform("std")
#     normalized = (df[mean.columns] - mean) / std
#     return normalized

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
                    points_per_money(points,money_spent),
                    perfect_games
                ]
                for i,x in enumerate(calc_vals):calc_maxes[i] = max(calc_maxes[i],x)
            data_appension[team_id]=dict(zip(CAT_NAMES,calc_vals))
        #normalize data
        for team_id,team_data in data_appension.items():
            if team_id=="x":continue #skip season
            for catname,catmax in zip(CAT_NAMES,calc_maxes):
                team_data[catname]/=catmax
            data_appension[team_id]=team_data
        data.append(data_appension)
    for team in TEAMS.itertuples(index=False):
        team_id, logo, colors, description, wiki_source, german_name = team
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

def get_seasonal_data(teams,attributes):
    """Gets seasonal_data"""
    CAT_NAMES = [f"cat{i+1}" for i in range(4)]
    data = []
    df = teams.merge(attributes,on="team_id")
    grouped_by_season = df.groupby("season")
    for season, group in grouped_by_season:
        season_data={"season":season}
        group=group[["team_id","points","goals","goals_against","perfect_games","money_spent"]]
        for row in group.itertuples(index=False):
            team_id,points,goals,goals_against,perfect_games,money_spent = row
            calc_vals=[
                goal_per_money(goals,money_spent),
                points_per_goal(points,goals),
                points_per_money(points,money_spent),
                perfect_games
            ]
            row_cats = dict(zip(CAT_NAMES,calc_vals))
            season_data[team_id]=row_cats
        data.append(season_data)
    return data

def calc_mean(l):
    length = len(l)
    assert (length>0)
    return sum(l)/length

def get_team_and_comp(main_team_id,comp_team_id):
    CAT_NAMES = [f"cat{i+1}" for i in range(4)]
    team=find_in_df(TEAMS,team_id=main_team_id)
    team_id_for_assertion, logo, colors, description, wiki_source, german_name = team
    if not team_id_for_assertion==main_team_id:return f"Actual team_id: {main_team_id}. Found: {team_id_for_assertion}"
    team_dict={
        "name":german_name,
        "description":description,
        "color":json.loads(colors)[0],
        "wiki_source":wiki_source,
        "founded":"?",
        "url":"?",
        "members":"?"
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
                    points_per_money(points,money_spent),
                    perfect_games
                ]
                #make calc_maxes contain max values for each cat
                for i,x in enumerate(calc_vals):
                    calc_maxes[i] = max(calc_maxes[i],x)
                    calc_sums[i].append(x)
                if team_id==main_team_id:btween_save[""]=calc_vals
                if team_id==comp_team_id:btween_save["c"]=calc_vals
        if comp_team_id is None: btween_save["c"]=[calc_mean(v) for v in calc_sums]
        btween_save = {k:[v/calc_maxes[i] for i,v in enumerate(vals)] for k,vals in btween_save.items()} #normalize data
        for appendix,cats in btween_save.items():
            for i,v in enumerate(cats):
                name=CAT_NAMES[i]
                data_appension[name+appendix]=v
        data.append(data_appension)
    team_dict["data"] = data
    return json.dumps(team_dict,ensure_ascii=False)
