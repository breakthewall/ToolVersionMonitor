<!DOCTYPE html>
<html>
<head>
    <title>Tool Version Monitor</title>
    <link rel="stylesheet" href="static/tvm.css">
</head>
<body>
{% set nb_tables = 2 %}
{% set nb_tools = rows|length %}
{% set nb = nb_tools / nb_tables %}
{% set nb = nb|int + 1 %}
<div class="row">
  {% for i in range(nb_tables) %}
    <div class="column">
        <table class="center">
            {% for row in rows[nb*i:nb*(i+1)] %}
                <tr>
                    <td>
                        <p class="badges">
                            {% for col in row[1] %}
                                {{ col }}</br>
                            {% endfor %}
                        </p>
                    </td>
                    <td>
                        <p class="tool">{{ row[0] }}</p>
                    </td>
                </tr>
            {% endfor %}
        </table>
    </div>
  {% endfor %}
</body>
</html>
