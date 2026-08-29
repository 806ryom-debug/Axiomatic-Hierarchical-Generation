import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. Parameter Settings & Initialization
# ==============================================================================

# Constant external energy influx (increase this to boost energy supply)
input_energy = 0.0  

# Saturation Limit Values for each mode
M_W_sat = 2.0
M_S_sat = 2.0
M_T_sat = 2.0

# Initial Values for the fundamental modes (Wave, Space, Time)
M_W = 0.2
M_S = 0.4
M_T = 0.3

# Time Evolution Configuration
dt = 0.01
T_max = 50.0
steps = int(T_max / dt)

# Allocation for trajectory tracking
W_list, S_list, T_list = [], [], []
time_axis = []

# ==============================================================================
# 2. Time Evolution Loop (Self-Referential Dynamics)
# ==============================================================================

for i in range(steps):
    t = i * dt
    W_list.append(M_W)
    S_list.append(M_S)
    T_list.append(M_T)
    time_axis.append(t)

    # --- 2-1. Calculate Base Variation with Energy Influx ---
    # Each fundamental mode receives a push based on interactions and external influx
    dW = (M_T_sat - M_T) - (M_S_sat - M_S) + input_energy
    dS = (M_W_sat - M_W) - (M_T_sat - M_T) + input_energy
    dT = (M_S_sat - M_S) - (M_W_sat - M_W) + input_energy

    # --- 2-2. Define Variation Vectors and Directional Gradients ---
    V_W = dW
    V_S = dS
    V_T = dT

    eps = 1e-8
    e_W = V_W / (abs(V_W) + eps)
    e_S = V_S / (abs(V_S) + eps)
    e_T = V_T / (abs(V_T) + eps)

    # --- 2-3. Generate Closed-Loop Circular Gradients (Uroboros Structure) ---
    # The rate of change of one mode drives the gradient of the next scale
    dS_grad = e_W * V_W
    dT_grad = e_S * V_S
    dW_grad = e_T * V_T

    grad_weight = 0.3

    dW_total = dW + grad_weight * dW_grad
    dS_total = dS + grad_weight * dS_grad
    dT_total = dT + grad_weight * dT_grad

    # --- 2-4. State Evolution (Mode Update) ---
    M_W += dt * dW_total
    M_S += dt * dS_total
    M_T += dt * dT_total

# ==============================================================================
# 3. Visualization & Output Plot
# ==============================================================================

plt.figure(figsize=(10, 5))
plt.plot(time_axis, W_list, label="Wave (W)", color="purple")
plt.plot(time_axis, S_list, label="Space (S)", color="teal")
plt.plot(time_axis, T_list, label="Time (T)", color="coral")

plt.xlabel("Time")
plt.ylabel("Mode Value")
plt.title("Closed-Loop Gradient Model with Constant Energy Input")
plt.legend()
plt.grid(True)
plt.show()
