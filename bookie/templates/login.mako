<%inherit file="base.mako"/>

<%block name="content">
<div class="row-fluid">
    <div class="span6">
        <h1>Please login:</h1>
        <form action="${url}" method="post">
            <input type="hidden" name="came_from" value="${came_from}"/>
            <input type="text" name="login" value="${login}"/><br/>
            <input type="password" name="password" value="${password}"/><br/>
            <!--input type="submit" name="form.submitted" value="Log In"/-->
            <button type="submit" name="submit" class="btn btn-primary">Log in</button>
        </form>
    </div>
</div>
</%block>
