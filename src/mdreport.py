#! /home/cpecc/ve_mdr/bin/python

import datetime
import uuid
import argparse
import csv
import html

import shortcodes
import pytz
import markdown

markdown_placeholders = {}

def placeholder(text):
    ph = str(uuid.uuid4())
    markdown_placeholders[ph] = text
    return ph

@shortcodes.register('current_time')
def current_time(context, content, pargs, kwargs):
    tz_name = pargs[0] if pargs else 'UTC'
    utc_time = pytz.utc.localize(datetime.datetime.utcnow())
    tz_time = utc_time.astimezone(pytz.timezone(tz_name))
    return tz_time.strftime('%a %b %d %Y %H:%M:%S %Z')

@shortcodes.register('include_file')
def include_file(context, content, pargs, kwargs):
    post_markdown = kwargs.get('post_markdown', 'False') == 'True'
    file_to_include = pargs[0]
    with open(file_to_include) as f:
        file_contents = f.read().strip()
        return placeholder(file_contents) if post_markdown else file_contents

@shortcodes.register('table_from_file')
def table_from_file(context, content, pargs, kwargs):
    table_file = pargs[0]
    with open(table_file, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    table_html = """
<table>
<thead>
<tr>
%s
</tr>
</thead>
<tbody>
%s
</tbody>
</table>
"""
    header = '\n'.join('<th>' + html.escape(e) + '</th>' for e in rows[0])
    body = []
    for row in rows[1:]:
        body.append('<tr>')
        for e in row:
            body.append('<td>' + html.escape(e) + '</td>')
        body.append('</tr>')
    body = '\n'.join(body)
    rendered_table = table_html % (header, body)
    return placeholder(rendered_table)

arg_parser = argparse.ArgumentParser(description='Process MarkdownReport')
arg_parser.add_argument('mdr_file', help='an mdr file to process')
args = arg_parser.parse_args()

with open(args.mdr_file) as f:
    text = f.read()

sc_parser = shortcodes.Parser()
output = sc_parser.parse(text, context=None)
html = markdown.markdown(output, extensions=['markdown.extensions.fenced_code',
    'markdown.extensions.tables'])
for ph, text in markdown_placeholders.items():
    html = html.replace(ph, text)

template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Output from %s</title>

<style>
body {
    font-family: sans-serif;
    line-height: 160%%;
    font-size: 12.8px;
    width: 760px;
    margin-left: auto;
    margin-right: auto;
}
h1 {
    margin-top: 30px;
    color: #47c;
}
:not(pre) > code {
    background-color: #f7f7f7;
    padding-left: 5px;
    padding-right: 5px;
}
pre {
    background-color: #f7f7f7;
    padding: 5px;
}
table:not(.display) {
    border-collapse: collapse;
}
table:not(.display) th {
    font-weight: bold;
    background-color: #f7f7f7;
}
table:not(.display) th, table:not(.display) td {
    border: 1px solid #ccc;
    padding: 6px 13px;
}
table:not(.display) tr {
    border-top: 1px solid #ccc;
    background-color: #fff;
}
figure {
    margin: 0px;
}
@media all {
    .page-break { display: none; }
}
@media print {
    .page-break { display: block; page-break-before: always; }
}
</style>
</head>
<body>
%s
</body>
</html>
"""
print(template % (args.mdr_file, html))