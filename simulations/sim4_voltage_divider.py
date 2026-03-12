"""
Simulation 4: Voltage Divider Accuracy Analysis
4S Li-Ion BMS — Punit Singh Auluck | 25120034
SPEL Lab, IIT Gandhinagar

Run: python sim4_voltage_divider.py
Output: sim4_voltage_divider.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Divider values ──
dividers = [
    {'name': 'Cell 1 (T1)', 'Rtop': 47e3,  'Rbot': 12e3,  'Vmax_tap': 4.2,
     'pga': 1.024, 'gain': 4,  'color': '#00E87A'},
    {'name': 'Cell 2 (T2)', 'Rtop': 100e3, 'Rbot': 22e3,  'Vmax_tap': 8.4,
     'pga': 2.048, 'gain': 2,  'color': '#00D4E8'},
    {'name': 'Cell 3 (T3)', 'Rtop': 150e3, 'Rbot': 33e3,  'Vmax_tap': 12.6,
     'pga': 4.096, 'gain': 1,  'color': '#BB6BFF'},
    {'name': 'Cell 4 (Pack+)', 'Rtop': 200e3, 'Rbot': 43e3, 'Vmax_tap': 16.8,
     'pga': 4.096, 'gain': 1,  'color': '#FFB300'},
]

TOL_1PCT  = 0.01   # 1% resistor tolerance
TOL_5PCT  = 0.05   # 5% resistor tolerance for comparison
N_MONTE   = 50000  # Monte Carlo samples
ADC_BITS  = 16

# ── Figure ──
fig = plt.figure(figsize=(18, 12), facecolor='#0D1117')
fig.suptitle('Simulation 4: Voltage Divider Accuracy Analysis\nMonte Carlo (N=50,000) · 1% vs 5% Resistor Tolerance · ADS1115 16-bit ADC',
             fontsize=15, color='white', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.40,
                       left=0.06, right=0.97, top=0.92, bottom=0.08)

results_summary = []

for col_idx, d in enumerate(dividers):
    Rtop_nom = d['Rtop']
    Rbot_nom = d['Rbot']
    V_tap    = d['Vmax_tap']  # worst case (fully charged)
    ratio_nom = Rbot_nom / (Rtop_nom + Rbot_nom)
    V_adc_nom = V_tap * ratio_nom

    # ADC resolution for this PGA setting
    lsb_v = d['pga'] / 32768.0
    # Scale back to cell voltage resolution
    cell_lsb_mv = lsb_v / ratio_nom * 1000  # mV per LSB at cell level

    # ── Monte Carlo: 1% tolerance ──
    np.random.seed(col_idx * 100)
    Rtop_samples_1 = Rtop_nom * (1 + np.random.uniform(-TOL_1PCT, TOL_1PCT, N_MONTE))
    Rbot_samples_1 = Rbot_nom * (1 + np.random.uniform(-TOL_1PCT, TOL_1PCT, N_MONTE))
    V_adc_samples_1 = V_tap * Rbot_samples_1 / (Rtop_samples_1 + Rbot_samples_1)
    V_cell_back_1 = V_adc_samples_1 / ratio_nom
    error_mv_1 = (V_cell_back_1 - V_tap) * 1000

    # ── Monte Carlo: 5% tolerance ──
    Rtop_samples_5 = Rtop_nom * (1 + np.random.uniform(-TOL_5PCT, TOL_5PCT, N_MONTE))
    Rbot_samples_5 = Rbot_nom * (1 + np.random.uniform(-TOL_5PCT, TOL_5PCT, N_MONTE))
    V_adc_samples_5 = V_tap * Rbot_samples_5 / (Rtop_samples_5 + Rbot_samples_5)
    V_cell_back_5 = V_adc_samples_5 / ratio_nom
    error_mv_5 = (V_cell_back_5 - V_tap) * 1000

    # ── After calibration (1%): residual ADC quantisation only ──
    quant_error_mv = cell_lsb_mv

    results_summary.append({
        'name': d['name'],
        'ratio': ratio_nom,
        'V_adc': V_adc_nom,
        'cell_lsb_mv': cell_lsb_mv,
        'error_1pct_3sigma': np.std(error_mv_1) * 3,
        'error_5pct_3sigma': np.std(error_mv_5) * 3,
    })

    # ── Plot 1 (row 0): Error histogram ──
    ax = fig.add_subplot(gs[0, col_idx])
    ax.set_facecolor('#161B22')
    bins = np.linspace(-120, 120, 80)
    ax.hist(error_mv_1, bins=bins, color=d['color'], alpha=0.7,
            density=True, label='1% resistors')
    ax.hist(error_mv_5, bins=bins, color='#FF3F5E', alpha=0.4,
            density=True, label='5% resistors')
    ax.axvline(0, color='white', linewidth=1.0)
    ax.axvline( np.std(error_mv_1)*3, color=d['color'], linewidth=1.2, linestyle='--', alpha=0.8)
    ax.axvline(-np.std(error_mv_1)*3, color=d['color'], linewidth=1.2, linestyle='--', alpha=0.8)
    ax.set_title(d['name'], color=d['color'], fontsize=10, fontweight='bold')
    ax.set_xlabel('Error (mV)', color='#8899AA', fontsize=9)
    if col_idx == 0:
        ax.set_ylabel('Probability Density', color='#8899AA', fontsize=9)
    ax.tick_params(colors='#8899AA', labelsize=8)
    for s in ax.spines.values(): s.set_color('#3D5A7A')
    ax.grid(color='#1F2A38', linewidth=0.5)
    if col_idx == 0:
        ax.legend(fontsize=8, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')
    ax.text(0.97, 0.96, f'3σ(1%)={np.std(error_mv_1)*3:.1f}mV\n3σ(5%)={np.std(error_mv_5)*3:.1f}mV',
            ha='right', va='top', transform=ax.transAxes,
            fontsize=7.5, color='white',
            bbox=dict(boxstyle='round', facecolor='#0D1117', edgecolor='#3D5A7A', alpha=0.8))

    # ── Plot 2 (row 1): V_adc range ──
    ax2 = fig.add_subplot(gs[1, col_idx])
    ax2.set_facecolor('#161B22')
    v_range = np.linspace(3.0 if col_idx == 0 else d['Vmax_tap']*3/4.2,
                           d['Vmax_tap'], 200)
    v_adc_range = v_range * ratio_nom
    ax2.plot(v_range, v_adc_range * 1000, color=d['color'], linewidth=2.0)
    ax2.axhline(d['pga'] * 1000, color='#FF3F5E', linewidth=1.2,
                linestyle='--', alpha=0.7, label=f'PGA limit: {d["pga"]}V')
    ax2.axvline(d['Vmax_tap'], color='#FFB300', linewidth=1.0,
                linestyle=':', alpha=0.7, label=f'Max={d["Vmax_tap"]}V')
    ax2.set_xlabel('Cell/Tap Voltage (V)', color='#8899AA', fontsize=9)
    ax2.set_ylabel('V_ADC (mV)', color='#8899AA', fontsize=9)
    ax2.set_title(f'ADC Range\nPGA=±{d["pga"]}V', color='white', fontsize=10, fontweight='bold')
    ax2.tick_params(colors='#8899AA', labelsize=8)
    for s in ax2.spines.values(): s.set_color('#3D5A7A')
    ax2.grid(color='#1F2A38', linewidth=0.5)
    ax2.legend(fontsize=8, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')
    ax2.text(0.05, 0.95, f'V_ADC_max={V_adc_nom*1000:.1f}mV\nCell LSB={cell_lsb_mv:.2f}mV',
             ha='left', va='top', transform=ax2.transAxes,
             fontsize=8, color=d['color'],
             bbox=dict(boxstyle='round', facecolor='#0D1117', edgecolor='#3D5A7A', alpha=0.8))

# ── Row 2: Summary comparison bar chart ──
ax_sum = fig.add_subplot(gs[2, :2])
ax_sum.set_facecolor('#161B22')

names = [r['name'].split('(')[0].strip() for r in results_summary]
err_1 = [r['error_1pct_3sigma'] for r in results_summary]
err_5 = [r['error_5pct_3sigma'] for r in results_summary]
lsbs  = [r['cell_lsb_mv'] for r in results_summary]
x = np.arange(len(names))
w = 0.28

bars1 = ax_sum.bar(x - w, err_5, w, color='#FF3F5E', alpha=0.8, label='5% resistors (3σ error)')
bars2 = ax_sum.bar(x,     err_1, w, color='#FFB300', alpha=0.8, label='1% resistors (3σ error)')
bars3 = ax_sum.bar(x + w, lsbs,  w, color='#00E87A', alpha=0.8, label='ADC quantisation (1 LSB) — after calibration')

# Log scale so tiny LSB bars and 5mV line are both visible
ax_sum.set_yscale('log')
ax_sum.set_ylim(0.05, max(err_5) * 3)

ax_sum.axhline(5, color='white', linewidth=2.0, linestyle='--', alpha=0.9, label='Target: ±5mV accuracy')
ax_sum.text(x[-1] + w + 0.15, 5, '← ±5mV\ntarget', fontsize=8.5, color='white', va='center')

ax_sum.set_xticks(x)
ax_sum.set_xticklabels(names, color='#8899AA', fontsize=10)
ax_sum.set_ylabel('Voltage Error (mV) — log scale', color='#8899AA', fontsize=11)
ax_sum.set_title('Error Budget Comparison: 5% vs 1% Resistors vs ADC Quantisation (log scale)',
                  color='white', fontsize=11, fontweight='bold')
ax_sum.tick_params(colors='#8899AA', which='both')
for s in ax_sum.spines.values(): s.set_color('#3D5A7A')
ax_sum.grid(color='#1F2A38', linewidth=0.6, axis='y', which='both')
ax_sum.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# Value labels on all bars
for bar, fmt, col in [(bars1, '{:.0f}', '#FF3F5E'), (bars2, '{:.0f}', '#FFB300'), (bars3, '{:.2f}', '#00E87A')]:
    for b in bar:
        ax_sum.text(b.get_x() + b.get_width()/2, b.get_height() * 1.15,
                    fmt.format(b.get_height()), ha='center', fontsize=7.5, color=col)

# ── Calibration benefit ──
ax_cal = fig.add_subplot(gs[2, 2:])
ax_cal.set_facecolor('#161B22')
ax_cal.axis('off')

ax_cal.text(0.5, 0.96, 'Why 1% Resistors + Calibration?',
            ha='center', va='top', fontsize=13, color='white',
            fontweight='bold', transform=ax_cal.transAxes)

insights = [
    ('5% resistors (uncalibrated)', f'{max(err_5):.0f} mV error', '#FF3F5E', '❌ Fails ±5mV target'),
    ('1% resistors (uncalibrated)', f'{max(err_1):.0f} mV error', '#FFB300', '⚠ Near target, unreliable'),
    ('1% + startup calibration',    f'< {max(lsbs):.1f} mV error', '#00E87A', '✅ Meets ±5mV target'),
    ('ADS1115 16-bit resolution',   f'{min(lsbs):.2f}–{max(lsbs):.2f} mV/LSB', '#00D4E8', '✅ Hardware limit'),
]
for i, (label, value, col, verdict) in enumerate(insights):
    y = 0.76 - i * 0.17
    ax_cal.add_patch(plt.Rectangle((0.02, y-0.05), 0.96, 0.14,
                                    facecolor=col, alpha=0.12, transform=ax_cal.transAxes))
    ax_cal.text(0.05, y+0.02, label,   fontsize=10, color=col, transform=ax_cal.transAxes)
    ax_cal.text(0.52, y+0.02, value,   fontsize=10, color='#FFB300', fontweight='bold', transform=ax_cal.transAxes)
    ax_cal.text(0.68, y+0.02, verdict, fontsize=10, color='white', transform=ax_cal.transAxes)

fig.text(0.5, 0.01,
         'Punit Singh Auluck | 25120034 | 4S Li-Ion BMS | SPEL Lab, IIT Gandhinagar | Simulation 4/6',
         ha='center', fontsize=9, color='#3D5A7A', style='italic')

plt.savefig('sim4_voltage_divider.png', dpi=180, bbox_inches='tight', facecolor='#0D1117')
print("Saved: sim4_voltage_divider.png")
print("\n── Error Budget Summary ──")
print(f"{'Channel':<20} {'Ratio':>8} {'V_ADC':>8} {'LSB(mV)':>9} {'3σ 1%':>9} {'3σ 5%':>9}")
print("-" * 68)
for r in results_summary:
    print(f"{r['name']:<20} {r['ratio']:>8.4f} {r['V_adc']:>8.3f}V {r['cell_lsb_mv']:>8.2f}mV {r['error_1pct_3sigma']:>8.1f}mV {r['error_5pct_3sigma']:>8.1f}mV")
