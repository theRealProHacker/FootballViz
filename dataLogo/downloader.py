import json
import requests
import os.path

with open("data.json","r") as f:
    d=json.load(f)


if not os.path.exists("logos"):
        os.makedirs("logos")

for id_,src in zip(d["team_id"],d["logo"]):
    result = requests.get(url=src) 
    print( "import l" + str(id_ )+" from './logo_" + str(id_) +".png';")

    with open(os.path.join("logos", f"logo_{id_}.png" ),"wb") as f:
        f.write(result.content)