% include('header.tpl')
<div>
    <div>
        <br/>
        <form action="/folder?f={{ folder }}" method="post">
            <button type="submit" name="change" value="command_delete">Delete selected</button>
            % if len(folders) > 1:
            <button type="submit" name="change" value="command_move">Move selected into:</button>
            <select name="target_folder">
                % for f in folders:
                    % if f != folder and f == 'INBOX':
                    <option value="{{ f }}">{{ f }}</option>
                    % end
                % end

                % for f in folders:
                    % if f != folder and f != 'INBOX':
                    <option value="{{ f }}">{{ f }}</option>
                    % end
                % end
            </select>
            % end
            <br/><br/>
            <table>
                <thead>
                    <tr>
                        <th><input type="checkbox" onchange="window.location.href='/folder?f={{ folder }}&check_all=1'"></th>
                        <th>UID</th>
                        <th>Date</th>
                        <th>Sender</th>
                        <th>Subject</th>
                    </tr>
                </thead>
                <tbody>
                    % for m in messages:
                    <tr>
                        <td><input type="checkbox" name="m{{ m.uid }}" id="m{{ m.uid }}" {{ checked if check_all else '' }}></td>
                        <td>{{ m.uid }}</td>
                        <td>{{ m.date.strftime('%d.%m.%Y %H:%M') }}</td>
                        <td>{{ m.sender }}</td>
                        <td><a href="/message/{{ m.uid }}?f={{ folder }}">{{ m.subject }}</a></td>
                    </tr>
                    % end
                </tbody>
            </table>
        </form>
    </div>
</div>
% include('footer.tpl')
