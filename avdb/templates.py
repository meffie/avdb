#
# Report templates
#

template = {

    'csv':"""\
{{#results}}
{{cell}},{{host}},{{node}},"{{version}}"
{{/results}}""",

    'html':"""\
<!DOCTYPE html>
<html>
<head>
<style>
body {
  margin: 3em;
}
h1 {
  font-family: sans-serif;
  font-size: 180%;
}
table {
  border-collapse: collapse;
}
table, th, td {
  border: 1px solid #999;
}
td {
  padding: .5em;
  padding-left: 1em;
  padding-right: 1em;
}
</style>
</head>
<body>
<h1>afs version tracking database</h1>
<table>
{{#results}}
<tr>
<td>{{cell}}</td>
<td>{{host}}</td>
<td>{{node}}</td>
<td>{{version}}</td>
</tr>
{{/results}}
</table>

<p>rendered on {{generated}}</p>
</body>
</html>""",
}
