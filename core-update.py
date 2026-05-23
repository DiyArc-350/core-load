import time
import sys
import psutil

def format_bytes(bytes_num):
    """Converts bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0

class CoreLoadAnalyzer:
    def __init__(self, interval=2, pps_idle_threshold=10):
        self.interval = interval
        self.pps_idle_threshold = pps_idle_threshold
        
        self.cpu_log = []
        self.mem_log = []
        self.start_time = None
        
        # Network tracking placeholders
        self.net_start = None
        self.net_prev = None
        
        # State tracking flags
        self.is_idle = False

    def start_monitoring(self):
        print("=" * 70)
        print(" 5G CORE LOAD REDUCTION ANALYZER INITIALIZED ")
        print(f" Monitoring traffic. Auto-pausing logs if total PPS drops below {self.pps_idle_threshold}.")
        print(" Press Ctrl+C to stop the traffic test and generate the summary.")
        print("=" * 70)
        
        self.start_time = time.time()
        self.net_start = psutil.net_io_counters()
        self.net_prev = self.net_start
        
        try:
            while True:
                # 1. Gather Metrics
                cpu_p = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                net_now = psutil.net_io_counters()
                
                # Calculate Delta metrics for the specific interval window
                bytes_sent_delta = net_now.bytes_sent - self.net_prev.bytes_sent
                bytes_recv_delta = net_now.bytes_recv - self.net_prev.bytes_recv
                pkts_sent_delta = net_now.packets_sent - self.net_prev.packets_sent
                pkts_recv_delta = net_now.packets_recv - self.net_prev.packets_recv
                
                # Convert deltas to rates per second
                pps_tx = pkts_sent_delta / self.interval
                pps_rx = pkts_recv_delta / self.interval
                bps_tx = bytes_sent_delta / self.interval
                bps_rx = bytes_recv_delta / self.interval
                
                total_current_pps = pps_tx + pps_rx
                
                # Update previous step network placeholder
                self.net_prev = net_now
                
                # 2. Check Traffic Threshold State
                if total_current_pps < self.pps_idle_threshold:
                    if not self.is_idle:
                        timestamp = time.strftime('%H:%M:%S')
                        print(f"[{timestamp}] Core traffic dropped below threshold ({int(total_current_pps)} PPS). Logging paused (Idling)...")
                        self.is_idle = True
                    
                    # Skip recording metrics and skip printing the ticker line during idle
                    time.sleep(self.interval)
                    continue
                else:
                    if self.is_idle:
                        timestamp = time.strftime('%H:%M:%S')
                        print(f"[{timestamp}] Traffic detected ({int(total_current_pps)} PPS). Resuming active core load logging.")
                        self.is_idle = False

                # 3. Record metrics for historical calculation (Only while active)
                self.cpu_log.append(cpu_p)
                self.mem_log.append(mem.percent)
                
                # 4. Output Live Ticker
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] CPU: {cpu_p:5.1f}% | RAM: {mem.percent:5.1f}% | "
                      f"Tx Rate: {format_bytes(bps_tx)}/s ({int(pps_tx)} PPS) | "
                      f"Rx Rate: {format_bytes(bps_rx)}/s ({int(pps_rx)} PPS)")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.generate_summary_report()

    def generate_summary_report(self):
        end_time = time.time()
        duration = end_time - self.start_time
        net_end = psutil.net_io_counters()
        
        # Calculate totals over the entire window
        total_tx_bytes = net_end.bytes_sent - self.net_start.bytes_sent
        total_rx_bytes = net_end.bytes_recv - self.net_start.bytes_recv
        total_tx_pkts = net_end.packets_sent - self.net_start.packets_sent
        total_rx_pkts = net_end.packets_recv - self.net_start.packets_recv
        
        # Security check if terminated instantly or spent entirely in idle
        if not self.cpu_log:
            print("\n" + "=" * 70)
            print(" 5G CORE LOAD ANALYSIS REPORT ")
            print("=" * 70)
            print(f"Total Session Duration : {duration:.2f} seconds")
            print("No active traffic data was logged during this session (Core was idle).")
            print("=" * 70 + "\n")
            return
            
        avg_cpu = sum(self.cpu_log) / len(self.cpu_log)
        max_cpu = max(self.cpu_log)
        avg_mem = sum(self.mem_log) / len(self.mem_log)
        max_mem = max(self.mem_log)
        
        avg_pps_tx = total_tx_pkts / duration if duration > 0 else 0
        avg_pps_rx = total_rx_pkts / duration if duration > 0 else 0
        avg_bps_tx = total_tx_bytes / duration if duration > 0 else 0
        avg_bps_rx = total_rx_bytes / duration if duration > 0 else 0

        # --- Report Layout ---
        print("\n" + "=" * 70)
        print("                   5G CORE LOAD ANALYSIS REPORT                    ")
        print("=" * 70)
        print(f"Total Session Duration : {duration:.2f} seconds")
        print(f"Active Monitored Points : {len(self.cpu_log) * self.interval} seconds of active traffic")
        print("-" * 70)
        print(f"{'Core Parameter Group':<24} | {'Active Average':<20} | {'Peak Performance':<20}")
        print("-" * 70)
        print(f"{'[Compute] CPU Capacity':<24} | {avg_cpu:.2f}%" + f" {' ' * 13} | {max_cpu:.2f}%")
        print(f"{'[Compute] Memory Load':<24} | {avg_mem:.2f}%" + f" {' ' * 13} | {max_mem:.2f}%")
        print(f"{'[UPF/SBI] Outbound (Tx)':<24} | {format_bytes(avg_bps_tx)}/s" + f" {' ' * 8} | {int(avg_pps_tx)} PPS (Avg)")
        print(f"{'[UPF/SBI] Inbound (Rx)':<24} | {format_bytes(avg_bps_rx)}/s" + f" {' ' * 8} | {int(avg_pps_rx)} PPS (Avg)")
        print("-" * 70)
        print(f"Total Network Footprint  | Tx Volume: {format_bytes(total_tx_bytes)} | Rx Volume: {format_bytes(total_rx_bytes)}")
        print("=" * 70)
        
        # --- Analytics Insight for Optimization Verification ---
        print("\nLOAD REDUCTION INSIGHTS FOR ENGINEER REVIEW:")
        print(f" - Packet Processing Overhead: Total packets handled = {total_tx_pkts + total_rx_pkts} frames.")
        print(f" - Control vs User Plane Balance: Your peak compute load was {max_cpu:.1f}%.")
        print(" - Performance Note: Summary statistics exclude data collected while the core was idling.")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    # Feel free to change the threshold value below.
    # pps_idle_threshold=10 means if combined Rx + Tx Packets Per Second is under 10, it pauses.
    analyzer = CoreLoadAnalyzer(interval=2, pps_idle_threshold=10)
    analyzer.start_monitoring()