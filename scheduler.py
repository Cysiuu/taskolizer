import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime

class Process:
    def __init__(self, pid, burst_time, arrival_time=0, priority=0):
        self.pid = pid
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.arrival_time = arrival_time
        self.priority = priority
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.age = 0


class Scheduler:
    def __init__(self):
        self.processes = []
        self.current_time = 0
        self.stats = {
            'avg_waiting_time': 0,
            'max_waiting_time': 0,
            'total_execution_time': 0
        }

    def load_processes(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            self.processes = [Process(**p) for p in data['processes']]

    def fcfs(self):
        results = []
        queue = sorted(self.processes, key=lambda p: p.arrival_time)
        current_time = 0

        for process in queue:
            if current_time < process.arrival_time:
                current_time = process.arrival_time

            process.start_time = current_time
            process.waiting_time = current_time - process.arrival_time
            current_time += process.burst_time
            process.completion_time = current_time

            results.append({
                'pid': process.pid,
                'start_time': process.start_time,
                'completion_time': process.completion_time,
                'waiting_time': process.waiting_time
            })

        self.calculate_stats(results)
        return results

    def round_robin(self, quantum=2):
        results = []
        queue = self.processes.copy()
        current_time = 0
        process_waiting_times = {p.pid: 0 for p in self.processes}
        completion_times = {p.pid: 0 for p in self.processes}

        for p in self.processes:
            p.remaining_time = p.burst_time

        while queue:
            if not queue:
                break

            process = queue.pop(0)

            if current_time < process.arrival_time:
                current_time = process.arrival_time

            # Update waiting time
            process_waiting_times[process.pid] += max(0, current_time - max(process.arrival_time,
                                                                            completion_times.get(process.pid,
                                                                                                 process.arrival_time)))

            execution_time = min(quantum, process.remaining_time)
            process.remaining_time -= execution_time

            results.append({
                'pid': process.pid,
                'start_time': current_time,
                'execution_time': execution_time,
                'waiting_time': process_waiting_times[process.pid]
            })

            current_time += execution_time
            completion_times[process.pid] = current_time

            if process.remaining_time > 0:
                queue.append(process)

        # Update final results with total waiting times
        final_results = []
        for result in results:
            result['completion_time'] = completion_times[result['pid']]
            final_results.append(result)

        self.calculate_stats(final_results)
        return results

    def priority_with_aging(self):
        results = []
        queue = self.processes.copy()
        current_time = 0

        while queue:
            # Increase age of waiting processes
            for process in queue:
                if current_time >= process.arrival_time:
                    process.age += 1

            # Select process with the highest priority (considering age)
            ready_processes = [p for p in queue if p.arrival_time <= current_time]
            if not ready_processes:
                current_time += 1
                continue

            selected = max(ready_processes,
                           key=lambda p: p.priority + p.age)

            selected.start_time = current_time
            selected.waiting_time = current_time - selected.arrival_time
            current_time += selected.burst_time
            selected.completion_time = current_time

            results.append({
                'pid': selected.pid,
                'start_time': selected.start_time,
                'completion_time': selected.completion_time,
                'waiting_time': selected.waiting_time,
                'final_priority': selected.priority + selected.age
            })

            queue.remove(selected)

        self.calculate_stats(results)
        return results

    def calculate_stats(self, results):
        waiting_times = [r['waiting_time'] for r in results if 'waiting_time' in r]
        if waiting_times:
            self.stats['avg_waiting_time'] = sum(waiting_times) / len(waiting_times)
            self.stats['max_waiting_time'] = max(waiting_times)
        else:
            self.stats['avg_waiting_time'] = 0
            self.stats['max_waiting_time'] = 0

        completion_times = [r['completion_time'] for r in results if 'completion_time' in r]
        self.stats['total_execution_time'] = max(completion_times) if completion_times else 0

    def generate_report(self, algorithm_name, results):
        filename = f'report_{algorithm_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(filename, 'w') as f:
            f.write(f"Simulation Report - {algorithm_name}\n")
            f.write("=" * 50 + "\n\n")

            f.write("Process Execution Timeline:\n")
            for result in results:
                f.write(f"Process {result['pid']}:\n")
                for key, value in result.items():
                    if key != 'pid':
                        f.write(f"  {key}: {value}\n")
                f.write("\n")

            f.write("\nStatistics:\n")
            for key, value in self.stats.items():
                f.write(f"{key}: {value:.2f}\n")


class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Scheduler Simulation")

        # Konfiguracja skalowania głównego okna
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.scheduler = Scheduler()
        self.animation_speed = 1.0
        self.current_time = 0
        self.setup_gui()

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)  # Lewa strona dostaje więcej miejsca
        main_frame.grid_columnconfigure(1, weight=1)  # Prawa strona mniej miejsca

        # Left panel for controls and visualization
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_panel.grid_rowconfigure(2, weight=1)  # Canvas row gets all extra space
        left_panel.grid_columnconfigure(0, weight=1)

        # Control Panel
        control_frame = ttk.Frame(left_panel, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Buttons
        ttk.Button(control_frame, text="Load Processes", command=self.load_processes).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Run FCFS", command=self.run_fcfs).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Run Round Robin", command=self.run_rr).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Run Priority", command=self.run_priority).grid(row=0, column=3, padx=5)

        # File name display
        self.filename_label = ttk.Label(control_frame, text="Current file: None", font=('TkDefaultFont', 10))
        self.filename_label.grid(row=1, column=0, columnspan=4, pady=5, sticky='w')

        # Animation Speed Control
        speed_frame = ttk.Frame(left_panel)
        speed_frame.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        speed_frame.grid_columnconfigure(1, weight=1)  # Make speed slider expand

        ttk.Label(speed_frame, text="Animation Speed:").grid(row=0, column=0, padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=3.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        # Time and Process Display
        self.time_label = ttk.Label(speed_frame, text="Time: 0")
        self.time_label.grid(row=0, column=2, padx=20)
        self.process_label = ttk.Label(speed_frame, text="Current Process: None")
        self.process_label.grid(row=0, column=3, padx=20)

        # Canvas frame with scrollbars
        canvas_frame = ttk.Frame(left_panel)
        canvas_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Canvas and scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        x_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        y_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        # Configure canvas scrolling
        self.canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        # Bind mouse wheel events
        self.canvas.bind('<MouseWheel>', self._on_mousewheel_y)
        self.canvas.bind('<Shift-MouseWheel>', self._on_mousewheel_x)
        self.canvas.bind('<Button-4>', self._on_mousewheel_y)
        self.canvas.bind('<Button-5>', self._on_mousewheel_y)
        self.canvas.bind('<Shift-Button-4>', self._on_mousewheel_x)
        self.canvas.bind('<Shift-Button-5>', self._on_mousewheel_x)

        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        x_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        y_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Right panel
        right_panel = ttk.Frame(main_frame, padding="10")
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.N, tk.S))
        right_panel.grid_rowconfigure(1, weight=1)  # Make treeview expand
        right_panel.grid_columnconfigure(0, weight=1)

        # Process List label
        ttk.Label(right_panel, text="Process List", font=('TkDefaultFont', 12, 'bold')).grid(
            row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Process Treeview
        self.process_tree = ttk.Treeview(right_panel,
                                         columns=('PID', 'Burst', 'Arrival', 'Priority', 'Status'),
                                         show='headings',
                                         height=15)
        self.process_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure treeview columns
        for col in ('PID', 'Burst', 'Arrival', 'Priority', 'Status'):
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=70, anchor=tk.CENTER)

        # Status label
        self.status_label = ttk.Label(right_panel, text="⚪ Ready to load processes",
                                      font=('TkDefaultFont', 10))
        self.status_label.grid(row=2, column=0, pady=10)

    def _on_mousewheel_y(self, event):
            """Obsługa przewijania pionowego"""
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")

    def _on_mousewheel_x(self, event):
            """Obsługa przewijania poziomego (z Shiftem)"""
            if event.num == 4 or event.delta > 0:
                self.canvas.xview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.xview_scroll(1, "units")

    def load_processes(self):
        try:
            filename = filedialog.askopenfilename(
                title="Select Process File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                self.scheduler.load_processes(filename)
                self.update_process_list()
                # Update filename display - show only the base filename, not the full path
                base_filename = filename.split('/')[-1] if '/' in filename else filename.split('\\')[-1]
                self.filename_label.config(text=f"Current file: {base_filename}")
                self.status_label.config(text="✅ Processes loaded successfully")
                messagebox.showinfo("Success", "Processes loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load processes: {str(e)}")
            self.status_label.config(text="❌ Error loading processes")
            self.filename_label.config(text="Current file: None")

    def update_process_list(self):
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        for process in self.scheduler.processes:
            self.process_tree.insert('', 'end', values=(
                process.pid,
                process.burst_time,
                process.arrival_time,
                process.priority,
                'Waiting'
            ))

    def visualize_results(self, results):
        self.canvas.delete('all')
        self.colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
        self.y_spacing = 50
        self.x_scale = 40

        # Calculate dimensions
        max_time = max(r.get('completion_time', r.get('start_time', 0) + r.get('execution_time', 0))
                       for r in results)
        process_count = len(set(r['pid'] for r in results))

        # Calculate canvas size
        canvas_width = max(800, 100 + (max_time + 1) * self.x_scale)
        canvas_height = max(400, 100 + process_count * self.y_spacing)

        # Configure canvas scrolling region
        self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

        # Draw timeline
        self.canvas.create_line(50, canvas_height - 50, canvas_width - 50, canvas_height - 50, arrow=tk.LAST)
        for i in range(0, int(max_time) + 1):
            x = 50 + (i * self.x_scale)
            self.canvas.create_line(x, canvas_height - 55, x, canvas_height - 45)
            self.canvas.create_text(x, canvas_height - 35, text=str(i))

        # Draw process labels on the left
        process_ids = sorted(list(set(r['pid'] for r in results)))
        for i, pid in enumerate(process_ids):
            y = 50 + (i * self.y_spacing)
            self.canvas.create_text(30, y + 20, text=f"P{pid}")

        # Reset process statuses and set up animation
        self.reset_process_statuses()
        self.results = results
        self.current_step = 0
        self.process_blocks = {}
        self.animate_step()

    def animate_step(self):
        if self.current_step < len(self.results):
            result = self.results[self.current_step]
            pid = result['pid']

            # Update process status
            self.update_process_status(pid, 'Running')

            # Update time and process labels
            start_time = result['start_time']
            self.time_label.config(text=f"Time: {start_time}")
            self.process_label.config(text=f"Current Process: P{pid}")

            # Calculate duration
            if 'execution_time' in result:
                duration = result['execution_time']
            else:
                duration = result['completion_time'] - result['start_time']

            # Calculate coordinates
            x1 = 50 + (start_time * self.x_scale)
            x2 = x1 + (duration * self.x_scale)
            process_ids = sorted(list(set(r['pid'] for r in self.results)))
            row = process_ids.index(pid)
            y1 = 50 + (row * self.y_spacing)
            y2 = y1 + 40

            # Create the process block with initial width of 0
            block = self.canvas.create_rectangle(
                x1, y1, x1, y2,
                fill=self.colors[pid % len(self.colors)],
                tags=f"block_{self.current_step}"
            )

            # Store block reference
            self.process_blocks[self.current_step] = block

            # Animate the block
            self.animate_block(block, x1, y1, x2, y2, pid, duration)
        else:
            # Animation finished
            self.time_label.config(text="Simulation Complete")
            self.process_label.config(text="Current Process: None")
            self.status_label.config(text="✅ Simulation completed")

    def animate_block(self, block, x1, y1, x2, y2, pid, duration):
        steps = int(20 * self.speed_var.get())  # Adjust steps based on speed
        dx = (x2 - x1) / steps
        delay = int(25 / self.speed_var.get())  # Adjust delay based on speed

        def update_block(step=0):
            if step < steps:
                current_x2 = x1 + (dx * (step + 1))
                self.canvas.coords(block, x1, y1, current_x2, y2)
                self.root.after(delay, lambda: update_block(step + 1))
            else:
                # Add process label
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=f"P{pid}"
                )
                # Move to next step
                self.update_process_status(pid, 'Completed')
                self.current_step += 1
                self.root.after(int(250 / self.speed_var.get()), self.animate_step)

        update_block()

    def reset_process_statuses(self):
        for item in self.process_tree.get_children():
            values = list(self.process_tree.item(item)['values'])
            values[4] = 'Waiting'
            self.process_tree.item(item, values=values)

    def update_process_status(self, pid, status):
        for item in self.process_tree.get_children():
            values = self.process_tree.item(item)['values']
            if values[0] == pid:
                values = list(values)
                values[4] = status
                self.process_tree.item(item, values=values)
                break

    def run_fcfs(self):
        if not self.scheduler.processes:
            messagebox.showerror("Error", "Please load processes first!")
            return
        results = self.scheduler.fcfs()
        self.scheduler.generate_report('FCFS', results)
        self.visualize_results(results)
        self.status_label.config(text="▶️ Running FCFS simulation")

    def run_rr(self):
        if not self.scheduler.processes:
            messagebox.showerror("Error", "Please load processes first!")
            return
        results = self.scheduler.round_robin()
        self.scheduler.generate_report('RoundRobin', results)
        self.visualize_results(results)
        self.status_label.config(text="▶️ Running Round Robin simulation")

    def run_priority(self):
        if not self.scheduler.processes:
            messagebox.showerror("Error", "Please load processes first!")
            return
        results = self.scheduler.priority_with_aging()
        self.scheduler.generate_report('Priority', results)
        self.visualize_results(results)
        self.status_label.config(text="▶️ Running Priority simulation")


if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()