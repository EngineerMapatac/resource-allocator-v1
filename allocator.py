import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math

class ResourceAllocator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.capacity_per_cycle = 0  
        self.start_date = datetime.now()
        self.nodes = []
        self.history = {"dates": [], "total_load": []}

    def load_configuration(self):
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.capacity_per_cycle = data.get("system_capacity_per_cycle", 0)
                
                # Parse Start Date
                s_date = data.get("start_date", datetime.now().strftime("%Y-%m-%d"))
                self.start_date = datetime.strptime(s_date, "%Y-%m-%d")

                self.nodes = data.get("active_nodes", [])
                
                # Sort by Interest Rate (Avalanche)
                self.nodes.sort(key=lambda x: x['overhead_factor'], reverse=True)
                
            print(f"[INIT] System Online. Capacity: {self.capacity_per_cycle} units/cycle")
        except FileNotFoundError:
            print(f"[ERROR] Config file '{self.config_file}' missing.")

    def run_simulation(self):
        cycle = 0
        current_date = self.start_date
        
        # Initial State
        current_total_load = sum(n['current_load'] for n in self.nodes)
        self.history["dates"].append(current_date)
        self.history["total_load"].append(current_total_load)

        # SIMULATION LOOP (1 Cycle = Approx 15 Days)
        while any(n['current_load'] > 0 for n in self.nodes):
            cycle += 1
            # Advance time by ~15 days (alternating 15th and 30th logic simplified)
            current_date += timedelta(days=15) 
            
            remaining_capacity = self.capacity_per_cycle
            
            for node in self.nodes:
                if node['current_load'] <= 0:
                    continue

                # 1. DETECT IF PAYMENT IS DUE THIS CYCLE
                # If mode is SEMI_MONTHLY, pay every cycle.
                # If mode is MONTHLY, pay only on even cycles (approx every 30 days).
                is_payment_due = True
                if node.get('cycle_mode') == "MONTHLY" and (cycle % 2 != 0):
                    is_payment_due = False

                if is_payment_due:
                    # ADD INTEREST (Overhead)
                    # Annual Rate / 24 (since there are 24 cycles in a year)
                    interest = (node['current_load'] * node['overhead_factor']) / 24
                    node['current_load'] += interest
                    
                    # PAY MINIMUM
                    min_pay = node['min_throughput']
                    # If semi-monthly, split monthly min payment in half? 
                    # Usually, loans specify monthly min. Let's assume input is PER PAYMENT.
                    payment = min(node['current_load'], min_pay)
                    node['current_load'] -= payment
                    remaining_capacity -= payment

            # 2. AVALANCHE (Extra money goes to highest interest loan)
            for node in self.nodes:
                if remaining_capacity <= 0:
                    break
                if node['current_load'] > 0:
                    # Only pay extra if payment is allowed this cycle
                    if node.get('cycle_mode') == "SEMI_MONTHLY" or (cycle % 2 == 0):
                        payment = min(node['current_load'], remaining_capacity)
                        node['current_load'] -= payment
                        remaining_capacity -= payment

            # Record History
            total_load = sum(n['current_load'] for n in self.nodes)
            self.history["dates"].append(current_date)
            self.history["total_load"].append(total_load)

            # Safety Break (20 Years)
            if cycle > 480: 
                print("[CRITICAL] Infinite loop. Debt not decreasing.")
                return

        self._generate_report(current_date)
        self._render_graph()

    def _generate_report(self, finish_date):
        print("\n--- MATURITY ANALYSIS REPORT ---")
        print(f"Projected Zero Date: {finish_date.strftime('%Y-%m-%d')}")
        
        # CHECK AGAINST SCHEDULED DEPRECATION (Maturity Dates)
        print("\n[DEPENDENCY AUDIT]")
        for node in self.nodes:
            # We assume the node is finished now.
            maturity_str = node.get('scheduled_deprecation')
            if maturity_str:
                maturity_date = datetime.strptime(maturity_str, "%Y-%m-%d")
                days_diff = (maturity_date - finish_date).days
                
                if days_diff >= 0:
                    print(f"[PASS] {node['id']} cleared before maturity. (Buffer: {days_diff} days)")
                else:
                    print(f"[FAIL] {node['id']} EXCEEDED scheduled maturity by {abs(days_diff)} days!")
            else:
                print(f"[INFO] {node['id']} has no fixed maturity date.")

    def _render_graph(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.history["dates"], self.history["total_load"], color='#2c3e50', label='Total Load')
        plt.title('Resource Deprecation (Bi-Monthly Cycles)')
        plt.xlabel('Timeline')
        plt.ylabel('Remaining Load')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.fill_between(self.history["dates"], self.history["total_load"], color='#e74c3c', alpha=0.1)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = ResourceAllocator('config/dependencies.json')
    app.load_configuration()
    app.run_simulation()
