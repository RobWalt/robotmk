#!/bin/bash
# This script gets executed as a hook after the Docker entrypoint script has 
# created the OMD site.  
# Note: the agent installed here has no relation to the CMK version in this container. 
# As agent installers are only available after the first login into the site, 
# we do not have access to them. Instead, a recent deb gets installed. Will work
# for most needs...  

echo "Installing the Checkmk agent..."
DEB=$(realpath $(dirname $0))/cmk_agent.deb
dpkg -i $DEB
