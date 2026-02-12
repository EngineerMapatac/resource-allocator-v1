import json
import math
from datetime import datetime, timedelta

class ResourceAllocator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.system_capacity = 0  # Your Monthly Payment Budget
        self.nodes = []           # Your Loans
        self.report_log = []

    def load_configuration(self):
        """Loads the external dependencies (loans) from the JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.system_capacity = data.get("monthly_system_capacity", 0)
                self.nodes = data.get("active_nodes", [])
                
                # Sort nodes by 'overhead_factor' (Interest Rate) descending
                # This is the "Avalanche Method" - mathematically fastest way to clear debt
                self.nodes.sort(key=lambda x: x['overhead_factor'], reverse=True)
                
            print(f"[INIT] Configuration loaded. System Capacity: {self.system_capacity} units/mo")
        except FileNotFoundError:
            print(f"[ERROR] Configuration file '{self.config_file}' not found.")

    def run_simulation(self):
        """Simulates the resource allocation cycle month by month."""
        month = 0
        total_overhead_cost = 0 # Total Interest Paid
        
        # Deep copy of nodes to not mess up original data during simulation
        active_nodes = [n.copy() for n in self.nodes]

        while any(n['current_load'] > 0 for n in active_nodes):
            month += 1
            monthly_overhead = 0
            remaining_capacity = self.system_capacity

            # 1. Apply Overhead (Interest) & Deduct Minimum Throughput (Min Payments)
            for node in active_nodes:
                if node['current_load'] > 0:
                    # Calculate Interest for this month
                    overhead = (node['current_load'] * node['overhead_factor']) / 12
                    monthly_overhead += overhead
                    node['current_load'] += overhead
                    
                    # Pay Minimum
                    payment = min(node['current_load'], node['min_throughput'])
                    node['current_load'] -= payment
                    remaining_capacity -= payment

            # 2. Allocate Remaining Capacity (Snowball/Avalanche) to highest priority node
            # We already sorted by overhead_factor (Interest Rate) in load_configuration
            for node in active_nodes:
                if remaining_capacity <= 0:
                    break
                if node['current_load'] > 0:
                    payment = min(node['current_load'], remaining_capacity)
                    node['current_load'] -= payment
                    remaining_capacity -= payment

            total_overhead_cost += monthly_overhead
            
            # Check for infinite loop (if interest > payment)
            if month > 600: # 50 years cap
                print("[CRITICAL WARNING] Resource leak detected. Overhead exceeds throughput.")
                return

        self._generate_final_report(month, total_overhead_cost)

    def _generate_final_report(self, months, total_overhead):
        today = datetime.now()
        completion_date = today + timedelta(days=months*30)
        
        print("\n--- SYSTEM OPTIMIZATION REPORT ---")
        print(f"Total Iterations (Months): {months}")
        print(f"Projected Release Date:    {completion_date.strftime('%B %Y')}")
        print(f"Total Overhead Waste:      {total_overhead:,.2f} units")
        print("----------------------------------")
        print("[SUCCESS] All external dependencies resolved.")

if __name__ == "__main__":
    # Create a dummy config file if it doesn't exist for testing
    # You should edit 'config/dependencies.json' with your REAL data later.
    import os
    if not os.path.exists('config/dependencies.json'):
        os.makedirs('config', exist_ok=True)
        dummy_data = {
            "monthly_system_capacity": 5000, 
            "active_nodes": [
                {"id": "NODE_A", "current_load": 20000, "overhead_factor": 0.15, "min_throughput": 500},
                {"id": "NODE_B", "current_load": 5000, "overhead_factor": 0.05, "min_throughput": 200}
            ]
        }
        with open('config/dependencies.json', 'w') as f:
            json.dump(dummy_data, f, indent=4)
        print("[SETUP] Created dummy 'config/dependencies.json'. Edit this file with real data.")

    app = ResourceAllocator('config/dependencies.json')
    app.load_configuration()
    app.run_simulation()