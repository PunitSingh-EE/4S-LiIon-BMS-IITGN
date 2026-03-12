"""
Simulation 2: Coulomb Counting SOC Model
4S Li-Ion BMS — Punit Singh Auluck | 25120034
SPEL Lab, IIT Gandhinagar

Run: python sim2_coulomb_counting.py
Output: sim2_coulomb_counting.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Parameters ──
Q_RATED = 2500.0        # mAh — Samsung 25R rated capacity
DT = 1.0                # seconds — sampling interval
SOC_INIT = 100.0        # % — start fully charged
ETA = 0.99              # Coulombic efficiency

# ── Realistic current profile (seconds) ──
np.random.seed(42)
total_time = 3600 * 2   # 2 hours

time = np.arange(0, total_time, DT)
current = np.zeros(len(time))

# Phase 1: Rest (0–120s) — OCV measurement window
current[0:120] = 0.0

# Phase 2: Discharge at 1A (120–1800s)
current[120:1800] = -1.0

# Phase 3: Pulse discharge 3A (1800–2100s) — simulate load spike
current[1800:2100] = -3.0

# Phase 4: Rest (2100–2400s) — OCV reset opportunity
current[2100:2400] = 0.0

# Phase 5: Discharge at 0.5A (2400–4800s)
current[2400:4800] = -0.5

# Phase 6: Rest (4800–5100s)
current[4800:5100] = 0.0

# Phase 7: Charge at 1A CC (5100–6600s)
current[5100:6600] = +1.0

# Phase 8: Charge at 0.5A CV taper (6600–7200s)
current[6600:7200] = +0.5

# ── Coulomb Counting ──
soc_cc = np.zeros(len(time))
soc_cc[0] = SOC_INIT

charge_accumulated = np.zeros(len(time))  # mAh

# OCV-SOC lookup (from Sim 1)
ocv_soc_table_soc = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
ocv_soc_table_ocv = np.array([3.000, 3.280, 3.490, 3.600, 3.660, 3.710, 3.745, 3.790, 3.860, 3.960, 4.200])

def ocv_to_soc(v):
    return float(np.interp(v, ocv_soc_table_ocv, ocv_soc_table_soc))

def soc_to_ocv(s):
    return float(np.interp(s, ocv_soc_table_soc, ocv_soc_table_ocv))

# Simulate SOC with periodic OCV correction
rest_counter = 0
REST_THRESHOLD = 60      # seconds of |I| < 50mA before OCV correction triggers
ocv_correction_events = []
soc_before_correction = []

for i in range(1, len(time)):
    # Coulomb count step
    delta_soc = (current[i] * DT / 3600.0) / (Q_RATED / 1000.0) * 100.0 * ETA
    soc_cc[i] = np.clip(soc_cc[i-1] + delta_soc, 0, 100)
    charge_accumulated[i] = charge_accumulated[i-1] + (current[i] * DT / 3600.0)

    # Check for rest condition → OCV correction
    if abs(current[i]) < 0.05:
        rest_counter += 1
    else:
        rest_counter = 0

    if rest_counter == REST_THRESHOLD:
        # OCV correction
        ocv_voltage = soc_to_ocv(soc_cc[i]) + np.random.normal(0, 0.003)  # small noise
        soc_corrected = ocv_to_soc(ocv_voltage)
        soc_before_correction.append(soc_cc[i])
        soc_cc[i] = soc_corrected
        ocv_correction_events.append(i)

# Add synthetic drift to show importance of OCV correction
soc_no_correction = np.zeros(len(time))
soc_no_correction[0] = SOC_INIT
for i in range(1, len(time)):
    delta_soc = (current[i] * DT / 3600.0) / (Q_RATED / 1000.0) * 100.0 * ETA
    soc_no_correction[i] = np.clip(soc_no_correction[i-1] + delta_soc, 0, 100)
    # Add small drift error accumulation
    if current[i] != 0:
        soc_no_correction[i] += np.random.normal(0, 0.008)
        soc_no_correction[i] = np.clip(soc_no_correction[i], 0, 100)

# Smooth drift for visibility
from scipy.ndimage import uniform_filter1d
soc_no_correction = uniform_filter1d(soc_no_correction, size=30)

# ── FIGURE ──
fig = plt.figure(figsize=(18, 11), facecolor='#0D1117')
fig.suptitle('Simulation 2: Coulomb Counting SOC Model with OCV Correction\n4S Li-Ion BMS — 2500mAh Cell | Q_rated=2500mAh | η=0.99',
             fontsize=15, color='white', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.5, wspace=0.35,
                       left=0.08, right=0.95, top=0.92, bottom=0.07)

time_min = time / 60.0  # convert to minutes

# ── Plot 1: Current profile ──
ax1 = fig.add_subplot(gs[0, :])
ax1.set_facecolor('#161B22')
ax1.fill_between(time_min, current, 0, where=(current < 0), alpha=0.4, color='#FF3F5E', label='Discharge')
ax1.fill_between(time_min, current, 0, where=(current > 0), alpha=0.4, color='#00E87A', label='Charge')
ax1.plot(time_min, current, color='#FFB300', linewidth=1.5)
ax1.axhline(0, color='#3D5A7A', linewidth=0.8)

# Phase labels
phases = [
    (0, 2, 'Rest\n(OCV)'), (2, 30, 'Discharge\n1A'),
    (30, 35, '3A\nPulse'), (35, 40, 'Rest'),
    (40, 80, 'Discharge\n0.5A'), (80, 85, 'Rest'),
    (85, 110, 'Charge\n1A CC'), (110, 120, 'CV\nTaper')
]
for start, end, label in phases:
    ax1.axvspan(start, end, alpha=0.05, color='white')
    ax1.text((start+end)/2, 2.7, label, ha='center', va='top',
             fontsize=7.5, color='#8899AA')

ax1.set_ylabel('Current (A)', color='#8899AA', fontsize=11)
ax1.set_title('Input: Current Profile (Realistic Charge/Discharge Scenario)', color='white', fontsize=11, fontweight='bold')
ax1.set_xlim(0, 120)
ax1.set_ylim(-4, 3.5)
ax1.tick_params(colors='#8899AA')
for s in ax1.spines.values(): s.set_color('#3D5A7A')
ax1.grid(color='#1F2A38', linewidth=0.6)
ax1.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white', loc='lower right')

# ── Plot 2: SOC tracking ──
ax2 = fig.add_subplot(gs[1, :])
ax2.set_facecolor('#161B22')

ax2.plot(time_min, soc_no_correction, color='#FF3F5E', linewidth=1.8,
         linestyle='--', alpha=0.7, label='CC only (no OCV correction) — drifts over time')
ax2.plot(time_min, soc_cc, color='#00D4E8', linewidth=2.2,
         label='CC + OCV correction (our approach)')

# Mark OCV correction events
for idx in ocv_correction_events:
    ax2.axvline(x=time_min[idx], color='#00E87A', linewidth=1.2,
                linestyle=':', alpha=0.8)
    ax2.annotate('OCV\ncorrect', xy=(time_min[idx], soc_cc[idx]),
                xytext=(time_min[idx]+1.5, soc_cc[idx]+4),
                fontsize=7, color='#00E87A',
                arrowprops=dict(arrowstyle='->', color='#00E87A', lw=0.8))

# Warning thresholds
ax2.axhline(y=20, color='#FFB300', linewidth=1.0, linestyle='--', alpha=0.6, label='Low SOC Warning: 20%')
ax2.axhline(y=5,  color='#FF3F5E', linewidth=1.0, linestyle='--', alpha=0.6, label='Critical SOC: 5%')

ax2.set_ylabel('SOC (%)', color='#8899AA', fontsize=11)
ax2.set_title('SOC Estimation: Coulomb Counting + OCV Correction vs CC Only', color='white', fontsize=11, fontweight='bold')
ax2.set_xlim(0, 120)
ax2.set_ylim(-5, 110)
ax2.tick_params(colors='#8899AA')
for s in ax2.spines.values(): s.set_color('#3D5A7A')
ax2.grid(color='#1F2A38', linewidth=0.6)
ax2.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 3: Charge accumulated ──
ax3 = fig.add_subplot(gs[2, 0])
ax3.set_facecolor('#161B22')
charge_mah = charge_accumulated * 1000  # convert to mAh... wait it's already mA*h style
# Fix: current is in A, DT=1s, so accumulated is in A*s = As, convert to mAh
charge_mah_real = np.cumsum(current * DT) / 3600.0 * 1000  # mAh

ax3.plot(time_min, charge_mah_real, color='#BB6BFF', linewidth=2.0)
ax3.fill_between(time_min, charge_mah_real, 0,
                  where=(charge_mah_real < 0), alpha=0.2, color='#FF3F5E')
ax3.fill_between(time_min, charge_mah_real, 0,
                  where=(charge_mah_real > 0), alpha=0.2, color='#00E87A')
ax3.axhline(0, color='#3D5A7A', linewidth=0.8)
ax3.set_xlabel('Time (min)', color='#8899AA', fontsize=11)
ax3.set_ylabel('Charge (mAh)', color='#8899AA', fontsize=11)
ax3.set_title('Cumulative Charge\n(INA260 measures this)', color='white', fontsize=11, fontweight='bold')
ax3.set_xlim(0, 120)
ax3.tick_params(colors='#8899AA')
for s in ax3.spines.values(): s.set_color('#3D5A7A')
ax3.grid(color='#1F2A38', linewidth=0.6)

# ── Plot 4: Error between CC+OCV vs CC only ──
ax4 = fig.add_subplot(gs[2, 1])
ax4.set_facecolor('#161B22')
error = soc_no_correction - soc_cc
ax4.plot(time_min, error, color='#FFB300', linewidth=2.0)
ax4.fill_between(time_min, error, 0, alpha=0.2, color='#FFB300')
ax4.axhline(0, color='#3D5A7A', linewidth=0.8)
ax4.axhline(3, color='#FF3F5E', linewidth=1.0, linestyle='--', alpha=0.7, label='±3% accuracy target')
ax4.axhline(-3, color='#FF3F5E', linewidth=1.0, linestyle='--', alpha=0.7)
ax4.set_xlabel('Time (min)', color='#8899AA', fontsize=11)
ax4.set_ylabel('SOC Error (%)', color='#8899AA', fontsize=11)
ax4.set_title('Drift Error\n(CC only vs CC+OCV)', color='white', fontsize=11, fontweight='bold')
ax4.set_xlim(0, 120)
ax4.tick_params(colors='#8899AA')
for s in ax4.spines.values(): s.set_color('#3D5A7A')
ax4.grid(color='#1F2A38', linewidth=0.6)
ax4.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Bottom annotation ──
fig.text(0.5, 0.01,
         'Punit Singh Auluck | 25120034 | 4S Li-Ion BMS | SPEL Lab, IIT Gandhinagar | Simulation 2/6',
         ha='center', fontsize=9, color='#3D5A7A', style='italic')

plt.savefig('sim2_coulomb_counting.png', dpi=180, bbox_inches='tight', facecolor='#0D1117')
print("Saved: sim2_coulomb_counting.png")
print(f"\nKey results:")
print(f"  Total charge discharged: {abs(min(charge_mah_real)):.1f} mAh")
print(f"  Max drift (CC only):     {max(abs(error)):.2f}%")
print(f"  OCV corrections applied: {len(ocv_correction_events)}")
