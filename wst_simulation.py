iimport numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 1. Parameter Settings
# =====================================================================
dt = 0.01
T_max = 120
steps = int(T_max / dt)

mode_types = ['Wave (W)', 'Space (S)', 'Time (T)']

class ModeNode:
    def __init__(self, index, mode_type, initial_val, energy_crit=8.0):
        self.index = index
        self.mode_type = mode_type
        self.val = float(initial_val)
        self.energy_crit = energy_crit
        
        self.energy_pool = 0.0
        
        self.time_list = []
        self.val_list = []
        self.active = False
        self.spawn_time = None
        self.triggered = False

    def activate(self, t):
        self.active = True
        self.spawn_time = t

    def update(self, t, prev_val):
        if not self.active:
            return False, 0.0

        # ★ Minimal nonlinear oscillation dynamics
        # d_val = -a * val + sin(prev)
        d_val = -0.4 * self.val + np.sin(prev_val)

        # ★ Dissipative energy accumulation: accumulate |val|
        step_energy = abs(self.val) * dt
        self.energy_pool += step_energy

        self.time_list.append(t)
        self.val_list.append(self.val)

        spawn_next = False
        seed = 0.0

        # ★ When energy exceeds threshold, spawn the next mode
        #    (seed is simply the current value)
        if self.energy_pool >= self.energy_crit and not self.triggered:
            self.triggered = True
            seed = self.val
            spawn_next = True

        # Update value
        self.val += dt * d_val
        self.val = np.clip(self.val, -1.2, 1.2)

        return spawn_next, seed

# =====================================================================
# 2. Time Evolution Loop (Minimal Hierarchical Emergence Model)
# =====================================================================
nodes = [ModeNode(0, mode_types[0], initial_val=0.1, energy_crit=6.0)]
nodes[0].activate(0.0)

for i in range(steps):
    t = i * dt
    active_nodes = [n for n in nodes if n.active]
    
    for idx, node in enumerate(active_nodes):
        # External perturbation for the first mode (simple sine wave)
        if idx > 0:
            prev_val = active_nodes[idx - 1].val
        else:
            prev_val = np.sin(t)

        spawn, seed = node.update(t, prev_val)
        
        # Spawn next mode when threshold is reached (W → S → T → W → …)
        if spawn and len(nodes) < 6:
            next_idx = len(nodes)
            next_type = mode_types[next_idx % 3]
            
            # Increase threshold slightly for higher layers
            new_node = ModeNode(
                next_idx,
                next_type,
                initial_val=seed,
                energy_crit=6.0 + next_idx * 2.0
            )
            new_node.activate(t)
            nodes.append(new_node)

# =====================================================================
# 3. Visualization
# =====================================================================
fig, axes = plt.subplots(len(nodes), 1, figsize=(12, 1.8 * len(nodes)), sharex=True)
if len(nodes) == 1:
    axes = [axes]

colors = {'Wave (W)': 'purple', 'Space (S)': 'teal', 'Time (T)': 'coral'}

for idx, node in enumerate(nodes):
    ax = axes[idx]
    c = colors.get(node.mode_type, 'black')
    
    ax.plot(
        node.time_list,
        node.val_list,
        label=f"Mode {idx}: {node.mode_type} (Spawn: {node.spawn_time:.1f})",
        color=c,
        linewidth=1.5
    )
    
    if node.spawn_time is not None and node.spawn_time > 0:
        ax.axvline(
            x=node.spawn_time,
            color="blue",
            linestyle=":",
            alpha=0.7,
            label="Spawn Point"
        )

    ax.set_ylabel(f"M_{idx}")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True)

axes[0].set_title("Minimal Hierarchical Emergence via Energy Accumulation")
axes[-1].set_xlabel("Time")
plt.tight_layout()
plt.show()


plt.tight_layout()
plt.show()

