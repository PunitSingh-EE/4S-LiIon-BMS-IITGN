"""
Simulation 6: IRLZ44N MOSFET Thermal Analysis
4S Li-Ion BMS — Punit Singh Auluck | 25120034
SPEL Lab, IIT Gandhinagar

Run: python sim6_mosfet_thermal.py
Output: sim6_mosfet_thermal.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── IRLZ44N Datasheet Parameters ──
RDS_10V   = 0.022   # Ω @ Vgs=10V, Tj=25°C
RDS_5V    = 0.025   # Ω @ Vgs=5V
RDS_4V    = 0.035   # Ω @ Vgs=4V
# Interpolated @ 3.3V
RDS_3V3   = 0.050   # Ω @ Vgs=3.3V (conservative estimate from datasheet curves)

VGS_TH_MIN = 1.0    # V
VGS_TH_MAX = 2.0    # V

# Thermal parameters
R_TH_JC   = 1.4    # °C/W — junction to case
R_TH_CS   = 0.5    # °C/W — case to heatsink (with thermal paste)
R_TH_SA_NO_HS  = 62.0   # °C/W — case to ambient, no heatsink (from datasheet RθJA - RθJC)
R_TH_SA_WITH_HS = 10.0  # °C/W — typical small clip-on heatsink

T_AMBIENT = 25.0   # °C

# ── Rds(on) temperature dependency ──
# From Fig 4 of datasheet: Rds(on) normalized vs Tj
# At 25°C: 1.0x, at 100°C: ~1.8x, at 175°C: ~3.0x
T_junction_range = np.linspace(25, 175, 100)
rds_norm = 1.0 + (T_junction_range - 25) / (175 - 25) * 2.0  # linear approx to datasheet curve

# ── Figure ──
fig = plt.figure(figsize=(18, 12), facecolor='#0D1117')
fig.suptitle('Simulation 6: IRLZ44N MOSFET Thermal Analysis\n4S BMS Protection Switch | Vgs=3.3V (ESP32) | TO-220 Package',
             fontsize=15, color='white', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.38,
                       left=0.07, right=0.96, top=0.92, bottom=0.08)

# ── Plot 1: Rds(on) vs Vgs ──
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#161B22')

vgs_vals = np.array([2.5, 3.0, 3.3, 4.0, 5.0, 10.0])
rds_vals = np.array([0.120, 0.070, 0.050, 0.035, 0.025, 0.022])

vgs_fine = np.linspace(2.0, 11.0, 300)
rds_interp = np.interp(vgs_fine, vgs_vals, rds_vals)

ax1.semilogy(vgs_fine, rds_interp * 1000, color='#00D4E8', linewidth=2.5)
ax1.scatter(vgs_vals, rds_vals * 1000, color='#FFB300', s=80, zorder=5, label='Datasheet points')

# Mark our operating point
ax1.axvline(3.3, color='#00E87A', linewidth=1.5, linestyle='--', label='ESP32 Vgs=3.3V')
ax1.scatter([3.3], [50], color='#FF3F5E', s=120, zorder=6, marker='*',
            label=f'Our op. point: ~50mΩ')
ax1.annotate('~50mΩ\n@ 3.3V', xy=(3.3, 50), xytext=(5, 60),
             fontsize=10, color='#FF3F5E',
             arrowprops=dict(arrowstyle='->', color='#FF3F5E', lw=1.0))

ax1.axvline(10, color='#3D5A7A', linewidth=1.0, linestyle=':', alpha=0.7, label='Datasheet spec @ 10V')
ax1.set_xlabel('Vgs (V)', color='#8899AA', fontsize=11)
ax1.set_ylabel('Rds(on) (mΩ) — log scale', color='#8899AA', fontsize=11)
ax1.set_title('Rds(on) vs Gate Voltage\nIRLZ44N @ 25°C', color='white', fontsize=11, fontweight='bold')
ax1.tick_params(colors='#8899AA')
for s in ax1.spines.values(): s.set_color('#3D5A7A')
ax1.grid(color='#1F2A38', linewidth=0.6, which='both')
ax1.legend(fontsize=8.5, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 2: Power loss vs current ──
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#161B22')

I_range = np.linspace(0, 15, 200)
P_25C   = I_range**2 * RDS_3V3           # at 25°C
P_100C  = I_range**2 * RDS_3V3 * 1.8    # at 100°C junction (hot)

ax2.plot(I_range, P_25C,  color='#00E87A', linewidth=2.2, label='Tj=25°C (cold start)')
ax2.plot(I_range, P_100C, color='#FF3F5E', linewidth=2.2, label='Tj=100°C (hot, Rds×1.8)')

# Mark our demo current
for I_demo, label, col in [(3, '3A demo', '#00D4E8'), (5, '5A max', '#FFB300')]:
    P_d = I_demo**2 * RDS_3V3
    P_h = I_demo**2 * RDS_3V3 * 1.8
    ax2.scatter([I_demo, I_demo], [P_d, P_h], color=col, s=80, zorder=5)
    ax2.axvline(I_demo, color=col, linewidth=1.0, linestyle=':', alpha=0.6)
    ax2.annotate(f'{label}\n{P_d:.2f}W–{P_h:.2f}W',
                xy=(I_demo, P_h), xytext=(I_demo+0.5, P_h+0.3),
                fontsize=8.5, color=col,
                arrowprops=dict(arrowstyle='->', color=col, lw=0.7))

ax2.axhline(5, color='#BB6BFF', linewidth=1.2, linestyle='--',
            label='Safe limit w/ heatsink (~5W)')
ax2.set_xlabel('Drain Current (A)', color='#8899AA', fontsize=11)
ax2.set_ylabel('Power Dissipation (W)', color='#8899AA', fontsize=11)
ax2.set_title('MOSFET Power Loss\nvs Current', color='white', fontsize=11, fontweight='bold')
ax2.set_ylim(0, 12)
ax2.tick_params(colors='#8899AA')
for s in ax2.spines.values(): s.set_color('#3D5A7A')
ax2.grid(color='#1F2A38', linewidth=0.6)
ax2.legend(fontsize=8.5, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 3: Junction temperature vs current ──
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor('#161B22')

R_total_no_hs  = R_TH_JC + R_TH_SA_NO_HS
R_total_with_hs = R_TH_JC + R_TH_CS + R_TH_SA_WITH_HS

Tj_no_hs   = T_AMBIENT + I_range**2 * RDS_3V3 * R_total_no_hs
Tj_with_hs = T_AMBIENT + I_range**2 * RDS_3V3 * R_total_with_hs

ax3.plot(I_range, Tj_no_hs,   color='#FF3F5E', linewidth=2.2, label='No heatsink')
ax3.plot(I_range, Tj_with_hs, color='#00E87A', linewidth=2.2, label='With clip-on heatsink')

ax3.axhline(150, color='#FF0000', linewidth=1.5, linestyle='--',
            alpha=0.8, label='Max Tj = 175°C')
ax3.axhline(100, color='#FFB300', linewidth=1.2, linestyle='--',
            alpha=0.7, label='Warning: 100°C')
ax3.axhline(T_AMBIENT, color='#3D5A7A', linewidth=0.8)

# Safe current with heatsink
I_safe = np.interp(150, Tj_with_hs, I_range)
ax3.axvline(I_safe, color='#00E87A', linewidth=1.2, linestyle=':',
            alpha=0.8)
ax3.annotate(f'Safe up to\n{I_safe:.0f}A with HS', xy=(I_safe, 150),
             xytext=(I_safe-4, 130), fontsize=9, color='#00E87A',
             arrowprops=dict(arrowstyle='->', color='#00E87A', lw=0.8))

ax3.set_xlabel('Drain Current (A)', color='#8899AA', fontsize=11)
ax3.set_ylabel('Junction Temperature (°C)', color='#8899AA', fontsize=11)
ax3.set_title('Junction Temp vs Current\n(Rds=50mΩ @ 3.3V)', color='white', fontsize=11, fontweight='bold')
ax3.set_ylim(20, 200)
ax3.tick_params(colors='#8899AA')
for s in ax3.spines.values(): s.set_color('#3D5A7A')
ax3.grid(color='#1F2A38', linewidth=0.6)
ax3.legend(fontsize=8.5, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 4: Rds(on) temperature derating ──
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_facecolor('#161B22')
ax4.plot(T_junction_range, rds_norm * RDS_3V3 * 1000, color='#BB6BFF', linewidth=2.2)
ax4.fill_between(T_junction_range, rds_norm * RDS_3V3 * 1000, RDS_3V3 * 1000,
                  alpha=0.15, color='#BB6BFF')
ax4.axhline(RDS_3V3 * 1000, color='#3D5A7A', linewidth=0.8, linestyle='--')
ax4.axvline(100, color='#FFB300', linewidth=1.2, linestyle='--', alpha=0.7,
            label=f'Rds @ 100°C = {RDS_3V3*1.8*1000:.0f}mΩ')
ax4.annotate(f'{RDS_3V3*1000:.0f}mΩ\n@ 25°C', xy=(25, RDS_3V3*1000),
             xytext=(60, RDS_3V3*1000*0.6),
             fontsize=9, color='#00E87A',
             arrowprops=dict(arrowstyle='->', color='#00E87A', lw=0.8))
ax4.set_xlabel('Junction Temperature (°C)', color='#8899AA', fontsize=11)
ax4.set_ylabel('Rds(on) (mΩ)', color='#8899AA', fontsize=11)
ax4.set_title('Rds(on) Temperature\nDerating', color='white', fontsize=11, fontweight='bold')
ax4.tick_params(colors='#8899AA')
for s in ax4.spines.values(): s.set_color('#3D5A7A')
ax4.grid(color='#1F2A38', linewidth=0.6)
ax4.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 5: Thermal resistance network ──
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_facecolor('#161B22')
ax5.axis('off')

ax5.text(0.5, 0.97, 'Thermal Resistance Network',
         ha='center', va='top', fontsize=12, color='white', fontweight='bold',
         transform=ax5.transAxes)
ax5.text(0.5, 0.87, 'Junction → Case → Heatsink → Ambient',
         ha='center', fontsize=9, color='#8899AA', transform=ax5.transAxes)

nodes = [
    (0.15, 'T_junction', 'Tj'),
    (0.38, 'T_case',     'Tc'),
    (0.61, 'T_heatsink', 'Ths'),
    (0.84, 'T_ambient',  'Ta=25°C'),
]
resistors = [
    (0.15, 0.38, 'RθJC\n1.4°C/W'),
    (0.38, 0.61, 'RθCS\n0.5°C/W'),
    (0.61, 0.84, 'RθSA\n10°C/W'),
]

for x, name, short in nodes:
    ax5.add_patch(plt.Circle((x, 0.60), 0.06, facecolor='#1D4D7B',
                               edgecolor='#00D4E8', linewidth=1.5,
                               transform=ax5.transAxes, clip_on=False))
    ax5.text(x, 0.60, short, ha='center', va='center',
             fontsize=8.5, color='white', fontweight='bold', transform=ax5.transAxes)
    ax5.text(x, 0.50, name, ha='center', fontsize=7.5, color='#8899AA',
             transform=ax5.transAxes)

for x1, x2, label in resistors:
    mid = (x1 + x2) / 2
    ax5.annotate('', xy=(x2-0.06, 0.60), xytext=(x1+0.06, 0.60),
                 arrowprops=dict(arrowstyle='->', color='#FFB300', lw=2.0),
                 xycoords='axes fraction', textcoords='axes fraction')
    ax5.text(mid, 0.70, label, ha='center', fontsize=8.5, color='#FFB300',
             transform=ax5.transAxes)

# Show calculation at 5A
P_5A = 5**2 * RDS_3V3 * 1.8   # worst case hot
Tj_5A = T_AMBIENT + P_5A * (R_TH_JC + R_TH_CS + R_TH_SA_WITH_HS)
Tc_5A = T_AMBIENT + P_5A * (R_TH_CS + R_TH_SA_WITH_HS)

calc_lines = [
    f'At I=5A, Rds=90mΩ (hot): P = {P_5A:.2f}W',
    f'Tj = 25 + {P_5A:.2f} × (1.4+0.5+10) = {Tj_5A:.0f}°C  ✅',
    f'Tc = 25 + {P_5A:.2f} × (0.5+10) = {Tc_5A:.0f}°C',
    f'Max rated Tj = 175°C — margin: {175-Tj_5A:.0f}°C  ✅ SAFE',
]
for i, line in enumerate(calc_lines):
    col = '#00E87A' if '✅' in line else 'white'
    ax5.text(0.05, 0.36 - i*0.09, line, fontsize=9, color=col,
             transform=ax5.transAxes,
             bbox=dict(boxstyle='round', facecolor='#0D1117', edgecolor='#3D5A7A', alpha=0.6) if i==3 else None)

# ── Plot 6: Summary table ──
ax6 = fig.add_subplot(gs[1, 2])
ax6.set_facecolor('#161B22')
ax6.axis('off')

ax6.text(0.5, 0.97, 'Design Verification Summary',
         ha='center', va='top', fontsize=12, color='white', fontweight='bold',
         transform=ax6.transAxes)

summary = [
    ('Vgs operating',      '3.3V (ESP32)',     'Logic-level: ✅'),
    ('Vgs threshold',      '1.0–2.0V',         'Fully on @ 3.3V ✅'),
    ('Rds(on) @ 3.3V',     '~50mΩ',            'Datasheet interpolated'),
    ('Rds(on) @ 100°C',    '~90mΩ',            '1.8× thermal derating'),
    ('P_loss @ 3A',        '0.81W (hot)',       'Well within TO-220 ✅'),
    ('P_loss @ 5A',        '2.25W (hot)',       'Heatsink needed ✅'),
    ('Tj @ 5A + HS',       f'{Tj_5A:.0f}°C',   f'Margin to 175°C: {175-Tj_5A:.0f}°C ✅'),
    ('Vds max',            '55V',               f'{55/16.8:.1f}× margin over 16.8V ✅'),
    ('Id rating',          '47A',               f'{47/5:.0f}× margin over 5A ✅'),
    ('Heatsink',           'TO-220 clip-on',    'Required for 5A operation'),
]
for i, (param, value, verdict) in enumerate(summary):
    y = 0.84 - i * 0.087
    col = '#00E87A' if '✅' in verdict else '#FFB300'
    bg = '#1A2A3A' if i % 2 == 0 else '#0F1A28'
    ax6.add_patch(plt.Rectangle((0.0, y-0.04), 1.0, 0.08,
                                  facecolor=bg, transform=ax6.transAxes))
    ax6.text(0.02, y,  param,   fontsize=8.5, color='#8899AA', transform=ax6.transAxes)
    ax6.text(0.40, y,  value,   fontsize=8.5, color='#FFB300', transform=ax6.transAxes)
    ax6.text(0.62, y,  verdict, fontsize=8.5, color=col,       transform=ax6.transAxes)

fig.text(0.5, 0.01,
         'Punit Singh Auluck | 25120034 | 4S Li-Ion BMS | SPEL Lab, IIT Gandhinagar | Simulation 6/6',
         ha='center', fontsize=9, color='#3D5A7A', style='italic')

plt.savefig('sim6_mosfet_thermal.png', dpi=180, bbox_inches='tight', facecolor='#0D1117')
print("Saved: sim6_mosfet_thermal.png")
print(f"\n── MOSFET Thermal Verification @ 5A ──")
print(f"  Rds(on) @ 3.3V, 25°C : {RDS_3V3*1000:.0f} mΩ")
print(f"  Rds(on) @ 3.3V, 100°C: {RDS_3V3*1.8*1000:.0f} mΩ (1.8× derating)")
print(f"  P_loss @ 5A (hot)    : {5**2 * RDS_3V3 * 1.8:.2f} W")
print(f"  Tj @ 5A with heatsink: {Tj_5A:.0f}°C (limit: 175°C, margin: {175-Tj_5A:.0f}°C) ✅")
