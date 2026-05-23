import socket
import struct
import time
import psutil

# Configuration settings
TARGET_IP = "10.40.1.220"
INTERVAL = 2  # Monitoring evaluation step in seconds
HOLD_TIME = 6  # How long to keep logging active after the last target hit

# Standard REST ports for 5G Core SBI Network Functions (AMF, SMF, UDM, etc.)
# Filtering for these ensures we focus on endpoint API traffic
TARGET_PORTS = [8000, 8001, 8002, 8080] 

class TargetedEndpointMonitor:
    def __init__(self, interface="any"):
        self.interface = interface
        self.cpu_log = []
        self.mem_log = []
        self.start_time = time.time()
        
        # Initialize a raw socket to capture IP traffic
        # ETH_P_IP (0x0800) filters for IPv4 packets natively at the kernel level
        self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
        
        if self.interface != "any":
            self.sock.bind((self.interface, 0))
        self.sock.setblocking(False)

    def run(self):
        print("=" * 70)
        print(" TARGETED 5G CORE ENDPOINT MONITOR INITIALIZED ")
        print(f" Target Host Destination : {TARGET_IP}")
        print(f" Sniffing Interface       : {self.interface}")
        print(" Press Ctrl+C to stop the test and print the final report.")
        print("=" * 70)

        is_idle = True
        last_hit_time = 0

        try:
            while True:
                traffic_detected = False
                
                # Fast-drain the socket buffer to check for recent target activity
                while True:
                    try:
                        packet, _ = self.sock.recvfrom(65535)
                        
                        # Parse the IPv4 Header (Starts after 14-byte Ethernet header)
                        ip_header = packet[14:34]
                        if len(ip_header) < 20:
                            continue
                            
                        iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                        src_ip = socket.inet_ntoa(iph[8])
                        dst_ip = socket.inet_ntoa(iph[9])
                        protocol = iph[6]
                        
                        # Check if our target IP matches either side of the pipe
                        if src_ip == TARGET_IP or dst_ip == TARGET_IP:
                            # Verify if it's TCP or UDP to extract ports
                            if protocol in [6, 17]:  # 6 = TCP, 17 = UDP
                                ip_header_len = (iph[0] & 0xF) * 4
                                transport_header = packet[14 + ip_header_len : 14 + ip_header_len + 4]
                                
                                if len(transport_header) >= 4:
                                    src_port, dst_port = struct.unpack('!HH', transport_header)
                                    
                                    # If it matches our targeted 5G interface ports, trigger logging
                                    if src_port in TARGET_PORTS or dst_port in TARGET_PORTS:
                                        traffic_detected = True
                                        last_hit_time = time.time()
                                        break
                                        
                    except BlockingIOError:
                        # Socket buffer is currently empty
                        break

                # State Machine Engine
                current_time = time.time()
                if (current_time - last_hit_time) < HOLD_TIME and last_hit_time > 0:
                    if is_idle:
                        print(f"[{time.strftime('%H:%M:%S')}] Active REST traffic detected with {TARGET_IP}. Tracking load...")
                        is_idle = False
                    
                    # Capture Core Load Metrics
                    cpu_p = psutil.cpu_percent(interval=None)
                    mem = psutil.virtual_memory().percent
                    self.cpu_log.append(cpu_p)
                    self.mem_log.append(mem)
                    
                    print(f"  -> TARGET STRESS | CPU: {cpu_p:5.1f}% | RAM: {mem:5.1f}%")
                else:
                    if not is_idle:
                        print(f"[{time.strftime('%H:%M:%S')}] Traffic to {TARGET_IP} quieted down. Pausing load logging.")
                        is_idle = True

                time.sleep(INTERVAL)

        except KeyboardInterrupt:
            self.print_summary_report()

    def print_summary_report(self):
        duration = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("               5G TARGETED TARGET LOAD REPORT                      ")
        print("=" * 70)
        print(f"Total Session Duration : {duration:.2f} seconds")
        
        if not self.cpu_log:
            print(f"No traffic events matched destination {TARGET_IP} on ports {TARGET_PORTS}.")
            print("Zero active load points recorded.")
            print("=" * 70 + "\n")
            return
            
        print(f"Active Monitoring Window : {len(self.cpu_log) * INTERVAL} seconds under workload")
        print("-" * 70)
        print(f"Average CPU usage during communication window : {sum(self.cpu_log)/len(self.cpu_log):.2f}%")
        print(f"Peak CPU spike during communication window    : {max(self.cpu_log):.2f}%")
        print(f"Average Memory footprint under endpoint load  : {sum(self.mem_log)/len(self.mem_log):.2f}%")
        print("=" * 70)
        print("Optimization Tip: Compare these stress peaks across your software versions.")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    # If you know the exact virtual interface name (e.g., 'eth0', 'br-int'), substitute it here.
    # 'any' captures across all active interfaces on the machine.
    monitor = TargetedEndpointMonitor(interface="any")
    monitor.run()