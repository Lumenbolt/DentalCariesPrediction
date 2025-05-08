import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import numpy as np
from fingerprint import detect_sensor_port, capture_fingerprint
from ml import MLPredictor
import cv2

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Dental Caries Detection")
        self.root.geometry("1280x720")
        self.root.configure(bg="#F0F2F5")
        
        self.enhanced_image = None
        self.ml_predictor = MLPredictor()
        self.sensor_check_active = True
        self._setup_gui()
        self.check_sensor()

    def _setup_gui(self):
        # Define modern color scheme
        bg_color = "#F0F2F5"
        accent_color = "#4A90E2"
        text_color = "#333333"
        success_color = "#4CAF50"
        error_color = "#F44336"
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TButton", font=("Arial", 12), padding=10, relief="flat")
        self.style.map("TButton", background=[("active", accent_color), ("!disabled", "#5C6BC0")],
                       foreground=[("active", "white"), ("!disabled", "white")])
        self.style.configure("Title.TLabel", font=("Arial", 24, "bold"), foreground=accent_color, background=bg_color)
        self.style.configure("Motto.TLabel", font=("Arial", 12), foreground=text_color, background=bg_color)
        self.style.configure("Result.TLabel", font=("Arial", 14), foreground=text_color, wraplength=600, background=bg_color)

        # Header Frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=(20, 10))
        ttk.Label(header_frame, text="Dermatoglyphic-based Dental Caries Detection", style="Title.TLabel").pack()

        # Horizontal Frame for Image Preview and Results
        self.image_results_frame = ttk.Frame(self.root)
        self.image_results_frame.pack(pady=20)

        # Image Preview Frame
        self.preview_frame = ttk.Frame(self.image_results_frame)
        self.preview_frame.pack(side=tk.LEFT, padx=20)
        preview_border = tk.Frame(self.preview_frame, bg=accent_color, padx=2, pady=2)
        preview_border.pack()
        self.preview_label = tk.Label(preview_border, bg="white")
        self.preview_label.pack()

        # Results Frame
        self.results_frame = ttk.Frame(self.image_results_frame)
        self.results_frame.pack(side=tk.LEFT, padx=20)
        result_border = tk.Frame(self.results_frame, bg=accent_color, padx=1, pady=1)
        result_border.pack(pady=10)
        result_bg = tk.Frame(result_border, bg="white", padx=15, pady=15)
        result_bg.pack()
        self.results_label = tk.Label(result_bg, font=("Arial", 14), wraplength=400, justify="left", bg="white")
        self.results_label.pack()

        # Control Panel Frame
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(pady=10)
        self.capture_btn = ttk.Button(self.control_frame, text="Capture Fingerprint", command=self.start_capture)
        self.retry_btn = ttk.Button(self.control_frame, text="Retake", state=tk.DISABLED, command=self.reset_flow)
        self.diagnose_btn = ttk.Button(self.control_frame, text="Diagnose", state=tk.DISABLED, command=self.start_diagnosis)
        self.capture_btn.pack()

        # Gender Selection Dropdown
        gender_frame = ttk.Frame(self.root)
        gender_frame.pack(pady=10)
        ttk.Label(gender_frame, text="Select Gender:", style="Motto.TLabel").pack(side=tk.LEFT, padx=5)
        self.gender_var = tk.StringVar(value="Select")
        gender_dropdown = ttk.Combobox(gender_frame, textvariable=self.gender_var, state="readonly")
        gender_dropdown['values'] = ("Male", "Female")
        gender_dropdown.pack(side=tk.LEFT, padx=5)

        # Status Panel
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(pady=10)
        status_bg = tk.Frame(self.status_frame, bg="#E1E5EA", padx=15, pady=10)
        status_bg.pack()
        self.status_label = tk.Label(status_bg, text="Initializing system...", font=("Arial", 14), wraplength=600, bg="#E1E5EA")
        self.status_label.pack()

        # Exit Button
        self.exit_frame = ttk.Frame(self.root)
        self.exit_frame.pack(pady=20, side=tk.BOTTOM)
        self.exit_btn = ttk.Button(self.exit_frame, text="Exit Program", command=self.exit_program)
        self.exit_btn.pack()

    def exit_program(self):
        self.sensor_check_active = False
        self.root.destroy()

    def start_diagnosis(self):
        """Start the diagnosis process."""
        gender = self.gender_var.get()
        if gender == "Select":
            messagebox.showerror("Error", "Please select a gender before diagnosing.")
            return

        self.diagnose_btn.config(state=tk.DISABLED)
        self.update_status("🩺 Diagnosing... Please wait.", "#4A90E2")
        threading.Thread(target=self._diagnosis_thread, args=(gender,), daemon=True).start()

    def check_sensor(self):
        if not self.sensor_check_active:
            return
        port = detect_sensor_port()
        if port:
            self.update_status("✅ Sensor connected! Place your finger on the scanner", "#4CAF50")
            self.capture_btn.config(state=tk.NORMAL)
        else:
            self.update_status("❌ Sensor not detected! Please connect your fingerprint scanner", "#F44336")
            self.capture_btn.config(state=tk.DISABLED)
            self.root.after(1000, self.check_sensor)

    def start_capture(self):
        self.capture_btn.config(state=tk.DISABLED)
        self.update_status("🔍 Please place your finger on the scanner plate and keep it still....", "#4A90E2")
        threading.Thread(target=self._capture_thread, daemon=True).start()

    def _capture_thread(self):
        try:
            def update_status_callback(message):
                self.root.after(0, lambda: self.update_status(message, "#4A90E2"))
            fingerprint_path = capture_fingerprint(status_callback=update_status_callback)
            img = cv2.imread(fingerprint_path)
            img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).resize((300, 300), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img_pil)
            self.preview_label.config(image=img_tk)
            self.preview_label.image = img_tk
            self.fingerprint_path = fingerprint_path
            self.root.after(0, lambda: self.update_status("✅ Fingerprint captured successfully!", "#4CAF50"))
            self.root.after(0, self.show_action_buttons)
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: messagebox.showerror("Error", f"❌ {error_message}"))
            self.root.after(0, self.check_sensor)

    def show_results(self, result_text):
        """Display the results in the results frame."""
        self.results_frame.pack(side=tk.LEFT, padx=20)  # Ensure visibility
        self.results_label.config(text=result_text, wraplength=400, justify="left")
        self.update_status("✅ Diagnosis complete!", "#4CAF50")

    def _diagnosis_thread(self, gender):
        """Threaded diagnosis process."""
        try:
            result = self.ml_predictor.analyze_fingerprint(self.fingerprint_path, gender)
            self.root.after(0, lambda: self.show_results(result))
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: messagebox.showerror("Error", f"❌ {error_message}"))
        finally:
            self.root.after(0, lambda: self.retry_btn.config(state=tk.NORMAL))

    def show_action_buttons(self):
        self.capture_btn.pack_forget()
        self.retry_btn.pack(side=tk.LEFT, padx=10)
        self.diagnose_btn.pack(side=tk.LEFT, padx=10)
        self.retry_btn.config(state=tk.NORMAL)
        self.diagnose_btn.config(state=tk.NORMAL)

    def reset_flow(self):
        self.enhanced_image = None
        self.preview_label.config(image="")
        self.results_frame.pack_forget()
        self.retry_btn.pack_forget()
        self.diagnose_btn.pack_forget()
        self.capture_btn.pack()
        self.check_sensor()
        self.start_capture()

    def update_status(self, text, color="black"):
        self.status_label.config(text=text, foreground=color)
        orig_bg = self.status_label.cget("background")
        self.status_label.config(background="#D6E4FF")
        self.root.after(100, lambda: self.status_label.config(background=orig_bg))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()