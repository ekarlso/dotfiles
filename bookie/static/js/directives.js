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
            /*
             * Inline overview: delete object and refresh objects
             * Inline edit (Same path as overview typically):
             *      delete, unset template
             *
             * Outline: delete the object and go back
             */
            if (!scope.crudDelete) {
                scope.crudDelete = function(object) {
                    /* Fire off a delete and as a callback we update objects */
                    scope.service.delete({accountId: scope.account.uuid, id: scope.object.id}, function() {
                        scope.text = attrs.text || "";
                        scope.$parent.objects = scope.service.query(scope.params);
                    });
                };
            }
        }
    };
});

/* Helper to create a edit button */
directives.directive("edit", ["$location", function($location) {
    return {
        restrict: "E",
        replace:  true,
        scope: { url: '@' },
        template: '<button class="btn btn-mini btn-info" ng-click="crudEdit()" ng-href="{{url}}"><i class="icon-edit"></i> {{text}}</a>',
        link: function(scope, element, attrs) {
            scope.text = attrs.text || "";
            /* Inline: We change object to the given object in args and set
             * template.
             *
             * Outline: If we're passed a URL then the next controller handles
             * the getting of the object, we simple use $location.path() to
             * change the location.
             */
            if (!scope.crudEdit) {
                scope.crudEdit = function(object) {
                    if (scope.url) {
                        $location.path(scope.url);
                        return;
                    } else {
                        scope.$parent.object = object;
                        scope.$parent.template = scope.tpl;
                    }
                };
            }
        }
    };
}]);

/* Save the object and return to the previous page */
directives.directive("save", function() {
    return {
        restrict: "E",
        replace: true,
        template: '<button class="btn btn-success" ng-click="crudSave()"><i class="icon-ok"></i> Save</a>',
        link: function(scope, element, attrs) {
            /* Inline: Undef Update objects using scope.params as argument and
             * undef template
             *
             * Outline: Go back
             */
            if (!scope.crudSave) {
                scope.crudSave = function() {
                    scope.object.$save(scope.params, function() {
                        if (scope.$parent.template) {
                            scope.$parent.objects = scope.service.query(scope.params)
                            scope.$parent.template = undefined;
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
            /* Inline: Undef template
             *
             * Outline: Go back()
             */
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
