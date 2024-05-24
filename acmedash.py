#!/usr/bin/env python3

"""
Copyright (C) 2024 Ray Mentose.
This app uses Flask & Gunicorn with ryt/runapp for deployment.
"""

import os
import sys
import csv
import html
import itertools

from flask import Flask
from flask import request
from urllib.parse import quote
from flask import render_template
from configparser import ConfigParser

app = Flask(__name__)

limitpath = ''
app_path  = '/acmedash'

# -- start: parse runapp.conf (if it exists) and make modifications
conf = 'runapp.conf'
if os.path.exists(conf):
  with open(conf) as cf:
    config = ConfigParser()
    config.read_file(itertools.chain(['[global]'], cf), source=conf)
    try:
      limitpath = config.get('global', 'limitpath').rstrip('/') + '/'
    except:
      limitpath = ''
    try:
      app_path = config.get('global', 'app_path')
    except:
      app_path = app_path
# -- end: parse runapp config


def get_query(param):
  """Get query string param (if exists & has value) or empty string"""
  try:
    return request.args.get(param) if request.args.get(param) else ''
  except:
    return ''


@app.route('/run',  methods=['GET'])
def run(subpath=None):

  getm        = get_query('m')
  getcmd      = get_query('cmd')

  view = { 
    'page'    : 'run',
    'getm'    : getm,
    'command' : '', 
    'error'   : False, 
    'message' : '' 
  }

  if getm and getcmd:
    getm = getm.rstrip('/')
    if os.path.isfile(f'{getm}/app/dashboard_run_commands.py'):
      sys.path.append(getm)
      view['message'] = getcmd
      view['command'] = getcmd
      # TODO // todo
      # import dashboard_run_commands.py and run the specified command
    else:
      view['error']   = True
      view['message'] = 'Sorry the run commands module could not be found in the metrics app directory.'
  else:
    if getm:
      view['message'] = f'Please specify a command. /run?m={getm}&cmd=command'
    else:
      view['message'] = 'Please specify a command and app directory path. /run?m=/Path/to/Metrics/&cmd=command'

  return render_template('acmedash.html', view=view)


@app.route('/garmin',  methods=['GET'])
def garmin(subpath=None):

  getm        = get_query('m')
  getcmd      = get_query('cmd')

  view = { 
    'page'    : 'garmin',
    'getm'    : getm,
    'command' : '', 
    'error'   : False, 
    'message' : '' 
  }

  if getm:
    getm = getm.rstrip('/')
    if os.path.isfile(f'{getm}/app/dashboard_garmin_connect.py'):
      sys.path.append(getm)
      view['message'] = getcmd
      view['command'] = getcmd
      # TODO // todo
      # import dashboard_run_commands.py and run the specified command
    else:
      view['error']   = True
      view['message'] = 'Sorry the dashboard garmin connect module could not be found in the metrics app directory.'
  else:
    view['message'] = 'Please specify an app directory path for the garmin connect module. /run?m=/Path/to/Metrics/'

  return render_template('acmedash.html', view=view)


@app.route('/', methods=['GET'])

def index(subpath=None):

  global app_path

  getm        = get_query('m')
  getview     = get_query('view')

  view   = { 
    'page'      : 'index',
    'getm'      : getm,
    'app_path'  : app_path 
  }


  return render_template('acmedash.html', view=view)


if __name__ == '__main__':
    app.run(debug=True)

