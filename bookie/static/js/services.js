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
            isArray: true
        },
        get: {
            method: "GET",
        },

    });
});
