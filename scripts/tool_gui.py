import tkinter as tk
from tkinter import ttk, filedialog
import threading
import traceback


class ToolGUI:
    def __init__(self, title, options, run_callback, size="700x600"):
        self.options = options
        self.run_callback = run_callback
        self.running = False

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.root.minsize(650, 450)

        self.widgets = {}
        self._log_buffer = []
        self._log_lock = threading.Lock()
        self._log_after_id = None
        self._log_flush_interval = 200

        self._build_ui()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame = ttk.Frame(self.root, padding=10)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        row = 0

        for name, config in self.options.items():
            widget_type = config["type"]
            label_text = config.get("label", name)

            if widget_type == "separator":
                separator = ttk.Separator(frame, orient="horizontal")
                separator.grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
                row += 1
                continue

            ttk.Label(frame, text=label_text).grid(
                row=row, column=0, sticky="w", pady=5
            )
            default = config.get("default", "")

            if widget_type == "folder":
                var = tk.StringVar(value=default)
                entry = ttk.Entry(frame, textvariable=var)
                entry.grid(row=row, column=1, sticky="ew", padx=(0, 5))
                ttk.Button(
                    frame,
                    text="Browse...",
                    command=lambda v=var: self._select_folder(v),
                ).grid(row=row, column=2)
                self.widgets[name] = var

            elif widget_type == "file":
                var = tk.StringVar(value=default)
                entry = ttk.Entry(frame, textvariable=var)
                entry.grid(row=row, column=1, sticky="ew", padx=(0, 5))
                ttk.Button(
                    frame,
                    text="Browse...",
                    command=lambda v=var: self._select_file(v, config.get("filetypes")),
                ).grid(row=row, column=2)
                self.widgets[name] = var

            elif widget_type == "text":
                var = tk.StringVar(value=default)
                ttk.Entry(frame, textvariable=var).grid(
                    row=row, column=1, columnspan=2, sticky="ew"
                )
                self.widgets[name] = var

            elif widget_type == "choice":
                values = config.get("values", [])
                initial = config.get("default", values[0] if values else "")
                var = tk.StringVar(value=initial)
                ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=values,
                    state="readonly",
                ).grid(row=row, column=1, columnspan=2, sticky="ew")
                self.widgets[name] = var

            elif widget_type == "multiselect":
                values = config.get("values", [])
                listbox = tk.Listbox(
                    frame,
                    selectmode="multiple",
                    height=6,
                    exportselection=False,
                )
                scrollbar = ttk.Scrollbar(
                    frame,
                    orient="vertical",
                    command=listbox.yview,
                )
                listbox.configure(yscrollcommand=scrollbar.set)
                listbox.grid(row=row, column=1, sticky="nsew", padx=(0, 5))
                scrollbar.grid(row=row, column=2, sticky="ns")

                for item in values:
                    listbox.insert("end", item)

                defaults = config.get("default", [])
                for i, item in enumerate(values):
                    if item in defaults:
                        listbox.selection_set(i)

                self.widgets[name] = listbox

            elif widget_type == "bool":
                var = tk.BooleanVar(value=bool(default))
                ttk.Checkbutton(frame, variable=var).grid(
                    row=row,
                    column=1,
                    columnspan=2,
                    sticky="w",
                )
                self.widgets[name] = var

            else:
                raise ValueError(f"Unsupported option type: {widget_type}")

            row += 1

        self.output = tk.Text(
            frame,
            wrap="none",
            height=15,
            state="disabled",
        )
        self.output.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        output_scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.output.yview,
        )
        output_scroll.grid(row=row, column=2, sticky="ns", pady=(10, 0))
        self.output.configure(yscrollcommand=output_scroll.set)
        frame.rowconfigure(row, weight=1)

        row += 1
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.status = ttk.Label(button_frame, text="Ready")
        self.status.grid(row=0, column=0, sticky="w")

        self.run_button = ttk.Button(button_frame, text="Run", command=self.run)
        self.run_button.grid(row=0, column=1)

        self.clear_button = ttk.Button(
            button_frame, text="Clear log", command=self.clear_log
        )
        self.clear_button.grid(row=0, column=2, sticky="e")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _select_folder(self, variable):
        folder = filedialog.askdirectory()
        if folder:
            variable.set(folder)

    def _select_file(self, variable, filetypes=None):
        filetypes = filetypes or [("All files", "*")]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            variable.set(file_path)

    def get_values(self):
        result = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, tk.Listbox):
                selected = widget.curselection()
                result[name] = [widget.get(i) for i in selected]
            else:
                result[name] = widget.get()
        return result

    def _call_on_main_thread(self, callback):
        """
        Execute a callback on the Tkinter main thread and
        return its result to the calling thread.
        """
        result = []
        exception = []
        event = threading.Event()

        def wrapper():
            try:
                result.append(callback())
            except Exception as e:
                exception.append(e)
            finally:
                event.set()

        self.root.after(0, wrapper)
        event.wait()

        if exception:
            raise exception[0]

        return result[0] if result else None

    def get_clipboard(self):
        """Get the current clipboard contents."""
        return self._call_on_main_thread(self.root.clipboard_get)

    def set_clipboard(self, text):
        """Replace the clipboard contents."""

        def update_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

        self._call_on_main_thread(update_clipboard)

    def log(self, text):
        with self._log_lock:
            self._log_buffer.append(str(text))
            if self._log_after_id is None:
                self._log_after_id = self.root.after(
                    self._log_flush_interval,
                    self._flush_log_buffer,
                )

    def _flush_log_buffer(self):
        with self._log_lock:
            lines = self._log_buffer
            self._log_buffer = []
            self._log_after_id = None

        if not lines:
            return

        self.output.config(state="normal")
        self.output.insert("end", "\n".join(lines) + "\n")
        self.output.config(state="disabled")
        self.output.see("end")

    def _set_status(self, text):
        if threading.current_thread() is threading.main_thread():
            self.status.config(text=text)
        else:
            self.root.after(0, self.status.config, {"text": text})

    def clear_log(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")

    def _run_complete(self):
        self.running = False
        self.run_button.config(state="normal")
        self._set_status("Ready")
        self.log("Finished.")

    def _run_in_thread(self, values):
        try:
            self.run_callback(values, self.log, self)
        except Exception:
            self.log(traceback.format_exc())
        finally:
            self.root.after(0, self._run_complete)

    def run(self):
        if self.running:
            return

        # Read all Tkinter widget values while still on the
        # main thread. Tkinter widgets must not be accessed
        # from the worker thread.
        values = self.get_values()

        self.running = True
        self.run_button.config(state="disabled")
        self._set_status("Running...")
        self.log("Starting...")

        thread = threading.Thread(
            target=self._run_in_thread,
            args=(values,),
            daemon=True,
        )

        thread.start()

    def _on_close(self):
        if self._log_after_id is not None:
            self.root.after_cancel(self._log_after_id)
            self._log_after_id = None
        self.root.quit()

    def show(self):
        self.root.mainloop()
