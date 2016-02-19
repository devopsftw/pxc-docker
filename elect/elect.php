#!/usr/bin/env php
<?php
// vim: sw=4:ts=4:noet:sta:

require('vendor/autoload.php');
require('App.php');

$app = new App;
$app->service = getenv('CLUSTER_NAME') ? getenv('CLUSTER_NAME') : 'cluster';
$app->run();
