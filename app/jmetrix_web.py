#!/usr/bin/env python3
from flask import Flask, request, render_template
import subprocess
import os
import logging
import util.logger as logger

log = logger.setup_custom_logger('root', logging.DEBUG)
app = Flask(__name__)

@app.route('/daily_rpt', methods=['GET'])
def run_daily_rpt():
    url = request.args.get('url')
    token = request.args.get('token')
    project = request.args.get('project')
    discovery = request.args.get('discovery')

    # Run the Python script using subprocess
    if discovery is not None:
        command = f'{os.getcwd()}/jmetrix.py daily_rpt -u "{url}" -t "{token}" -p "{project}" -V -d'
    else:
        command = f'{os.getcwd()}/jmetrix.py daily_rpt -u "{url}" -t "{token}" -p "{project}" -V'

    log.debug(command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr

    return render_template('preformatted.html', output=output)

@app.route('/swimlane_rpt', methods=['GET'])
def run_swimlane_rpt():
    url = request.args.get('url')
    token = request.args.get('token')
    project = request.args.get('project')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    jira_label = request.args.get('jira_label')
    extra_jira_label = request.args.get('extra_jira_label')

    # Run the Python script using subprocess
    if extra_jira_label is not None:
        command = f'{os.getcwd()}/jmetrix.py swimlane_rpt -u "{url}" -t "{token}" -p "{project}" -f "{date_from}" -T "{date_to}" -l "{jira_label}" -L "{extra_jira_label}" -V'
    else:
        command = f'{os.getcwd()}/jmetrix.py swimlane_rpt -u "{url}" -t "{token}" -p "{project}" -f "{date_from}" -T "{date_to}" -l "{jira_label}" -V'

    log.debug(command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr

    return render_template('preformatted.html', output=output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,  debug=True)

