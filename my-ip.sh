#!/bin/bash

#
# prints the IP address asspociated with the primary network interface
# of the host
#

default_network_interface=$(route | grep default | awk '{print $8}')
ip=$(ifconfig ${default_network_interface} | grep 'inet addr' | awk '{print $2}' | awk -F : '{print $2}')
echo "primary network interface IP: ${ip}"

public_ip=$(dig +short myip.opendns.com @resolver1.opendns.com)
echo "public IP: ${public_ip}"
