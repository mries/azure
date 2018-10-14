#!/bin/bash

today=`date +%Y%m%d%H%M.%S` # or whatever pattern you desire
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
	function lic()
	{
	echo  Disk performance Test Tool.  Tests disk IO and bandwidth throughput.
        echo  Copyright \(C\) 2018  Markus Ries
	echo
	echo  This program is free software: you can redistribute it and/or modify
    	echo  it under the terms of the GNU General Public License as published by
    	echo  the Free Software Foundation, either version 3 of the License, or
    	echo  \(at your option\) any later version.
	echo
	echo    This program is distributed in the hope that it will be useful,
	echo    but WITHOUT ANY WARRANTY; without even the implied warranty of
	echo    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	echo    GNU General Public License for more details.
	echo
	echo    You should have received a copy of the GNU General Public License
	echo    along with this program.  If not, see <https://www.gnu.org/licenses/>.
	}

    function dirOut()
	{
	 perfOut=$(ls /tmp|grep performance)
	     if [[ -d "$perfOut"  ]]; then 
	     ioStat
	    elif [[ $perfOut == "" ]]; then
	          mkdir /tmp/performance
                  outDir="/tmp/performance"
	  	  ioStat
	      fi
}
    function fstabCopy()
    {

egrep -i "uuid|sd" /etc/fstab >> $outDir/fstab_$today


}

# Function for user to verify their selections

    function selections()
	{
	echo Your selections:
	echo Disk mount point: $disk
	echo Filename: $fileName
	echo Filesize: $outFile
	echo Blocksize: $blockSize
	echo Test duration \(sec\): $blockSize
	echo output number of jobs: $jobs
	echo date : $today
	echo y = Continue, n = Start over & read answer
	     if [[ $answer == "y" ]]; then 
	     echo Continuing. 
	     sleep .5
	     ioStat
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
iostat -dhmNtxz 1 $time >>$outDir/iostat_$today &
	rm -rf $diski/test
	Fio
}

#Fio function for the disk read write test. 
    function Fio()
    {

	fio -filename=$disk/test -iodepth=64 -ioengine=libaio -direct=1 -rw=randwrite -bs=$blockSize"k" -size=$outFile"G" -numjobs=$jobs -runtime=$time -group_reporting -name=test-randwrite  >>$outDir/fio-test_write_$today &

	fstabCopy
}
        clear	
	echo "####################################################"
	echo "# Performance testing with fio                     #"
	echo "#                                                  #"
	echo "# v:1.1                                            #"
	echo "# 2018/9/27                                        #"
	echo "# Press h, help or ? anytime for usage and L       #"
	echo "# for license.                                     #" 
	echo "# Fio install instructions.                        #"
	echo "####################################################"

#Selection input by user

	echo Disk mount point:&read disk 
       	   if [[ $disk = "?" || $disk == "help" || $disk == "h"  ]]; then 
	      usage 
	   fi
	#read  rg
#	echo Write filename: &read fileName
#	    if [[ $fileName == "?" || $fileName == "help" || $fileName == "h"  ]]; then
#	       usage
#	    
#	    fi

	echo Write blocksize \(bw\) in kb: &read blockSize
	    if [[ $blockSize == "?" || $blockSize == "help" || $blockSize == "h"  ]]; then
	       usage
	    
	    fi

	echo Write number of jobs \(parallel processes\): &read jobs
	    if [[ $jobs == "?" || $jobs == "help" || $jobs == "h"  ]]; then
	       usage
	    
	    fi

	echo Write test duration\(sec\)  &read time
	    if [[ $time == "?" || $time == "help" || $time == "h"  ]]; then
	       usage
	    
	    fi


	echo output filesize [GB]: &read outFile
	    if [[ $outFile == "?" || $outFile == "help" || $outfile == "h"  ]]; then
	       usage
	    else 
	    selections
    fi
dirOut
#ioStat
#Fio


