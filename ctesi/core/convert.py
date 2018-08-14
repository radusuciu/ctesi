"""Interfaces with cravatt-rawprocessor."""
import config.config as config
import time
import requests


def convert(path, success_callback=None, status_callback=None):
    # start conversion
    requests.get(config.CONVERT_URL + '/convert/' + path)

    # poll every 30 seconds
    polling_interval = 30
    running = True
    status = None

    while running:
        start = time.clock()
        status = get_status(path)

        if 'status' in status:
            if status_callback:
                status_callback(status)

            if status['status'] == 'success':
                running = False
                if success_callback:
                    success_callback(status)
            elif status['status'] == 'fail':
                running = False

        work_duration = time.clock() - start
        time.sleep(polling_interval - work_duration)

    return status


def cancel_convert(path):
    return requests.get(config.CONVERT_URL + '/abort/' + path)


def get_status(path):
    r = requests.get(config.CONVERT_URL + '/status/' + path)
    return r.json()
