from flask import Flask, request

from flask_cors import cross_origin
from backend import get_all_teams, get_team_and_comp

app=Flask(__name__)

@app.route("/teams")
@cross_origin(origin='*', headers=['Content-Type', 'Application/json'])
def api_route():
    get_id=request.args.get("id")
    get_comp=request.args.get("comp")
    if get_id is None:
        return get_all_teams()
    else:
        try:
            team_id=int(get_id)
            comp_team_id=int(get_comp)
        except TypeError:
            raise
        return get_team_and_comp(team_id,comp_team_id)

if __name__ == "__main__":
    app.run("0.0.0.0",debug=True)
    
