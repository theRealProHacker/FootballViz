from flask import Flask, request

from flask_cors import cross_origin
from backend import get_all_teams, get_team_and_comp

app=Flask(__name__)

@cross_origin(origin='*', headers=['Content-Type', 'Application/json'])
@app.route("/teams")
def api_route():  
        team_id= int(request.args.get("id"))  if "id" in request.args else -1
        comp_team_id= int(request.args.get("comp")) if "comp" in request.args else  None

        if(team_id == -1 and comp_team_id == None) :
            out = get_all_teams() 
        elif(team_id != -1):
            out = get_team_and_comp(team_id , comp_team_id) 
        else: 
            return {"error": "paramters are rong" }, 400, {"Access-Control-Allow-Origin": "*"}

        return out , 200, {"Access-Control-Allow-Origin": "*"}

if __name__ == "__main__":
    app.run()
 
