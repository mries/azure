#!/bin/bash
#PU=$(echo $t|awk '{split($1,a,"."); print a[1]}')
#today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire
today=$(date "+%m%d%H%s")"-"$(date +"%Z")"-"$(hostname) #adding date,timezone,hostname to output files.
log=performance.out
function usage()
    {
	clear
	echo 
	echo  "#######################################################################################################"
	echo  "#     Nothing special required for installation                                                      ##"
	echo  "#     This is a watch script that runs all of the time like a daemon                                 ##"
	echo  "#     and only wakes when cpu    utiliztion exceeds the  max threshold in x                          ##"
	echo  "#     When high cpu     utiliazion occurs script wakes and starts collecting info from               ##"
	echo  "#     top, free, and ifconfig (throughput) which is written to performance.out for later analysis.   ##"
	echo  "#                                                                                                    ##"
	echo  "#######################################################################################################" 
	exit                              
}
function perf()
while true; do 

	t=$(top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;print sum}')
	MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')
	while [[ $MEM -gt $thresh ]] 
	do
		top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;system("iostat -dxmt"); system("free -m"); system("top -b -n1")}'>>$today.$log
    		t=$(top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;print sum}')
		MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')
	done
done

function killscript()
{
	echo killing process
	#kill -9 $(ps -ef|grep memPerformance|grep -v grep|awk '{print $2}'|sort|head -n1)
	kill -9 $(cat /tmp/cpuPerformance.pid)
#	kill -9 $(ps -ef |grep  awk |grep -v grep |awk '{print $2}'|head -n1)
}


function runscript()
{	
	echo Max memory threshold in "%" "(h|help|? provides usage)":&read thresh
       	   if [[ $thresh = "?" || $thresh == "help" || $thresh == "h"  ]]; then 
	      usage 
fi
perf &
echo "$!" > /tmp/cpuPerformance.pid
}
#clear

echo " 'execute' to run CPU checker, 'stop' to stop run existing process:" & read answer


             if [[ "$answer" == "execute" ]]; then
		runscript
             elif [[ "$answer" == "stop" ]]; then
		  killscript
             elif  [[  "$answer" != "execute" || "$answer" != "stop" || -z "$answer" ]]; then
                  echo You must select execute or stop
             fi
#Selection input by user
