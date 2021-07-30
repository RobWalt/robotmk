#!/bin/bash

SECRETFILE=/opt/omd/sites/cmk/var/check_mk/web/automation/automation.secret

if [ ! -r $SECRETFILE ]; then 
    echo "ERROR: In order to create a dummy host with this script, you must first log into the cmk site for the very first time. "
    exit 1
fi

SECRET=$(cat $SECRETFILE)
HOST=localhost:5000
SITE=cmk

echo "Creating a dummy host via webapi.py ... "
curl -k "http://$HOST/$SITE/check_mk/webapi.py?action=add_host&_username=automation&_secret=$SECRET&request_format=python&output_format=python" -d "request={'hostname': 'win10simdows', 'folder': '', 'attributes': {'ipaddress': '192.168.116.8'}, 'create_folders': '1'}"
cmk -IIv win10simdows
cmk -R