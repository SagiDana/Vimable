#!/usr/bin/python3

from flask import Flask, request
from flask import Response

from threading import Thread
from requests import get
import os

app = Flask(__name__)

port = None
name = None
env = {}

@app.route('/shutdown', methods=["GET"])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if not func:
        raise RuntimeError("Not running with the Werkzeug Server...")
    func()
    return "shuting down..."

@app.route('/', methods=["GET"])
def index():
    return Response()

@app.route('/execute', methods=["POST"])
def execute():
    global env
    code = request.data.decode('utf-8')

    import sys
    from io import StringIO


    try:
        codeOut = StringIO()
        codeErr = StringIO()

        sys.stdout = codeOut
        sys.stderr = codeErr

        exec(code, env)

        # restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # codeErr.getvalue()
        output = codeOut.getvalue()

        codeOut.close()
        codeErr.close()
    except Exception as e:
        output = str(e)


    return Response(output)

# @app.route('/', methods=["GET"])
# def index():
    # return Response("hh")


def run_flask():
    global port

    app.run(host='127.0.0.1',
            port=port,
            threaded=True,
            debug=True,
            use_reloader=False)

def is_port_available(port):
    import socket, errno
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ret = False

    try:
        s.bind(("127.0.0.1", 5555))
        ret = True

    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            ret = False
        else:
            # TODO?
            pass
    finally:
        s.close()

    return ret

def find_available_port():
    start_range = 1337
    end_range = 1437
    for port in range(start_range, end_range):
        if is_port_available(port):
            return port
    return None

def setup_environment(_name):
    global port
    global name
    port  = find_available_port()
    name = _name

    with open(f"/tmp/vimable_{name}", "w+") as f:
        f.write(f"http://127.0.0.1:{port}/")

def clean_environment():
    global name
    os.remove(f"/tmp/vimable_{name}")

def start(name):
    setup_environment(name)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

def stop():
    global port
    get(f"http://127.0.0.1:{port}/shutdown")

    clean_environment()

def export(name, value):
    global env
    env[name] = value


def main():
    start("exmaple")

    import time
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass

    stop()

if __name__ == '__main__':
    main()
