# Race-Strategy-Simulator
A more in depth **Python** application which once more use **Tkinter & Matplotlib**, to model Formula 1 tyre behaviour, lap times, and pit stop strategy.I Utilized the physics from my **Tyre Degradation Simulator** and made a strategy simulator which allows you to choose the track and "race" against 7 other drivers.

---

##  Features

- **Interactive GUI (Tkinter)**
  - Dropdown menus for tyre compound, track, and driver aggression
  - Live race simulation with lap-by-lap output
  - Graphs showing lap times and tire wear  

- **Physics-Based Tyre Model**
  - Grip influenced by wear, temperature, and pressure
  - Compound-specific degradation rates (Soft/Medium/Hard)
  - Aggression slider to simulate push vs conserve driving styles

- **Strategy & Failures**
  - Automatic lap time calculation
  - Punctures if tyre wear exceeds 85%
  - Pit stop modelling with time loss

- **Data Export & Visualisation**
  - Export full race data to CSV
  - Plots tyre grip vs laps with Matplotlib

---

## 🔧 Physics & Real-World Link

- **Tyre Wear**
  - Softs: fastest laps, degrade quickly
  - Mediums: balanced pace vs longevity
  - Hards: slow but consistent

- **Temperature Effects**
  - Peak grip at ~90 °C
  - Cold tyres (<70 °C) → underperformance
  - Hot tyres (>120 °C) → grip loss

- **Pressure Effects**
  - FIA baseline: 2.2 bar
  - Deviations (under/over inflation) penalise grip

- **Track Influence**
  - Base lap time derived from F1 telemetry
  - Abrasiveness (e.g., Silverstone high, Monaco low)
  - Random factors (traffic, wind, driver error)

- **Punctures**
  - Wear >85% → chance of puncture
  - Lap impact = +20s time loss (historical failures)

- **Aggression Factor**
  - High aggression = faster laps, more wear
  - Low aggression = slower, longer tyre life

---

## Screenshots

<img width="1900" height="993" alt="image" src="https://github.com/user-attachments/assets/4c0a4eeb-497e-4a39-90b6-fa3b7b8ed556" />



## How to Run

1) Clone this repository:  [https://github.com/IJF1/Race-Strategy-Simulator.git](https://github.com/IJF1/Race-Strategy-Simulator.git)
2) Install requirements , MATPLOTLIB may be required - Copy this (pip install matplotlib) into CMD ,TKinter is pre-installed on Python
3) Run the simulator
4) Please refer to the short video in this repository on how to use the application
5) When a CSV file is saved it is saved to downloads as f1_simulation_your_laps_{timestamp}.csv , The CSV file contains lap, compound, grip, wear, temperature, pressure, punctured and lap_time for the simulation that has been run


---

## Skills Demonstrated

- **Applied Physics & Engineering**  
  - Modelled tyre grip degradation using physics-inspired equations  
  - Simulated thermal, pressure, and wear effects on performance  

- **Software Development**  
  - Built a full GUI using Tkinter for user interaction  
  - Designed modular Python classes for tyres, stints, and tracks  

- **Data Analysis & Visualisation**  
  - Exported stint data into CSV for post-race analysis  
  - Visualised grip vs laps with Matplotlib, mirroring F1 telemetry plots  

- **Race Strategy Thinking**  
  - Implemented pit stop losses, tyre compound choices, and puncture risk  
  - Explored how aggression vs conservation changes stint life  

- **Problem-Solving & Simulation**  
  - Balanced realism with simplification for computational efficiency  
  - Created reproducible scenarios to test strategic outcomes  


---

## Future Improvements

- More detailed fuel load modelling
- Integration of DRS/ERS for lap time deltas
- Weather conditions (wet tyres, rain transitions)
- Track-specific degradation curves based on FIA data

---
## Author

**Imaad Javaid**  
 [Imaad.Javaid@outlook.com](mailto:Imaad.Javaid@outlook.com) 

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/imaad-javaid-854941369)  
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/IJF1)

---

 *This project is part of my **F1 Simulation Portfolio**, showcasing my passion for motorsport engineering and ability to apply physics + coding to realistic race scenarios.*



