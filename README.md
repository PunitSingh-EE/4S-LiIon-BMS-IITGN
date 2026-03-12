# 4S-LiIon-BMS-IITGN
Discrete component-based 4S Li-Ion Battery Management System | ESP32 + ADS1115 + INA260 | SPEL Lab, IIT Gandhinagar
# 4S Li-Ion Battery Management System (BMS)

**Student:** Punit Singh Auluck | Roll No: 25120034  
**Supervisor:** Prof. Pallavi Bhardwaj  
**Lab:** Smart Power Electronics Laboratory (SPEL), IIT Gandhinagar  
**Status:** 🔄 In Progress — Hardware Build Phase

---

## Overview

A discrete component-based 4S Li-Ion BMS designed without 
dedicated BMS ICs — built for full understanding of every 
subsystem from sensing to protection to SOC estimation.

**Pack:** 4S Li-Ion | 12.0V–16.8V | ~10Wh

---

## System Architecture

| Subsystem | Component | Details |
|---|---|---|
| Voltage Sensing | 2× ADS1115 | 16-bit I²C, PGA optimised per channel |
| Current Sensing | INA260 | Internal 2mΩ shunt, 15A, 0.15% accuracy |
| Temperature | 2× NTC 10kΩ β=3950 | Beta equation firmware |
| Protection | 2× IRLZ44N | Back-to-back, OV/UV/OC/OT |
| Cell Balancing | 4× 2N7002 + 47Ω | Passive top-balancing, 89mA |
| MCU | ESP32 DevKit v1 | I²C master + SPI + WiFi |
| Display | ILI9341 2.4" TFT | Real-time dashboard |

---

## Protection Thresholds

| Fault | Threshold | Action |
|---|---|---|
| Overvoltage | >4.25V/cell | Open CHG MOSFET |
| Undervoltage | <2.9V/cell | Open DSG MOSFET |
| Overcurrent | >5A | Open DSG MOSFET |
| Overtemperature | >60°C | Open both MOSFETs |
| Low temperature | <0°C | Block charging |

---

## SOC Algorithm

- **Primary:** Coulomb Counting — integrates INA260 current
- **Correction:** OCV lookup when |I| < 50mA for >60s
- **SOH:** Capacity fade per cycle + internal resistance tracking
- **Persistence:** ESP32 NVS flash

---

## Repository Structure
```
4S-LiIon-BMS-IITGN/
│
├── simulations/
│   ├── sim1_ocv_soc.py
│   ├── sim2_coulomb_counting.py
│   ├── sim3_ntc_temperature.py
│   ├── sim4_voltage_divider.py
│   ├── sim5_passive_balancing.py
│   └── sim6_mosfet_thermal.py
│
├── firmware/            # Coming soon
├── hardware/            # Coming soon
└── README.md
```

---

## Simulation Results

| # | Simulation | Key Finding |
|---|---|---|
| 1 | OCV–SOC Curve | Flat region 30–70% — CC required |
| 2 | Coulomb Counting + OCV | SOC drift <3% with correction |
| 3 | NTC Characterization | Temperature resolution 0.04°C |
| 4 | Voltage Divider Monte Carlo | Calibration → <0.71mV error |
| 5 | Passive Balancing | 90 min convergence, 47Ω safe |
| 6 | MOSFET Thermal | Tj = 52°C @ 5A with heatsink |

---

## Timeline

| Milestone | Date | Status |
|---|---|---|
| Architecture & simulations | Mar 2026 | ✅ Complete |
| Component procurement | Mar 12, 2026 | ✅ Ordered |
| Hardware build | Mar–Apr 2026 | 🔄 Pending |
| Firmware development | Apr 2026 | 🔄 Pending |
| Testing & validation | Apr 2026 | 🔄 Pending |

---

## References

1. G. L. Plett, *Battery Management Systems Vol. 1*, Artech House, 2015
2. Linear Technology, LTC6804 Datasheet, 2014
3. Texas Instruments, INA260 Datasheet, SBOS598C, 2015
4. Infineon Technologies, IRLZ44N Datasheet, PD91268D
