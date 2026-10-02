import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# Semantic Field
# =====================================================

class SemanticField:

    def __init__(self):

        self.names = []
        self.levels = []

        self.A = None
        self.W = None

        self.u = None
        self.v = None

        self.generated_modes = set()

    # -------------------------------------------------

    def add_node(self, name, level=0):

        self.names.append(name)
        self.levels.append(level)

        n = len(self.names)

        if self.A is None:

            self.A = np.zeros((1,1))
            self.W = np.zeros((1,1))

            self.u = np.zeros(1,dtype=complex)
            self.v = np.zeros(1,dtype=complex)

            return

        old_n = n - 1

        A2 = np.zeros((n,n))
        W2 = np.zeros((n,n))

        A2[:old_n,:old_n] = self.A
        W2[:old_n,:old_n] = self.W

        self.A = A2
        self.W = W2

        self.u = np.pad(self.u,(0,1))
        self.v = np.pad(self.v,(0,1))

    # -------------------------------------------------

    def connect(self,i,j,strength=1.0):

        self.A[i,j] = strength
        self.A[j,i] = strength

# =====================================================
# Gauge Laplacian
# =====================================================

def gauge_laplacian(u,A,W,g):

    N = len(u)

    result = np.zeros_like(u)

    for i in range(N):

        total = 0

        for j in range(N):

            if A[i,j] > 0:

                transported = (
                    u[j]
                    * np.exp(-1j*g*W[i,j])
                )

                total += transported - u[i]

        result[i] = total

    return result

# =====================================================
# Mode Discovery
# =====================================================

def discover_modes(
    history,
    threshold=0.35
):

    if history.shape[0] < 20:
        return []

    C = np.cov(history.T)

    eigvals,eigvecs = np.linalg.eigh(C)

    idx = np.argsort(eigvals)[::-1]

    eigvals = eigvals[idx]
    eigvecs = eigvecs[:,idx]

    modes = []

    for k in range(min(3,len(eigvals))):

        vec = eigvecs[:,k]

        active = np.where(
            np.abs(vec) > threshold
        )[0]

        if len(active) >= 2:

            modes.append(
                (
                    eigvals[k],
                    active
                )
            )

    return modes

# =====================================================
# Macro Node Creation
# =====================================================

def create_macro_node(
    field,
    members,
    eigval
):

    member_names = tuple(
        sorted(
            field.names[i]
            for i in members
        )
    )

    if member_names in field.generated_modes:
        return

    field.generated_modes.add(member_names)

    mode_name = (
        "MODE("
        +
        ",".join(member_names[:4])
        +
        ")"
    )

    field.add_node(
        mode_name,
        level=1
    )

    new_id = len(field.names)-1

    for m in members:

        field.connect(
            new_id,
            m,
            strength=1.0
        )

        tension = 1.0/(eigval+1e-5)

        field.W[new_id,m] = tension
        field.W[m,new_id] = tension

    field.u[new_id] = np.mean(
        field.u[members]
    )

    print(
        "\n[NEW MACRO NODE]"
    )
    print(mode_name)

# =====================================================
# Build Initial Graph
# =====================================================

field = SemanticField()

base_nodes = [

    "startup",
    "founder",
    "funding",
    "investor",

    "AI",
    "GPU",
    "LLM",
    "agent"
]

for n in base_nodes:
    field.add_node(n)

links = [

    (0,1),(0,2),(1,2),(2,3),

    (4,5),(4,6),(4,7),
    (5,6),(6,7)
]

for i,j in links:
    field.connect(i,j)

np.random.seed(42)

field.W = (
    np.random.normal(
        0,
        0.4,
        field.W.shape
    )
)

field.W = (
    field.W +
    field.W.T
)/2

# =====================================================
# Parameters
# =====================================================

DT = 0.05
STEPS = 1200

C_WAVE = 1.4
DAMPING = 0.05

BASE_G = 0.6

history = []

# =====================================================
# Input
# =====================================================

def inject(step,N):

    pulse = np.zeros(N)

    if 50 <= step <= 100:

        pulse[4] = 8
        pulse[6] = 10

    if 300 <= step <= 350:

        pulse[0] = 8
        pulse[2] = 10

    if 700 <= step <= 750:

        pulse[4] = 8
        pulse[0] = 8
        pulse[6] = 8
        pulse[2] = 8

    return pulse

# =====================================================
# Main Loop (Updated Version)
# =====================================================

for step in range(STEPS):

    macro = np.mean(np.real(field.u))

    g = BASE_G * (1 + 0.2 * np.sin(macro))

    diffusion = gauge_laplacian(
        field.u,
        field.A,
        field.W,
        g
    )

    # Generate node-wise noise adapted to the current expanded network size
    current_N = len(field.u)
    noise = (
        np.random.normal(0, 0.02, current_N)
        + 1j * np.random.normal(0, 0.02, current_N)
    )

    pulse = inject(step, current_N)

    # Compute dv_dt
    dv_dt = (
        (C_WAVE**2) * diffusion
        - DAMPING * field.v
        + pulse
        + noise
    )

    # Perform explicit assignment (copy) to handle array size expansion
    field.v = field.v + dv_dt * DT
    field.u = field.u + field.v * DT

    history.append(np.real(field.u).copy()) # Copy values instead of reference to save history

    # -------------------------
    # Mode emergence
    # -------------------------
    if (
        step > 0
        and step % 100 == 0
    ):
        recent = np.array(history[-100:])
        modes = discover_modes(recent)

        for eigval, members in modes:
            create_macro_node(
                field,
                members,
                eigval
            )

#=====================================================
# Visualization (Completed Version)
# =====================================================
history_max = max(len(h) for h in history)
padded = []
for h in history:
    vec = np.zeros(len(field.names))
    vec[:len(h)] = h
    padded.append(vec)
history_arr = np.array(padded)

plt.figure(figsize=(14, 8))

# 1. Plot base nodes
for i, name in enumerate(field.names):
    if field.levels[i] == 0:
        plt.plot(history_arr[:, i], alpha=0.7, linewidth=1.5, label=name)

# 2. Plot emergent macro nodes (level 1) distinguished by dashed/thick lines
for i, name in enumerate(field.names):
    if field.levels[i] > 0:
        # Find emergence timing (the first index where value is non-zero)
        birth_idx = np.where(history_arr[:, i] != 0)[0]
        if len(birth_idx) > 0:
            t_start = birth_idx[0]
            plt.plot(np.arange(t_start, STEPS), history_arr[t_start:, i], 
                     linestyle="--", linewidth=2.5, label=f"★ {name}")

plt.title("Semantic Field Dynamics with Emergent Macro Nodes", fontsize=14)
plt.xlabel("Time Step", fontsize=12)
plt.ylabel("Activation (Real Part)", fontsize=12)
plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
