import tkinter as tk
from tkinter import ttk, filedialog
import threading
import traceback


class ToolGUI:
    def __init__(self, title, options, run_callback):
        self.options = options
        self.run_callback = run_callback

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("700x600")

        self.widgets = {}

        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        row = 0

        for name, config in self.options.items():
            ttk.Label(frame, text=config.get("label", name)).grid(
                row=row, column=0, sticky="w", pady=5
            )

            widget_type = config["type"]

            if widget_type == "folder":
                var = tk.StringVar(value=config.get("default", ""))

                entry = ttk.Entry(frame, textvariable=var, width=60)
                entry.grid(row=row, column=1)

                ttk.Button(
                    frame, text="Browse", command=lambda v=var: self.select_folder(v)
                ).grid(row=row, column=2)

                self.widgets[name] = var

            elif widget_type == "text":
                var = tk.StringVar(value=config.get("default", ""))

                ttk.Entry(frame, textvariable=var, width=60).grid(row=row, column=1)

                self.widgets[name] = var

            elif widget_type == "choice":
                var = tk.StringVar(value=config["values"][0])

                ttk.Combobox(
                    frame, textvariable=var, values=config["values"], state="readonly"
                ).grid(row=row, column=1)

                self.widgets[name] = var

            elif widget_type == "multiselect":
                listbox = tk.Listbox(
                    frame, selectmode="multiple", height=6, exportselection=False
                )

                for item in config["values"]:
                    listbox.insert("end", item)

                listbox.grid(row=row, column=1, sticky="ew")

                defaults = config.get("default", [])

                for i, item in enumerate(config["values"]):
                    if item in defaults:
                        listbox.selection_set(i)

                self.widgets[name] = listbox

            elif widget_type == "bool":
                var = tk.BooleanVar(value=config.get("default", False))

                ttk.Checkbutton(frame, variable=var).grid(row=row, column=1)

                self.widgets[name] = var

            row += 1

        self.output = tk.Text(frame, height=15)
        self.output.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=10)

        row += 1

        ttk.Button(frame, text="Run", command=self.run).grid(row=row, column=1)

    def select_folder(self, variable):
        folder = filedialog.askdirectory()

        if folder:
            variable.set(folder)

    def get_values(self):
        result = {}

        for name, widget in self.widgets.items():

            if isinstance(widget, tk.Listbox):
                selected = widget.curselection()
                result[name] = [widget.get(i) for i in selected]

            else:
                result[name] = widget.get()

        return result

    def log(self, text):
        self.output.insert("end", text + "\n")
        self.output.see("end")

    def run(self):
        values = self.get_values()

        try:
            self.run_callback(values, self.log)
        except Exception:
            self.log(traceback.format_exc())

    def show(self):
        self.root.mainloop()
