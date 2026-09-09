import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ===== 1. 20層システムのパラメータ自動設計 =====
N_layers = 20

# 各層のL, C, Rを幾何級数（グラデーション）で自動生成
# 20層で値が爆発しないよう、拡大率を少しマイルドに調整
C_list = np.array([0.5 * (1.12**i) for i in range(N_layers)])
L_list = np.array([1.0 * (1.15**i) for i in range(N_layers)])
R_list = np.array([2.0 * (0.96**i) for i in range(N_layers)])
R1_base = 15.0

K = 0.4       # 隣接レイヤー間の結合定数
alpha = 0.5   # 第20層（最上位）から第1層（最下位）へのトップダウン変調強度

# ===== 2. 指定された階層（1, 5, 15層目）への独立パルス入力関数 =====
# インデックス表記では 0層目, 4層目, 14層目 に対応
def get_layer_pulse(t, layer_idx, intensity_factor):
    # 1層目 (idx=0): 超高速の連射パルス
    if layer_idx == 0:
        if (10.0 <= t <= 12.0) or (13.5 <= t <= 15.0) or (100.0 <= t <= 102.0) or (103.5 <= t <= 105.0):
            return 8.0 * intensity_factor
            
    # 5層目 (idx=4): 中間の長さのパルス（時間をずらして注入）
    elif layer_idx == 4:
        if (30.0 <= t <= 34.0) or (130.0 <= t <= 134.0):
            return 5.0 * intensity_factor
            
    # 15層目 (idx=14): ゆったりとした長周期のパルス（さらに時間をずらす）
    elif layer_idx == 14:
        if (60.0 <= t <= 67.0) or (160.0 <= t <= 167.0):
            return 3.0 * intensity_factor
            
    return 0.0

# ===== 3. 20階層システム方程式の汎用記述 =====
# 状態変数 x は [q0, i0, q1, i1, ..., q19, i19] (要素数 40)
def multi_layered_brain_ode(t, x, intensity_factor):
    dxdt = np.zeros_like(x)
    
    # 電圧 Vc と 電流 i の抽出
    qs = x[0::2]
    is_ = x[1::2]
    vcs = qs / C_list

    # 最上位層（Layer 20）による、最下位層（Layer 1）のダイナミック抵抗変調
    R1_dynamic = R1_base / (1.0 + alpha * vcs[-1])
    
    # 脳内の自発熱雑音（最上位層を駆動）
    brain_noise = np.random.normal(0, 0.05)

    for n in range(N_layers):
        dq_dt = is_[n]
        
        # 基本の散逸（R）と復元（Vc）
        Rn = R1_dynamic if n == 0 else R_list[n]
        di_dt = - Rn * is_[n] - vcs[n]
        
        # 下位層からのボトムアップ結合（前層の電流の絶対値を積分源にする非線形結合）
        if n > 0:
            di_dt += K * (vcs[n-1] - vcs[n]) + 1.5 * np.abs(is_[n-1])
        # 上位層へのトップダウン結合
        if n < N_layers - 1:
            di_dt -= K * (vcs[n] - vcs[n+1])
            
        # 指定レイヤー（1, 5, 15層）への外部パルス注入
        di_dt += get_layer_pulse(t, n, intensity_factor)
        
        # 最上位層（Layer 20）のみ、背景ノイズを追加
        if n == N_layers - 1:
            di_dt += brain_noise
            
        # 配列への格納
        dxdt[2*n] = dq_dt
        dxdt[2*n+1] = di_dt

    return dxdt

# ===== 4. 階層数相図（ヒートマップ）の計算スイープ =====
t_span = (0, 200)
t_eval = np.linspace(t_span[0], t_span[1], 3000)
x0 = np.zeros(2 * N_layers)

# 縦軸のスイープ（パルス全体の強度係数を 0.0 から 3.0 まで 30段階で変化させる）
intensity_steps = 30
intensities = np.linspace(0.0, 3.0, intensity_steps)
phase_matrix = np.zeros((intensity_steps, N_layers))

print("20層バージョンの階層数相図を計算中...（少し時間がかかります）")
for idx, factor in enumerate(intensities):
    # シミュレーション実行
    sol = solve_ivp(lambda t, x: multi_layered_brain_ode(t, x, factor), 
                    t_span, x0, t_eval=t_eval, method='RK45', rtol=1e-4, atol=1e-6)
    
    # 各層の電圧の標準偏差（活動の激しさ）を計算して格納
    for n in range(N_layers):
        qn = sol.y[2*n]
        vcn = qn / C_list[n]
        phase_matrix[idx, n] = np.std(vcn)
    print(f"進捗: {idx+1}/{intensity_steps}")

# ===== 5. 20層階層数相図のプロット =====
plt.figure(figsize=(12, 8))
plt.imshow(phase_matrix, origin='lower', aspect='auto',
           extent=[1, N_layers, intensities[0], intensities[-1]], cmap='plasma')

plt.colorbar(label="Neural/Material Activity (Voltage StdDev)")
plt.title("20-Layer Hierarchical Phase Diagram (Pulses at L1, L5, L15)")
plt.xlabel("Layer Number (n)")
plt.ylabel("Pulse Intensity Factor")
plt.xticks(range(1, N_layers + 1))
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()
