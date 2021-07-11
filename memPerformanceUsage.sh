#!/bin/bash
PU=$(echo $t|awk '{split($1,a,"."); print a[1]}')
#today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire
today=$(date "+%m%d%H%s")"-"$(date +"%Z")"-"$(hostname) #adding date,timezone,hostname to output files.
log=performance.out

##################################################################################
#    This program is free software: you can redistribute it and/or modify        #
#    it under the terms of the GNU General Public License as published by        #
#    the Free Software Foundation, either version 3 of the License, or           #
#    (at your option) any later version.                                         #
#                                                                                #
#    This program is distributed in the hope that it will be useful,             #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
#    GNU General Public License for more details.                                #
#                                                                                #
#    You should have received a copy of the GNU General Public License           #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.      #
##################################################################################

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
	echo  "#     options for memPerformanceUsabge:                                                              ##"
	echo  "#     execute -> executes script                                                                     ##"
	echo  "#       -- [threshold in $ memory usage]                                                             ##"
	echo  "#     stop    -> stops script                                                                        ##"
	echo  "#                                                                                                    ##"
	echo  "#     After executing you will be prompted to either "execute" or "stop" script.                     ##"
	echo  "#######################################################################################################" 
	exit                              
}
function perf()
while true; do 

	t=$(top -b -n1|grep -A10 PID|grep -v %MEM|awk '{  sum += $10 } END { sum > $thresh;print sum}')
	MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')
	while [[ $MEM -gt $thresh ]] 
	do
    		top -b -n1|grep -A10 PID|grep -v %MEM|awk '{  sum += $10 } END { sum > $thresh;system("iostat -dxmt"); system("free -m"); system("top -b -n1")}'>>$today.$log
    		t=$(top -b -n1|grep -A10 PID|grep -v %MEM|awk '{  sum += $10 } END { sum > $thresh;print sum}')
		MEM=$(echo $t|awk '{split($1,a,"."); print a[1]}')

	done
done

function killscript()
{
	echo killing process
	kill -9 $(cat /tmp/memPerformance.pid)
}


function runscript()
{	
	echo Max memory threshold in "%" "(h|help|? provides usage)":&read thresh
       	   if [[ $thresh = "?" || $thresh == "help" || $thresh == "h"  ]]; then 
	      usage 
fi
perf &
echo "$!" > /tmp/memPerformance.pid
}

echo " 'execute' to run memory checker, 'stop' to stop run existing process:" & read answer


             if [[ "$answer" == "execute" ]]; then
		runscript
             elif [[ "$answer" == "stop" ]]; then
		  killscript
             elif  [[  "$answer" != "execute" || "$answer" != "stop" || -z "$answer" ]]; then
                  echo You must select execute or stop
             fi
