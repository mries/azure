# Azure 


####README#####

Ver: 1.1

2 Scripts for troubleshooting an Azure Linux  VMs in bash. This 
1. os-swapdisk.sh: Script for troubleshooting a VM that has failed boot without deleting VM
2. diskPerformance.sh: Script for checking disk performance of attahced disks.
 echo Disk Performance tests using fio.
        Required: fio installed
        Redhat: yum makecache fastcache && yum install fio
        Centos: yum makecache fastcache && yum install fio
        Suse:   https://software.opensuse.org/download.html?project=home%3Amalcolmlewis%3ASLE_12_General&package=fio
        Ubuntu: apt-get update && apt-get install fio



If Using Linux rather than cloudshell for os-swapdisk.sh  it is quicker to run in a docker container on Ubuntu:


#Set up cli in a docker container in ubuntu
sudo -i
apt-get update && apt-get install docker.io -y
alias azcli1=“docker run -it microsoft/azure-cli:0.10.13”
azcli1

easiest way to execute os-swapdisk.sh:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/os-swapdisk.sh )

Using diskPerformance.sh
run this on the affected VM:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/diskPerformance.sh )

cpuPerformance.sh
Run this on the affected VM:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/cpuPerformance.sh)

CPU threshold script that, when executed, sleeps until an event causes the top 10 processes in top to exceed the user's predefined threshold.
When the threashold is reached or exceeded it startes taking metrics for top, free, and ifconfig (network throughput)
- Script 2 selections, "execute" which then prompts you for a threshold in % cpu  utilization. The second option is "stop" which stops the script.

memPerformanceUsage.sh
Run this on the affected VM:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/memPerformanceUsage.sh)

mem uage script that, when executed, sleeps until a process using more memory than provided threshold is detedcted within the top 10 processes. 
When the threshold is reached or exceeded it begins collecting metrics from top, free, and iostat.  When the event disappears the script returns to sleep.
- Script 2 selections, "execute" which then prompts you for a threshold in % memory usage. The second option is "stop" which stops the script.


-- Note: If executing memPerformanceUsage.sh or cpuPerformance.sh script remotely the process name will be something similar to  bash /dev/fd/63.  If you want to find the parent process (for manually killing process) type  cat  /tmp/memPerformance.pid
