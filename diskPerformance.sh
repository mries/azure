#!/bin/bash

today=`date +%Y-%m-%d.%H:%M:%S` # or whatever pattern you desire
#Usage function
    function usage()
    {
	echo ""
	echo  
	echo Disk Performance tests using fio.
	echo required: fio installed
	echo redhat:
	echo yum makecache fastcache && yum install fio 
	echo centos: 
	echo yum makecache fastcache && yum install fio
	echo suse:
	echo https://software.opensuse.org/download.html?project=home%3Amalcolmlewis%3ASLE_12_General&package=fio
	echo ubuntu: 
	echo apt-get update && apt-get install fio
	exit
}
# Function for user to verify their selections

    function selections()
	{
	echo Your selections:
	echo Disk mount point: $disk
	echo Filename: $fileName
	echo output filesize: $outFile
	 echo y = Continue, n = Start over & read answer
	     if [[ $answer == "y" ]]; then 
	     echo Continuing. 
	     sleep .5
	    elif [[ $answer == "n" ]]; then
	          echo Starting over
	  	  sleep 1
		  eval "./performance.sh"
	     elif  [[  $answer != "y" || "$answer" != "y" || -z "$answer" ]]; then
	          echo You must select Y or N
	          exit 1
	      fi
}

   
# This is the iostat function for tracking io statistics

    function ioStat()
    {
	iostat -dhmNtxz 1 75 >>iostat.$today &
	rm -rf $disk/$fileName
echo "	rm -f $disk/$fileName"
}

#Fio function for the disk read write test. 
    function Fio()
    {

#fio -filename=$disk/$fileName -iodepth=64 -ioengine=libaio -direct=1 -rw=randwrite -bs=4k -size=$outFile"G" -numjobs=64 -runtime=60 -group_reporting -name=test-randwrite >>fio-test-write.$today &	

fio -filename=$disk/$fileName -iodepth=64 -ioengine=libaio -direct=1 -rw=randwrite -bs=4k -size=$outFile"G" -numjobs=64 -runtime=60 -group_reporting -name=test-randwrite >>fio-test-write.$today &	

# fio -filename=$disk/$fileName -iodepth=64 -ioengine=libaio -direct=1 -rw=randwrite -bs=4k -size=$outFile"G" -numjobs=64 -runtime=60 -group_reporting -name=test-randread >>fio-test-read.$today &	

fio -filename=$disk/$fileName -iodepth=64 -ioengine=libaio -direct=1 -rw=randwrite -bs=4k -size=$outFile"G" -numjobs=64 -runtime=60 -group_reporting -name=test-randread >>fio-test-read.$today &
}
        clear	
	echo "####################################################"
	echo "# Performance testing with fio                     #"
	echo "#                                                  #"
	echo "# v:0.1                                            #"
	echo "# 2018/7/5                                         #"
	echo "# Press h, help or ? anytime for usage and         #"
	echo "# Fio install instructions.                        #"
	echo "####################################################"

#Selection input by user

	echo Disk mount point:&read disk 
       	   if [[ $disk = "?" || $disk == "help" || $disk == "h"  ]]; then 
	      usage 
	   fi
	#read  rg
	echo Write filename: &read fileName
	    if [[ $fileName == "?" || $fileName == "help" || $fileName == "h"  ]]; then
	       usage
	    fi

	echo output filesize [GB]: &read outFile
	    if [[ $outFile == "?" || $outFile == "help" || $outfile == "h"  ]]; then
	       usage
	    fi

	
ioStat
Fio
