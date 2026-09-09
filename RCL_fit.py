import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# ==========================================
# 1. 実データの読み込みと前処理（なまらせ処理）
# ==========================================
df = pd.read_csv("VIXCLS_TED_CSD.csv")

serial_days = pd.to_numeric(df["observation_date"], errors="coerce")
df["Date"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(serial_days, unit="D")
df = df.rename(columns={"VIXCLS": "VIX", "TEDRATE": "TED", "CSD": "CDS"})
df = df.set_index("Date")

df_num = df[["VIX", "TED", "CDS"]].apply(pd.to_numeric, errors="coerce").ffill()

# ターゲットとなる正規化実データ (平均0, 標準偏差1)
df_norm = (df_num - df_num.mean()) / df_num.std()
df_diff = df_norm.diff().dropna()

# 隠れた多層プロセスを疑似表現するなまらせ処理
span_latent_layers = 15 
df_diff["Iin_latent"] = df_diff["VIX"].clip(lower=0).ewm(span=span_latent_layers, adjust=False).mean()

t_max_index = len(df_diff) - 1
t_steps = np.arange(len(df_diff))
t_eval = np.linspace(0, t_max_index, len(df_diff))

Iin_tempered_func = interp1d(t_steps, df_diff["Iin_latent"], kind="linear", fill_value="extrapolate")

# 事前生成ノイズ（確定化）
np.random.seed(42)
raw_noise = np.random.normal(0, 0.05, len(df_diff))
brain_noise_func = interp1d(t_steps, raw_noise, kind="linear", fill_value="extrapolate")

# 目標波形の配列（プロットの比較用）
target_VIX = df_norm.loc[df_diff.index, "VIX"].values
target_TED = df_norm.loc[df_diff.index, "TED"].values
target_CDS = df_norm.loc[df_diff.index, "CDS"].values

# 回路骨格（容量・慣性パラメータ）
C1, L1 = 0.5, 1.0
C2, L2 = 5.0, 15.0   # 2層目をなまらせるための大容量設定
C3, L3 = 10.0, 50.0

# ==========================================
# 2. 確定した最適パラメータの直接入力
# ==========================================
R1_base = 15.0000
R2      = 0.1000
R3      = 0.0800
K12     = 4.5000
K23     = 3.5000
alpha   = 0.6000
gain_In = 28.0000
gain_i1 = 18.0000

# ==========================================
# 3. システム方程式の定義
# ==========================================
def optimized_market_system(t, x):
    q1, i1, q2, i2, q3, i3 = x

    Vc1 = q1 / C1
    Vc2 = q2 / C2
    Vc3 = q3 / C3

    R1_dynamic = R1_base / (1.0 + alpha * Vc3)
    Iin = Iin_tempered_func(t) * gain_In
    brain_noise = brain_noise_func(t)

    dq1_dt = i1
    di1_dt = (- R1_dynamic * i1 - Vc1 - K12 * (Vc1 - Vc2) + Iin) / L1

    dq2_dt = i2
    di2_dt = (- R2 * i2 - Vc2 + K12 * (Vc1 - Vc2) - K23 * (Vc2 - Vc3) + gain_i1 * np.abs(i1)) / L2

    dq3_dt = i3
    di3_dt = (- R3 * i3 - Vc3 + K23 * (Vc2 - Vc3) + brain_noise) / L3

    return [dq1_dt, di1_dt, dq2_dt, di2_dt, dq3_dt, di3_dt]

# ==========================================
# 4. シミュレーションの実行
# ==========================================
x0 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
# 💡 t_eval を明示的に渡すことで、指定した時間ステップ（1007点）で強制的に解を出力させます
sol = solve_ivp(optimized_market_system, (0, t_max_index), x0, t_eval=t_eval, method='RK45')

# 状態変数の抽出
q1_out, i1_out, q2_out, i2_out, q3_out, i3_out = sol.y

sim_Vc1 = q1_out / C1  # 第1層の電圧 (VIXに対応)
sim_i2  = i2_out       # 第2層の電流 (TEDに対応)
sim_Vc3 = q3_out / C3  # 第3層の電圧 (CDSに対応)

# 💡 [超重要安全策] ソルバーが実際に出力したステップ数（524など）に、日付データ側を安全にスライスして合わせる
sim_len = len(sol.t)
plot_dates = df_diff.index[:sim_len]
plot_target_VIX = target_VIX[:sim_len]
plot_target_TED = target_TED[:sim_len]
plot_target_CDS = target_CDS[:sim_len]
plot_Iin_latent = df_diff["Iin_latent"].values[:sim_len]
plot_vix_diff   = df_diff["VIX"].clip(lower=0).values[:sim_len]

# ==========================================
# 5. 最終プロットの描画
# ==========================================
plt.figure(figsize=(14, 10))

# 1段目：なまらせ入力
plt.subplot(4, 1, 1)
plt.plot(plot_dates, plot_vix_diff, color="gray", alpha=0.3, label="Raw VIX Diff")
plt.plot(plot_dates, plot_Iin_latent, color="black", lw=2, label="Tempered Input (EMA span=15)")
plt.title("Input Dynamics: Latent Micro-Macro Process", fontsize=12, fontweight='bold')
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

# 2段目：第1層（VIX）
plt.subplot(4, 1, 2)
plt.plot(plot_dates, sim_Vc1, color="blue", lw=2, label="Model Layer 1: Vc1 (VIX)")
plt.plot(plot_dates, plot_target_VIX, color="blue", alpha=0.3, linestyle=":", label="Actual VIX (Normalized)")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

# 3段目：第2層（TED）
plt.subplot(4, 1, 3)
plt.plot(plot_dates, sim_i2, color="orange", lw=2, label="Model Layer 2: i2 (TED)")
plt.plot(plot_dates, plot_target_TED, color="orange", alpha=0.3, linestyle=":", label="Actual TED (Normalized)")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

# 4段目：第3層（CDS）
plt.subplot(4, 1, 4)
plt.plot(plot_dates, sim_Vc3, color="red", lw=2, label="Model Layer 3: Vc3 (CDS)")
plt.plot(plot_dates, plot_target_CDS, color="red", alpha=0.3, linestyle=":", label="Actual CDS (Normalized)")
plt.xlabel("Date")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()
