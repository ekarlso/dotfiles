'use strict';

/* App Module */
var app = angular.module("bookie", ["bookieServices"]);

app.config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/accounts', {templateUrl: 'static/partials/user_accounts.html', controller: AccountCtrl}).
            when('/:accountId/home', {templateUrl: 'static/partials/account.html'}).
            when('/:accountId/settings', {templateUrl: 'static/partials/account_settings.html'}).
            when('/:accountId/location', {templateUrl: 'static/partials/location.html',  controller: LocationCtrl}).
            when('/:accountId/location/:id', {templateUrl: 'static/partials/location-detail.html', controller: LocationDetailCtrl}).
            when('/:accountId/entity', {templateUrl: 'static/partials/entity.html',  controller: EntityCtrl}).
            when('/:accountId/entity/:id', {templateUrl: 'static/partials/entity-detail.html', controller: EntityDetailCtrl}).
        otherwise({redirectTo: "/"});
}]);


/* Add utility stuff to rootScope - www.deansofer.com */
app.run(["$rootScope", "$routeParams", function($rootScope, $routeParams) {
    /**
    * Wrapper for angular.isArray, isObject, etc checks for use in the view
    *
    * @param type {string} the name of the check (casing sensitive)
    * @param value {string} value to check
    */
    $rootScope.is = function(type, value) {
        return angular['is'+type](value);
    };

    /**
    * Wrapper for $.isEmptyObject()
    *
    * @param value	{mixed} Value to be tested
    * @return boolean
    */
    $rootScope.empty = function(value) {
        return $.isEmptyObject(value);
    };

    /**
    * Debugging Tools
    *
    * Allows you to execute debug functions from the view
    */
    $rootScope.log = function(variable) {
	    console.log(variable);
    };

    /**
    * Alert function
    *
    */
    $rootScope.alert = function(text) {
	    alert(text);
    };

    $rootScope.back = function() {
        history.back();
    };

    /**
    * Easy access to route params
    */
    $rootScope.params = $routeParams;
}]);


function LocationCtrl($scope, Location) {
    $scope.locations = Location.query($scope.params);
}

function LocationDetailCtrl($scope, Location) {
    $scope.location = Location.get($scope.params)
}

function EntityCtrl($scope, Entity) {
    $scope.entities = Entity.query($scope.params);
}

function EntityDetailCtrl($scope, Entity) {
    $scope.entity = Entity.get($scope.params)
}

function AccountCtrl($scope, AccountState) {
    $scope.setAccount = AccountState.setAccount;
    $scope.setDefault = AccountState.setDefault;

    $scope.isCurrent = function(account) {
        var d = $scope.default;

        if (d && account.uuid === d.uuid) {
            return;
        } else {
            return account;
        }
    }
};


function AccountNavCtrl($scope) {
};
