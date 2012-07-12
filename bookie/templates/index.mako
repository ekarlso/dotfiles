<%inherit file="base.mako"/>

<%block name="content">
    <div class="hero-unit">
        <h1>Welcome to Bookie!</h1>
        <p>
            Bookie is a booking application for Rental companies....
        </p>

        % if request.user is None:
            <br />
            <p>Hi, I can see you are not logged in... Click <a class="btn btn-success" href="${request.route_url('login')}">Login</a> to login!
        % endif
    </div>
</%block>
