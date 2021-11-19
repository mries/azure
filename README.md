# Azure 


####README#####



5 Scripts for troubleshooting an Azure Linux  VMs in bash. This 

1. os-swapdisk.sh ver. 1.1:
   Script for troubleshooting a VM that has failed boot without deleting VM

2. diskPerformance.sh ver. 1.0: 
   Script for checking disk performance of attahced disks.
   echo Disk Performance tests using fio.
        Required: fio installed
        Redhat: yum makecache fastcache && yum install fio
        Centos: yum makecache fastcache && yum install fio
        Suse:   https://software.opensuse.org/download.html?project=home%3Amalcolmlewis%3ASLE_12_General&package=fio
        Ubuntu: apt-get update && apt-get install fio

3. cpuPerformanceCheck.sh ver, 2.1:
   CPU threshold script that, when executed, sleeps until an event causes the top 10 processes in top to exceed the user's predefined threshold.
   When the threashold is reached or exceeded it startes taking metrics for top, free, and ifconfig (network throughput)
   - Script has  2 selections, "execute" which then prompts you for a threshold in % cpu  utilization. The second option is "stop" which stops the script.

4. memPerformanceUsage.sh ver. 2.1:
   mem uage script that, when executed, sleeps until a process using more memory than provided threshold is detedcted within the top 10 processes.
   - Script has  2 selections, "execute" which then prompts you for a threshold in % memory usage. The second option is "stop" which stops the script.

5. vmPerformance.sh ver. 1.0:
   Simple script, that when executed simply collects iotop, iostat, top, ps and lsof performance data and outputs log to /opt/performance.
   Because it is loging to /opt script will need to be run as root. The script will hold a session for the diration of the test.

If Using Linux rather than cloudshell for os-swapdisk.sh  It is quicker to run in a docker container on Ubuntu:



How to set up cli in a docker container in ubuntu
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
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/cpuPerformanceCheck.sh)

memPerformanceUsage.sh
Run this on the affected VM:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/memPerformanceUsage.sh)

vmPerformance.sh
Run this on the affected VM:
bash <(curl -s  https://raw.githubusercontent.com/mries/azure/master/vmPerformance.sh)

-- Note: If executing memPerformanceUsage.sh or cpuPerformanceCheck.sh script remotely the process name will be something similar to  bash /dev/fd/63.  If you want to find the parent process (for manually killing process) type  cat  /tmp/memPerformance.pid or  cat  /tmp/cpuPerformanceCheck.sh
