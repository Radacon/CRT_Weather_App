import time
import os
import csv

def read_cpu_temp():
    """Read the CPU temperature from sysfs and convert to °C."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            # The temperature is typically in millidegrees Celsius
            temp_millideg = f.read().strip()
            return float(temp_millideg) / 1000.0
    except Exception as e:
        print("Error reading CPU temperature:", e)
        return None

def main():
    csv_file = './cputemp.csv'
    # If the CSV file doesn't exist, create it and write the header.
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Temperature_C'])
    
    try:
        while True:
            temp = read_cpu_temp()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if temp is not None:
                output = f"{timestamp} - CPU Temperature: {temp:.2f}°C"
                print(output)
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, f"{temp:.2f}"])
            else:
                print(f"{timestamp} - CPU Temperature: Error")
            # Wait for 5 seconds before taking the next reading
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nTerminated by user.")

if __name__ == '__main__':
    main()
