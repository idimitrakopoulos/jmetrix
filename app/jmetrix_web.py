#!/usr/bin/env python3
from flask import Flask, request, render_template
import subprocess
import os
import logging
import util.logger as logger

log = logger.setup_custom_logger('root', logging.DEBUG)
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return 'OK'

@app.route('/daily_rpt', methods=['GET'])
def run_daily_rpt():
    url = request.args.get('url')
    token = request.args.get('token')
    project = request.args.get('project')

    if None in [url, token, project]:
        return "Bad Request", 400

    discovery = request.args.get('discovery')

    command = [f'{os.getcwd()}/jmetrix.py', 'daily_rpt', '-u', url, '-t', token, '-p', project, '-V']
    if discovery is not None:
        command.append('-d')

    log.debug(" ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
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

    # Check if any required parameters are missing
    if None in [url, token, project, date_from, date_to, jira_label]:
        return "Bad Request", 400

    extra_jira_label = request.args.get('extra_jira_label')

    command = [f'{os.getcwd()}/jmetrix.py', 'swimlane_rpt', '-u', url, '-t', token, '-p', project, '-f', date_from, '-T', date_to, '-l', jira_label, '-V']
    if extra_jira_label is not None:
        command.extend(['-L', extra_jira_label])

    log.debug(" ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + result.stderr

    return render_template('preformatted.html', output=output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


