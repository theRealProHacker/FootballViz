import json

from flask import Flask

from cat_calculator import *
from data_getter import get_data

app=Flask(__name__)

MATCHES=get_data("Match")
TEAMS=get_data("Team")
ATTRIBUTES=get_data("Team_Attributes")
TRANSFERS=get_data("Transfers")

def rgb_to_hex(rgb):
    """Converts an rgb color as list or tuple to a hex string for html"""
    #https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '#%02x%02x%02x' % tuple(rgb)

def get_data(teams,attributes,cumulative:bool):
    """Merges teams with attributes and sometimes makes the cumulative data for the Stream Graph"""
    CAT_NAMES = [f"cat{i+1}" for i in range(4)]
    def put_together(single_cats,before_cats):
        """Puts together the values for this row and the values before and returns the data for 
        the api and the new current vals"""
        next_cats={}
        for k,v in before_cats.items():
            try:
                next_cats[k] = v + single_cats[k]
            except KeyError:
                print(single_cats,before_cats,next_cats)
        return ([before_cats,next_cats],next_cats)
    data = []
    df = teams.merge(attributes,on="team_id")
    grouped_by_season = df.groupby("season")
    for season, group in grouped_by_season:
        season_data={"season":season}
        group=group[["team_id","points","goals","goals_against","perfect_games","money_spent"]]
        if cumulative:current_vals={cn:0 for cn in CAT_NAMES}
        for row in group.itertuples(index=False):
            team_id,points,goals,goals_against,perfect_games,money_spent = row
            calc_vals=[
                goal_per_money(goals,money_spent),
                points_per_goal(points,goals),
                points_per_money(points,money_spent),
                goals_against_per_point(goals_against,points)
            ]
            row_cats = dict(zip(CAT_NAMES,calc_vals))
            if cumulative:
                season_data[team_id],current_vals=put_together(row_cats,current_vals)
            else:
                season_data[team_id]=row_cats
        data.append(season_data)
    return data

@app.route("/teams")
def get_all_teams():
    teams=[]
    data=get_data(TEAMS,ATTRIBUTES)
    for team in TEAMS.itertuples(index=False):
        _,team_id, name, short_name, logo, colors, description, wiki_source, german_name = team #one needs to skip the first value (_0), but I don't understand why it even exists even though index was set to false
        colors=json.loads(colors)
        teams.append({
            "dataKey":team_id,
            "id":team_id,
            "color":rgb_to_hex(colors[0])
        })
    result={
        "data":data,
        "teams":teams
        }
    return json.dumps(result,ensure_ascii=False)

@app.route("/teams?id=<team_id>&comp=<comp_team_id>")
def get_team_and_comp(team_id,comp_team_id=None):
    def calc_mean(l):
        length = len(l)
        assert (length>0)
        return sum(l)/length
    #from https://stackoverflow.com/questions/41255215/pandas-find-first-occurrence
    team=TEAMS.iloc[TEAMS["team_id"].eq(team_id).idxmax()]
    _,team_id_for_assertion, name, short_name, logo, colors, description, wiki_source, german_name = team
    assert team_id_for_assertion==team_id
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
    filter_team=TEAMS
    if comp_team_id:
        filter_team=filter_team[filter_team["team_id"].isin([team_id,comp_team_id])]
    pure_data=get_data(filter_team,ATTRIBUTES,cumulative=False)
    for season_data in pure_data:
        data_addition={"x":season_data["season"]}
        for cat,value in season_data[team_id].items():
            data_addition[cat]=value
            data_addition[str(cat)+"c"]=calc_mean([team_data[cat] for k,team_data in season_data.items() if not k in ["season",team_id]])
        data.append(data_addition)
    team_dict["data"] = data
    return json.dumps(team_dict,ensure_ascii=False)

if __name__ == "__main__":
    app.run("0.0.0.0")
    
