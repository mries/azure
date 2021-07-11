#! /bin/bash


today=$(date "+%m%d%H%s")"-"$(date +"%Z")"-"$(hostname) #adding date,timezone,hostname to output files.
perForm=/opt/performance

#Usage function
    function usage()
    {
	echo ""
	echo  
	echo " No regular usage"
	echo  "Input must be in minutes"
	exit
}




        echo "####################################################"
	echo "# VM Performance testing                           #"
	echo "#                                                  #"
	echo "# v:2.0                                            #"
	echo "# 2018/10/14                                       #"
	echo "# Required iotop, iostat which may require         #"
	echo "# installation.                                    #"
	echo "####################################################"





echo minutes to run:&read min
           s=$(($min*60))
 	   if [[ $disk = "?" || $disk == "help" || $disk == "h"  ]]; then 
	      usage 
       	   fi



if  [ ! -d "$perForm" ]; then
mkdir $perForm
fi

( sleep $s ) & # <-- The long running process.

t=0
#while jobs %1 &>/dev/null ; do
while [ $t -le $s ]; do
    vmstat -a  -d -t -d >>$perForm/vmStat.$today
    iotop -otbn1>>$perForm/iotop.$today
    iostat -dxmyt 1 1 >>$perForm/iostat.$today
    top -n1 -b -d 1 -o +%CPU |grep -A 15  average>>$perForm/top-cpu.$today 
    top -n1 -b -d 1 -o +%MEM |grep -A 15  average>>$perForm/top-mem.$today 
    ps axjf>$perForm/ps.$today
    lsof +L -s  +w>$perForm/lsof.$today
	t=$(( $t + 1 ))
clear
echo "Time left" $(($s-$t))"s"


    sleep 1    
done
echo Done.



