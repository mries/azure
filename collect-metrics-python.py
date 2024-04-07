import time
import subprocess
import psutil

# Predetermined CPU usage threshold in percentage
cpu_threshold = 50

# Interval between checks in seconds
check_interval = 5

# Function to collect required information
def collect_info():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Collect TCP throughput
    tcp_info = subprocess.check_output(["tcpstat", "-i", "eth0", "-t", "5", "1"]).decode()

    # Collect top process information
    top_info = subprocess.check_output(["top", "-b", "-n", "1"]).decode()

    # Collect iostat information
    iostat_info = subprocess.check_output(["iostat", "-c", "1", "1"]).decode()

    # Collect ps information
    ps_info = subprocess.check_output(["ps", "aux"]).decode()

    # Save collected information to a log file
    log_file = "monitoring_log.txt"
    with open(log_file, "a") as f:
        f.write("Timestamp: {}\n".format(timestamp))
        f.write("TCP Throughput:\n{}\n".format(tcp_info))
        f.write("Top Process Information:\n{}\n".format(top_info))
        f.write("iostat Information:\n{}\n".format(iostat_info))
        f.write("ps Information:\n{}\n".format(ps_info))
        f.write("---------------------------------------\n")

while True:
    # Get the CPU usage of the top process
    top_cpu_usage = float(subprocess.check_output(["top", "-b", "-n", "1"]).decode().split("\n")[2].split()[8])

    if top_cpu_usage >= cpu_threshold:
        print("Top process CPU usage is above threshold. Collecting information...")
        collect_info()

    time.sleep(check_interval)
