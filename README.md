# Azure 


####README#####

Ver: 1.1

Script for troubleshooting an Azure VM using Azure CLI in bash. This script can be used in either run in bash or cloudshell.

Using Linux rather than cloudshell it is quicker to run in a docker container on Ubuntu:


#Set up cli in a docker container in ubuntu
sudo -i
apt-get update && apt-get install docker.io -y
alias azcli1=“docker run -it microsoft/azure-cli:0.10.13”
azcli1

easiest way to execute:
 bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/os-swapdisk.sh )
