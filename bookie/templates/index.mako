<%inherit file="base.mako"/>

<%block name="content">
    <div class="hero-unit">
        <h1>Welcome to Bookie!</h1>
        <p>
            Bookie is a booking application for Rental companies....
        </p>

        % if request.user is None:
            <br />
            <p>Hi, I can see you are not logged in... Click ${api.utils.create_anchor('here', 'login')} here if you wish to login</p>
        % endif
    </div>
</%block>
