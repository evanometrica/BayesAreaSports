import argparse
from data_ingest import ingester




parser = argparse.ArgumentParser()
parser.add_argument("db_path", type=str,
                    help="filepath of database")
parser.add_argument("-t", "--type_update", choices= [0,1,2], default = 0, type=int,
                    help="0 = update scores, 1= init new database, 2 = add years")
parser.add_argument("-min", "--min_year", type=int, default= 1960, choices=range(1960,2020),
                    help="first year to init")
parser.add_argument("-max", "--max_year", type=int, default= 2016, choices=range(1960,2020),
                    help="last year to init")
args = parser.parse_args()

ingest = ingester(args.db_path)
if args.type_update == 0:
	ingest.add_current()
elif  args.type_update == 1:
	years = range(args.min_year, args.max_year +1 )
	ingest.init_database(years)
else:
	years = range(args.min_year, args.max_year + 1)
	ingest.add_years(years)
