
/* global angular */


(function () {
    'use strict';
    angular
            .module('GitApi', ['restangular', 'restangular-object-cache', 'ngStorage', 'ngRoute', 'ui.router', 'ngAnimate', 'blockUI'])
            .config(['RestangularProvider', '$routeProvider', 'blockUIConfig', '$interpolateProvider',
                function (RestangularProvider, $routeProvider, blockUIConfig, $interpolateProvider) {
                    
                    // handle the template tag because of jinja uses the {{ && }}
                    $interpolateProvider.startSymbol('[[').endSymbol(']]');

                    // set the default angular route handlers
                    RestangularProvider.setBaseUrl('/api/v1');
                    RestangularProvider.setDefaultHttpFields({cache: true});

                    // Change the default overlay message
                    blockUIConfig.message = 'Loading.....!';

                    // Change the default delay to 100ms before the blocking is visible
                    blockUIConfig.delay = 100;

                    // Disable automatically blocking of the user interface
                    blockUIConfig.autoBlock = false;

                    // Disable clearing block whenever an exception has occurred
                    blockUIConfig.resetOnException = false;

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
            .service('GitApiService', ['Restangular,', 'RestangularObjectCache', '$sessionStorage', 'blockUI', function (Restangular, RestangularObjectCache, $sessionStorage, blockUI) {
                    var self = this;
                    RestangularObjectCache.track('employees');

                    self.getGistList = function (username) {
                        blockUI.start("My custom message");
                        console.log(username + RestangularObjectCache);
                    };

                    return self;
                }])
            .factory('GitApiFactory', ['GitApiService', '$sessionStorage', function (GitApiService, $sessionStorage) {
                    function GitApi() {
                        var self = this;

                        self.getGistList = function (username) {

                            return GitApiService.getGistList(username);
                        };
                    }

                    return new GitApi();
                }])
            .controller('GitApiController', ['$scope', '$sessionStorage', 'GitApiFactory', '$log', function ($scope, $sessionStorage, GitApiFactory, $log) {
                    var self = this;

                    // define a list of left menu
                    $scope.leftMenuItems = ['ReadMe', 'Overview', 'List', 'Search', 'Export'];

                    // get the first element as default
                    $scope.selleftMenuItem = $scope.leftMenuItems[0];

                    // update select menu   
                    $scope.setLeftMenu = function (menu) {
                        $log.log("Menu: " + menu);
                        switch (menu) {
                            case 'List':
                                GitApiFactory.getGistList('sterlingmichel');
                                break;
                            default:
                                break;
                        }
                        $scope.selleftMenuItem = menu;
                    };

                }]);
}());

