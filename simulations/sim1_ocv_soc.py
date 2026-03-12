import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.interpolate import CubicSpline

# ── Real 18650 OCV-SOC data points (from published literature)
# Source: Plett 2015, Battery Management Systems Vol.1
# Also matches Samsung 25R / LG MJ1 published discharge curves
soc_points = np.array([0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95, 100])
ocv_points = np.array([3.000, 3.132, 3.280, 3.395, 3.490, 3.550, 3.600,
                        3.660, 3.710, 3.745, 3.790, 3.860, 3.960, 4.070, 4.200])

# Cubic spline interpolation for smooth curve
cs = CubicSpline(soc_points, ocv_points)
soc_fine = np.linspace(0, 100, 1000)
ocv_fine = cs(soc_fine)

# Derivative: dOCV/dSOC (used in EKF-based BMS)
docv_dsoc = cs(soc_fine, 1)

# ── FIGURE ──
fig = plt.figure(figsize=(16, 10), facecolor='#0D1117')
fig.suptitle('Simulation 1: Open Circuit Voltage (OCV) vs State of Charge (SOC)\n18650 Li-Ion Cell — Samsung 25R / LG MJ1 Profile',
             fontsize=16, color='white', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35,
                       left=0.08, right=0.95, top=0.90, bottom=0.08)

# ── PLOT 1: OCV vs SOC main curve ──
ax1 = fig.add_subplot(gs[0, :])
ax1.set_facecolor('#161B22')

ax1.plot(soc_fine, ocv_fine, color='#00D4E8', linewidth=2.5, label='OCV Curve (Cubic Spline Fit)', zorder=3)
ax1.scatter(soc_points, ocv_points, color='#FFB300', s=80, zorder=5, label='Reference Data Points (Literature)', marker='D')

# Protection thresholds
ax1.axhline(y=4.200, color='#FF3F5E', linewidth=1.5, linestyle='--', alpha=0.8, label='Max Charge Cutoff: 4.200V (100% SOC)')
ax1.axhline(y=4.250, color='#FF0000', linewidth=1.2, linestyle=':', alpha=0.6, label='Overvoltage Protection Trip: 4.250V')
ax1.axhline(y=3.000, color='#FF3F5E', linewidth=1.5, linestyle='--', alpha=0.8, label='Min Discharge Cutoff: 3.000V (0% SOC)')
ax1.axhline(y=2.900, color='#FF0000', linewidth=1.2, linestyle=':', alpha=0.6, label='Undervoltage Protection Trip: 2.900V')

# Key SOC markers
key_socs = [25, 50, 75]
for s in key_socs:
    v = float(cs(s))
    ax1.axvline(x=s, color='#3D5A7A', linewidth=0.8, linestyle=':', alpha=0.7)
    ax1.annotate(f'{v:.3f}V', xy=(s, v), xytext=(s+1.5, v+0.04),
                fontsize=9, color='#00E87A',
                arrowprops=dict(arrowstyle='->', color='#00E87A', lw=1.0))

ax1.set_xlabel('State of Charge (%)', color='#8899AA', fontsize=12)
ax1.set_ylabel('Open Circuit Voltage (V)', color='#8899AA', fontsize=12)
ax1.set_title('Full OCV–SOC Characteristic Curve', color='white', fontsize=13, fontweight='bold')
ax1.set_xlim(0, 100)
ax1.set_ylim(2.75, 4.40)
ax1.tick_params(colors='#8899AA')
ax1.spines['bottom'].set_color('#3D5A7A')
ax1.spines['left'].set_color('#3D5A7A')
ax1.spines['top'].set_color('#3D5A7A')
ax1.spines['right'].set_color('#3D5A7A')
ax1.grid(color='#1F2A38', linewidth=0.6, alpha=0.8)
ax1.legend(loc='upper left', fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A',
           labelcolor='white', framealpha=0.9)

# Fill usable region
ax1.fill_between(soc_fine, ocv_fine, 2.75, where=(ocv_fine >= 3.0) & (ocv_fine <= 4.2),
                  alpha=0.07, color='#00D4E8')

# ── PLOT 2: dOCV/dSOC (sensitivity) ──
ax2 = fig.add_subplot(gs[1, 0])
ax2.set_facecolor('#161B22')

ax2.plot(soc_fine, docv_dsoc * 100, color='#BB6BFF', linewidth=2.0)
ax2.fill_between(soc_fine, docv_dsoc * 100, 0, alpha=0.15, color='#BB6BFF')
ax2.axhline(y=0, color='#3D5A7A', linewidth=0.8)

# Mark flat region (low sensitivity = hard to estimate SOC)
flat_region = (soc_fine >= 30) & (soc_fine <= 70)
ax2.fill_between(soc_fine[flat_region], (docv_dsoc * 100)[flat_region], 0,
                  alpha=0.25, color='#FFB300', label='Flat region\n(Coulomb Count\ndominates here)')

ax2.set_xlabel('SOC (%)', color='#8899AA', fontsize=11)
ax2.set_ylabel('dOCV/dSOC (V per 100%)', color='#8899AA', fontsize=11)
ax2.set_title('OCV Sensitivity\n(dOCV/dSOC)', color='white', fontsize=12, fontweight='bold')
ax2.set_xlim(0, 100)
ax2.tick_params(colors='#8899AA')
for spine in ax2.spines.values(): spine.set_color('#3D5A7A')
ax2.grid(color='#1F2A38', linewidth=0.6, alpha=0.8)
ax2.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# Add annotation
ax2.annotate('Flat zone: 30–70% SOC\nCC must dominate here', xy=(50, 0.003),
             fontsize=8.5, color='#FFB300', ha='center')

# ── PLOT 3: Lookup table used in firmware ──
ax3 = fig.add_subplot(gs[1, 1])
ax3.set_facecolor('#161B22')

# Firmware uses 11-point lookup table
fw_soc =  np.array([  0,  10,  20,  30,  40,  50,  60,  70,  80,  90, 100])
fw_ocv = np.array([3.000, 3.280, 3.490, 3.600, 3.660, 3.710, 3.745, 3.790, 3.860, 3.960, 4.200])

ax3.step(fw_soc, fw_ocv, color='#00E87A', linewidth=2.0, where='post', label='Firmware Lookup Steps')
ax3.plot(soc_fine, ocv_fine, color='#00D4E8', linewidth=1.5, alpha=0.5, linestyle='--', label='True Curve')
ax3.scatter(fw_soc, fw_ocv, color='#FFB300', s=90, zorder=5, marker='s')

# Error between step and true
fw_ocv_interp = cs(fw_soc)
for i in range(len(fw_soc)):
    ax3.annotate(f'{fw_ocv[i]:.3f}V\n→{fw_soc[i]}%',
                xy=(fw_soc[i], fw_ocv[i]),
                fontsize=6.5, color='#8899AA', ha='center', va='bottom',
                xytext=(fw_soc[i], fw_ocv[i] + 0.025))

ax3.set_xlabel('SOC (%)', color='#8899AA', fontsize=11)
ax3.set_ylabel('OCV (V)', color='#8899AA', fontsize=11)
ax3.set_title('11-Point Firmware\nLookup Table', color='white', fontsize=12, fontweight='bold')
ax3.set_xlim(-2, 102)
ax3.set_ylim(2.85, 4.35)
ax3.tick_params(colors='#8899AA')
for spine in ax3.spines.values(): spine.set_color('#3D5A7A')
ax3.grid(color='#1F2A38', linewidth=0.6, alpha=0.8)
ax3.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Bottom annotation bar ──
fig.text(0.5, 0.01,
         'Punit Singh Auluck | 25120034 | 4S Li-Ion BMS | SPEL Lab, IIT Gandhinagar | Simulation 1/6',
         ha='center', va='bottom', fontsize=9, color='#3D5A7A', style='italic')

plt.savefig('sim1_ocv_soc.png', dpi=180, bbox_inches='tight',
            facecolor='#0D1117')
print("Saved sim1_ocv_soc.png")

# Print firmware table for documentation
print("\n── 11-Point OCV-SOC Lookup Table (for firmware) ──")
print(f"{'SOC (%)':>10} | {'OCV (V)':>10}")
print("-" * 25)
for s, v in zip(fw_soc, fw_ocv):
    print(f"{s:>10} | {v:>10.3f}")

# Key insight
print(f"\n── Key Observations ──")
print(f"Flattest region: 30–70% SOC (dV/dSOC < {min(docv_dsoc[300:700])*100:.4f} V/%)")
print(f"Steepest region: 0–10% and 90–100% SOC")
print(f"Voltage range used: 3.000V – 4.200V ({4.200-3.000:.3f}V swing)")
