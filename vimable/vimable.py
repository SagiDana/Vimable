#!/usr/bin/python3

from flask import Flask, request
from flask import Response

from threading import Thread
from requests import get
import os

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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

def get_relvant_object(base):
    global env
    previous_words = base.split()
    
    if len(previous_words) < 1: word = ''
    else: word = previous_words[-1].strip()

    if '(' in word:
        word = word[word.rfind('('):]

    objects = word.split('.')

    part_of_word = ''
    if not word.endswith('.'):
        part_of_word = objects[-1]
        objects = objects[:-1]

    current_level = 0
    current_object = None

    while len(objects)-1 >= current_level:
        current_level += 1

        try:
            current_object = eval('.'.join(objects[:current_level]), env)
        except Exception as e: break

    return current_object, part_of_word

@app.route('/completion', methods=["POST"])
def completion():
    global env

    base = request.data.decode('utf-8')

    obj, part = get_relvant_object(base)

    candidates = []

    if not obj: candidates = list(env.keys())
    else: candidates = dir(obj)[::-1]

    matches = []
    for candidate in candidates:
        if not candidate.startswith(part): continue

        candidate = candidate[len(part):]
        matches.append(candidate)

    return Response(','.join(matches))


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
