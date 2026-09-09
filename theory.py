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
df = df.rename(columns={"VIXCLS": "VIX", "TEDRATE": "TED", "CDS": "CDS"})
df = df.set_index("Date")

df_num = df[["VIX", "TED", "CDS"]].apply(pd.to_numeric, errors="coerce").ffill()

df_norm = (df_num - df_num.mean()) / df_num.std()
df_diff = df_norm.diff().dropna()

span_latent_layers = 10
df_diff["Iin_latent"] = df_diff["VIX"].clip(lower=0).ewm(span=span_latent_layers, adjust=False).mean()

t_max_index = len(df_diff) - 1
t_steps = np.arange(len(df_diff))
t_eval = np.linspace(0, t_max_index, len(df_diff))

Iin_tempered_func = interp1d(t_steps, df_diff["Iin_latent"], kind="linear", fill_value="extrapolate")

np.random.seed(42)
raw_noise = np.random.normal(0, 0.05, len(df_diff))
brain_noise_func = interp1d(t_steps, raw_noise, kind="linear", fill_value="extrapolate")

target_VIX = df_norm.loc[df_diff.index, "VIX"].values
target_TED = df_norm.loc[df_diff.index, "TED"].values
target_CDS = df_norm.loc[df_diff.index, "CDS"].values

# ==========================================
# 2. 統合モデルのパラメータ設定
# ==========================================
C1, L1 = 0.8, 0.3
C2, L2 = 5.0, 15.0   
C3, L3 = 10.0, 50.0

VIX_sat = 6.0
TED_sat = 6.0
CDS_sat = 6.0

R1_base = 15.0000
R2      = 0.1000
R3      = 0.0800
alpha   = 0.6000
gain_In = 22.0000
gain_i1 = 5.0000

G_vix = 2.5
G_ted = 1.0
G_cds = 0.5

# スイッチの鋭さを決めるパラメータ（大きいほどシャープ、小さいほどマイルド）
beta_switch = 2 

# ==========================================
# 3. 統合システム方程式（飽和巡回 × RLC回路）
# ==========================================
def integrated_market_system(t, x):
    q1, i1, q2, i2, q3, i3 = x

    Vc1 = q1 / C1
    Vc2 = i2      
    Vc3 = q3 / C3

    dVIX_sat = VIX_sat - Vc1
    dTED_sat = TED_sat - Vc2
    dCDS_sat = CDS_sat - Vc3

    dVIX = dVIX_sat - dTED_sat
    dTED = dTED_sat - dCDS_sat
    dCDS = dCDS_sat - dVIX_sat

    # 【💡 高速化コア変更点】 符号関数を滑らかな tanh に変更してチャタリングを防ぐ
    eVIX = np.tanh(beta_switch * dVIX)
    eTED = np.tanh(beta_switch * dTED)
    eCDS = np.tanh(beta_switch * dCDS)

    R1_dynamic = R1_base * (1.0 + alpha * np.maximum(0, Vc3))
    Iin = Iin_tempered_func(t) * gain_In
    brain_noise = brain_noise_func(t)

    dq1_dt = i1
    di1_dt = (- R1_dynamic * i1 - Vc1 + G_vix * eVIX * dVIX_sat + Iin) / L1

    dq2_dt = i2
    di2_dt = (- R2 * i2 - Vc2 + G_ted * eTED * dTED_sat + gain_i1 * np.abs(i1)) / L2

    dq3_dt = i3
    di3_dt = (- R3 * i3 - Vc3 + G_cds * eCDS * dCDS_sat + brain_noise) / L3

    return [dq1_dt, di1_dt, dq2_dt, di2_dt, dq3_dt, di3_dt]

# ==========================================
# 4. シミュレーションの実行
# ==========================================
x0 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

# 【💡 高速化コア変更点】 method を 'Radau' に変更し、許容誤差を現実的な値に設定
sol = solve_ivp(
    integrated_market_system, 
    (0, t_max_index), 
    x0, 
    t_eval=t_eval, 
    method='Radau', 
    rtol=1e-4, 
    atol=1e-7
)

q1_out, i1_out, q2_out, i2_out, q3_out, i3_out = sol.y

sim_Vc1 = q1_out / C1  
sim_i2  = i2_out       
sim_Vc3 = q3_out / C3  

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

plt.subplot(4, 1, 1)
plt.plot(plot_dates, plot_vix_diff, color="gray", alpha=0.3, label="Raw VIX Diff")
plt.plot(plot_dates, plot_Iin_latent, color="black", lw=2, label="Tempered Input (EMA span=15)")
plt.title("Integrated Dynamics: Saturation Cycle × Latent RLC Process (Optimized Solver)", fontsize=12, fontweight='bold')
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

plt.subplot(4, 1, 2)
plt.plot(plot_dates, sim_Vc1, color="blue", lw=2, label="Model Layer 1: Vc1 (VIX)")
plt.plot(plot_dates, plot_target_VIX, color="blue", alpha=0.3, linestyle=":", label="Actual VIX (Normalized)")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

plt.subplot(4, 1, 3)
plt.plot(plot_dates, sim_i2, color="orange", lw=2, label="Model Layer 2: i2 (TED)")
plt.plot(plot_dates, plot_target_TED, color="orange", alpha=0.3, linestyle=":", label="Actual TED (Normalized)")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

plt.subplot(4, 1, 4)
plt.plot(plot_dates, sim_Vc3, color="red", lw=2, label="Model Layer 3: Vc3 (CDS)")
plt.plot(plot_dates, plot_target_CDS, color="red", alpha=0.3, linestyle=":", label="Actual CDS (Normalized)")
plt.xlabel("Date")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()
