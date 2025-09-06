"""
F1 race simulator , which uses TKinter GUI and matplotlib for graphs.
This simulator uses the maths and physics logic from my first programme but it lets you run a simplified Formula 1 race with three tracks, tyre compounds,
and drivers. It tracks lap times, tyre wear, pit stops, tyre punctures, and displays results in a GUI
with charts and live leaderboard.This simulator focuses more on tyre strategy and is more like a game .However it uses the same physics and has the same concepts but an improved UI

"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import csv
import os
from datetime import datetime

# TRACK DEFINITIONS
# Each track has base lap times for each tyre compound (soft/medium/hard),  a wear rate modifier, track variation, and abrasion factor which influences tyre wear.(All specific to each track)
TRACKS = {
    "Monza": {
        "soft":    {"base_time": 81.5, "wear_rate": 0.025},
        "medium":  {"base_time": 82.1, "wear_rate": 0.018},
        "hard":    {"base_time": 83.0, "wear_rate": 0.012},
        "track_variation": 1.1,
        "abrasion": 1.0  
    },
    "Silverstone": {
        "soft":    {"base_time": 87.8, "wear_rate": 0.025},
        "medium":  {"base_time": 88.5, "wear_rate": 0.018},
        "hard":    {"base_time": 89.8, "wear_rate": 0.012},
        "track_variation": 1.2,
        "abrasion": 1.1
    },
    "Monaco": {
        "soft":    {"base_time": 73.2, "wear_rate": 0.025},
        "medium":  {"base_time": 74.3, "wear_rate": 0.018},
        "hard":    {"base_time": 75.0, "wear_rate": 0.012},
        "track_variation": 1.4,
        "abrasion": 0.8
    }
}

# Tyre class with physics from the first sim
class Tyre:
    def __init__(self, compound='soft', initial_temp=90, initial_pressure=2.2):
        self.compound = compound.lower()
        self.optimal_temp = 90         # Optimal temperature (oC)
        self.optimal_pressure = 2.2    # Optimal pressure (bar)
        self.puncture_threshold = 0.85 # Puncture threshold (wear > 85%)
        self.punctured = False
        
        # Compound-specific parameters
        if self.compound == 'soft':
            self.wear_rate = 0.025
            self.temp_sensitivity = 1.2
            self.base_grip = 1.1
        elif self.compound == 'medium':
            self.wear_rate = 0.018
            self.temp_sensitivity = 1.0
            self.base_grip = 1.0
        else:
            self.wear_rate = 0.012
            self.temp_sensitivity = 0.8
            self.base_grip = 0.9
        
        self.temperature = initial_temp
        self.pressure = initial_pressure
        self.wear = 0.0
        self.grip = self.base_grip
    
    def update(self, aggression=1.0, track_abrasion=1.0):
        if self.punctured:
            self.grip = 0.0
            return self.get_status()
        
        # Temperature update: warm up if cold, cool down if hot
        temp_change = (self.optimal_temp - self.temperature) * 0.1
        temp_change += aggression * 2.5
        self.temperature += temp_change * self.temp_sensitivity
        
        # Pressure adjustment based on temperature change
        self.pressure *= (1 + (self.temperature - self.optimal_temp) * 0.0035)
        
        # Wear increase: driven by base wear rate, aggression, track abrasion and sliding
        sliding_factor = max(0, 1.2 - self.grip) # sliding increases wear
        wear_increment = self.wear_rate * aggression * track_abrasion * (1 + sliding_factor)
        self.wear += wear_increment
        
        # Extra wear penalties for extreme temps
        if self.temperature > 120:
            self.wear += 0.02 * (self.temperature - 120) / 10
        elif self.temperature < 70:
            self.wear += 0.01 * (70 - self.temperature) / 10
        
        # Grip calculation based on wear, temp and pressure deviation
        wear_effect = max(0, 1 - self.wear)
        temp_diff = abs(self.temperature - self.optimal_temp)
        temp_effect = max(0.1, 1 - (temp_diff / 100) ** 2)
        pressure_diff = abs(self.pressure - self.optimal_pressure)
        pressure_effect = max(0.1, 1 - pressure_diff / 2)
        
        self.grip = self.base_grip * wear_effect * temp_effect * pressure_effect
        
        # Puncture if worn out
        if self.wear >= self.puncture_threshold:
            self.punctured = True
            self.grip = 0.0
        
        # Clamp wear at 1.0 max
        if self.wear > 1.0:
            self.wear = 1.0
        
        return self.get_status()
    
    def get_status(self):
        return {
            'compound': self.compound,
            'grip': round(self.grip, 3),
            'wear': round(self.wear * 100, 1),  # Percent
            'temperature': round(self.temperature, 1),
            'pressure': round(self.pressure, 3),
            'punctured': self.punctured
        }

# Lap and driver classes 
class LapData:
    def __init__(self, lap_number, lap_time, tire_wear, tire_compound, pit_stop, tire_puncture, temperature, pressure):
        self.lap_number = lap_number
        self.lap_time = lap_time
        self.tire_wear = tire_wear
        self.tire_compound = tire_compound
        self.pit_stop = pit_stop
        self.tire_puncture = tire_puncture
        self.temperature = temperature
        self.pressure = pressure

class Driver:
    def __init__(self, name, ai_skill=0.0, initial_tire='medium'):
        self.name = name
        self.ai_skill = ai_skill  
        self.lap_data = []
        self.total_time = 0.0
        self.current_lap = 0
        self.tyre = Tyre(compound=initial_tire)
        self.pit_stop_count = 0 
    
    def simulate_lap(self, sim, aggression=1.0):
        tyre = self.tyre
        compound = tyre.compound
        base_time = sim.tire_compounds[compound]['base_time']
        
        # User driver uses slider aggression, Aggression is random for the ai each lap 
        if self.name == "You":
            lap_aggression = aggression
        else:
            lap_aggression = 1.0 + random.uniform(-0.15, 0.15)
        
        track_abrasion = sim.get_track_abrasion()
        
        # Update tyre physics
        tyre_status = tyre.update(aggression=lap_aggression, track_abrasion=track_abrasion)
        
        # Grip affects lap time (more wear/less grip = slower)
        grip_factor = 1.0 + (1.0 - tyre_status['grip']) * 3.0  
        lap_time = base_time * grip_factor
        
        # Add randomness and AI skill adjusted each lap 
        lap_time += random.gauss(0, 0.2)
        lap_time += self.ai_skill
        
        # Huge penalty if tyre punctured
        if tyre_status['punctured']:
            lap_time += 20
        
        self.total_time += lap_time
        self.current_lap += 1
        
        self.lap_data.append(LapData(
            self.current_lap,
            lap_time,
            tyre_status['wear'],
            compound,
            False,  # pit stop is handled separately
            tyre_status['punctured'],
            tyre_status['temperature'],
            tyre_status['pressure']
        ))

class F1Simulator:
    def __init__(self, total_laps=50, initial_tire='medium', track_name='Silverstone'):
        self.total_laps = total_laps
        self.track_name = track_name
        self.current_lap = 0
        self.race_time = 0.0
        self.pit_stop_scheduled = False
        self.next_pit_compound = None
        self.drivers = []
        self.pit_events = [] 
        self.user_aggression = 1.0   
    
    @property
    def tire_compounds(self):
        compounds = TRACKS[self.track_name]
        grip_values = {'soft': 1.0, 'medium': 0.95, 'hard': 0.85} 
        return {k: {**v, 'grip': grip_values[k]} for k,v in compounds.items() if k in grip_values}
    
    def get_track_variation(self):
        return TRACKS[self.track_name]['track_variation']
    
    def get_track_abrasion(self):
        return TRACKS[self.track_name].get('abrasion', 1.0)
    
    def simulate_next_lap(self):
        if self.current_lap >= self.total_laps:
            return False, "Race completed!"
        warning_msg = ""
        pit_msg = ""

        # Perform pit stop if scheduled for user
        if self.pit_stop_scheduled:
            user_driver = next(d for d in self.drivers if d.name == "You")
            new_compound = self.next_pit_compound if self.next_pit_compound else random.choice(['soft', 'medium', 'hard'])
            user_driver.tyre = Tyre(compound=new_compound)
            user_driver.pit_stop_count += 1
            self.pit_stop_scheduled = False
            self.next_pit_compound = None
            pit_msg = f"You pitted for {new_compound.upper()} tires on Lap {self.current_lap + 1}"
            self.pit_events.append(pit_msg)

        # Simulate user lap with aggression slider value
        user_driver = next(d for d in self.drivers if d.name == "You")
        user_driver.simulate_lap(self, aggression=self.user_aggression)

        # Simulate AI laps with random aggression
        for driver in self.drivers:
            if driver.name != "You" and driver.current_lap < self.total_laps:
                # AI simple pit logic
                if driver.tyre.wear > 0.80 or driver.tyre.punctured:
                    new_compound = random.choice(['soft', 'medium', 'hard'])
                    driver.tyre = Tyre(compound=new_compound)
                    driver.pit_stop_count += 1
                    self.pit_events.append(f"{driver.name} pitted for {new_compound.upper()} tires on Lap {self.current_lap + 1}")
                driver.simulate_lap(self)
        
        # Update race state
        self.current_lap += 1
        self.race_time = max(driver.total_time for driver in self.drivers)
        
        # Check user tyre warnings
        tyre_status = user_driver.tyre.get_status()
        if tyre_status['punctured']:
            warning_msg = "TIRE PUNCTURE! Lap time severely affected. Pit stop recommended."
        elif tyre_status['wear'] > 90:
            warning_msg = "Critical tire wear! Consider making a pit stop soon."
        elif pit_msg:
            warning_msg = pit_msg
        return True, warning_msg
    
    def manual_pit_stop(self, compound):
        if self.current_lap == 0:
            return "Race not started yet."
        if self.pit_stop_scheduled:
            return "Pit stop already scheduled."
        self.pit_stop_scheduled = True
        self.next_pit_compound = compound
        return f"Manual pit stop scheduled for next lap with {compound.upper()} tires."

class F1SimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F1 Race Simulator")
        self.root.geometry("1300x800")
        # colour and font scheme
        self.colors = {
            'bg': '#1e1e2d',
            'frame_bg': '#2c2c3c',
            'fg': 'white',
            'accent_soft': '#ff5555',
            'accent_medium': '#ffff00',
            'accent_hard': '#ffffff',
            'button_bg': '#2c2c3c',
            'button_fg': 'white'
        }
        self.font_header = ('Arial', 24, 'bold')
        self.font_title = ('Arial', 12)
        self.font_status = ('Arial', 14)
        self.font_text = ('Arial', 10)
        self.sim = F1Simulator()
        self.driver_names = ['You', 'Verstappen', 'Norris', 'Leclerc', 'Hamilton', 'Sainz', 'Piastri', 'Alonso']
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        # Style configurations
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['button_bg'], foreground=self.colors['button_fg'])
        style.configure('Header.TLabel', font=self.font_header, background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Title.TLabel', font=self.font_title, background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'])
        
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="F1 Race Simulator", style='Header.TLabel').pack()
        ttk.Label(header_frame, text="F1 Race strategy Simulator , Made by Imaad Javaid", style='Title.TLabel').pack()
        
        # Controls
        control_frame = ttk.LabelFrame(main_frame, text="Race Control", style='TLabelframe')
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Total Laps:").grid(row=0, column=0, padx=5, pady=5)
        self.laps_var = tk.IntVar(value=50)
        laps_spin = ttk.Spinbox(control_frame, from_=1, to=100, textvariable=self.laps_var, width=10)
        laps_spin.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Tire Compound:").grid(row=0, column=2, padx=5, pady=5)
        self.tire_var = tk.StringVar(value='medium')
        tire_combo = ttk.Combobox(control_frame, textvariable=self.tire_var,
                                  values=('soft', 'medium', 'hard'), state='readonly')
        tire_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Track:").grid(row=0, column=4, padx=5, pady=5)
        self.track_var = tk.StringVar(value='Silverstone')
        track_combo = ttk.Combobox(control_frame, textvariable=self.track_var,
                                  values=list(TRACKS.keys()), state='readonly')
        track_combo.grid(row=0, column=5, padx=5, pady=5)
        
        # Aggression slider
        ttk.Label(control_frame, text="Your Aggression:").grid(row=0, column=6, padx=5, pady=5)
        self.aggression_var = tk.DoubleVar(value=1.0)
        self.aggr_slider = tk.Scale(control_frame, from_=0.5, to=1.5, orient=tk.HORIZONTAL, resolution=0.05,
                                    variable=self.aggression_var, width=25, length=120,
                                    bg=self.colors['bg'], fg=self.colors['fg'], highlightthickness=0)
        self.aggr_slider.grid(row=0, column=7, padx=5, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Race", command=self.start_race)
        self.start_btn.grid(row=0, column=8, padx=5, pady=5)
        self.reset_btn = ttk.Button(control_frame, text="Reset", command=self.reset_race, state=tk.DISABLED)
        self.reset_btn.grid(row=0, column=9, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Laps to Progress:").grid(row=0, column=10, padx=5, pady=5)
        self.laps_to_progress_var = tk.IntVar(value=1)
        self.laps_slider = tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                    variable=self.laps_to_progress_var, width=25, length=120,
                                    bg=self.colors['bg'], fg=self.colors['fg'], highlightthickness=0)
        self.laps_slider.grid(row=0, column=11, padx=5, pady=5)
        
        self.next_btn = ttk.Button(control_frame, text="Next Lap", command=self.next_lap, state=tk.DISABLED)
        self.next_btn.grid(row=0, column=12, padx=5, pady=5)
        
        self.pitstop_btn = ttk.Button(control_frame, text="Manual Pit Stop", command=self.manual_pit_stop, state=tk.DISABLED)
        self.pitstop_btn.grid(row=0, column=13, padx=5, pady=5)
        
        self.export_btn = ttk.Button(control_frame, text="Export to CSV", command=self.export_csv, state=tk.DISABLED)
        self.export_btn.grid(row=0, column=14, padx=5, pady=5)
        
        # Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Current Status", style='TLabelframe')
        status_frame.pack(fill=tk.X, pady=10)
        
        def make_label(text, var, col):
            ttk.Label(status_frame, text=text).grid(row=0, column=col, padx=10, pady=5)
            ttk.Label(status_frame, textvariable=var, font=self.font_status).grid(row=1, column=col, padx=10, pady=5)
        
        self.lap_time_var = tk.StringVar(value="--:--.---")
        self.tire_status_var = tk.StringVar(value="MEDIUM")
        self.tire_cond_var = tk.StringVar(value="Fresh")
        self.status_var = tk.StringVar(value="Waiting to start...")
        self.current_track_var = tk.StringVar(value=self.track_var.get())
        
        make_label("Last Lap Time:", self.lap_time_var, 0)
        make_label("Current Tires:", self.tire_status_var, 1)
        make_label("Tire Condition (Wear% | Temp oC | Pressure):", self.tire_cond_var, 2)
        ttk.Label(status_frame, text="Race Status:").grid(row=0, column=3, padx=10, pady=5)
        ttk.Label(status_frame, textvariable=self.status_var, font=self.font_status, foreground='red').grid(row=1, column=3, padx=10, pady=5)
        make_label("Track:", self.current_track_var, 4)
        
        # Race Frame
        race_frame = ttk.LabelFrame(main_frame, text="Race Status", style='TLabelframe')
        race_frame.pack(fill=tk.X, pady=10)
        
        def make_race_label(text, var, col):
            ttk.Label(race_frame, text=text).grid(row=0, column=col, padx=10, pady=5)
            ttk.Label(race_frame, textvariable=var, font=self.font_status).grid(row=1, column=col, padx=10, pady=5)
        
        self.lap_var = tk.StringVar(value="0/50")
        self.time_var = tk.StringVar(value="0:00.000")
        self.best_lap_var = tk.StringVar(value="--:--.---")
        self.wear_var = tk.StringVar(value="0.0%")
        
        make_race_label("Current Lap:", self.lap_var, 0)
        make_race_label("Race Time:", self.time_var, 1)
        make_race_label("Best Lap Time:", self.best_lap_var, 2)
        make_race_label("Tire Wear:", self.wear_var, 3)
        
        # Leaderboard Frame
        leaderboard_frame = ttk.LabelFrame(main_frame, text="Live Leaderboard", style='TLabelframe')
        leaderboard_frame.pack(fill=tk.X, pady=10)
        self.leaderboard = ttk.Treeview(leaderboard_frame, columns=("position", "name", "laps", "time", "compound", "pitstops"),
                                       show="headings", selectmode="none", height=len(self.driver_names))
        for col, w in zip(("position", "name", "laps", "time", "compound", "pitstops"), (60, 120, 80, 120, 100, 80)):
            self.leaderboard.heading(col, text=col.title())
            self.leaderboard.column(col, width=w, anchor=tk.CENTER)
        self.leaderboard.pack(fill=tk.X, pady=5)
        
        # Pit Stop Events Box
        pit_frame = ttk.LabelFrame(main_frame, text="Pit Stop Events", style='TLabelframe')
        pit_frame.pack(fill=tk.X, pady=10)
        self.pit_text = tk.Text(pit_frame, height=4, wrap="word", bg=self.colors['frame_bg'], fg=self.colors['fg'], state='disabled')
        self.pit_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(pit_frame, orient="vertical", command=self.pit_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pit_text['yscrollcommand'] = scrollbar.set
        
        # Charts
        chart_frame = ttk.Frame(main_frame, style='TFrame')
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(16, 6))
        self.fig.subplots_adjust(hspace=0.3)
        self.fig.set_facecolor(self.colors['bg'])
        self.ax1.set_facecolor(self.colors['frame_bg'])
        self.ax2.set_facecolor(self.colors['frame_bg'])
        for ax in [self.ax1, self.ax2]:
            ax.tick_params(colors=self.colors['fg'])
            ax.xaxis.label.set_color(self.colors['fg'])
            ax.yaxis.label.set_color(self.colors['fg'])
            ax.title.set_color(self.colors['fg'])
            for spine in ax.spines.values():
                spine.set_color(self.colors['fg'])
            ax.grid(True, color='#444444')
        self.ax1.set_title('Lap Times', color=self.colors['fg'])
        self.ax1.set_xlabel('Lap Number', color=self.colors['fg'])
        self.ax1.set_ylabel('Time (seconds)', color=self.colors['fg'])
        self.ax2.set_title('Tire Wear', color=self.colors['fg'])
        self.ax2.set_xlabel('Lap Number', color=self.colors['fg'])
        self.ax2.set_ylabel('Percentage', color=self.colors['fg'])
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def start_race(self):
        self.sim = F1Simulator(total_laps=self.laps_var.get(),
                               initial_tire=self.tire_var.get(),
                               track_name=self.track_var.get())
        self.sim.user_aggression = self.aggression_var.get()  # Set initial aggression from slider
        self.current_track_var.set(self.track_var.get())
        self.sim.drivers = [Driver(name, ai_skill=0.0 if name == "You" else random.uniform(-1.2, 1.0),
                                  initial_tire=self.tire_var.get())
                            for name in self.driver_names]
        self.start_btn.state(['disabled'])
        self.reset_btn.state(['!disabled'])
        self.next_btn.state(['!disabled'])
        self.pitstop_btn.state(['!disabled'])
        self.export_btn.state(['disabled'])
        self.status_var.set("Race started! Click 'Next Lap' to progress")
        self.sim.pit_events.clear()
        self.pit_text.config(state='normal')
        self.pit_text.delete("1.0", tk.END)
        self.pit_text.config(state='disabled')
        self.update_ui()
        self.update_charts()
        self.update_leaderboard()
    
    def reset_race(self):
        self.sim = F1Simulator(total_laps=self.laps_var.get(),
                               initial_tire=self.tire_var.get(),
                               track_name=self.track_var.get())
        self.current_track_var.set(self.track_var.get())
        self.sim.drivers = [Driver(name, ai_skill=0.0 if name == "You" else random.uniform(-1.2, 1.0),
                                  initial_tire=self.tire_var.get())
                            for name in self.driver_names]
        self.start_btn.state(['!disabled'])
        self.reset_btn.state(['disabled'])
        self.next_btn.state(['disabled'])
        self.pitstop_btn.state(['disabled'])
        self.export_btn.state(['disabled'])
        self.status_var.set("Race reset")
        self.sim.pit_events.clear()
        self.pit_text.config(state='normal')
        self.pit_text.delete("1.0", tk.END)
        self.pit_text.config(state='disabled')
        self.update_ui()
        self.update_charts()
        self.update_leaderboard()
    
    def next_lap(self):
        self.sim.user_aggression = self.aggression_var.get()  
        laps_to_run = self.laps_to_progress_var.get()
        for _ in range(laps_to_run):
            cont, status = self.sim.simulate_next_lap()
            self.status_var.set(status)
            if not cont:
                self.next_btn.state(['disabled'])
                self.pitstop_btn.state(['disabled'])
                self.export_btn.state(['!disabled'])
                self.status_var.set("Race completed! Export your results")
                break
        self.update_ui()
        self.update_charts()
        self.update_leaderboard()
        self.update_pit_log()
    
    def manual_pit_stop(self):
        compound = self.manual_pit_stop_dialog()
        if not compound:
            return
        result = self.sim.manual_pit_stop(compound)
        self.status_var.set(result)
    
    def manual_pit_stop_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Pit Stop")
        dialog.geometry("300x120")
        dialog.configure(bg=self.colors['bg'])
        tk.Label(dialog, text="Choose tire compound for next pit stop:", bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=10)
        compound_var = tk.StringVar(value=self.sim.drivers[0].tyre.compound)
        combo = ttk.Combobox(dialog, values=['soft', 'medium', 'hard'], textvariable=compound_var, state='readonly')
        combo.pack(pady=5)
        result = {"compound": None}
        def on_ok():
            result["compound"] = compound_var.get()
            dialog.destroy()
        def on_cancel():
            dialog.destroy()
        btn_frame = tk.Frame(dialog, bg=self.colors['bg'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=5)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window()
        return result["compound"]
    # Improved export to csv function ,Every CSV file is unique as it uses a Timestamp
    def export_csv(self):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(downloads_folder, f"f1_simulation_your_laps_{timestamp}.csv")
        user_driver = next((d for d in self.sim.drivers if d.name == "You"), None)
        if not user_driver or not user_driver.lap_data:
            messagebox.showinfo("Export Failed", "No lap data available for your driver. Run the simulation first!")
            return
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Lap', 'Lap Time', 'Tire Compound', 'Tire Wear %', 'Temperature (oC)', 'Pressure (bar)', 'Pit Stop', 'Tire Puncture', 'Track'])
                for lap in user_driver.lap_data:
                    writer.writerow([
                        lap.lap_number,
                        f"{lap.lap_time:.3f}",
                        lap.tire_compound,
                        f"{lap.tire_wear:.1f}",
                        f"{lap.temperature}",
                        f"{lap.pressure}",
                        "Yes" if lap.pit_stop else "No",
                        "Yes" if lap.tire_puncture else "No",
                        self.sim.track_name
                    ])
            messagebox.showinfo("Download Complete", f"Your driver lap data saved to:\n{filename}")
            self.status_var.set(f"CSV exported to: {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV.\n{e}")
            self.status_var.set("Error exporting CSV.")
    
    def update_ui(self):
        self.lap_var.set(f"{self.sim.current_lap}/{self.sim.total_laps}")
        self.time_var.set(self.format_time(self.sim.race_time))
        self.current_track_var.set(self.sim.track_name)
        user_driver = next((d for d in self.sim.drivers if d.name == "You"), None)
        if user_driver and user_driver.lap_data:
            last_lap = user_driver.lap_data[-1]
            self.lap_time_var.set(f"{last_lap.lap_time:.3f}s")
            self.tire_status_var.set(user_driver.tyre.compound.upper())
            tyre_status = user_driver.tyre.get_status()
            self.wear_var.set(f"{tyre_status['wear']:.1f}%")
            self.tire_cond_var.set(f"{tyre_status['wear']:.1f}% | {tyre_status['temperature']}oC | {tyre_status['pressure']} bar")
            best_lap_time = min(lap.lap_time for lap in user_driver.lap_data)
            self.best_lap_var.set(f"{best_lap_time:.3f}s")
        else:
            self.lap_time_var.set("--:--.---")
            self.tire_status_var.set(self.tire_var.get().upper())
            self.wear_var.set("0.0%")
            self.tire_cond_var.set("Fresh")
            self.best_lap_var.set("--:--.---")
    
    def update_charts(self):
        user_driver = next((d for d in self.sim.drivers if d.name == "You"), None)
        if not user_driver or not user_driver.lap_data:
            self.ax1.clear()
            self.ax2.clear()
            self.ax1.set_title('Lap Times', color=self.colors['fg'])
            self.ax1.set_xlabel('Lap Number', color=self.colors['fg'])
            self.ax1.set_ylabel('Time (seconds)', color=self.colors['fg'])
            self.ax2.set_title('Tire Wear', color=self.colors['fg'])
            self.ax2.set_xlabel('Lap Number', color=self.colors['fg'])
            self.ax2.set_ylabel('Percentage', color=self.colors['fg'])
            self.canvas.draw()
            return
        laps = [lap.lap_number for lap in user_driver.lap_data]
        times = [lap.lap_time for lap in user_driver.lap_data]
        wear = [lap.tire_wear for lap in user_driver.lap_data]
        compounds = [lap.tire_compound for lap in user_driver.lap_data]
        compound_colors = {
            "soft": self.colors['accent_soft'],
            "medium": self.colors['accent_medium'],
            "hard": self.colors['accent_hard']
        }
        
        self.ax1.clear()
        self.ax2.clear()
        for ax in [self.ax1, self.ax2]:
            ax.tick_params(colors=self.colors['fg'])
            ax.xaxis.label.set_color(self.colors['fg'])
            ax.yaxis.label.set_color(self.colors['fg'])
            ax.title.set_color(self.colors['fg'])
            for spine in ax.spines.values():
                spine.set_color(self.colors['fg'])
            ax.grid(True, color='#444444')
        start_idx = 0
        last_compound = compounds[0]
        for i in range(1, len(laps)+1):
            if i == len(laps) or compounds[i] != last_compound:
                self.ax1.plot(
                    laps[start_idx:i],
                    times[start_idx:i],
                    'o-',
                    color=compound_colors[last_compound],
                    label=last_compound.capitalize()
                )
                self.ax2.plot(
                    laps[start_idx:i],
                    wear[start_idx:i],
                    'o-',
                    color=compound_colors[last_compound]
                )
                if i < len(laps):
                    last_compound = compounds[i]
                    start_idx = i
        self.ax1.set_title('Lap Times', color=self.colors['fg'])
        self.ax1.set_xlabel('Lap Number', color=self.colors['fg'])
        self.ax1.set_ylabel('Time (seconds)', color=self.colors['fg'])
        handles, labels = self.ax1.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax1.legend(by_label.values(), by_label.keys())
        self.ax2.set_title('Tire Wear', color=self.colors['fg'])
        self.ax2.set_xlabel('Lap Number', color=self.colors['fg'])
        self.ax2.set_ylabel('Percentage', color=self.colors['fg'])
        self.canvas.draw()
    
    def update_leaderboard(self):
        self.leaderboard.delete(*self.leaderboard.get_children())
        standings = []
        for drv in self.sim.drivers:
            laps = drv.current_lap
            tstr = self.format_time(drv.total_time)
            compound = drv.tyre.compound.upper()
            standings.append((drv.name, laps, drv.total_time, tstr, compound, drv.pit_stop_count))
        standings.sort(key=lambda x: (-x[1], x[2]))
        for idx, (name, laps, t, tstr, compound, pits) in enumerate(standings, 1):
            self.leaderboard.insert(
                "", "end",
                values=(idx, name, laps, tstr, compound, pits),
                tags=("you",) if name == "You" else ()
            )
        self.leaderboard.tag_configure("you", background="#ffff88")
    
    def update_pit_log(self):
        if self.sim.pit_events:
            self.pit_text.config(state='normal')
            for event in self.sim.pit_events:
                self.pit_text.insert(tk.END, event + "\n")
            self.sim.pit_events.clear()
            self.pit_text.see(tk.END)
            self.pit_text.config(state='disabled')
    
    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:06.3f}"

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    app = F1SimulatorApp(root)
    root.mainloop()

