#!/bin/sh

if [ -z "$XTRABACKUP_PASSWORD" ]; then
	echo "XTRABACKUP_PASSWORD not set"
	exit 1
fi

PASS=$(echo "$XTRABACKUP_PASSWORD" | sha256sum | awk '{print $1;}')
echo $PASS > /etc/container_environment/CLUSTERCHECK_PASSWORD

