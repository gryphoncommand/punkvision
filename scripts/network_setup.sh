#!/bin/sh
# sets up the networking

mv /etc/dhcpcd.conf /etc/dhcpcd.conf.OLD

./scripts/network_update.sh

exit 0
