import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ==========================================
# 1. Data Structure: Union-Find
# ==========================================

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1
            return True
        return False

# ==========================================
# 2. Simulation Environment Settings
# ==========================================

np.random.seed(42)
N_NODES = 35         # Number of elements
BOX_SIZE = 100       # Finite boundary condition
STEPS = 150          # Extended time steps to see the transformation
MAX_RADIUS = 28      # Maximum radius of expanding bubbles

positions = np.random.uniform(0, BOX_SIZE, size=(N_NODES, 2))
radii_timeline = np.linspace(0, MAX_RADIUS, STEPS)

# Dynamic evolutionary variables
node_colors = np.zeros(N_NODES, dtype=int)  # All start with Color 0 (Teal)
warped = False
warp_frame = -1
zero_holes_counter = 0

radius_history = []
holes_history = []

# ==========================================
# 3. Initialize Plot (Strictly English Only)
# ==========================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

def init():
    # 【修正点】毎フレームの配列リセット（文字消去）をここから除去
    ax1.clear()
    ax1.set_xlim(0, BOX_SIZE)
    ax1.set_ylim(0, BOX_SIZE)
    ax1.set_aspect('equal')
    ax1.set_title("Micro Space: Autonomous Layer Expansion", fontsize=11, fontweight='bold')
    ax1.set_xlabel("X Space")
    ax1.set_ylabel("Y Space")

    ax2.clear()
    ax2.set_xlim(0, MAX_RADIUS)
    ax2.set_ylim(0, 10)
    ax2.set_title("Macro Status: Multi-Layer Topological Holes", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Bubble Radius (Self-Driven Expansion)")
    ax2.set_ylabel("Total Active Holes (Betti-1)")
    ax2.grid(True, linestyle='--', alpha=0.5)

# ==========================================
# 4. Main Dynamics & Animation Loop
# ==========================================

def update(frame):
    global warped, warp_frame, zero_holes_counter, node_colors, radius_history, holes_history

    # 【追加機能】最初のステップ（あるいはリピート開始時）のみ、安全にデータを初期化する
    if frame == 0:
        radius_history = []
        holes_history = []
        warped = False
        warp_frame = -1
        zero_holes_counter = 0
        node_colors = np.zeros(N_NODES, dtype=int)

    current_radius = radii_timeline[frame]
    init()

    # Track metrics per color layer independently
    total_holes = 0
    universe_area = BOX_SIZE ** 2

    # [0, 1] の配列をループ処理
    for c_id in [0, 1]:
        c_indices = np.where(node_colors == c_id)[0]
        n_c = len(c_indices)
        if n_c == 0:
            continue

        uf = UnionFind(N_NODES)
        active_edges = 0
        union_count = 0

        # Link generation inside the same color channel
        for i_idx in range(n_c):
            for j_idx in range(i_idx + 1, n_c):
                i = c_indices[i_idx]
                j = c_indices[j_idx]
                dist_ij = np.linalg.norm(positions[i] - positions[j])
                if dist_ij <= (current_radius * 2):
                    active_edges += 1
                    if uf.union(i, j):
                        union_count += 1

        raw_loops = active_edges - union_count

        # Coarse-grained choking effect within its own layer
        bubble_area_c = n_c * (np.pi * (current_radius ** 2))
        occupancy_rate_c = min(1.0, bubble_area_c / universe_area)

        holes_c = raw_loops * (1.0 - occupancy_rate_c)
        total_holes += round(max(0.0, holes_c))

    # --- Evolution Trigger: Autonomous Phase Transformation ---
    if not warped and current_radius > 6.0 and total_holes == 0:
        zero_holes_counter += 1
        if zero_holes_counter >= 4:
            warped = True
            warp_frame = frame
            # Spontaneous symmetry breaking: half of the nodes morph into Color 1
            shuffle_indices = np.arange(N_NODES)
            np.random.shuffle(shuffle_indices)
            node_colors[shuffle_indices[N_NODES // 2:]] = 1
    else:
        if not warped:
            zero_holes_counter = 0

    radius_history.append(current_radius)
    holes_history.append(total_holes)

    # --- Render Micro Space (Left Panel) ---
    for i, (x, y) in enumerate(positions):
        c_str = 'teal' if node_colors[i] == 0 else 'darkorange'
        circle = plt.Circle((x, y), current_radius, color=c_str, alpha=0.09, ec=c_str, lw=0.5, zorder=1)
        ax1.add_patch(circle)

    ax1.scatter(positions[:, 0], positions[:, 1], c='black', zorder=3, s=20)

    for i in range(N_NODES):
        for j in range(i + 1, N_NODES):
            if node_colors[i] == node_colors[j]:
                dist = np.linalg.norm(positions[i] - positions[j])
                if dist <= (current_radius * 2):
                    c_line = 'teal' if node_colors[i] == 0 else 'darkorange'
                    ax1.plot([positions[i, 0], positions[j, 0]], [positions[i, 1], positions[j, 1]],
                             color=c_line, alpha=0.35, lw=1.2, zorder=2)

    ax1.text(3, BOX_SIZE - 12,
             f"Step: {frame}\nRadius: {current_radius:.2f}\nTotal Holes: {total_holes}\nMulti-Layer: {'ON' if warped else 'OFF'}",
             bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))

    # --- Render Macro Status with Dynamic Autoscale (Right Panel) ---
    ax2.plot(radius_history, holes_history, color='crimson', lw=2.5)
    if radius_history:
        ax2.scatter(radius_history[-1], holes_history[-1], color='crimson', s=40, zorder=3)

    if warped and warp_frame != -1:
        ax2.axvline(radii_timeline[warp_frame], color='purple', linestyle=':', lw=2.0)
        ax2.text(radii_timeline[warp_frame] + 0.3, ax2.get_ylim()[1] * 0.15,
                 "Warp Event: Yn3rd Variable Injected", color='purple', fontsize=9, fontweight='bold')

    max_holes_ever = max(holes_history) if len(holes_history) > 0 else 0
    if max_holes_ever > 0:
        ax2.set_ylim(-0.5, max(max_holes_ever * 1.2, 5.0))

    ax2.set_xlim(0, MAX_RADIUS)

    if warped and frame > warp_frame + 5 and total_holes == 0:
        phase_text = "Phase 5: High-Order Ultimate Jamming"
        text_color = 'darkred'
    elif warped:
        phase_text = "Phase 4: Transformation (Multi-Layer Emergence)"
        text_color = 'purple'
    elif frame > 40 and total_holes == 0:
        phase_text = "Phase 3: Saturation & Freezing (Topological Jamming)"
        text_color = 'red'
    elif radius_history and total_holes >= max_holes_ever * 0.7 and total_holes > 0:
        phase_text = "Phase 2: Critical Edge (Peak Context Emergence)"
        text_color = 'darkorange'
    else:
        phase_text = "Phase 1: Self-Driven Expansion (Birth of Order)"
        text_color = 'teal'

    ax2.text(0.5, ax2.get_ylim()[1] * 0.92, f"Status: {phase_text}", color=text_color, fontsize=10, fontweight='bold')

# Global Title Setting
fig.suptitle("W-S-T Toy Model: Multi-Layer Topological Transformation: Overcoming Structural Jamming by\nInjecting Chromatic Dimension", fontsize=11, fontweight='bold')

ani = FuncAnimation(fig, update, frames=STEPS, init_func=init, repeat=False, interval=50)
plt.tight_layout()
plt.show()