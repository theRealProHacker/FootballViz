from flask import Flask, request

from flask_cors import cross_origin
from backend import get_all_teams, get_team_and_comp, getMoneyDayData, getPointGoalData, getPefectGameData , get_average_goals_per_win

app=Flask(__name__)

@cross_origin(origin='*', headers=['Content-Type', 'Application/json'])
@app.route("/teams")
def teams():  
        team_id= int(request.args.get("id"))  if "id" in request.args else -1
        comp_team_id= int(request.args.get("comp")) if "comp" in request.args else  None
        if(team_id == -1 and comp_team_id == None) :
            out = get_all_teams() 
        elif(team_id != -1):
            out = get_team_and_comp(team_id , comp_team_id) 
        else: 
            return {"error": "paramters are wrong" }, 400, {"Access-Control-Allow-Origin": "*"}
        return out , 200, {"Access-Control-Allow-Origin": "*"}

@cross_origin(origin='*', headers=['Content-Type', 'Application/json'])
@app.route("/matchinformation")
def getMetaInformation():  
        team_id= int(request.args.get("id"))  if "id" in request.args else -1
        season = request.args.get("season") if "season" in request.args else  -1
        kind = request.args.get("kind") if "kind" in request.args else  -1
        out = {"error": "paramters are wrong" }
        print(team_id, season, kind)
        if(team_id == -1 or season == -1 or kind == -1):
            return out, 400, {"Access-Control-Allow-Origin": "*"}
        elif(kind == "moneyday"):
            out = getMoneyDayData(team_id, season)
        elif(kind == "pointgoal"):
            out = getPointGoalData(team_id, season)
        elif(kind == "perfectgames"):
            out = getPefectGameData(team_id, season)
        elif(kind == "avgvic"):
            out = get_average_goals_per_win(team_id, season) 
        else:
            return out, 400, {"Access-Control-Allow-Origin": "*"} 
        return out , 200, {"Access-Control-Allow-Origin": "*"}

if __name__ == "__main__":
    app.run()
 
