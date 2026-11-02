import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 宇宙の初期条件 (ミニマル・パラメータ)
# ==========================================
W, S, T = 0.1, 0.0, 0.0
STEPS = 300
dt = 0.05

history = np.zeros((STEPS, 3))

# ==========================================
# 2. ウロボロス・ダイナミクス (自己参照ループ)
# ==========================================
for step in range(STEPS):
    history[step] = [W, S, T]

    dW = -S - 0.05 * W                  # 空間の歪みが波を押え込む (飽和コスト)
    dS = W + 0.1 * T * S                # 時間の慣性(T)が、空間の歪み(S)を非線形に爆発させる
    dT = (S**2) - 0.1 * T               # 空間の歪みのゴミが底に沈澱し、時間の矢 (T)を生成する

    # 状態の更新 (時間積分)
    W += dW * dt
    S += dS * dt
    T += dT * dt

# ==========================================
# 3. 創発の軌跡の可視化 (修正版)
# ==========================================
fig = plt.figure(figsize=(12, 5))
fig.suptitle("W-S-T Uroboros Model: Autonomous Scale-Expansion", fontsize=12, fontweight='bold')

# 左画面：ミクロの関係性が紡ぎ出す「自発的拡大の螺旋」
ax1 = fig.add_subplot(121, projection='3d')
ax1.plot(history[:, 0], history[:, 1], history[:, 2], color='crimson', lw=2)
ax1.set_title("3D Phase Trajectory (W-S-T Spiral)")
ax1.set_xlabel("Wave (W)")
ax1.set_ylabel("Space (S)")
ax1.set_zlabel("Time (T)")
ax1.grid(True, alpha=0.3)

# 右画面：すべての要素のダイナミクスをプロット
ax2 = fig.add_subplot(122)
ax2.plot(history[:, 0], label='Wave (W: Micro)', color='teal', lw=1.5)
ax2.plot(history[:, 1], label='Space (S: Macro Distortion)', color='darkorange', lw=1.5)
ax2.plot(history[:, 2], label='Time (T: Context Sedimentation)', color='purple', lw=2, linestyle='--')
ax2.set_title("Temporal Evolution & Context Sedimentation")
ax2.set_xlabel("Time Steps")
ax2.set_ylabel("Value")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
