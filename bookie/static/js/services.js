'use strict';

/* Services */
var services = angular.module("bookieServices", ["ngResource"]);

services.factory("Entity", function($resource, $routeParams) {
    return $resource("/:accountId/entity/:id", {}, {
        query: {
            method: "GET",
            isArray: true
        }
    });
});

services.factory("Location", function($resource, $routeParams) {
    return $resource("/:accountId/location/:id", {}, {
        query: {
            method: "GET",
            isArray: true
        }
    });
});

services.factory("Account", function($resource, $routeParams) {
    return $resource("/user/account/:id", {}, {
        query: {
            method: "GET",
        },
        get: {
            method: "GET",
        },
        setDefault: {
            method: "POST"
        }
    });
});

/* Service for setting account states globally */
services.service("AccountState", function($rootScope, $location, Account) {
    var root = $rootScope;
    var this_ = this;

    this._updateAccounts = function(cb) {
        Account.query(cb)
    }

    this._updateAccounts(function(data) {
        /* Three scenarios:
        * A) No default in server response, set it to first account available
        * B) Default > data.default
        *
        * C) Lastly if routeParams.accountId should override both setting the
        *    current account
        */
        if (!root.account) {
            if (!data.default) {
                root.account = data.accounts[0]
            } else {
                root.account = data.default
            }

            if (root.params.accountId) {
                angular.forEach(data.accounts, function(a) {
                    if (a.uuid == root.params.accountId) {
                        root.account = a;
                    }
                });
            }
        }

        root.accounts = data.accounts;
        root.default = data.default;
    });

    this.updateAccounts = function() {
        this._updateAccounts(function(data) {
            root.accounts = data.accounts;
        });
    }

    this.setAccount = function(account) {
        root.account = account;
        $location.path("#" + account.uuid + "/home")
    }

    this.setDefault = function(account) {
        Account.setDefault({}, {accountId: account.uuid}, function() {
            root.default = account
        });
    }
});
