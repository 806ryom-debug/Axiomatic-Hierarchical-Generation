import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ===== 1. パラメータ設定（5層） =====
R1_base, L1, C1 = 15.0, 1.0, 0.5
R2, L2, C2 = 3.0, 3.0, 1.5
R3, L3, C3 = 1.5, 8.0, 3.0
R4, L4, C4 = 0.5, 20.0, 6.0
R5, L5, C5 = 0.1, 60.0, 12.0

K12 = 0.5
K23 = 0.4
K34 = 0.3
K45 = 0.2

alpha = 0.4

# ===== 外部パルス入力（各層に異なる周波数で入れる） =====
def pulse_layer1(t):
    if (10 <= t <= 12) or (13.5 <= t <= 15):
        return 8.0
    if (100 <= t <= 102) or (103.5 <= t <= 105):
        return 8.0
    return 0.0

def pulse_layer2(t):
    if (20 <= t <= 22) or (24 <= t <= 26):
        return 4.0
    if (120 <= t <= 122) or (124 <= t <= 126):
        return 4.0
    return 0.0

def pulse_layer3(t):
    if (40 <= t <= 43) or (46 <= t <= 49):
        return 2.5
    if (140 <= t <= 143) or (146 <= t <= 149):
        return 2.5
    return 0.0

def pulse_layer4(t):
    if (70 <= t <= 75):
        return 1.5
    if (160 <= t <= 165):
        return 1.5
    return 0.0

# ===== 2. 5階層システム方程式 =====
def layered_brain_5layer(t, x):
    q1, i1, q2, i2, q3, i3, q4, i4, q5, i5 = x

    Vc1 = q1 / C1
    Vc2 = q2 / C2
    Vc3 = q3 / C3
    Vc4 = q4 / C4
    Vc5 = q5 / C5

    R1_dynamic = R1_base / (1 + alpha * Vc5)

    diss_1 = np.abs(i1)
    diss_2 = np.abs(i2)

    brain_noise = np.random.normal(0, 0.05)

    # --- 第1層 ---
    dq1_dt = i1
    di1_dt = (-R1_dynamic * i1
              - Vc1
              - K12 * (Vc1 - Vc2)
              + pulse_layer1(t)) / L1

    # --- 第2層 ---
    dq2_dt = i2
    di2_dt = (-R2 * i2
              - Vc2
              + K12 * (Vc1 - Vc2)
              - K23 * (Vc2 - Vc3)
              + 2.0 * diss_1
              + pulse_layer2(t)) / L2

    # --- 第3層（新規パルス） ---
    dq3_dt = i3
    di3_dt = (-R3 * i3
              - Vc3
              + K23 * (Vc2 - Vc3)
              - K34 * (Vc3 - Vc4)
              + 1.5 * diss_2
              + pulse_layer3(t)) / L3

    # --- 第4層（新規パルス） ---
    dq4_dt = i4
    di4_dt = (-R4 * i4
              - Vc4
              + K34 * (Vc3 - Vc4)
              - K45 * (Vc4 - Vc5)
              + pulse_layer4(t)) / L4

    # --- 第5層（マクロ波） ---
    dq5_dt = i5
    di5_dt = (-R5 * i5
              - Vc5
              + K45 * (Vc4 - Vc5)
              + brain_noise) / L5

    return [dq1_dt, di1_dt,
            dq2_dt, di2_dt,
            dq3_dt, di3_dt,
            dq4_dt, di4_dt,
            dq5_dt, di5_dt]

# ===== 3. シミュレーション =====
x0 = [0.0] * 10
t_span = (0, 200)
t_eval = np.linspace(t_span[0], t_span[1], 5000)

sol = solve_ivp(layered_brain_5layer, t_span, x0,
                t_eval=t_eval, method='RK45',
                rtol=1e-5, atol=1e-7)

t = sol.t
q1, i1, q2, i2, q3, i3, q4, i4, q5, i5 = sol.y

Vc1 = q1 / C1
Vc2 = q2 / C2
Vc3 = q3 / C3
Vc4 = q4 / C4
Vc5 = q5 / C5

# ===== 4. 可視化 =====
plt.figure(figsize=(12, 14))

plt.subplot(5, 1, 1)
plt.plot(t, [pulse_layer1(tt) for tt in t], color="black")
plt.plot(t, [pulse_layer2(tt) for tt in t], color="gray")
plt.plot(t, [pulse_layer3(tt) for tt in t], color="purple")
plt.plot(t, [pulse_layer4(tt) for tt in t], color="brown")
plt.title("Input Pulses (Layers 1–4)")
plt.grid(True)

plt.subplot(5, 1, 2)
plt.plot(t, Vc1, color="blue")
plt.title("Layer 1: Micro Spike")
plt.grid(True)

plt.subplot(5, 1, 3)
plt.plot(t, Vc2, color="orange")
plt.title("Layer 2: Local Spike")
plt.grid(True)

plt.subplot(5, 1, 4)
plt.plot(t, Vc3, color="green")
plt.title("Layer 3: Mid-term Context (Pulse Added)")
plt.grid(True)

plt.subplot(5, 1, 5)
plt.plot(t, Vc5, color="red")
plt.title("Layer 5: Global Macro Wave (Fractal-like)")
plt.grid(True)

plt.tight_layout()
plt.show()
# --- 合成波の計算 ---
combined_345 = Vc3 + Vc4 + Vc5

# --- 合成波の表示 ---
plt.figure(figsize=(12, 6))
plt.plot(t, combined_345, color="purple", lw=2)
plt.title("Combined Wave: Layer 3 + Layer 4 + Layer 5")
plt.xlabel("Time (t)")
plt.ylabel("Voltage (V)")
plt.grid(True)
plt.show()

# ===== 5. 【新規追加】階層数相図（Hierarchical Phase Diagram）の自動生成 =====

# 縦軸のスイープパラメータ：Layer 1 への入力パルスの強さ（0.0 〜 20.0）
intensity_steps = 40
intensities = np.linspace(0.0, 20.0, intensity_steps)
num_layers = 5

# 相図のデータを蓄積する2次元配列 (縦軸：入力強度, 横軸：階層数)
phase_matrix = np.zeros((intensity_steps, num_layers))

print("階層数相図を計算中...")
for idx, intensity in enumerate(intensities):
    
    # 入力強度を動的に書き換えるローカル関数
    def dynamic_pulse_layer1(t):
        if (10 <= t <= 12) or (13.5 <= t <= 15): return intensity
        if (100 <= t <= 102) or (103.5 <= t <= 105): return intensity
        return 0.0

    # ループ内用の方程式（Layer 1 の入力を動的パルスに変更）
    def loop_system(t, x):
        q1, i1, q2, i2, q3, i3, q4, i4, q5, i5 = x
        Vc1, Vc2, Vc3, Vc4, Vc5 = q1/C1, q2/C2, q3/C3, q4/C4, q5/C5
        R1_dynamic = R1_base / (1 + alpha * Vc5)
        
        # 方程式の中身（上のコードと同一、pulse_layer1 のみ書き換え）
        dxdt = layered_brain_5layer(t, x)
        # Layer 1 の di1_dt 項のパルス入力を上書き
        dxdt[1] = (dxdt[1]*L1 - pulse_layer1(t) + dynamic_pulse_layer1(t)) / L1
        return dxdt

    # シミュレーション実行
    loop_sol = solve_ivp(loop_system, t_span, x0, t_eval=t_eval, method='RK45', rtol=1e-4, atol=1e-6)
    
    # 各層の電圧の標準偏差（＝波の振幅・エネルギーの激しさ）を計算
    v_amplitudes = [
        np.std(loop_sol.y[0] / C1),  # Layer 1
        np.std(loop_sol.y[2] / C2),  # Layer 2
        np.std(loop_sol.y[4] / C3),  # Layer 3
        np.std(loop_sol.y[6] / C4),  # Layer 4
        np.std(loop_sol.y[8] / C5)   # Layer 5
    ]
    
    phase_matrix[idx, :] = v_amplitudes

# === 階層数相図のプロット ===
plt.figure(figsize=(10, 7))
# 縦軸：入力強度、横軸：階層数（1〜5）のヒートマップ
plt.imshow(phase_matrix, origin='lower', aspect='auto',
           extent=[1, num_layers, intensities[0], intensities[-1]], cmap='plasma')

plt.colorbar(label="Neural/Material Activity (Voltage StdDev)")
plt.title("World First: Hierarchical Phase Diagram")
plt.xlabel("Layer Number (n)")
plt.ylabel("Input Pulse Intensity (Layer 1)")
plt.xticks(range(1, num_layers + 1))
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()