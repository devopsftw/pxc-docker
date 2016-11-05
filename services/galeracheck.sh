#!/bin/sh
exec /bin/galera-healthcheck -password="$CLUSTERCHECK_PASSWORD" -pidfile=/var/run/galera-healthcheck.pid -user clustercheck
