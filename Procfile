heroku config:add BUILDPACK_URL=https://github.com/conda/conda-buildpack.git
worker: python ~/src/main/run_ingest.py nba.db -t 1 -min 1971 -max 2019
web: bokeh serve — port=$PORT — allow-websocket-origin=bayesareasports.herokuapp.com — address=0.0.0.0 — use-xheaders ~/src/main/app.py

