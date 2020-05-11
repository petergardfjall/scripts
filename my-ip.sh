#!/bin/bash

#
# prints the IP address asspociated with the primary network interface
# of the host
#

default_wired_netif=$(route | grep default | grep -v wl | awk '{print $8}')
if [ -n "${default_wired_netif}" ]; then
    wireless_ip=$(ifconfig ${default_wired_netif} | grep 'inet ' | awk '{print $2}')
    echo "primary wired network interface IP: ${wireless_ip}"
fi

default_wireless_netif=$(route | grep default | grep wl | awk '{print $8}')
if [ -n "${default_wireless_netif}" ]; then
    wireless_ip=$(ifconfig ${default_wireless_netif} | grep 'inet ' | awk '{print $2}')
    echo "primary wireless network interface IP: ${wireless_ip}"
fi


public_ip=$(dig +short myip.opendns.com @resolver1.opendns.com)
echo "public IP: ${public_ip}"
