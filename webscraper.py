import json
import re

import bs4
import pandas as pd
import requests
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as prc


def get_between(string:str,start:str,end:str,with_brackets=None):
    """A function that returns all substrings of the string that are between two strings (like brackets or slashes)"""
    if with_brackets is None:
        with_brackets=True
    #re.escape escapes all characters that need to be escaped
    new_start=re.escape(start)
    new_end=re.escape(end)
    pattern=f"{new_start}.*?{new_end}"
    res=re.findall(pattern,string)
    if with_brackets:
        return res #-> this is with the brackets
    else:
        return [x[len(start):-len(end)] for x in res]#-> this is without the brackets

def find(key,l):
    for x in l:
        if key(x):return x

def scrape_transm():
    """The main scrape function which returns the transfers and the team infos"""
    base_url ="https://www.transfermarkt.de/bundesliga/transfers/wettbewerb/L1"
    result={}
    transfers=[]
    for season in range(2008,2016):
        #make the request and select the soup
        compatible_season=f"{season}/{season+1}"
        url=f"{base_url}/plus/?saison_id={season}"
        response = requests.get(url, headers={'User-Agent': 'Custom'} )
        response.raise_for_status()
        html_doc = response.text
        soup = bs4.BeautifulSoup(html_doc, 'html.parser')
        subsoup= soup.select_one("div.large-8.columns")
        #clear all doubles for mobile view
        for show_small in subsoup.find_all(class_="show-for-small"):show_small.clear()
        for show_small in subsoup.find_all(class_="kurzpos-transfer-cell"):show_small.clear()
        teams=[]
        for item in subsoup.select(".box"):
            header=item.find(class_="table-header")
            if header is None: continue
            logo=header.find("a")
            _id=int(get_between(logo["href"],"verein/","/",False)[0])
            this_team={
                "name":logo["title"],
                "id":_id,
                #"team_href":base_url+logo["href"],
                #"logo_src":"head".join(logo.find("img")["src"].rsplit("small",1))
                "logo_src":f"https://tmssl.akamaized.net/images/wappen/head/{_id}.png" #the logo is static, but we still record it for every season for simplicity
            }
            #extra infos 
            for attr in item.select(".transfer-zusatzinfo-box"):
                for attr,val in [x.split(": ") for x in attr.text.replace("\t","").splitlines() if x]:
                    this_team[attr]=val
            teams.append(this_team)
            # tranfer table
            table_html=str(item)
            tables=pd.read_html(table_html,flavor="bs4")
            assert(len(tables)==2)
            deletions=[["Nat.","Position","Unnamed: 4","Alter","Abgebender Verein"],
                        ["Nat.","Position","Unnamed: 4","Alter","Aufnehmender Verein"]]
            replacements=[{"Abgebender Verein.1":"Verein","Zugang":"Name"},
                            {"Aufnehmender Verein.1":"Verein","Abgang":"Name"}]
            ingoing=[True,False]
            for i,df in enumerate(tables):
                for to_delete in deletions[i]: # Ein Filter wäre wahrscheinlich effizienter
                    del df[to_delete]
                df=df.rename(columns=replacements[i])
                #(season,team_name,money,player_name,ingoing,interacting_team)
                for original_tuple in df.itertuples(index=False):
                    name,marktwert,verein,ablöse=original_tuple
                    new_tuple=(compatible_season,this_team["name"],ablöse,name,ingoing[i],verein)
                    transfers.append(new_tuple)
        result[compatible_season]=teams
    return {
        "team_infos":result,
        "transfers":transfers
        }

def get_team_dict(team_name_ids:list,scraped_teams:list):
    """
    @params
    team_name_ids: list of (id,name) tuples of all teams in the database
    scraped_teams: list of scraped teams as dict with a "name" attribute
    @returns: A dict with the team ids mapped to the scraped names
    """
    result={}
    for db_teams in team_name_ids:
        # fuzzywuzzy benutzen, um die levenstein distanz zu berechnen
        _id,name=db_teams
        scraped_team_names=[x["name"] for x in scraped_teams]
        found_name=find(lambda scraped_team_name:fuzz.ratio(scraped_team_name.lower(),name.lower())>=70,scraped_team_names)
        result[_id]=found_name
    return result

def get_scraped():
    with open("scrape_result.json","r",encoding="utf-8") as file: 
        return json.load(file)

def fold_scraped(d:dict):
    """Folds the teams dict into a static list were the season is irrelevant"""
    done_teams=[]
    result = []
    for v in d.values():
        for team in v:
            if team["name"] not in done_teams:
                result.append(team)
                done_teams.append(team["name"])
    return result

if __name__ == '__main__':
    scraped=scrape_transm()
    # for x in scraped["2016/2017"]:
    #     print(x["name"])
    with open("scrape_result.json","w",encoding="utf-8") as file: 
        json.dump(scraped,file,indent=4,ensure_ascii=False)

