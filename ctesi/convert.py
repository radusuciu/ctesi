"""Interfaces with cravatt-rawprocessor."""
import config.config as config
import time
import requests


def convert(path, callback=None):
    # start conversion
    requests.get(config.CONVERT_URL + '/convert/' + path)

    # poll every 30 seconds
    polling_interval = 30
    running = True

    # if we are passed a callback then return only when conversion is done
    while running:
        start = time.clock()
        status = get_status(path)

        if 'status' in status and status['status'] == 'success':
            running = False
            if callback:
                callback(status)

            return status

        work_duration = time.clock() - start
        time.sleep(polling_interval - work_duration)


def get_status(path):
    r = requests.get(config.CONVERT_URL + '/status/' + path)
    return r.json()
