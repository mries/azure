PU=$(echo $t|awk '{split($1,a,"."); print a[1]}')
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
	echo  "#     and only wakes when memory utiliztion exceeds the  max threshold in x                          ##"
	echo  "#     When high memory  utiliazion occurs script wakes and starts collecting info from               ##"
	echo  "#     top, free, and ifconfig (throughput) which is written to performance.out for later analysis.   ##"
	echo  "#                                                                                                    ##"
	echo  "#######################################################################################################" 
	exit                              
}
function perf()
while true; do 

	t=$(top -b -n1|grep -A10 PID|grep -v %MEM|awk '{  sum += $9 } END { sum > $thresh;print sum}')
	MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')
	while [[ $MEM -gt $thresh ]] 
	do
		#echo $CPU
		#echo "test"
    		top -b -n1|grep -A10 PID|grep -v %CPU|awk '{  sum += $9 } END { sum > $thresh;system("ifconfig"); system("free -m"); system("top -b -n1")}'>>$today.$log
    		t=$(top -b -n1|grep -A10 PID|grep -v %MEM|awk '{  sum += $9 } END { sum > $thresh;print sum}')
		MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')

	done
done

function killscript()
{
	echo killing process
	kill -9 $(ps -ef|grep cpuPerformance|grep -v grep|awk '{print $2}'|head -n1)
}


function runscript()
{	
	echo Max processor threshold in "%" "(h|help|? provides usage)":&read thresh
       	   if [[ $thresh = "?" || $thresh == "help" || $thresh == "h"  ]]; then 
	      usage 
fi
perf &
}
#clear

echo " 'execute' to run cpu checker, 'stop' to stop run existing process:" & read answer


             if [[ "$answer" == "execute" ]]; then
		runscript
             elif [[ "$answer" == "stop" ]]; then
		  killscript
             elif  [[  "$answer" != "execute" || "$answer" != "stop" || -z "$answer" ]]; then
                  echo You must select execute or stop
             fi
#Selection input by user
