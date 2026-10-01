#Glass Dynamics toy model
import numpy as np
import matplotlib.pyplot as plt

# [Added] Fix random seed for reproducibility.
# This ensures that anyone who runs it will reproduce the exact same "staircase graph" shown in the README.
np.random.seed(7) 

class UnionFind:
    """
    Disjoint-Set data structure to strictly and equivalently group simultaneous multi-body collisions.
    Eliminates dependency on execution order and treats topological coupling relations as mathematically equivalent.
    """
    def __init__(self, n):
        self.parent = list(range(n))
    
    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path Compression
        return self.parent[i]
    
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j

class GlassWSTNode:
    """
    Information/physical node (particle) that performs autonomous boundary breaches and mass rewriting.
    """
    def __init__(self, node_id, initial_pos, initial_mass=1.0):
        self.id = node_id
        self.q = initial_pos      # State (Position: cumulative value of integration)
        self.v = 0.0              # Rate of change (Velocity: residue of differentiation)
        self.initial_mass = initial_mass  # Base invariant mass to prevent duplicate counting during coupling
        self.mass = initial_mass  # System's current "Effective Mass" (Inertia / integration degree of macro degrees of freedom)
        
        # Trajectory history buffers (for post-hoc physical property evaluation and verification)
        self.history_q = []
        self.history_v = []
        
        # Dynamic record of topological entanglement (cluster coupling)
        self.entangled_with = set([node_id])

class GlassUniversalEngine:
    """
    Integrated engine simulating potential-free phase transitions in a closed-loop structure.
    """
    def __init__(self, num_nodes=20, cage_size=1.5):
        # Initial particle placement (applies high-density and random fluctuations mimicking a liquid state)
        self.nodes = [
            GlassWSTNode(i, initial_pos=float(i) * 0.4 + np.random.uniform(-0.1, 0.1)) 
            for i in range(num_nodes)
        ]
        self.num_nodes = num_nodes
        self.cage_size = cage_size  # Boundary width emerging macroscopically as an integration constant (cage size)

    def step(self, external_forces, dt):
        """
        1. Mechanics Step (F=ma) ── Pure functional form-free computation without pre-configured interaction potentials.
        """
        # Universally apply a "total external force" proportional to the aggregate mass of particles belonging to a cluster (entanglement)
        adjusted_forces = np.array(external_forces, dtype=float)
        for node in self.nodes:
            if len(node.entangled_with) > 1:
                cluster_indices = list(node.entangled_with)
                # Aggregate the total external force of the entire cluster to ensure physical consistency of F=ma
                total_force = np.sum([external_forces[idx] for idx in cluster_indices])
                adjusted_forces[node.id] = total_force

        for i, node in enumerate(self.nodes):
            # Determine acceleration: a = F_total / M_effective
            acceleration = adjusted_forces[i] / node.mass
            node.v += acceleration * dt
            node.q += node.v * dt
            
            # Record internal state history
            node.history_q.append(node.q)
            node.history_v.append(node.v)

        """
        2. Structural Update Step ── Dynamic topology hacking via "post-hoc evaluation" of boundary breaches (perfect inelastic amalgamation with restitution coefficient e=0).
        """
        self_evaluate_post_hoc_collisions(self)

def self_evaluate_post_hoc_collisions(engine):
    """
    Core algorithm that detects 'post-hoc' whether boundaries were actually breached at the end of the conflict 
    between differentiation (velocity) and integration (position), dynamically rewriting system rules (mass/inertia).
    """
    uf = UnionFind(engine.num_nodes)
    
    # 1. Synchronize previously formed topological coupling relationships to UnionFind
    for i in range(engine.num_nodes):
        for j in engine.nodes[i].entangled_with:
            uf.union(i, j)
            
    # 2. Post-hoc detection of new boundary breaches (collisions)
    has_new_collision = False
    for i in range(engine.num_nodes):
        for j in range(i + 1, engine.num_nodes):
            # Skip pairs belonging to the same cluster
            if uf.find(i) == uf.find(j):
                continue
                
            current_distance = np.abs(engine.nodes[i].q - engine.nodes[j].q)
            
            # Boundary breach criterion: when spatial distance shrinks below the macroscopic cage size
            if current_distance < engine.cage_size:
                uf.union(i, j)
                has_new_collision = True

    # Maintain current state if no new breaches occur
    if not has_new_collision:
        return

    # 3. Classify particle groups into macro clusters for each updated root
    groups = {}
    for i in range(engine.num_nodes):
        root = uf.find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(i)

    # 4. Batch update physical quantities for each cluster (order-independent exact macro-statistical calculation)
    for root, indices in groups.items():
        if len(indices) <= 1:
            continue
            
        # Calculate exact total effective mass (M) without duplication from the sum of unique base masses
        total_mass = sum(engine.nodes[idx].initial_mass for idx in indices)
        
        # Calculate common synchronized cluster velocity based on the momentum conservation law in a perfectly inelastic collision
        total_momentum = sum(engine.nodes[idx].initial_mass * engine.nodes[idx].v for idx in indices)
        combined_velocity = total_momentum / total_mass
        
        # Calculate exact center-of-mass position with mass weighting to synchronize spatial constraints
        total_weighted_q = sum(engine.nodes[idx].initial_mass * engine.nodes[idx].q for idx in indices)
        combined_position = total_weighted_q / total_mass
        
        combined_entangled = set(indices)
        
        # Batch rewrite the newly emerged macro rules (mass, velocity, position) into all nodes within the cluster
        for idx in indices:
            node = engine.nodes[idx]
            
            # Output log to console only at the exact moment a new coalescence (cross-coupling) occurs
            if len(combined_entangled) > len(node.entangled_with):
                if node.id == idx and idx == min(indices):
                    print(f"[Simultaneous Boundary Breach] Particles {indices} combined. Total Mass: {total_mass}, Center of Mass: {combined_position:.3f}")
            
            node.mass = total_mass
            node.v = combined_velocity
            node.q = combined_position
            node.entangled_with = set(combined_entangled)

# ─── Simulation Execution and Plotting ───
if __name__ == "__main__":
    num_nodes = 15  # Number of particles corresponding to the crowded train metaphor
    duration = 500  # Number of time steps
    dt = 0.05
    
    # Initialize engine (boundary width optimized to 0.1 to match initial spacing)
    engine = GlassUniversalEngine(num_nodes=num_nodes, cage_size=0.1)
    
    pos_history = [[] for _ in range(num_nodes)]
    mass_history = [[] for _ in range(num_nodes)]
    
    print("Starting potential-free glass transition (cross-coupling freeze) simulation...")
    
    for step in range(duration):
        # Minute thermal noise representing stochastic disturbances from the external environment (seeds for future emergence)
        forces = np.random.uniform(-2.0, 2.0, num_nodes)
        
        # 1-step update
        engine.step(forces, dt)
        
        # Record states
        for i, node in enumerate(engine.nodes):
            pos_history[i].append(node.q)
            mass_history[i].append(node.mass)

    # 📊 Result Visualization (plots abrupt changes in macro properties / titration curve-like sudden rises)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Upper Plot: Particle trajectories (process where micro lines converge into a single macro bundle)
    for i in range(num_nodes):
        ax1.plot(pos_history[i], alpha=0.7)
    ax1.set_ylabel("Particle Position (q)")
    ax1.set_title("Glass Dynamics (Strict & Stable Architecture)")
    ax1.grid(True)
    
    # Lower Plot: Effective mass of each particle (discontinuous step-wise increase via post-hoc hacking)
    for i in range(num_nodes):
        ax2.plot(mass_history[i], alpha=0.7)
    ax2.set_ylabel("Effective Mass (M)")
    ax2.set_xlabel("Time Steps")
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()