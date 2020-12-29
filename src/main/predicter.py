import pandas as pd
import sqlite3
import scipy.stats
import numpy as np

class predicter (object):

    def __init__(self, db_path):
        self.db_path = db_path

    @staticmethod
    def rescale_parameters(alpha, beta, total):
        """
        A function to take a fitted beta distribution and rescale based on different
        strength of prior (alpha + beta)
        """
        cur_scale = alpha + beta
        rescale = total / cur_scale
        return alpha * rescale, beta * rescale
    
    @staticmethod
    def create_params (p, N):
        """
        Create alha and beta paramaters for a win pct and strength of prior
        """
        alpha = p*N
        beta = (1-p) *N
        return alpha, beta
    
    @staticmethod
    def cdf_record (alpha, beta, cur_wins, cur_losses, n_games = 72 ):
        """
        For a prior win distribution and current record, create a probability of
        remaining wins as a DataFrame
        """
        remaining_games = n_games - (cur_wins + cur_losses)
        more_wins = range(remaining_games + 1)
        out = {'wins':[],'prob':[]}
        for win in more_wins:
            remaining_pct = win*1.0 / remaining_games
            prob = scipy.stats.beta.sf(remaining_pct, alpha , beta)
            out['wins'].append(cur_wins + win)
            out['prob'].append(round(prob,4)*100)
        return pd.DataFrame.from_dict(out)

    @staticmethod
    def custom_projection (p, N, cur_wins, cur_losses, n_games = 72):
        """
        Create a custom projection, based on some prior probability
        some prior strength, and a current record
        """
        alpha, beta = create_params(p,N)
        return cdf_record (alpha, beta, cur_wins, cur_losses, n_games = 72 )

    def lookup_current (self, team):
        """
        lookup_current current record of a team in db
        """
        conn = sqlite3.connect(self.db_path)
        qry_str = 'SELECT MAX(wins) as wins, MAX(losses) as losses FROM current WHERE short = "{0}"'.format(team)
        out = pd.read_sql(qry_str, conn)
        return out.wins[0], out.losses[0]

    def get_wins (self, min_percentile, max_percentile):
        qry_str = """SELECT team, year, short, wins, pct 
        FROM historical 
        WHERE percentile BETWEEN {0} AND {1} AND game = 82""". \
            format(str(min_percentile), str(max_percentile))
        conn = sqlite3.connect(self.db_path)
        teams  = pd.read_sql(qry_str, conn)
        return teams

    def get_teams_list (self):
        qry_str = """SELECT DISTINCT short FROM current"""
        conn = sqlite3.connect(self.db_path)
        teams  = pd.read_sql(qry_str, conn)
        return teams.short.tolist()


    def fit_beta (self, wins_frame):
        """
        Fit a beta distrubtion based on historical win pct for a teams between 
        a certain percentile in the league
        """
        win_pct = wins_frame.pct
        
        fitted = scipy.stats.beta.fit(win_pct, floc =0 , fscale = 1)
        return fitted

        
    def update_projection (self, alpha, beta, current_team):
        """
        Update a project for a team, based on an emperical, range and strength (and team name)
        """
        ## get current record of team
        wins, losses = self.lookup_current (current_team)
        ## updated priors
        alpha_prime = alpha + wins
        beta_prime = beta + losses
        return predicter.cdf_record (alpha_prime, beta_prime, wins, losses)

    def calc_sensitivity (self, current_team, win_thresh = 50, min_pct = .05, max_pct = .95, by_pct = 0.05,
            min_we = 1, max_we = 40, by_we = 1, n_games = 72):
        wins, losses = self.lookup_current (current_team) 
        remaining_games = n_games - (wins + losses)
        remaining_wins = win_thresh - wins
        remaining_pct = remaining_wins*1.0 / remaining_games
        pct_range = np.arange(min_pct, max_pct + by_pct, by_pct)
        we_range = np.arange(min_we, max_we + by_we, by_we)
        
        out = {"pct":[], "we":[], "prob":[]}
        for pct in pct_range:
            for we in we_range:
                alpha, beta = predicter.create_params (pct, we)
                prob = scipy.stats.beta.sf(remaining_pct, alpha , beta)
                out['pct'].append(pct)
                out['we'].append(we)
                out['prob'].append(round(prob*100,2))
        return out 

    def vis_data (self, min_percentile, max_percentile, current_team, prior_games = None):
        wins_frame = self.get_wins(min_percentile, max_percentile)
        fitted = self.fit_beta(wins_frame)
        alpha, beta = fitted[0], fitted[1]
        if prior_games:
            alpha_1, beta_1 = predicter.rescale_parameters(alpha, beta, prior_games)
        else:
            alpha_1, beta_1 = alpha, beta
        wins, losses = self.lookup_current (current_team)
        alpha_prime = alpha_1 + wins
        beta_prime = beta_1 + losses
        cdf = predicter.cdf_record (alpha_prime, beta_prime, wins, losses)

        out = {}
        out['stats']= {
            'wins':wins,
            'losses': losses,
            'emperical_win_pct': round( 100* alpha/ (alpha + beta),2) ,
            'prior_ge': int(round(alpha + beta,0 ))
        }
        out['prior_hist'] = wins_frame
        out['prior'] = (alpha, beta)
        out['prior_rescaled'] = (alpha_1, beta_1)
        out['posterior'] = (alpha_prime, beta_prime)
        out['cdf'] = cdf
        return out
