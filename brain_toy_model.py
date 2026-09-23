import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

# ===== 1. Spatiotemporal Resolution Settings =====
GRID_SIZE = 40             # 2D spatial grid size (40x40 neural field)
DX = 1.0                   # Grid spacing for spatial derivatives (dx, dy)
DT = 0.05                  # Time step for real-time temporal derivatives (dt)
STEPS = 1000               # Total number of simulation time steps

# Physical and Gauge Parameters
C_WAVE = 1.5               # Wave propagation speed
DAMPING = 0.04             # Baseline dissipation rate (resistive damping)
ALPHA = 0.5                # Top-down modulation gain (macro global wave controlling micro sensitivity)

# --- Gauge Theory Parameters (Introduction of the "Weak Interaction") ---
G_COUPLING = 0.3           # Coupling constant for the gauge field (strength of local spatial tension)

# ===== 2. Initial States (Variables for 2nd-Order Coupled Covariant Wave Equation) =====
# Extend the potential field 'u' to a complex field.
# The real part represents the observable potential, while the imaginary part represents the local internal phase/reference.
u = np.zeros((GRID_SIZE, GRID_SIZE), dtype=complex)
v = np.zeros((GRID_SIZE, GRID_SIZE), dtype=complex)  # Time derivative field of potential (∂u/∂t)

# Initialize the "Gauge Field" (weak interaction) permeating each spatial link (x and y directions).
# This introduces slight spatial variations in the initial reference configurations to induce local interaction.
np.random.seed(42)  # Fixed seed for reproducibility
W_x = np.random.normal(0, 0.2, (GRID_SIZE, GRID_SIZE))
W_y = np.random.normal(0, 0.2, (GRID_SIZE, GRID_SIZE))

# Function to inject irregular external pulse currents (sensory inputs) into specific 2D coordinates (center)
def get_external_pulse(t_step):
    if (100 <= t_step <= 130) or (500 <= t_step <= 530):
        pulse = np.zeros((GRID_SIZE, GRID_SIZE), dtype=complex)
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2
        # Inject the real part (actual voltage input) and a subtle imaginary part (phase disruption)
        pulse[cx-2:cx+3, cy-2:cy+3] = 10.0 + 2.0j
        return pulse
    return np.zeros((GRID_SIZE, GRID_SIZE), dtype=complex)

# Biological thermal noise (Complex white noise: potential fluctuations and phase jitter)
def get_brain_noise():
    real_noise = np.random.normal(0, 0.2, (GRID_SIZE, GRID_SIZE))
    imag_noise = np.random.normal(0, 0.2, (GRID_SIZE, GRID_SIZE))
    return real_noise + 1j * imag_noise

# Arrays for data logging (recording the observable real part = potential)
history_center = []        # Real-time trajectory of the central spatial point
history_global_mean = []   # Spatial global average (macro-level global wave / ECoG)

# ===== 3. Real-Time Spatiotemporal "Covariant" Calculus Loop =====
for t in range(STEPS):
    
    # Calculate the mean potential of the entire space (Macro wave: Context)
    macro_context = np.mean(np.real(u))
    
    # Self-referential loop: The macro field dynamically modulates the micro-level coupling strength.
    # As global activity rises, the gauge coupling fluctuates, altering boundary permeability and inducing self-limitation.
    dynamic_damping = DAMPING / (1.0 + ALPHA * np.abs(macro_context))
    current_g = G_COUPLING * (1.0 + 0.2 * np.sin(macro_context))

    # 【Steps 1 & 2: Computation of the Gauge-Covariant Laplacian (D²u)】
    # Instead of simple adjacent subtraction, the neighboring references are parallel-transported 
    # via the gauge field Wμ before computing the difference. 
    # This mathematically embeds the "local tension of competing references" into the spatial derivative.
    laplacian = np.zeros_like(u)
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            # Indices accounting for periodic boundary conditions (torus structure)
            x_plus  = (x + 1) % GRID_SIZE
            x_minus = (x - 1) % GRID_SIZE
            y_plus  = (y + 1) % GRID_SIZE
            y_minus = (y - 1) % GRID_SIZE

            # --- Gauge Covariant Derivative in the x-direction ---
            # Parallel-transport the neighboring references by rotating them via W_x
            u_right = u[x_plus, y] * np.exp(-1j * current_g * W_x[x, y])
            u_left  = u[x_minus, y] * np.exp(1j * current_g * W_x[x_minus, y])
            u_xx_covariant = (u_right - 2 * u[x, y] + u_left) / (DX**2)
            
            # --- Gauge Covariant Derivative in the y-direction ---
            # Parallel-transport the neighboring references by rotating them via W_y
            u_up   = u[x, y_plus] * np.exp(-1j * current_g * W_y[x, y])
            u_down = u[x, y_minus] * np.exp(1j * current_g * W_y[x, y_minus])
            u_yy_covariant = (u_up - 2 * u[x, y] + u_down) / (DX**2)
            
            # Synthesize the covariant Laplacian
            laplacian[x, y] = u_xx_covariant + u_yy_covariant

    # Retrieve external inputs and neural noise
    I_in = get_external_pulse(t)
    noise = get_brain_noise()

    # 【Step 3: Temporal Differentiation (Progression of the Covariant Wave Equation)】
    # The gauge-covariant spatial derivative directly drives the temporal evolution (system dynamics)
    # ∂v/∂t = c²D²u - γv + I_in + Noise
    dv_dt = (C_WAVE**2) * laplacian - dynamic_damping * v + I_in + noise

    # 【Step 4: Temporal Integration (Real-Time Update via Euler's Method)】
    v += dv_dt * DT  # Integrate acceleration to update velocity (Stage 1)
    u += v * DT      # Integrate velocity to update potential/phase position (Stage 2)

    # Log observable physical quantities (Real part of the complex field = potential field)
    history_center.append(np.real(u[GRID_SIZE//2, GRID_SIZE//2]))
    history_global_mean.append(macro_context)

history_center = np.array(history_center)
history_global_mean = np.array(history_global_mean)

# ===== 4. Visualization of Multiscale Spatiotemporal Analysis =====
time_axis = np.arange(STEPS) * DT

plt.figure(figsize=(12, 10))

# Top: Micro-level (central space point) potential time series
plt.subplot(3, 1, 1)
plt.plot(time_axis, history_center, color="blue", label="Micro Layer: Covariant Potential u(cx, cy, t)")
plt.title("Micro-level Real-Time Spatiotemporal Dynamics (with Gauge Field)")
plt.ylabel("Potential (Real Part)")
plt.grid(True)
plt.legend()

# Middle: Macro-level (global spatial mean) emergent wave (simulated ECoG)
plt.subplot(3, 1, 2)
plt.plot(time_axis, history_global_mean, color="red", label="Macro Layer: Global Field Mean (Emerged ECoG)")
plt.title("Macro-level Global Field Emergence from Spatial Interaction")
plt.ylabel("Global Mean Voltage")
plt.grid(True)
plt.legend()

# Bottom: Power Spectral Density (PSD) of macro spontaneous waves (verification of 1/f fractal scaling)
plt.subplot(3, 1, 3)
true_fs = 1.0 / DT  # Effective sampling frequency
f, psd = welch(history_global_mean, fs=true_fs, nperseg=256)

plt.semilogy(f, psd, color="purple", label="Covariant Emerged Frequency Profile")
plt.title("Frequency Analysis (PSD) - Verification of 1/f Fractal Slope via Gauge Cohesion")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")
plt.xlim(0.05, true_fs / 2)
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
