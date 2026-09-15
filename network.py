import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# -----------------------------
# 0. Initial Configuration
# -----------------------------
N = 300
steps = 5
min_deg, max_deg = 15, 30  # Initial degree potential range
c_values = np.arange(0.20, 0.41, 0.01)  # Fine sweep from 0.20 to 0.40 with 0.01 steps
num_samples = 100          # Number of independent worlds (seeds) for validation

mean_community_counts = []
std_community_counts = []  # Array to record the magnitude of fluctuations (Std Dev)

print("Simulating 100 seeds for each 'c' value to measure fluctuation...")

# -----------------------------
# 1. Sweep Execution
# -----------------------------
for c in c_values:
    sample_counts = []
    
    for seed in range(num_samples):
        np.random.seed(seed)
        degrees = np.random.randint(min_deg, max_deg + 1, size=N)
        connected = np.zeros((N, N), dtype=bool)
        
        for t in range(steps):
            quota = degrees * c  
            while True:
                candidates = np.where(quota >= 1.0)[0]
                if len(candidates) == 0:
                    break
                order = candidates[np.argsort(quota[candidates])[::-1]]
                changed = False
                for i in order:
                    if quota[i] < 1.0:
                        continue
                    possible = np.where(~connected[i])[0]
                    possible = possible[possible != i]  # Exclude self-connection
                    if len(possible) == 0:
                        continue
                    j = np.random.choice(possible)
                    connected[i, j] = True
                    connected[j, i] = True
                    degrees[i] += 1
                    degrees[j] += 1
                    quota[i] -= 1.0
                    quota[j] -= 1.0
                    changed = True
                if not changed:
                    break
                    
        # --- Community Detection ---
        G = nx.from_numpy_array(connected.astype(int))
        if G.number_of_edges() > 0:
            communities = nx.community.louvain_communities(G, seed=0)
            sample_counts.append(len(communities))
        else:
            sample_counts.append(N)  # If isolated, counts equal total nodes
            
    # Calculate mean and standard deviation (fluctuation index)
    mean_community_counts.append(np.mean(sample_counts))
    std_community_counts.append(np.std(sample_counts))  # Indicator of structural flexibility

print("Simulation complete! Plotting...")

# -----------------------------
# 2. Visual Plotting
# -----------------------------
fig, ax1 = plt.subplots(figsize=(10, 5))

# Primary Axis: Mean Number of Communities (Blue)
color = 'tab:blue'
ax1.set_xlabel('Constant (c)', fontsize=12)
ax1.set_ylabel('Mean Number of Communities', color=color, fontsize=12)
ax1.plot(c_values, mean_community_counts, marker='o', color=color, linewidth=2, label="Mean Count")
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.5)

# Secondary Axis: Standard Deviation / Fluctuation Potential (Purple)
ax2 = ax1.twinx()  
color = 'tab:purple'
ax2.set_ylabel('Fluctuation Potential (Std Dev)', color=color, fontsize=12)
ax2.plot(c_values, std_community_counts, marker='^', color=color, linewidth=2.5, linestyle='-', label="Fluctuation (Std Dev)")
ax2.tick_params(axis='y', labelcolor=color)

# X-axis ticks configuration with 0.01 resolution
ax1.set_xticks(c_values)
ax1.set_xticklabels([f"{v:.2f}" for v in c_values], rotation=45)

plt.title("Identifying the Most Flexible 'c' Region (Mean vs Fluctuation Potential)", fontsize=14)
fig.tight_layout()
plt.show()
