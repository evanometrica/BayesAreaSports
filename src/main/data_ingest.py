

import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
import sqlite3

class ingester (object):

    def __init__(self, db_path):
        self.db_path = db_path

    @staticmethod
    def get_current_records():
        """
        Gets the current records for each NBA team and outputs to DataFrame
        """
        standings_url = "http://www.basketball-reference.com/leagues/NBA_2020.html#site_menu_link"

        response = urllib.request.urlopen(standings_url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        eastern = soup.find("div", {"id":"all_confs_standings_E"}).findAll("tr", {"class":"full_table"})
        western = soup.find("div", {"id":"all_confs_standings_W"}).find_all("tr", {"class":"full_table"})

        records = {'short':[], 'team':[], 'name':[], 'wins':[], 'losses':[], 'ppg':[], 'papg':[]}
        for row in (eastern + western):
            #Get name and clean name
            name = row.find("th", {"data-stat":"team_name"}).get_text()
            name = str(name[:name.find(u'\xa0')])
            if name[-1]=="*": name = name[:-1]
            team = name.replace(" ","_").lower()
            records['team'].append(team)
            records['name'].append(name)
            #Get Abrev
            url = row.find("a")['href']
            short = url[7:10]
            #wins 
            wins = int(row.find("td", {"data-stat":"wins"}).get_text())
            records['wins'].append(wins)
            #losses
            losses = int(row.find("td", {"data-stat":"losses"}).get_text())
            records['losses'].append(losses)
            #ppg
            ppg = float(row.find("td", {"data-stat":"pts_per_g"}).get_text())
            records['ppg'].append(ppg)
            #papg
            papg = float(row.find("td", {"data-stat":"opp_pts_per_g"}).get_text())
            records['papg'].append(papg)
            ##short
            url = row.find("a")['href']
            short = str(url[7:10])
            records['short'].append(short)
        records_frame = pd.DataFrame.from_dict(records)[["team", "name", "short", "wins","losses","ppg","papg"]]
        records_frame['games'] = records_frame['wins'] + records_frame['losses']
        return records_frame


    @staticmethod
    def get_team_season(team_url):
        """
        Gets the historical records for each NBA team in a season and outputs to DataFrame
        """
        response = urllib.request.urlopen(team_url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        records = soup.find("div", {"id":"all_games"}).findAll("tr")
        game_dict= {"game":[], "wins":[], "losses":[],'date':[]}
        for row in records:
            game= row.find("th", {"data-stat":"g"}).get_text()
            if game == "G": #Ignore header rows
                pass
            else:
                game_dict['game'].append(int(game))
                #Get wins
                wins = row.find("td", {"data-stat":"wins"}).get_text()
                game_dict['wins'].append(int(wins))
                # Get losses
                losses = row.find("td", {"data-stat":"losses"}).get_text()
                game_dict['losses'].append(int(losses))
                # Game Date
                date = row.find("td", {"data-stat":"date_game"})['csk']
                date = int(date.replace("-",""))
                game_dict['date'].append(date)

        game_frame = pd.DataFrame.from_dict(game_dict)[["game", "wins", "losses", "date"]]
        return game_frame


    @staticmethod
    def get_historical_year(year):
        """
        Gets the historical records for all NBA teams in a season and outputs to DataFrame
        """
        url = "http://www.basketball-reference.com/leagues/NBA_{0}.html".format(str(year))
        response = urllib.request.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        eastern = soup.find("div", {"id":"all_divs_standings_E"}).findAll("tr", {"class":"full_table"})
        western = soup.find("div", {"id":"all_divs_standings_W"}).findAll("tr", {"class":"full_table"})
        info = []
        for row in (eastern + western):
            name = row.find("th", {"data-stat":"team_name"}).get_text()
            name = str(name[:name.find(u'\xa0')])
            if name[-1]=="*": name = name[:-1]
            team = name.replace(" ","_").lower()
            url = row.find("a")['href']
            short = str(url[7:10])
            info.append((team, short))
        frames = []
        for team in info:
            url = "http://www.basketball-reference.com/teams/{0}/{1}_games.html".format(team[1],year)
            team_season = ingester.get_team_season(url)
            team_season['team'] = str(team[0])
            team_season['short']= str(team[1])
            team_season['year'] = int(year)
            frames.append(team_season)
        season  = pd.concat(frames)
        season.reset_index(drop=True, inplace=True)
        season['pct'] = season.wins/season.game*1.0
        season['percentile'] = season.groupby('game')['pct'].rank(pct=True, method ="first")
        return season

    @staticmethod
    def get_historical(years):
        """
        Gets the historical records for all NBA teams in a range of seasons and outputs to DataFrame
        """
        results = []
        for year in years:
            result = ingester.get_historical_year(year)
            results.append(result)
        historical_frame = pd.concat(results)[["year", "team", "short", "game", "wins", "losses", "pct", "percentile", "date"]]
        return historical_frame

    @staticmethod
    def get_games_month(year, month):
        season_month_url = "http://www.basketball-reference.com/leagues/NBA_{0}_games-{1}.html".format(year, month)
        response = urllib.request.urlopen(season_month_url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        schedule= soup.find("div", {"id":"div_schedule"}).tbody.find_all("tr")
        results = {'date':[], 'home':[], 'away':[], 'home_pts':[], 'away_pts':[]}
        for row in schedule:
            try:
                # Date
                date = row.find("th", {"data-stat":"date_game"})['csk']
                date = str(date)[:-4]
                results['date'].append(int(date))
                #Home team
                home = row.find("td", {"data-stat":"home_team_name"}).find("a")["href"]
                home = str(home)[7:10]
                results['home'].append(home) 
                #Vistor team
                away = row.find("td", {"data-stat":"visitor_team_name"}).find("a")["href"]
                away = str(away)[7:10]
                results['away'].append(away)
                #Home Points
                home_pts = row.find("td", {"data-stat":"home_pts"}).get_text()
                home_pts = int(home_pts)
                results['home_pts'].append(home_pts)
                #
                away_pts = row.find("td", {"data-stat":"visitor_pts"}).get_text()
                away_pts = int(away_pts)
                results['away_pts'].append(away_pts)
            except:
                pass
        return pd.DataFrame.from_dict(results)

    @staticmethod
    def get_games_season(year):
        months = ["october", "november", "december", "january", "february", "march", "april", "may", "june"]
        season_dfs = [] 
        for month in months:
            print (year, month)
            try:
                season_dfs.append(ingester.get_games_month(year,month))
            except:
                print ("missing")
                pass
        season_df = pd.concat(season_dfs).reset_index()
        season_df.sort_values('date', inplace=True)
        season_df['home_win'] = 1*(season_df['home_pts'] > season_df['away_pts'])
        season_df['winner'] = season_df.apply(lambda x: x['home'] if x['home_win'] else x['away'],1 )
        season_df['loser'] = season_df.apply(lambda x: x['away'] if x['home_win'] else x['home'],1 )
        return season_df

    @staticmethod
    def season_games_engineer_winloss (season_df):
        winners =  season_df[["date","winner"]]
        winners["win"] = 1
        winners["loss"] = 0
        winners.rename(index= str, columns={"winner":"team"}, inplace = True)
                       
        losers =  season_df[["date","loser"]]
        losers["win"] = 0
        losers["loss"] = 1
        losers.rename(index= str, columns={"loser":"team"} , inplace = True)
                       
        team_record = pd.concat([winners, losers]).sort_values("date").reset_index(drop=True)
        cum_stat = team_record.sort_values("date").groupby("team").cumsum()
        team_record["cum_wins"] = cum_stat['win']
        team_record["cum_losses"] = cum_stat['loss']
        team_record["cum_games"] =  team_record["cum_wins"] +  team_record["cum_losses"]
        team_record['win_pct'] =  team_record["cum_wins"]*1.0/team_record["cum_games"]
                                                                          
        team_record.drop(["win", "loss"], axis =1, inplace = True)
        
        season_df = pd.merge(season_df, team_record, 
            left_on= ["date", "home"],
            right_on = ["date", "team"],
            suffixes = ("", "_home")
        ) 
        
        season_df = pd.merge(season_df, team_record, 
        left_on= ["date", "away"],
        right_on = ["date", "team"],
        suffixes = ("", "_away")
        )
        season_df.drop(["team", "team_away"], axis =1, inplace = True)
        season_df.rename(index= str,
            columns={"cum_losses":"cum_losses_home",
            "cum_wins":"cum_wins_home"  ,  
            "cum_games":"cum_games_home",    
            "win_pct":"win_pct" }, inplace = True)
        return  season_df

    @staticmethod
    def get_historical_games (years):
        game_years = []
        for year in years:
            season_df = ingester.get_games_season(year)
            game_years.append(ingester.season_games_engineer_winloss(season_df))
        return pd.concat(game_years)

    def init_database (self, years):
        """
        Initializes a database, for a set of seasons
        """
        conn = sqlite3.connect(self.db_path)
        historical = ingester.get_historical(years)
        historical.to_sql("historical", conn, index=False, if_exists='replace')
        games = ingester.get_historical_games(years)
        games.to_sql("games", conn, index=False, if_exists='replace')
        current = ingester.get_current_records()
        current.to_sql("current", conn, index=False, if_exists='replace')

    def add_years(self, years):
        """
        Adds additional years to the historical record
        """
        conn = sqlite3.connect(self.db_path)
        qry_str = "SELECT DISTINCT year FROM historical"
        present_years = pd.read_sql(qry_str, conn)['year'].tolist()
        years_toget =  [x for x in years if x not in present_years]
        games = ingester.get_historical_games(years_toget)
        games.to_sql("games", conn, index=False, if_exists='append')
        historical = ingester.get_historical(years_toget)
        historical.to_sql("historical", conn, index=False, if_exists='append')
        
    def add_current (self):
        """
        Updates the current records for a database
        """
        conn = sqlite3.connect(self.db_path )
        qry_str = "SELECT * FROM current"
        all_current = pd.read_sql(qry_str, conn)
        current = ingester.get_current_records()
        all_current = pd.concat([all_current, current])
        all_current.drop_duplicates(inplace=True)
        all_current.to_sql("current", conn, index=False, if_exists='replace')

