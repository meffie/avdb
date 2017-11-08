#
# Report templates
#

template = {

    'csv':"""\
{{#results}}
{{cell.name}},{{host.address}},{{node.name}},{{version.added}},"{{version.version}}"
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
<thead>
<tr>
<th>cellname</th>
<th>address</th>
<th>node</th>
<th>added date</th>
<th>version string</th>
</tr>
</thead>
<tbody>
{{#results}}
<tr>
<td>{{cell.name}}</td>
<td>{{host.address}}</td>
<td>{{node.name}}</td>
<td>{{version.added}}</td>
<td>{{version.version}}</td>
</tr>
{{/results}}
</tbody>
</table>

<p>rendered on {{generated}}</p>
</body>
</html>""",
}
