#!/usr/bin/env python3

"""Metrics Dashboard Module"""

"""
The Metrics dashboard module provides a web interface for analyzing and displaying metrics logs & data.
"""

# TODO: Idea inspirations from gyroscope -> https://gyrosco.pe/aprilzero/

import os
import re
import sys
import csv
import html
import traceback
import pandas as pd

from datetime import datetime, timedelta
from urllib.parse import urlparse
from flask import request
from io import StringIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import macros

# date & time definitions

today = datetime.today()
today_f = (today.strftime('%Y-%m-%d'), today.strftime('%b %-d'), today.strftime('%m/%d')) # %b %-d, %Y

yest = today - timedelta(days=1)
yest_f = (yest.strftime('%Y-%m-%d'), yest.strftime('%b %-d'), yest.strftime('%m/%d'))

weekstart = today - timedelta(days=(today.weekday() + 1) % 7)
weekstart_f = (weekstart.strftime('%Y-%m-%d'), weekstart.strftime('%b %-d'), weekstart.strftime('%m/%d'))

monthstart = today.replace(day=1)
monthstart_f = (monthstart.strftime('%Y-%m-%d'), monthstart.strftime('%b %-d'), monthstart.strftime('%m/%d'))

year = today.strftime('%Y')
yearstart_f = (f'{year}-01-01', 'Jan 1', '01/01')


def get_query(param):
  """Get query string param (if exists & has value) or empty string"""
  try:
    return request.args.get(param) if request.args.get(param) else ''
  except:
    return ''


def url_modify(val):
  """Modify url parts with custom replacements"""
  if val:
    url_replacements = {
      '!!' : '#', # replace !! (double exclamation) in urls to # (hashtag) as alternative to '%23'
    }
    for rk, rv in url_replacements.items():
      val = val.replace(rk, rv)

    return val

  else:
    return ''


def query_link(params = {}):
  """Create a query string link with the dict"""
  add = ''
  if params:
    mod_params = {}
    for p in params:
      if params[p] == ':default:':
        val = get_query(p)
        if val:
          add += f'{p}={val}&'
      elif not params[p]:
        add += ''
      else:
        add += f'{p}={params[p]}&'

  add = add.rstrip('&')
  m = get_query('m')

  return f'?m={m}&{add}'.rstrip('&')


def webcsv_link(file):
  """Create a link to the file through webcsv (if installed & running)"""
  host = urlparse(request.url_root).hostname
  port = urlparse(request.url_root).port
  csvurl = gen_csv_file
  if port == 8100:
    preurl = f'http://{host}:8002'
  else:
    preurl = f'https://{host}/:8002'
    csvurl = csvurl.replace('/var/www/Metrics/Metrics/', '')

  return f'{preurl}/webcsv?f={csvurl}'


def html_return_error(text):
  return f'<div class="error">{text}</div>'

# data analysis functions

def create_periods(periods):
  html = ''
  for i, p in enumerate(periods):
    arrow = f'<a class="arrow" href="https://tools.redment.com/year?from={p["from"][2]}&to={p["to"][2]}" target="blank">&rarr;</a>'
    html += '<div class="periodstats">'
    if p['from'][1] == p['to'][1]:
      html += f"<b>{p['label']}:</b> {p['from'][1]} {arrow} <ul>"
    else:
      html += f"<b>{p['label']}:</b> {p['from'][1]} - {p['to'][1]} {arrow} <ul>"
    html += ''.join((
                    f"<li>Total work hours: {p['metrics']['total_work_hours']}</li>",
                    f"<li>Total project hours: {p['metrics']['total_project_hours']}</li>",
                  ))
    html += '</ul></div>'

  return html


def parse_filter(qfilter):
  """Parse a filter (query) string and convert it into dictionary with keys, values, & attributes"""

  empty_filter = [{
    'key'       : '', 
    'col_num'   : '', 
    'val'       : '',
    'is_quoted' : False,
    'val_nq'    : '',
  }]

  if qfilter:
    filter_dicts = []
    filter_instances = qfilter.split(',')
    for f in filter_instances:
      # set default column to 'Description' if no column specified (i.e. no ':')
      f = f if ':' in f else f'Description:{f}'
      filter_parts = f.split(':')
      if len(filter_parts) == 2:
        filter_key = filter_parts[0]
        filter_val = filter_parts[1]
        filter_col_num = int(''.join(filter(str.isdigit, filter_key))) if any(char.isdigit() for char in filter_key) else 0
        if re.match(r'^col[0-9]+', filter_key):
          filter_key = 'QUERY_FILTER_COLUMN'
        filter_dicts.append({
          'key'       : filter_key,
          'col_num'   : filter_col_num,
          'val'       : filter_val,
          'is_quoted' : True if (filter_val.startswith('"') and filter_val.endswith('"')) or (filter_val.startswith("'") and filter_val.endswith("'")) else False,
          'val_nq'    : filter_val.strip('\'"')
        })
      else:
        filter_dicts = empty_filter
  else:
    return empty_filter

  return filter_dicts


def get_total_hours(df, start_date, end_date, qf=''):
  """Get the sum of distanceMI for qf (activity) (if not empty) from start_date through end_date"""

  # filter dataframe if qf is specified
  if qf:
    df = df_activity_filter(df, qf)

  #df['startTimeLocal'] = pd.to_datetime(df['startTimeLocal'])

  # case for single date (i.e. start & end are the same)
  #if start_date == end_date:
  #  mask = (df['startTimeLocal'].dt.date == pd.to_datetime(start_date).date())
  # duration periods (2 or more)
  #else:
  #  mask = (df['startTimeLocal'].dt.date >= pd.to_datetime(start_date).date()) & (df['startTimeLocal'].dt.date <= pd.to_datetime(end_date).date())
  
  #filtered_df = df.loc[mask]

  #return round(filtered_df['distanceMI'].sum(), 2)
  return 0


def df_activity_filter(odf, qf):
  """Filter rows of data from df (DataFrame) using qf ('query filter' activity name)"""

  df = odf.copy() # copy odf / [o]riginal [df]

  fi = parse_filter(qf)

  if len(fi) > 1: # multiple filters

    ## note: multiple filters method copied exactly from single filter, but put inside a loop for each filter query ##

    for f_val in fi:
      fi_key = f_val['key']
      fi_val = f_val['val']

      if fi_key == 'QUERY_FILTER_COLUMN':
        fi_key = df.columns[f_val['col_num']-1]

      if f_val['is_quoted'] == True: # exact match e.g. "Music" .. check if val_nq (no quote) == column value
        df = df[df[fi_key] == f_val['val_nq']] if fi_key in df else pd.DataFrame({})
      else:
        df = df[df[fi_key].str.contains(fi_val, na=False)] if fi_key in df else pd.DataFrame({})

  else: # single filter

    fi_key = fi[0]['key']
    fi_val = fi[0]['val']

    if fi_key == 'QUERY_FILTER_COLUMN':
      fi_key = df.columns[fi[0]['col_num']-1]

    if fi[0]['is_quoted'] == True: # exact match e.g. "Music" .. check if val_nq (no quote) == column value
      df = df[df[fi_key] == fi[0]['val_nq']] if fi_key in df else pd.DataFrame({})
    else:
      df = df[df[fi_key].str.contains(fi_val, na=False)] if fi_key in df else pd.DataFrame({})

  return df


def html_table_from_dataframe(df, apply_filters=False):
  """Create html table view from pandas dataframe of csv data"""

  #### start: filters & periods ###

  if apply_filters:

    # ?filter=:filter:
    qf = url_modify(get_query('filter'))
    if qf:
      df = df_activity_filter(df, qf)

    # ?periods=:period:
    qp = get_query('periods')
    if qp:
      qp_table = {
        'today'     : (today_f[0], today_f[0]),
        'yesterday' : (yest_f[0], yest_f[0]),
        'week'      : (weekstart_f[0], today_f[0]),
        'month'     : (monthstart_f[0], today_f[0]),
        'year'      : (yearstart_f[0], today_f[0]),
      }
      if qp in qp_table and 'Date' in df:
        qp = qp_table[qp]

        # make a copy of original date column before conversion
        df['OriginalDate'] = df['Date']
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

        # convert start_date and end_date to datetime
        start_date = pd.to_datetime(qp[0], format='%Y-%m-%d') # from
        end_date = pd.to_datetime(qp[1], format='%Y-%m-%d') # to

        # filter rows between start_date and end_date
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        # copy original date back & drop extra column
        df['Date'] = df['OriginalDate']
        df = df.drop(columns=['OriginalDate'])

  #### end: filters & periods ####

  qs = get_query('sort')

  csv_str = StringIO()
  df.to_csv(csv_str, index=False)
  csv_str.seek(0)  # Go back to the start of the StringIO object
  csv_content = csv_str.getvalue()

  html_table = '<table class="csv-table">\n'
  csv_reader = csv.reader(csv_content.splitlines(), skipinitialspace=True) # added {skipinitialspace=True} to fix issue with commas inside quoted cells
  headers = next(csv_reader)

  html_table += '<tr>'
  for header in headers:
    header = html.escape(header)
    html_table += f'<th>{header}</th>'
  html_table += '</tr>\n'

  # sorting: za -> Z-A
  if qs:
    if qs == 'za':
      csv_reader = reversed(list(csv_reader))

  for row in csv_reader:
    html_table += '<tr>'
    for cell in row:
      cell = html.escape(cell)
      html_table += f'<td>{cell}</td>'
    html_table += '</tr>\n'
    
  html_table += '</table>'

  return {
    'html'       : html_table,
    'total'      : len(df),
    'total_hrs'  : df[df['Description'] != 'Total Logged Hours']['Hours'].sum() if 'Description' in df else 0,
  }


def ifxyz(x, y, z, default = ''):
  """Return z if x == y else default (or empty) string"""
  return z if x == y else default


#### ---- main metrics dashboard process start ---- ####

# define metrics & log files

gen_dir       = f"{get_query('m').rstrip('/')}/gen/"
gen_csv_file  = ''


# shortcuts for quotes & new lines

q = '"'
nl = "\n"
lnl = "\\n"


# query string parameters

qf = url_modify(get_query('filter'))
qp = get_query('periods')
qs = get_query('sort')

# default view & periods filtering views (files: today.csv yesterday.csv year.csv) 

if ( qp == 'year' or 
     qp == 'month' or 
     qp == 'week' ) and os.path.isfile(f'{gen_dir}{year}.csv'):
  gen_csv_file  = f'{gen_dir}{year}.csv'

elif (qp == 'today' or not qp) and os.path.isfile(f'{gen_dir}{today.strftime("%Y-%m-%d")}.csv'): # today and Default
  gen_csv_file  = f'{gen_dir}{today_f[0]}.csv'

elif (qp == 'yesterday' or not qp) and os.path.isfile(f'{gen_dir}{yest_f[0]}.csv'):
  gen_csv_file  = f'{gen_dir}{yest_f[0]}.csv'

elif os.path.isfile(f'{gen_dir}{year}.csv'): # use year.csv for all other cases (if file exists)
  gen_csv_file  = f'{gen_dir}{year}.csv'


# load & analyze data with pandas

if gen_csv_file:

  # Load the csv file as a DataFrame
  df = pd.read_csv(gen_csv_file) if os.path.isfile(gen_csv_file) else pd.DataFrame({})

  # define periods

  # custom calculations
  tod_total_work_hours = '--' # get_total_hours(df, today_f[0], today_f[0], 'C1:"Work"')
  tod_total_project_hours = '--' # get_total_hours(df, today_f[0], today_f[0], 'C1:"Projects"')

  yest_total_work_hours = '--' # get_total_hours(df, yest_f[0], yest_f[0], 'C1:"Work"')
  yest_total_project_hours = '--' # get_total_hours(df, yest_f[0], yest_f[0], 'C1:"Projects"')

  week_total_work_hours = '--' # get_total_hours(df, weekstart_f[0], today_f[0], 'C1:"Work"')
  week_total_project_hours = '--' # get_total_hours(df, weekstart_f[0], today_f[0], 'C1:"Projects"')

  month_total_work_hours = '--' # get_total_hours(df, monthstart_f[0], today_f[0], 'C1:"Work"')
  month_total_project_hours = '--' # get_total_hours(df, monthstart_f[0], today_f[0], 'C1:"Projects"')

  year_total_work_hours = '--' # get_total_hours(df, yearstart_f[0], today_f[0], 'C1:"Work"')
  year_total_project_hours = '--' # get_total_hours(df, yearstart_f[0], today_f[0], 'C1:"Projects"')

  periods = [
    {
      'label' : 'Today',
      'from'  : (today_f[0], today_f[1], today_f[2]),
      'to'    : (today_f[0], today_f[1], today_f[2]),
      'metrics' : {
        'total_work_hours'    : tod_total_work_hours,
        'total_project_hours' : tod_total_project_hours,
      }
    },
    {
      'label' : 'Yesterday',
      'from'  : (yest_f[0], yest_f[1], yest_f[2]),
      'to'    : (yest_f[0], yest_f[1], yest_f[2]),
      'metrics' : {
        'total_work_hours'    : yest_total_work_hours,
        'total_project_hours' : yest_total_project_hours,
      }
    },
    {
      'label' : 'This week',
      'from'  : (weekstart_f[0], weekstart_f[1], weekstart_f[2]),
      'to'    : (today_f[0], today_f[1], today_f[2]),
      'metrics' : {
        'total_work_hours'    : week_total_work_hours,
        'total_project_hours' : week_total_project_hours,
      }
    },
    {
      'label' : 'This month',
      'from'  : (monthstart_f[0], monthstart_f[1], monthstart_f[2]),
      'to'    : (today_f[0], today_f[1], today_f[2]),
      'metrics' : {
        'total_work_hours'    : month_total_work_hours,
        'total_project_hours' : month_total_project_hours,
      }
    },
    {
      'label' : 'This year',
      'from'  : (yearstart_f[0], yearstart_f[1], yearstart_f[2]),
      'to'    : (today_f[0], today_f[1], today_f[2]),
      'metrics' : {
        'total_work_hours'    : year_total_work_hours,
        'total_project_hours' : year_total_project_hours,
      }
    }
  ]

  frame_table = html_table_from_dataframe(df, apply_filters=True)

  scroll_hash = '' # set to: "#activities" to enable scroll hash

  output_html = ''.join((

    f'<h3>Metrics {year}</h3>',
    'Summary Reports: <br>',
    '- Projects: Subprojects: Miniprojects: Microprojects <br>',
    '- Total Hours: Projects, Work, Study, Training, Practice <br> ',
    '- Started, Finished, Active, Archived <br><br>',
    '<div class="periodstats-outer">',
    create_periods(periods),
    '</div>',

    '<table class="plain">',
     # note: the CSV link below requires/assumes webcsv being installed/used & running on the machine
     f'<td><h4 id="activities">Metrics CSV (<a href="{ webcsv_link(gen_csv_file) }" target="_blank">{ os.path.basename(gen_csv_file) }</a>)</h4></td>',
     f'<td><div class="filter-search">',
        '<table class="plain">',
         f'<td><input type="text" placeholder="C1:Music,C2:Practice" id="filter-query" value="{ html.escape(qf) }"></td>',
          '<td><button id="filter-go">Go</button></td>',
        '</table>',
      '</div></td>',
    '</table>',

    '<div class="filters">',
       '<div class="filter-lists">',
         '<span class="dim">Filters:</span> ',
        f'<a href="{ query_link({ "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qf,"","bold") }">Default</a>, ',
        f'<a href="{ query_link({ "filter" : "C1:Work", "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qf,"C1:Work","bold") }">Work</a>, ',
        f'<a href="{ query_link({ "filter" : "C1:Projects", "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qf,"C1:Projects","bold") }">Projects</a>, ',
        f'<a href="{ query_link({ "filter" : "C1:Study", "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qf,"C1:Study","bold") }">Study</a>, ',
        f'<a href="{ query_link({ "filter" : "C1:Practice", "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qf,"C1:Practice","bold") }">Practice</a>',
       '</div>',
    '</div>',

    '<div class="periods"> <span class="dim">Periods:</span> ',
    f'<a href="{ query_link({ "filter" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qp,"","bold") }">Default</a>, ',
    f'<a href="{ query_link({ "filter" : ":default:", "periods" : "today" }) }{ scroll_hash }" class="{ ifxyz(qp,"today","bold") }">Today</a>, ',
    f'<a href="{ query_link({ "filter" : ":default:", "periods" : "yesterday" }) }{ scroll_hash }" class="{ ifxyz(qp,"yesterday","bold") }">Yesterday</a>, ',
    f'<a href="{ query_link({ "filter" : ":default:", "periods" : "week" }) }{ scroll_hash }" class="{ ifxyz(qp,"week","bold") }">This Week</a>, ',
    f'<a href="{ query_link({ "filter" : ":default:", "periods" : "month" }) }{ scroll_hash }" class="{ ifxyz(qp,"month","bold") }">This Month</a>, ',
    f'<a href="{ query_link({ "filter" : ":default:", "periods" : "year" }) }{ scroll_hash }" class="{ ifxyz(qp,"year","bold") }">This Year</a> ',
    ' &middot; ',
    ' <span class="dim">Sort:</span> ',
      f'<a href="{ query_link({ "filter" : ":default:", "periods" : ":default:" }) }{ scroll_hash }" class="{ ifxyz(qs,"","bold") }">A-Z</a> ',
      f'<a href="{ query_link({ "filter" : ":default:", "periods" : ":default:", "sort": "za" }) }{ scroll_hash }" class="{ ifxyz(qs,"za","bold") }">Z-A</a> ',
    '</div>',

    f'<div class="table-outer" id="data-scroller">{ frame_table["html"] }</div>',

    '<div class="details">',
      f'Total: <b>{ frame_table["total"] }</b>, <i>{ round(frame_table["total_hrs"], 2) }hrs</i> ',
       '<a href="javascript:;" onclick="downloadCSV();" class="right">Download</a>',
    '</div>',


    f'''

    <script type="text/javascript">

      // -- query filter search input functions -- //

      function urlPrep(str) {{
        str = encodeURIComponent(str);
        str = str.replace(/%3A/g,":"); // ignore :
        return str;
      }}

      var fquery = document.getElementById('filter-query');
      var fgo = document.getElementById('filter-go');

      function filterGo(){{
        var link = "{ query_link({ "filter": f"{ q } + urlPrep(fquery.value) + { q }", "periods" : "year" if not qp else ":default:" }) }{ scroll_hash }";
        window.location.href = link;
      }}

      fquery.addEventListener('keyup', function(e){{ if ( e.key === "Enter" ) {{ e.preventDefault(); filterGo(); }} }});
      fgo.addEventListener('click', filterGo);


      // -- scroll to bottom of data table on #activities -- //
      
      if ( window.location.hash.includes('activities') ) {{
        var dataScroller = document.getElementById('data-scroller');
        dataScroller.scrollTop = dataScroller.scrollHeight;
      }}


      // -- csv downloader for rendered table -- //

      function downloadCSV() {{

        var table = document.querySelector(".csv-table");
        var rows = Array.from(table.querySelectorAll("tr"));
        var csvContent = "";

        rows.forEach(function(row, rowIndex) {{
            var columns = Array.from(row.querySelectorAll("td, th"));

            columns.forEach(function(column, columnIndex) {{
              csvContent += '"' + column.innerText.replace(/"/g, '""') + '"';
              if ( columnIndex < columns.length - 1 ) {{
                csvContent += ',';
              }}
            }});
            csvContent += "\\n";
        }});

        csvContent += "{',' + macros.hours_to_human(round(frame_table["total_hrs"], 2)) + ',,,,,Total Hours,' + str(round(frame_table["total_hrs"], 2))  + ','+lnl if qf else ''}";

        var downloadLink = document.createElement("a");
        var blob = new Blob(["\\ufeff", csvContent]);
        var url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = '{os.path.basename(gen_csv_file)}';

        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      }}

    </script>

    ''',

  ))

