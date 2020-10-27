% include('header.tpl')
<div>
    <div>&nbsp;</div>
    <div>
        <br/>
        <br/>
        % if login_error:
            <p>Error: {{ login_error }}</p>
        % end
        <br/>
        <br/>
        <form method="post">
            <div>
                <label for="inputPassword">Password</label>
                <div>
                    <input type="password" id="inputPassword" name="password" autofocus/>
                </div>
            </div>
            <br/>
            <div>
                <div>
                    <button type="submit">Sign in</button>
                </div>
            </div>
        </form>
    </div>
    <div>&nbsp;</div>
</div>
% include('footer.tpl')
