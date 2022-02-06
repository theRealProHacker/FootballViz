import json
import sqlite3
import requests
import pandas as pd
import wikipedia
from bs4 import BeautifulSoup
from image_color import color_from_image
from webscraper import get_scraped, get_team_dict, fold_scraped

class SQLite:
    """
    A minimal sqlite3 context handler that removes pretty much all
    boilerplate code from the application level.
    From: https://stackoverflow.com/questions/26793753/using-a-context-manager-for-connecting-to-a-sqlite3-database
    """
    def __init__(self,path):
        self.path = path

    def __enter__(self):
        self.connection: sqlite3.Connection = sqlite3.connect(self.path)
        # self.connection.row_factory = sqlite3.Row  #this for getting the column names!
        self.cursor: sqlite3.Cursor = self.connection.cursor()
        # do not forget this or you will not be able to use methods of the
        # context handler in your with block
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

original="original_database.sqlite"
o_db = SQLite(original)
GERMANY_ID = 7809
wikipedia.set_lang("de")
online=True

def pandas_query(query:str):
    with o_db as sql:
        return pd.read_sql_query(query,sql.connection,parse_dates="date")

def find(key,l):
    for x in l:
        if key(x):return x

def make_seasons():
    """Returns a list of seasons ordered from oldest to latest"""
    for season in range (2008,2016):
        yield f"{season}/{season+1}"

def parse_money(string:str):
    """Parses scraped money as string to float"""
    EXTRAS=["Leihgebühr:"]
    ZERO_VALUES=["ablösefrei","Leihe","Leih-Ende"]
    if string in ["0","-","?"] or any([v in string for v in ZERO_VALUES]):return 0
    #big problem to discuss: What do we do with question marks
    for extra in EXTRAS: string=string.replace(extra,"")
    split=string.split()
    unit_dict={
        "":1,
        "Tsd.":1000,
        "Mio.":1000000
    }
    unit=""
    try:
        float_str,=split #try 1
        print(float_str)
    except ValueError: #too manyarguments to unpack
        try:
            float_str,unit,currency=split #try 3
        except ValueError: #too many/not enough arguments to unpack
            float_str,currency=split #try 2
        assert(currency=="€")
    value=float(float_str.replace(",","."))*unit_dict[unit]
    return value

def wiki_scrape(url):
    response=requests.get(url)
    soup = BeautifulSoup(response.text,features="html5lib")
    attributes_dict={"Gründung":"founded","Mitglieder":"members","Website":"url"}
    info_box = soup.select_one("table.infobox")
    table_dict={}
    def process_number(s:str):
        for i,char in enumerate(s):
            if char in "[(":
                return s[0:i]
        return s
    for tr in info_box.select("tr"):
        tds=[td.text.strip() for td in tr.select("td")]
        if len(tds)==2:
            attr=attributes_dict.get(tds[0])
            if attr:
                table_dict[attr]=process_number(tds[1])
    return table_dict

def assemble_tables():
    team_extras,transfers=get_scraped().values()
    flattened_teams=fold_scraped(team_extras)
    def select_cols(table,cols): 
        return f"SELECT {','.join(cols)} FROM {table}"
    def rename_with(df,replacement):
        """Renames the df columns with the given replacement"""
        columns=df.columns.values.tolist()
        rename={old:new for old,new in zip(columns,replacement)}
        return df.rename(columns=rename)
    result={}
    # Matches
    def assemble_match():
        columns=["match_api_id","season","date","home_team_api_id","away_team_api_id","home_team_goal","away_team_goal"]
        query=select_cols("Match",columns)+f" WHERE (country_id=={GERMANY_ID})"
        df=pandas_query(query) #automatically parses dates
        replacement=["match_id","season","date","home_id","away_id","home_goals","away_goals"]
        df=rename_with(df,replacement)
        return df
    
    #Teams
    def assemble_team(matches):
        """This takes the id, name and long name from the original database"""
        german_team_ids=set()
        for _,match in matches.iterrows():
            german_team_ids.add(match["home_id"])
            #german_team_ids.add(match["away_id"])
        columns=["team_api_id","team_long_name","team_short_name"]
        query=select_cols("Team",columns) 
        df=pandas_query(query)
        replacement=["team_id","name","short_name"]
        df=rename_with(df,replacement)
        df=df[df["team_id"].isin(german_team_ids)].reset_index(drop=True)
        return df
    
    #Team logos and colors
    def update_teams(teams):
        """This updates the teams with the infos from the webscraper like logo and coor and description"""
        scraped_names=[]
        logos=[]
        colors=[]
        descriptions=[]
        wikipedia_sources=[]
        wd={"founded":[],"members":[],"url":[]}
        for _,team in teams.iterrows():
            _id=team["team_id"]
            try:
                found_name=team_dict[_id]
            except KeyError:
                print(f"KeyError on {team['name']}")
                raise
            scraped_names.append(found_name)
            found_entry=find(lambda x: x["name"]==found_name,flattened_teams)
            logo=found_entry["logo_src"]
            logos.append(logo)
            if online:
                color=color_from_image(logo)
                colors.append(json.dumps(color,ensure_ascii=False))
                wiki_page = wikipedia.page(found_name)
                descriptions.append(wiki_page.summary)
                wikipedia_sources.append(wiki_page.url)
                wiki_data=wiki_scrape(wiki_page.url)
                for k in wd.keys():
                    wd[k].append(wiki_data.get(k))
            else:
                colors.append(None)
                descriptions.append(None)
                wikipedia_sources.append(None)
        teams=teams.assign(logo=logos,color=colors,description=descriptions,wiki_source=wikipedia_sources,homepage=wd["url"],founded=wd["founded"],members=wd["members"],german_name=scraped_names)
        return teams
    
    #Team_Attributes
    def assemble_attributes(teams,matches):
        """Team attribues are all attributes which change over the seasons/are dependant on the seasons. 
        E.g. points, perfect games, goals and goals against or money spent. 
        The function takes teams and matches"""
        rows=[]
        for _,team in teams.iterrows():
            for season in make_seasons():
                team_id=team["team_id"]
                scraped_name=team_dict[team_id]
                found_team=find(lambda team:team["name"]==scraped_name,team_extras[season])
                if found_team is None: 
                    rows.append((0,)*7)
                    continue
                money_spent=parse_money(found_team["Ausgaben"])
                #calculates points, goals,goals_against and perfect games for each team and season by hand from all matches 
                points=0
                goals=0
                goals_against=0
                perfect_games=0
                sides=["home","away"]
                season_matches=matches[matches["season"] == season]
                for side in sides:
                    opponent_side=find(lambda x:not x == side,sides)
                    side_matches=season_matches[season_matches[f"{side}_id"] == team_id]
                    for _,m in side_matches.iterrows():
                        own_goals=m[f"{side}_goals"]
                        opponent_goals=m[f"{opponent_side}_goals"]
                        goals+=own_goals
                        goals_against+=opponent_goals
                        if opponent_goals==0 and own_goals > 0:
                            perfect_games+=1
                        if opponent_goals==own_goals: #draw
                            points+=1
                        elif opponent_goals<own_goals: #win
                            points+=3
                rows.append((team_id,season,points,goals,goals_against,perfect_games,money_spent))
        df=pd.DataFrame(rows,columns=["team_id","season","points","goals","goals_against","perfect_games","money_spent"])
        return df
    
    #Transfers
    def assemble_transfers():
        rows = []
        swapped_team_dict={y:x for x,y in team_dict.items()}
        error_teams=set()
        for transfer in transfers:
            scraped_name = transfer[1]
            money_str=transfer[2]
            try:
                transfer[1]=swapped_team_dict[scraped_name] #from name to id
                transfer[2]=parse_money(money_str) #parse money
                rows.append(transfer)
            except KeyError:
                error_teams.add(transfer[1])
        df = pd.DataFrame(rows,columns=["season", "team_id","money","player_name","ingoing","interacting_team"])
        #error message for error_teams
        if error_teams:print("Teams that are in the scraped but not in the original table:\n"+str(error_teams))
        return df
    
    result["Match"]=assemble_match()
    result["Team"]=assemble_team(result["Match"])
    team_dict=get_team_dict(result["Team"][["team_id","name"]].to_numpy().tolist(),flattened_teams)
    result["Team"]=update_teams(result["Team"])
    result["Team_Attributes"]=assemble_attributes(result["Team"],result["Match"])
    result["Transfers"]=assemble_transfers()
    for k,dataframe in result.items():
        # print("\n"+k)
        # print(dataframe.info())
        dataframe.to_csv(f"database/{k}.csv")
    print("Pretty successful")


 



if(__name__ == "__main__"):
    assemble_tables() 
