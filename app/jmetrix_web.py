import flask

app = flask.Flask(__name__)

@app.route('/jmetrix', methods=['GET'])
def jmetrix():
    url = request.args.get('url')
    token = request.args.get('token')
    project = request.args.get('project')
    verbose = request.args.get('verbose', 'False')

    result = subprocess.run(['./jmetrix.py', 'daily_rpt', url, token, project, verbose], capture_output=True)

    return result.stdout


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
