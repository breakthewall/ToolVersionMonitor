<!DOCTYPE html>
<html>
<head>
    <title>Tool Version Monitor</title>
    <link rel="stylesheet" href="static/tvm.css">
</head>
<body>
    <table class="center">
        %for row in rows[0:2]:
            <tr>
                <td>
                    <p class="badges">
                        %for col in row[1]:
                            {{!col}}</br>
                        %end
                    </p>
                </td>
                <td>
                    <p class="tool">{{!row[0]}}</p>
                </td>
            </tr>
        %end
    </table>
    <table class="center">
        %for row in rows[2:4]:
            <tr>
                <td>
                    <p class="badges">
                        %for col in row[1]:
                            {{!col}}</br>
                        %end
                    </p>
                </td>
                <td>
                    <p class="tool">{{!row[0]}}</p>
                </td>
            </tr>
        %end
    </table>
</body>
</html>
