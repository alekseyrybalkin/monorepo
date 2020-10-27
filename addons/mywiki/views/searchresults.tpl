% include('header.tpl')
% include('searchform.tpl')
<table>
% for result in results:
<tr>
    <td>{{ result['rank'] + 1 }}</td>
    <td>{{ result['percent'] }}%</td>
    <td>
<a href="/article?name={{ result['name'] }}&query={{ query }}">{{ result['name'] }}</a><br/>
    </td>
</tr>
% end
</table>
% include('footer.tpl')
