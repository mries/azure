#!/usr/bin/env python3
'''
/* 
 * Copyright (C) 2025 Markus Ries
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
'''

from __future__ import print_function
import os
import time
import subprocess
import sys
from datetime import datetime

# Global variables
log_file = None
threshold = None
pid_file = "/tmp/cpuPerformance.pid"

def usage():
    """
    Display usage instructions.
    """
    print("\n" + "#" * 100)
    print("#                                                                                                    ##")
    print("#     This is a watch script that runs all of the time like as a daemon                              ##")
    print("#     and only wakes when CPU utilization exceeds the max threshold.                                 ##")
    print("#     When high CPU utilization occurs, the script wakes and starts collecting info                  ##")
    print("#     from top, free, and iostat, which is written to                                                ##")
    print("#     ./[mmddhhmm]-[timezone]-[systemname].performance.out for later analysis.                       ##")
    print("#                                                                                                    ##")
    print("#     To run simple run the script, you will be then asked to execute or stop.                       ##")
    print("#     Stop kills the process and execute starts the script.                                          ##")
    print("#                                                                                                    ##")
    print("#    When executed  a cpu % threshold needs to be entered.  That is the high water mark              ##")
    print("#   which is when the script will wake and start collecting performance data.  When the event        ##")
    print("#    ends the script will go back to  sleep  until the event occurs again.                           ##")
    print("#                                                                                                    ##")
    print("#    To stop the script simply run the script again and enter stop instead of  execute.              ##")
    print("#     Sysstat is required for this script:                                                           ##")
    print("#     Redhat/Centos/Oracle:            yum install sysstat                                           ##")
    print("#     Ubuntu/Debian:                   apt install sysstat                                           ##")  
    print("#     Suse:                            zypper install sysstat                                        ##")
    print("#" + "#" * 100)
    sys.exit()

def get_cpu_utilization():
    """
    Get total CPU utilization by summing up the %CPU column from `top`.
    """
    try:
        process = subprocess.Popen(
            ["top", "-b", "-n1"], stdout=subprocess.PIPE, universal_newlines=True
        )
        output, _ = process.communicate()
        if sys.version_info[0] == 2:
            output = output.decode("utf-8")
        lines = output.splitlines()
        cpu_usage = 0
        for line in lines:
            if "PID" in line:  # Start reading after the header
                break
        for line in lines[lines.index(line) + 1:]:
            cols = line.split()
            if len(cols) > 8:  # Ensure %CPU column exists
                cpu_usage += float(cols[8])
        return cpu_usage
    except Exception as e:
        print("Error calculating CPU usage: {}".format(e))
        return 0

def perf():
    """
    Monitor performance and log data when CPU utilization exceeds the threshold.
    """
    global log_file
    while True:
        cpu_usage = get_cpu_utilization()
        if cpu_usage > threshold:
            print("High CPU usage detected: {}%".format(cpu_usage))
            with open(log_file, "a") as f:
                f.write("CPU Utilization exceeded threshold.\n")
                subprocess.Popen(["iostat", "-dxmt"], stdout=f, universal_newlines=True).communicate()
                subprocess.Popen(["free", "-m"], stdout=f, universal_newlines=True).communicate()
                subprocess.Popen(["top", "-b", "-n1"], stdout=f, universal_newlines=True).communicate()
        time.sleep(5)  # Check every 5 seconds

def killscript():
    """
    Kill the running script using the stored PID.
    """
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 9)
        print("Process terminated.")
        os.remove(pid_file)
    except Exception as e:
        print("Error stopping the process: {}".format(e))

def runscript():
    """
    Start the performance monitoring script.
    """
    global threshold, log_file
    try:
        # Handle input compatibility
        if sys.version_info[0] == 2:
            threshold = float(raw_input("Enter max CPU threshold in %: "))
        else:
            threshold = float(input("Enter max CPU threshold in %: "))
    except ValueError:
        print("Invalid input. Please provide a numeric value.")
        return

    # Generate the log file name with timestamp, timezone, and hostname
    timestamp = datetime.now().strftime("%m%d%H%S")
    timezone = time.tzname[0]
    hostname = os.uname()[1]
    log_file = "{}-{}-{}.performance.out".format(timestamp, timezone, hostname)

    # Run the performance monitoring in a background process
    pid = os.fork()
    if pid == 0:  # Child process
        perf()
    else:  # Parent process
        print("Script running with PID: {}".format(pid))
        with open(pid_file, "w") as f:
            f.write(str(pid))

def main():
    """
    Main function to handle user input and control the script.
    """
    print("'execute' to run CPU checker, 'stop' to stop existing process:")
    if sys.version_info[0] == 2:
        action = raw_input().strip().lower()
    else:
        action = input().strip().lower()

    if action == "execute":
        runscript()
    elif action == "stop":
        killscript()
    else:
        print("You must select either 'execute' or 'stop'.")
        usage()

if __name__ == "__main__":
    main()
