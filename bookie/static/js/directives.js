'use strict';

/* Directives */
var directives = angular.module("bookie.directives", ["ui"]);


/* A whole menu to be used on the top of a overview page */
directives.directive("objectsMenu", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<div><refresh></refresh> <create></create><br/>Showing {{objects.length}} objects</div>'
    };
});


directives.directive("refresh", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn btn-mini btn-primary" ng-click="refreshObjects()"><i class="icon-refresh"></i> Refresh</button>',
        link: function(scope, element, attrs, controller) {
            scope.refreshObjects = function() {
                scope.objects = scope.service.query(scope.params);
            }
        }
    };
});


/* Create something new */
directives.directive("create", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn btn-mini btn-success" ng-click="crudAdd()"><i class="icon-plus"></i> Add</button>',
        link: function(scope, element, attrs) {
            if (!scope.crudAdd) {
                scope.crudAdd = function() {
                    scope.object = new scope.service();
                    scope.template = scope.tpl;
                };
            }
        }
    };
});

/* Delete button and update objects */
directives.directive("delete", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn btn-mini btn-danger" ng-click="crudDelete()"><i class="icon-remove icon-white"></i> {{text}}</button>',
        link: function(scope, element, attrs, controller) {
            if (!scope.crudDelete) {
                scope.crudDelete = function() {
                    /* Fire off a delete and as a callback we update objects */
                    scope.service.delete({accountId: scope.account.uuid, id: scope.object.id}, function() {
                        /* If we have objects refresh them */
                        scope.text = attrs.text || "";
                        scope.$parent.objects = scope.service.query(scope.params);
                    });
                }
            };
        }
    };
});

/* Helper to create a edit button */
directives.directive("edit", function() {
    return {
        restrict: "E",
        replace:  true,
        scope: { url: '@' },
        template: '<a class="btn btn-mini btn-info" ng-href="{{url}}"><i class="icon-edit"></i> {{text}}</a>',
        link: function(scope, element, attrs) {
            scope.text = attrs.text || "";
        }
    };
});

/* Save the object and return to the previous page */
directives.directive("save", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn btn-success" ng-click="crudSave()"><i class="icon-ok"></i> Save</a>',
        link: function(scope, element, attrs) {
            if (!scope.crudSave) {
                scope.crudSave = function() {
                    scope.object.$save(scope.params, function() {
                        if (scope.$parent.template) {
                            scope.$parent.template = undefined;
                            scope.objects = scope.service.query(scope.params)
                        } else {
                            scope.back();
                        }
                    });
                };
            }
        }
    };
});


directives.directive("cancel", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn" ng-click="crudCancel()"><i class="icon-remove"></i> Cancel</button>',
        link: function(scope, element, attrs) {
            if (!scope.crudCancel) {
                scope.crudCancel = function() {
                    if (scope.$parent.template) {
                        scope.$parent.template = undefined;
                    } else {
                        scope.back();
                    }
                };
            }
        }
    };
});

