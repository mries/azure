#! /bin/bash


today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire
perForm="/opt/performance"

#Usage function
    function usage()
    {
	echo ""
	echo  
	echo " No regular usage
	echo " Input must be in minutes
	exit
}




        echo "####################################################"
	echo "# VM Performance testing                           #"
	echo "#                                                  #"
	echo "# v:0.1                                            #"
	echo "# 2018/10/14                                       #"
	echo "# Required iotop, iostat which may require         #"
	echo "# installation.                                    #"
	echo "####################################################"



today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire

#top -b -n2 -Hc>>top.$today
#vmstat -a  -d -t -d 1 5 >>vmStatout.$today
#iotop -otbn5>>ioStat.$today
#ps axjf>ps.$today
#lsof +L -s  +w>lsof.$today



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
    top -b -n1 -Hc>>$vmperForm/top.$today
    vmstat -a  -d -t -d >>$perForm/vmStatout.$today
    iotop -otbn1>>$perForm/ioStat.$today
    ps axjf>$perForm/ps.$today
    lsof +L -s  +w>$perForm/lsof.$today
	t=$(( $t + 1 ))
clear
echo "Time left in seconds:" $(($s-$t))


    sleep 1    
done
echo Done.



