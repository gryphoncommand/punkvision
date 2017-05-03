#!/bin/sh
# updates networking information

cp templates/template_dhcpcd.conf /etc/dhcpcd.conf

sed -i -e "s/@OLD@/$(sed 's:/:\\/:g' /etc/dhcpcd.conf.OLD)/g" /etc/dhcpcd.conf
sed -i -e "s/@TEAM@/$(sed 's:/:\\/:g' ./TE.AM)/g" /etc/dhcpcd.conf
sed -i -e "s/@RPI@/$(sed 's:/:\\/:g' ./R.PI)/g" /etc/dhcpcd.conf

exit 0
