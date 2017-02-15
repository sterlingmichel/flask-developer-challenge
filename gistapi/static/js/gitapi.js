
/* global angular */


(function () {
    'use strict';
    angular
            .module('GitApi', ['restangular', 'restangular-object-cache', 'ngStorage', 'ngRoute', 'ui.router', 'ngAnimate', 'ngTouch', 'ui.grid'])
            .config(['RestangularProvider', '$routeProvider', '$interpolateProvider', '$logProvider',
                function (RestangularProvider, $routeProvider, $interpolateProvider, $logProvider) {

                    // enable the loging to display
                    $logProvider.debugEnabled(true);

                    // set the default angular route handlers
                    RestangularProvider.setBaseUrl('/api/v1');
                    RestangularProvider.setDefaultHttpFields({cache: false});

                    // Handle all the route at the client side
                    $routeProvider
                            .when('/', {
                                controller: 'GitApiController',
                                templateUrl: '/static/partials/index.html'
                            })
                            .otherwise({
                                redirectTo: '/'
                            });

                }])
            .factory('GitApiService', ['$sessionStorage', 'Restangular', '$q', function ($sessionStorage, Restangular, $q) {

                    var getGistList = function (username) {

                        var deferred = $q.defer();

                        Restangular
                                .one('gist')
                                .one(username)
                                .getList('list')
                                .then(function (data) {
                                    deferred.resolve(data);
                                });

                        return deferred.promise;
                    };

                    return {
                        getGistList: getGistList
                    };
                }])
            .service('GitApiFactory', ['$sessionStorage', 'GitApiService', function ($sessionStorage, GitApiService) {
                    function GitApi() {
                        this.getGistList = function (username) {
                            return GitApiService.getGistList(username);
                        };
                    }

                    return new GitApi();
                }])
            .run(['$rootScope', function ($rootScope) {
                    $rootScope.safeApply = function (fn) {
                        var phase = this.$root.$$phase;
                        if (phase === '$apply' || phase === '$digest') {
                            if (fn && (typeof (fn) === 'function')) {
                                fn();
                            }
                        } else {
                            this.$apply(fn);
                        }
                    };
                }])
            .controller('GitApiController', ['$scope', '$sessionStorage', 'GitApiFactory', '$log', 'uiGridConstants', function ($scope, $sessionStorage, GitApiFactory, $log, uiGridConstants) {
                    var self = this;

//                    // gridAPI
//                    $scope.gridApi = null;

                    // binding the search field
                    $scope.filterValue = "";

                    // grab & set for user
                    $scope.givenUser = "codeithuman";

                    // define a list of left menu
                    $scope.leftMenuItems = ['ReadMe', 'List'];

                    // get the first element as default
                    $scope.selleftMenuItem = $scope.leftMenuItems[0];

                    // Store the object results
                    $scope.gridOptions = {
                        paginationPageSizes: [25, 50, 75],
                        paginationPageSize: 25,
                        onRegisterApi: function (gridApi) {
                            $scope.gridApi = gridApi;
                            $scope.gridApi.grid.registerRowsProcessor($scope.singleFilter, 200);
                            $scope.safeApply();
                        },
                        columnDefs: [
                            {name: 'id'},
                            {name: 'name'},
                            {name: 'created_at'}
                        ],
                        data: []
                    };

                    $scope.filter = function () {
                        $scope.gridApi.grid.refresh();
                    };

                    // Adding a single filter
                    $scope.singleFilter = function (renderableRows) {
                        var matcher = new RegExp($scope.filterValue, 'i');

                        renderableRows.forEach(function (row) {
                            var match = false;
                            ['id', 'name', 'created_at'].forEach(function (field) {
                                if (row.entity[field].match(matcher)) {
                                    match = true;
                                }
                            });
                            if (!match) {
                                row.visible = false;
                            }
                        });
                        return renderableRows;
                    };

                    // update select menu   
                    $scope.setLeftMenu = function (menu) {
                        $log.log("Menu: " + menu);
                        switch (menu) {
                            case 'List':
                                GitApiFactory
                                        .getGistList($scope.givenUser)
                                        .then(function (gists) {
                                            angular.forEach(gists, function (gist, i) {
                                                $scope.gridOptions.data.push({
                                                    id: gist.id,
                                                    name: gist.description,
                                                    created_at: gist.created_at
                                                });
                                            });
                                        });
                                break;
                            default:
                                break;
                        }
                        $scope.selleftMenuItem = menu;
                    };

                }]);
}());

