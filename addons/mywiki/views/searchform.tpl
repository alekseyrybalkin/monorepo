<div style="margin-bottom: 4px;">
    <div style="display: inline; float: left; font-weight: bold; font-size: 1.6em; line-height: 1.1em;">
        <form style="margin-top: 40px; display: inline;" action="/">
            <a style="font-size: 1em;" href="/">⊟</a>&nbsp;
        </form>
        {{ name }}
        % if short_description:
        <div style="font-size: 0.6em; font-weight: normal;">{{ short_description }}</div>
        % end
    </div>
    <div style="display: inline; float: right;">
        <form style="margin-top: 40px; display: inline;" action="/">
            <input style="font-size: 1.1em;" type="text" name="query" value="{{ query }}"></input>
            <input style="font-size: 1.1em;" type="submit" value="search"/>
        </form>
    </div>
    <br/>
    <br/>
    % if short_description:
    <br/>
    % end
</div>
