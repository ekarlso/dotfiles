'use strict';


/* App Module */
var app = angular.module("bookie", ["bookie.services", "bookie.directives"]);

app.config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/', {templateUrl: "static/partials/index.html", controller: MainCtrl}).
            when('/about', {templateUrl: 'static/partials/about.html', controller: AccountCtrl}).
            when('/accounts', {templateUrl: 'static/partials/user_accounts.html', controller: AccountCtrl}).
            when('/:accountId/home', {templateUrl: 'static/partials/account.html'}).
            when('/:accountId/settings', {templateUrl: 'static/partials/account_settings.html'}).
            when('/:accountId/booking', {templateUrl: 'static/partials/booking.html', controller: BookingCtrl}).
            when('/:accountId/booking/:id', {templateUrl: 'static/partials/booking-detail.html', controller: BookingDetailCtrl}).
            when('/:accountId/category', {templateUrl: 'static/partials/category.html',  controller: CategoryCtrl}).
            when('/:accountId/category/:id', {templateUrl: 'static/partials/category-detail.html', controller: CategoryDetailCtrl}).
            when('/:accountId/customer', {templateUrl: 'static/partials/customer.html',  controller: CustomerCtrl}).
            when('/:accountId/customer/:id', {templateUrl: 'static/partials/customer-detail.html', controller: CustomerDetailCtrl}).
            when('/:accountId/entity', {templateUrl: 'static/partials/entity.html', controller: EntityCtrl}).
            when('/:accountId/entity/:id', {templateUrl: 'static/partials/entity-detail.html', controller: EntityDetailCtrl}).
            when('/:accountId/location', {templateUrl: 'static/partials/location.html',  controller: LocationCtrl}).
            when('/:accountId/location/:id', {templateUrl: 'static/partials/location-detail.html', controller: LocationDetailCtrl}).
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


function MainCtrl($scope) {
}


function BookingCtrl($scope, Booking) {
    $scope.service = Booking;
    $scope.objects = $scope.service.query($scope.params);
}


function BookingDetailCtrl($scope, Booking) {
    $scope.service = Booking;
    $scope.object = $scope.service.get($scope.params)
}


function CustomerCtrl($scope, Customer) {
    $scope.service = Customer;
    $scope.objects = $scope.service.query($scope.params);

    $scope.addObject = function() {
        $scope.tpl = "static/partials/add.html";
    }
}

function CustomerDetailCtrl($scope, Customer) {
    $scope.service = Customer;
    $scope.object = $scope.service.get($scope.params)
}

function CategoryCtrl($scope, Category) {
    $scope.service = Category;
    $scope.objects = $scope.service.query($scope.params);
}

function CategoryDetailCtrl($scope, Category) {
    $scope.service = Category;
    $scope.object = $scope.service.get($scope.params)
}

function EntityCtrl($scope, Entity) {
    $scope.service = Entity;
    $scope.objects = $scope.service.query($scope.params);

    $scope.tpl = "static/partials/entity-detail.html"
}

function EntityDetailCtrl($scope, Entity) {
    $scope.service = Entity;
    $scope.object = $scope.service.get($scope.params)
}


function LocationCtrl($scope, Location) {
    $scope.service = Location;
    $scope.objects = $scope.service.query($scope.params);
}

function LocationDetailCtrl($scope, Location) {
    $scope.service = Location;
    $scope.object = $scope.service.get($scope.params)
}

function AccountCtrl($scope, AccountState) {
    $scope.setAccount = AccountState.setAccount;
    $scope.setDefault = AccountState.setDefault;

    /*
     * Filter out the current account from the overview
    */
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
