% include('header.tpl')
<div>
    <div>
        <form action="/folders?delete=1" method="post">
            <h5>Your folders:</h5><br/>
            % for f in folders:
            <div><label><input type="radio" name="folder_to_delete" value="{{ f }}"><span>{{ f }}</span></label></div>
            % end
            <br/>
            <button type="submit" value="delete">Delete selected folder</button>
        </form>
    </div>
    <div>
        <form action="/folders?create=1" method="post">
            <h5>New folder:</h5><br/>
            <input type="text" name="new_folder"/>
            <br/><br/>
            <button type="submit" value="create">Create new folder</button>
        </form>
    </div>
</div>
% include('footer.tpl')
