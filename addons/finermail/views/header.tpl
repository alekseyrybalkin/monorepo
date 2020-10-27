<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"/>

    <title>{{ title }}Finer Mail</title>
    <link rel="shortcut icon" href="/static/finermail.ico"/>
    <link rel="stylesheet" type="text/css" href="/static/finermail.css?v=3"/>
</head>
<body>
    <div>
        % if page not in ('login', 'error') and folders:
        <div>
            <div>
                % for f in folders:
                    % if f == 'INBOX':
                    <a href="/folder?f={{ f }}">{{ f }}</a>
                    % end
                % end
                % for f in folders:
                    % if f != 'INBOX':
                    <a href="/folder?f={{ f }}">{{ f }}</a>
                    % end
                % end
            </div>
            <div class="right-menu">
                <a href="/folders">Manage folders</a>
                <a href="/?logout=true">Logout</a>
            </div>
        </div>
        <br/>
        % end
