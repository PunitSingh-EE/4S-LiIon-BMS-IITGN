"""
Simulation 3: NTC Thermistor — Beta Equation Characterization
4S Li-Ion BMS — Punit Singh Auluck | 25120034
SPEL Lab, IIT Gandhinagar

Run: python sim3_ntc_temperature.py
Output: sim3_ntc_temperature.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── NTC Parameters ──
R0    = 10000.0     # Ohms at T0
T0    = 298.15      # K (25°C reference)
BETA  = 3950.0      # K — datasheet value
R_PULLUP = 10000.0  # Ohms — pullup resistor
VCC   = 3.3         # V — supply voltage
ADC_BITS = 16       # ADS1115
ADC_MAX  = 2**ADC_BITS - 1  # 65535

# ── Temperature range ──
T_celsius = np.linspace(-20, 80, 1000)
T_kelvin  = T_celsius + 273.15

# ── Beta equation: R_NTC(T) ──
R_ntc = R0 * np.exp(BETA * (1.0/T_kelvin - 1.0/T0))

# ── Voltage divider output: V_adc = VCC * R_NTC / (R_pullup + R_NTC) ──
V_adc = VCC * R_ntc / (R_PULLUP + R_ntc)

# ── ADC raw counts ──
# ADS1115 with PGA = ±4.096V, so LSB = 4.096/32768
PGA_RANGE = 4.096
adc_raw = (V_adc / PGA_RANGE) * 32768

# ── Inverse: ADC counts → Temperature (firmware algorithm) ──
def adc_to_temperature(adc_count):
    """Firmware function: convert ADS1115 reading to temperature in °C"""
    v = (adc_count / 32768.0) * PGA_RANGE
    r_ntc = R_PULLUP * v / (VCC - v)
    t_kelvin = 1.0 / (1.0/T0 + (1.0/BETA) * np.log(r_ntc / R0))
    return t_kelvin - 273.15

# Verify round-trip accuracy
T_recovered = adc_to_temperature(adc_raw)
error_celsius = T_recovered - T_celsius

# ── Sensitivity: dV/dT ──
dv_dt = np.gradient(V_adc, T_celsius)  # V/°C

# ── Protection thresholds ──
CHARGE_STOP_HIGH  = 45.0   # °C — stop charging above this
DISCHARGE_STOP    = 60.0   # °C — stop discharging above this
CHARGE_STOP_LOW   = 0.0    # °C — stop charging below this
OPTIMAL_LOW       = 15.0
OPTIMAL_HIGH      = 35.0

def temp_to_vadc(t):
    tk = t + 273.15
    r = R0 * np.exp(BETA * (1.0/tk - 1.0/T0))
    return VCC * r / (R_PULLUP + r)

# ── FIGURE ──
fig = plt.figure(figsize=(18, 12), facecolor='#0D1117')
fig.suptitle('Simulation 3: NTC Thermistor (10kΩ, β=3950) Characterization\nTemperature Sensing for Li-Ion BMS — Voltage Divider + ADS1115',
             fontsize=15, color='white', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38,
                       left=0.07, right=0.96, top=0.92, bottom=0.08)

# ── Plot 1: R vs T ──
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#161B22')
ax1.semilogy(T_celsius, R_ntc, color='#FF3F5E', linewidth=2.2)
ax1.axvline(25, color='#FFB300', linestyle='--', linewidth=1.2, alpha=0.7, label='R=10kΩ @ 25°C')
ax1.scatter([25], [10000], color='#FFB300', s=80, zorder=5)
ax1.annotate('10kΩ @ 25°C', xy=(25, 10000), xytext=(32, 15000),
             fontsize=9, color='#FFB300',
             arrowprops=dict(arrowstyle='->', color='#FFB300', lw=0.8))
ax1.set_xlabel('Temperature (°C)', color='#8899AA', fontsize=11)
ax1.set_ylabel('NTC Resistance (Ω) — log scale', color='#8899AA', fontsize=11)
ax1.set_title('R vs T\n(Beta Equation)', color='white', fontsize=11, fontweight='bold')
ax1.tick_params(colors='#8899AA')
for s in ax1.spines.values(): s.set_color('#3D5A7A')
ax1.grid(color='#1F2A38', linewidth=0.6, which='both')
ax1.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 2: V_adc vs T (what ADS1115 actually sees) ──
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#161B22')

# Shade zones
ax2.axvspan(-20, CHARGE_STOP_LOW, alpha=0.15, color='#4A9EFF', label='No-charge zone (<0°C)')
ax2.axvspan(OPTIMAL_LOW, OPTIMAL_HIGH, alpha=0.10, color='#00E87A', label='Optimal zone (15–35°C)')
ax2.axvspan(CHARGE_STOP_HIGH, 80, alpha=0.15, color='#FFB300', label='No-charge zone (>45°C)')
ax2.axvspan(DISCHARGE_STOP, 80, alpha=0.15, color='#FF3F5E', label='No-discharge (>60°C)')

ax2.plot(T_celsius, V_adc, color='#00D4E8', linewidth=2.5)

# Mark protection threshold voltages
for t_thresh, label, col in [
    (CHARGE_STOP_LOW,   '0°C',  '#4A9EFF'),
    (CHARGE_STOP_HIGH,  '45°C', '#FFB300'),
    (DISCHARGE_STOP,    '60°C', '#FF3F5E'),
]:
    v_thresh = temp_to_vadc(t_thresh)
    ax2.axhline(v_thresh, color=col, linewidth=1.0, linestyle=':', alpha=0.8)
    ax2.annotate(f'{label} → {v_thresh:.3f}V', xy=(t_thresh, v_thresh),
                xytext=(t_thresh+4, v_thresh+0.05),
                fontsize=8, color=col,
                arrowprops=dict(arrowstyle='->', color=col, lw=0.7))

ax2.set_xlabel('Temperature (°C)', color='#8899AA', fontsize=11)
ax2.set_ylabel('V_ADC (V)', color='#8899AA', fontsize=11)
ax2.set_title('ADC Voltage vs Temp\n(Voltage Divider Output)', color='white', fontsize=11, fontweight='bold')
ax2.tick_params(colors='#8899AA')
for s in ax2.spines.values(): s.set_color('#3D5A7A')
ax2.grid(color='#1F2A38', linewidth=0.6)
ax2.legend(fontsize=7.5, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 3: Sensitivity dV/dT ──
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor('#161B22')
ax3.plot(T_celsius, abs(dv_dt) * 1000, color='#BB6BFF', linewidth=2.0)  # mV/°C
ax3.fill_between(T_celsius, abs(dv_dt) * 1000, 0, alpha=0.15, color='#BB6BFF')

# ADS1115 resolution line
lsb_mv = (PGA_RANGE / 32768.0) * 1000
ax3.axhline(lsb_mv, color='#00E87A', linewidth=1.5, linestyle='--',
            label=f'ADS1115 LSB = {lsb_mv:.3f} mV/LSB\n(16-bit @ ±4.096V PGA)')
ax3.set_xlabel('Temperature (°C)', color='#8899AA', fontsize=11)
ax3.set_ylabel('|dV/dT| (mV/°C)', color='#8899AA', fontsize=11)
ax3.set_title('Sensor Sensitivity\n|dV/dT|', color='white', fontsize=11, fontweight='bold')
ax3.tick_params(colors='#8899AA')
for s in ax3.spines.values(): s.set_color('#3D5A7A')
ax3.grid(color='#1F2A38', linewidth=0.6)
ax3.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# Min sensitivity → max temperature error
min_sens = abs(dv_dt[500]) * 1000   # at ~30°C
temp_resolution = lsb_mv / min_sens
ax3.annotate(f'Min sensitivity @ 30°C:\n{min_sens:.2f} mV/°C\n→ T resolution: {temp_resolution:.2f}°C',
             xy=(30, min_sens), xytext=(40, min_sens + 2),
             fontsize=8.5, color='#FFB300',
             arrowprops=dict(arrowstyle='->', color='#FFB300', lw=0.8))

# ── Plot 4: Firmware round-trip accuracy ──
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_facecolor('#161B22')
ax4.plot(T_celsius, error_celsius * 1000, color='#00E87A', linewidth=2.0)
ax4.fill_between(T_celsius, error_celsius * 1000, 0, alpha=0.15, color='#00E87A')
ax4.axhline(0, color='#3D5A7A', linewidth=0.8)
ax4.set_xlabel('Temperature (°C)', color='#8899AA', fontsize=11)
ax4.set_ylabel('Error (m°C)', color='#8899AA', fontsize=11)
ax4.set_title('Beta Eq. Round-trip Error\n(ADC → T → compare)', color='white', fontsize=11, fontweight='bold')
ax4.tick_params(colors='#8899AA')
for s in ax4.spines.values(): s.set_color('#3D5A7A')
ax4.grid(color='#1F2A38', linewidth=0.6)
ax4.annotate(f'Max error: {max(abs(error_celsius*1000)):.4f} m°C\n(numerical precision only)',
             xy=(0, 0), xytext=(20, max(abs(error_celsius*1000))*0.5),
             fontsize=9, color='#00E87A')

# ── Plot 5: Lookup table used in firmware ──
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_facecolor('#161B22')

fw_temps = np.arange(-20, 85, 5)
fw_vadc  = np.array([temp_to_vadc(t) for t in fw_temps])

ax5.plot(T_celsius, V_adc, color='#00D4E8', linewidth=1.5, alpha=0.5, linestyle='--', label='Continuous')
ax5.scatter(fw_temps, fw_vadc, color='#FFB300', s=60, zorder=5, label='Firmware lookup points')
ax5.step(fw_temps, fw_vadc, color='#FFB300', linewidth=1.5, where='mid', alpha=0.7)

ax5.set_xlabel('Temperature (°C)', color='#8899AA', fontsize=11)
ax5.set_ylabel('V_ADC (V)', color='#8899AA', fontsize=11)
ax5.set_title('Firmware Lookup\n(5°C step, linear interp)', color='white', fontsize=11, fontweight='bold')
ax5.tick_params(colors='#8899AA')
for s in ax5.spines.values(): s.set_color('#3D5A7A')
ax5.grid(color='#1F2A38', linewidth=0.6)
ax5.legend(fontsize=9, facecolor='#161B22', edgecolor='#3D5A7A', labelcolor='white')

# ── Plot 6: Protection threshold summary ──
ax6 = fig.add_subplot(gs[1, 2])
ax6.set_facecolor('#161B22')
ax6.axis('off')

thresholds = [
    ('< 0°C',    f'{temp_to_vadc(0):.3f}V',   'Block Charging',       '#4A9EFF'),
    ('> 45°C',   f'{temp_to_vadc(45):.3f}V',  'Block Charging',       '#FFB300'),
    ('> 60°C',   f'{temp_to_vadc(60):.3f}V',  'Block Discharge',      '#FF3F5E'),
    ('> 70°C',   f'{temp_to_vadc(70):.3f}V',  'Emergency Cutoff',     '#FF0000'),
    ('15–35°C',  f'{temp_to_vadc(15):.3f}–{temp_to_vadc(35):.3f}V', 'Optimal Zone', '#00E87A'),
]

ax6.text(0.5, 0.97, 'Protection Thresholds', ha='center', va='top',
         fontsize=12, color='white', fontweight='bold', transform=ax6.transAxes)
ax6.text(0.5, 0.88, 'V_ADC comparison values for ESP32 firmware',
         ha='center', va='top', fontsize=9, color='#8899AA', transform=ax6.transAxes)

for i, (temp, vadc, action, col) in enumerate(thresholds):
    y = 0.75 - i * 0.14
    ax6.add_patch(plt.Rectangle((0.02, y-0.04), 0.96, 0.12,
                                 facecolor=col, alpha=0.15, transform=ax6.transAxes))
    ax6.text(0.08, y+0.02, temp,   fontsize=11, color=col, fontweight='bold', transform=ax6.transAxes)
    ax6.text(0.38, y+0.02, vadc,   fontsize=10, color='#FFB300', transform=ax6.transAxes)
    ax6.text(0.62, y+0.02, action, fontsize=10, color='white', transform=ax6.transAxes)

fig.text(0.5, 0.01,
         'Punit Singh Auluck | 25120034 | 4S Li-Ion BMS | SPEL Lab, IIT Gandhinagar | Simulation 3/6',
         ha='center', fontsize=9, color='#3D5A7A', style='italic')

plt.savefig('sim3_ntc_temperature.png', dpi=180, bbox_inches='tight', facecolor='#0D1117')
print("Saved: sim3_ntc_temperature.png")
print(f"\n── NTC Threshold Voltages (for firmware comparison) ──")
for temp, vadc, action, _ in thresholds:
    print(f"  {temp:8s} → V_ADC = {vadc}  → {action}")
print(f"\n── Temperature Resolution ──")
print(f"  ADS1115 LSB       = {lsb_mv:.4f} mV")
print(f"  Sensitivity@25°C  = {abs(dv_dt[500])*1000:.3f} mV/°C")
print(f"  T resolution@25°C = {lsb_mv / (abs(dv_dt[500])*1000):.4f} °C")
