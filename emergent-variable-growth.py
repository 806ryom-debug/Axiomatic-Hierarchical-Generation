import numpy as np
import matplotlib.pyplot as plt

# ===== 1. Parameter Settings =====
INIT_NODES = 10       # Initial number of variables (system capacity)
STEPS = 200           # Total number of simulation steps
np.random.seed(7)

# Initial State Definition
# State field 'u' (accumulated potential) and 'W' representing connection parameters
u = np.random.normal(0, 0.5, INIT_NODES)
# Gauge Coupling Matrix W (reconciliation criteria / relational tension; 0 means uncoupled)
W = np.zeros((INIT_NODES, INIT_NODES))
for i in range(INIT_NODES):
    # Establish initial gauge links in a ring/torus topology
    W[i, (i + 1) % INIT_NODES] = np.random.uniform(-0.5, 0.5)

# Arrays for data logging (tracked via lists due to dynamic system size scaling)
history_variable_counts = []
history_macro_activity = []

# ===== 2. Spatiotemporal Calculus Loop with Dynamic Variable Propagation =====
for t in range(STEPS):
    current_size = len(u)
    history_variable_counts.append(current_size)
    
    # ─── 【Spatial Integration】Extraction of Macro Context ───
    macro_context = np.mean(np.abs(u))
    history_macro_activity.append(macro_context)
    
    # Self-referential loop: Macro activity dynamically modulates the gauge switch threshold (sensitivity)
    switch_threshold = 0.3 * (1.0 + 0.5 * np.sin(macro_context))
    
    # ─── 【Spatial Differentiation】Relational Distortion via Gauge-Switching ───
    diff_matrix = np.zeros((current_size, current_size))
    for i in range(current_size):
        for j in range(current_size):
            if W[i, j] != 0:
                # Parallel-transport adjacent reference configurations before computing the spatial derivative
                diff_matrix[i, j] = u[j] * np.cos(W[i, j]) - u[i]

    # ─── 【Temporal Integration】Cumulative State Evolution ───
    # Spatially aggregate the local differences to drive acceleration
    total_diff = np.sum(diff_matrix, axis=1)
    u += total_diff * 0.1  # Continuous temporal integration of states
    u += np.random.normal(0, 0.05, current_size)  # Ubiquitous micro thermal noise (stochastic differentiation)

    # ─── 【Autonomous Variable Generation and Elimination via Gauge-Switching】 ───
    new_nodes_to_add = []
    nodes_to_remove = []
    
    # 1. Variable Multiplication (Spawning mediating bypass nodes when structural tension breaks symmetry)
    for i in range(current_size):
        for j in range(current_size):
            if W[i, j] != 0:
                # Check if the localized relational distortion breaks through the macro-configured critical threshold
                if np.abs(diff_matrix[i, j]) > switch_threshold:
                    # Spawn a new mediating variable to dissipate localized structural stress
                    new_nodes_to_add.append((i, j))
    
    # 2. Variable Pruning (Annihilating redundant variables that have dropped out of active dynamics)
    for i in range(current_size):
        # Identify variables that are overly synchronized or have decayed into inactivity
        if np.abs(u[i]) < 0.01:
            nodes_to_remove.append(i)

    # ─── Dynamic Topological Rewriting (Array Resizing and Re-coupling) ───
    # Expand the state arrays when a phase-transition switch (variable generation) is triggered
    if len(new_nodes_to_add) > 0:
        num_new = len(new_nodes_to_add)
        u = np.append(u, np.random.normal(0, 0.1, num_new))
        
        # Scale up the coupling matrix W to embed the newly generated gauge configurations
        new_W = np.zeros((current_size + num_new, current_size + num_new))
        new_W[:current_size, :current_size] = W
        
        for k, (i, j) in enumerate(new_nodes_to_add):
            new_index = current_size + k
            # Intercept the over-strained link (i->j) by placing the new variable in between to restore cohesion
            new_W[i, j] = 0  # Decouple the over-strained link
            new_W[i, new_index] = W[i, j] * 0.5
            new_W[new_index, j] = np.random.uniform(-0.2, 0.2)
        W = new_W

    # Execute dynamic metabolic pruning (deleting from the highest index downward to preserve array integrity)
    if len(nodes_to_remove) > 0:
        nodes_to_remove = sorted(list(set(nodes_to_remove)), reverse=True)
        for idx in nodes_to_remove:
            if len(u) > 3:  # Prevent total structural collapse by enforcing a baseline grid floor
                u = np.delete(u, idx)
                W = np.delete(W, idx, axis=0)
                W = np.delete(W, idx, axis=1)

# ===== 3. Multiscale Visual Analysis of Self-Propagating Dynamics =====
time_axis = np.arange(STEPS)

plt.figure(figsize=(12, 6))

# Top: Time series tracking the autonomous expansion/contraction of system size
plt.subplot(2, 1, 1)
plt.plot(time_axis, history_variable_counts, color="green", linewidth=2, label="Dynamic Variables (Node Count)")
plt.title("Emergence of Variables: How the System Size Evolves via Gauge-Switching")
plt.ylabel("Number of Active Variables")
plt.grid(True)
plt.legend()

# Bottom: Trajectory of the emergent macro-level global system energy
plt.subplot(2, 1, 2)
plt.plot(time_axis, history_macro_activity, color="orange", linewidth=1.5, label="Macro Context (System Energy)")
plt.xlabel("Simulation Steps")
plt.ylabel("Macro Activity Mean")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
