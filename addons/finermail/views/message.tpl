% include('header.tpl')
<div>
    <div>
        <h5>Date: {{ message.date.strftime('%d.%m.%Y %H:%M') }}</h5>
        <h5>From: {{ message.sender }}</h5>
        <h5>Subject: {{ message.subject }}</h5>
        <br/>
        % if message.body:
        <pre><span class="message-body">{{ message.body }}</span></pre>
        % else:
        <span class="message-body">{{ !message.body_html }}</span>
        % end
    </div>
</div>
% include('footer.tpl')
