import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 1. Parameter Settings & Initialization (Axiomatic System)
# =====================================================================
dt = 0.01
T_max = 100
steps = int(T_max / dt)

# Saturation limits for each mode
M_W_sat, M_S_sat, M_T_sat = 2.0, 2.0, 2.0

# Initial state of Hierarchy H_n [Wave, Space, Time]
H_n = np.array([0.2, 0.4, 0.3])

# [Axiom 4] Critical scale triggering phase transition
S_crit = 1.35  

# Lists for data logging
time_list = []
H_W_list, H_S_list, H_T_list = [], [], []
S_n_list = []
phase_transitions = []  # Timestamps of phase transitions

# =====================================================================
# 2. Time Evolution Loop (Implementing the Four Axioms)
# =====================================================================
for i in range(steps):
    t = i * dt
    time_list.append(t)
    H_W_list.append(H_n[0])
    H_S_list.append(H_n[1])
    H_T_list.append(H_n[2])

    # --- 2-1. [Axiom 1] Compute Internal Variation & Natural Scale S_n ---
    # Based on the W-S-T Ouroboros gradient interaction
    dW = (M_T_sat - H_n[2]) - (M_S_sat - H_n[1])
    dS = (M_W_sat - H_n[0]) - (M_T_sat - H_n[2])
    dT = (M_S_sat - H_n[1]) - (M_W_sat - H_n[0])
    
    dH_dlambda = np.array([dW, dS, dT])
    
    # Natural scale S_n defined as the norm of internal variations
    S_n = np.linalg.norm(dH_dlambda)
    S_n_list.append(S_n)

    # --- 2-2. [Axiom 4] Phase Transition & Structural Discontinuity ---
    if S_n >= S_crit:
        phase_transitions.append(t)
        
        # 1. Discontinuous structural jump (mapping to a new macro state)
        H_next_direction = -dH_dlambda / (S_n + 1e-8) 
        H_n = H_n + H_next_direction * 2.0  
        
        # 2. Energy reset via structural memory dissipation (R_n)
        H_n = np.tanh(H_n) * 0.5  
        
    else:
        # --- 2-3. [Axiom 2 & 3] Continuous Hierarchical Generation ---
        H_next_direction = dH_dlambda / (S_n + 1e-8)
        H_n += dt * H_next_direction

# =====================================================================
# 3. Visualization
# =====================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

# Top Plot: W-S-T Hierarchy State Evolution
ax1.plot(time_list, H_W_list, label="Wave (W)", color="purple")
ax1.plot(time_list, H_S_list, label="Space (S)", color="teal")
ax1.plot(time_list, H_T_list, label="Time (T)", color="coral")
for pt in phase_transitions:
    ax1.axvline(x=pt, color="red", linestyle="--", alpha=0.4)
ax1.set_ylabel("Hierarchy State H_n")
ax1.set_title("Evolution of H_n with Axiomatic Phase Transitions")
ax1.legend()
ax1.grid(True)

# Bottom Plot: Natural Scale S_n Transition & Reset
ax2.plot(time_list, S_n_list, label="Natural Scale S_n", color="black", linewidth=1.5)
ax2.axhline(y=S_crit, color="red", linestyle=":", label="Critical Scale S_crit")
for pt in phase_transitions:
    ax2.axvline(x=pt, color="red", linestyle="--", alpha=0.4, label="Phase Transition" if pt == phase_transitions[0] else "")
ax2.set_xlabel("Time")
ax2.set_ylabel("Scale Norm ||S_n||")
ax2.set_title("Natural Scale Congestion and Structural Jumps")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

