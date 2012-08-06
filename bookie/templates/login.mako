<%inherit file="base.mako"/>

<%block name="content">
<div class="row-fluid">
    <div class="span6">
        <h1>Please login:</h1>
        <form action="${url}" method="post">
            <input type="hidden" name="came_from" value="${came_from}"/>
            <input type="text" name="user_name" value="${user_name}"/><br/>
            <input type="password" name="password" value="${password}"/><br/>
            <!--input type="submit" name="form.submitted" value="Log In"/-->

            <div class="form-actions">
                <button type="submit" name="submit" class="btn btn-success">Log in</button>
            </div>

            <div>
                <h4 class="alert-heading">${_("Forgot something?")}</h4>
                Fill out your username above and click <em>${_("Reset password")}</em> below to receive a e-mail to reset your password!
            </div>
            <div class="form-actions">
                <button type="submit" name="reset-password" class="btn btn-primary">${_("Reset password")}</button>
            </div>
        </form>
    </div>
</div>
</%block>
