#!/usr/bin/env python3
from flask import Flask, request, render_template
import subprocess
import urllib.parse

app = Flask(__name__)

@app.route('/daily_rpt', methods=['GET'])
def run_script():
    url = request.args.get('url')
    token = request.args.get('token')
    project = request.args.get('project')

    # Run the Python script using subprocess
    command = f'/mnt/c/Users/i.dimitrakopoulos/PycharmProjects/jmetrix/app/jmetrix.py daily_rpt -u "{url}" -t "{token}" -p "{project}" -V'

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout

    return render_template('output.html', output=output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,  debug=True)
