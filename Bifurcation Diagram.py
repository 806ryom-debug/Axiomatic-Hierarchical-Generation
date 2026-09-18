import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# -----------------------------
# 0. Configuration & Parameters
# -----------------------------
N = 300
steps = 40
fixed_cost = 0.30      # Fixed structural maintenance cost (deflationary pressure)

# Sweep parameter c (inflow rate) across the critical boundary [0.20, 0.45]
c_values = np.arange(0.20, 0.46, 0.01)

x_c = []
y_boss = []
y_common = []

print("Sweeping constant 'c' to verify the shift of the critical point...")

# -----------------------------
# 1. Phase Sweep Execution
# -----------------------------
for c in c_values:
    # Fix random seed per parameter to ensure structural comparability under stochastic selection
    np.random.seed(42)
    
    # Stratified initial states: 150 privileged nodes (deg=50) vs 150 common nodes (deg=20)
    degrees = np.concatenate([np.full(N // 2, 50.0), np.full(N // 2, 20.0)])
    connected = np.zeros((N, N), dtype=bool)
    dynamic_quota = np.zeros(N, dtype=float)
    
    for t in range(1, steps + 1):
        # Adaptive Feedback Loop: Inflow (c) and Deflation (fixed_cost) proportional to current degrees
        dynamic_quota += degrees * c
        dynamic_quota -= degrees * fixed_cost
        
        # --- Pruning Phase (Bankruptcy Mechanism) ---
        while True:
            # Detect nodes incapable of sustaining current links (negative quota buffer)
            bankrupts = np.where((dynamic_quota < 0.0) & (degrees > 0))[0]
            if len(bankrupts) == 0:
                break
            
            # Select the most vulnerable node (maximum financial/topological stress)
            worst_i = bankrupts[np.argmin(dynamic_quota[bankrupts])]
            
            connected_nodes = np.where(connected[worst_i])[0]
            if len(connected_nodes) == 0:
                dynamic_quota[worst_i] = 0.0  # Reset buffer if no links remain to be pruned
                continue
                
            # Disconnect from the neighbor under the highest structural distress
            j = connected_nodes[np.argmin(dynamic_quota[connected_nodes])]
            
            connected[worst_i, j] = False
            connected[j, worst_i] = False
            degrees[worst_i] -= 1
            degrees[j] -= 1
            
            # Reclaim maintenance cost upon connection pruning
            dynamic_quota[worst_i] += fixed_cost
            dynamic_quota[j] += fixed_cost

        # --- Attachment Phase (Stochastic Preferential Selection) ---
        while True:
            # Identify active nodes with sufficient quota to initiate new connections
            candidates = np.where(dynamic_quota >= 1.0)[0]
            if len(candidates) == 0:
                break
            
            # The most affluent node initiates the link-building behavior
            best_i = candidates[np.argmax(dynamic_quota[candidates])]
            
            possible = np.where(~connected[best_i])[0]
            possible = possible[possible != best_i]  # Exclude self-loops
            
            if len(possible) == 0:
                dynamic_quota[best_i] = 0.0  # Terminate infinite loop if saturation limit is reached
                continue
                
            # Determine target nodes stochastically, proportional to current quota abundance
            target_quotas = dynamic_quota[possible]
            target_quotas = np.maximum(target_quotas, 1e-5)  # Avoid numerical zero division
            probabilities = target_quotas / np.sum(target_quotas)
            
            j = np.random.choice(possible, p=probabilities)
            
            # Establish bilateral structural connection
            connected[best_i, j] = True
            connected[j, best_i] = True
            degrees[best_i] += 1
            degrees[j] += 1
            dynamic_quota[best_i] -= 1.0
            dynamic_quota[j] -= 1.0

    # Extract final topological structural metrics
    G = nx.from_numpy_array(connected.astype(int))
    actual_degrees = [d for n, d in G.degree()]
    
    # Store results split by initial class tier
    for idx, d in enumerate(actual_degrees):
        x_c.append(c)
        if idx < N // 2:
            y_boss.append(d)
        else:
            y_common.append(d)

# -----------------------------
# 2. Bifurcation Diagram Visualization
# -----------------------------
plt.figure(figsize=(11, 6))

# Map the stratified node layers into the phase transition space
plt.scatter(x_c[:len(y_boss)], y_boss, color='gold', alpha=0.25, s=8, label="Privileged Stratum (Initial Degree: 50)")
plt.scatter(x_c[len(y_boss):], y_common, color='tab:blue', alpha=0.25, s=8, label="Common Stratum (Initial Degree: 20)")

plt.title(f"Verification of Critical Point Shift (Fixed link_cost = {fixed_cost})", fontsize=13)
plt.xlabel("Constant (c) [Inflow Rate / Injection Strength]", fontsize=11)
plt.ylabel("Final Connection Degree at t=40 (Structural Saturation)", fontsize=11)
plt.xticks(c_values[::2])
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc="upper left", markerscale=3)
plt.tight_layout()
plt.show()
