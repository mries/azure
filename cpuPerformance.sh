#!/bin/bash
today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire
log=performance.out
function usage()
    {
	clear
	echo 
	echo  "#######################################################################################################"
	echo  "#     Nothing special required for installation                                                      ##"
	echo  "#     This is a watch script that runs all of the time like a daemon                                 ##"
	echo  "#     and only wakes when cpu utiliztion exceeds the  Max processor threshold in x                   ##"
	echo  "#     When the high processor utiliazion occurs script wakes and starts collecting info from         ##"
	echo  "#     top, free, and ifconfig (throughput) which is written to performance.out for later analysis.   ##"
	echo  "#                                                                                                    ##"
	echo  "#######################################################################################################" 
	exit                              
}
function perf()
while true; do 

	t=$(top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;print sum}')
	CPU=$(echo $t|awk '{split($1,a,"."); print a[1]}')
	while [[ $CPU -gt $thresh ]] 
	do
		#echo $CPU
		#echo "test"
    		top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;system("ifconfig"); system("free -m"); system("top -b -n1")}'>>$today.$log
    		t=$(top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;print sum}')
		CPU=$(echo $t|awk '{split($1,a,"."); print a[1]}')

	done
done


#clear

#Selection input by user

	echo Max processor threshold in "%" "(h|help|? provides usage)":&read thresh
       	   if [[ $thresh = "?" || $thresh == "help" || $thresh == "h"  ]]; then 
	      usage 
fi
perf
