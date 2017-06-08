#!/bin/bash

PROJECT_HOME="/home/ctesi/ctesi"
# install requirements in virtual environment
cd "${PROJECT_HOME}" || exit
python3.5 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# start celery daemon
rm celeryd.pid celery.log
celery -A ctesi.celery worker --workdir="${PROJECT_HOME}" -Ofair --loglevel=info --logfile=celery.log --detach

# run the server
if [[ -n $DEBUG && $DEBUG == true ]]; then
    flask run -h 0.0.0.0
else
    gunicorn --config=config/gunicorn.py ctesi:app
fi
