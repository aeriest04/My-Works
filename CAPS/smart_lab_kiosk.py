import os
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector
from datetime import datetime
import threading
import serial
import time

# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="capstone",   # change if needed
            database="smartlab"
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        return None

# -------------------------------------------------------------
# FINGERPRINT MANAGER
# -------------------------------------------------------------
class FingerprintManager:
    def __init__(self, port='COM8', baudrate=57600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print("[ARDUINO] [FINGERPRINT] Sensor connected.")
        except serial.SerialException as e:
            print(f"[FINGERPRINT ERROR] {e}")
            self.ser = None
        self.last_msg = ""

    def send_command(self, cmd):
        if self.ser:
            self.ser.write((cmd + "\n").encode())
            print(f"[SENT TO ARDUINO] {cmd}")

    def read_serial(self, callback=None):
        if not self.ser:
            return
        while True:
            try:
                line_bytes = self.ser.readline()
                if not line_bytes:
                    continue
                line = line_bytes.decode(errors='ignore').strip()
                if line and line != self.last_msg:
                    self.last_msg = line
                    if callback:
                        callback(line)
            except Exception as e:
                print(f"[ERROR] Serial read: {e}")
                time.sleep(0.1)

    def start_reading(self, callback=None):
        t = threading.Thread(target=self.read_serial, args=(callback,), daemon=True)
        t.start()

# -------------------------------------------------------------
# ON-SCREEN KEYBOARD (FIXED AT BOTTOM)
# -------------------------------------------------------------
class OnScreenKeyboard(tk.Frame):
    def __init__(self, master, target_entry, hide_callback=None):
        super().__init__(master, bg="#222")
        self.master = master
        self.target_entry = target_entry
        self.hide_callback = hide_callback
        self.create_keys()
        self.pack(side="bottom", fill="x")

    def create_keys(self):
        keys = [
            ['1','2','3','4','5','6','7','8','9','0','Backspace'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M','.','_'],
            ['Space','Clear','Hide']
        ]

        for row_keys in keys:
            row_frame = tk.Frame(self, bg="#222")
            row_frame.pack(pady=2)
            for key in row_keys:
                btn = tk.Button(
                    row_frame, text=key,
                    width=7 if key not in ("Space", "Hide") else 12,
                    height=2,
                    bg="#555", fg="white",
                    font=("Poppins", 14, "bold"),
                    command=lambda val=key: self.key_press(val)
                )
                btn.pack(side="left", padx=2, pady=2)

    def key_press(self, key):
        if key == "Backspace":
            current = self.target_entry.get()
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, current[:-1])
        elif key == "Space":
            self.target_entry.insert(tk.END, " ")
        elif key == "Clear":
            self.target_entry.delete(0, tk.END)
        elif key == "Hide":
            self.destroy()
            if self.hide_callback:
                self.hide_callback()
        else:
            self.target_entry.insert(tk.END, key)

# -------------------------------------------------------------
# SMART LAB KIOSK
# -------------------------------------------------------------
class SmartLabKiosk:
    def __init__(self, root):
        self.root = root
        self.root.title("🔬 Smart Lab Borrowing Kiosk")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda e: self.root.attributes('-fullscreen', False))

        self.user = None
        self.borrowed_items = {}
        self.history_logs = []
        self.keyboard = None  # track current keyboard

        self.image_dir = r"C:\Users\Yannabii\Desktop\CAPS\images"

        self.qr_items = {
            "BKR123456": {"name": "Beaker", "img": "beaker.jpg"},
            "MTR789101": {"name": "Multimeter", "img": "meter.jpg"},
            "MSC456789": {"name": "Microscope", "img": "micro.jpg"},
            "PSU654321": {"name": "Power Supply", "img": "psu.jpg"},
            "SLD987654": {"name": "Soldering Kit", "img": "solder.jpg"}
        }

        self.placeholder_img = ImageTk.PhotoImage(Image.new("RGB", (200, 150), color="gray"))

        self.fp_manager = FingerprintManager()
        self.fp_manager.start_reading(callback=self.handle_fingerprint_msg)

        self.show_login_panel()

    # -------------------------------------------------------------
    # FINGERPRINT CALLBACK
    # -------------------------------------------------------------
    def handle_fingerprint_msg(self, msg):
        self.root.after(0, self.process_fingerprint_msg, msg)

    def process_fingerprint_msg(self, msg):
        print(f"[ARDUINO] {msg}")
        if not hasattr(self, 'message_label'):
            return

        if "Place finger" in msg:
            self.message_label.config(text="Place finger on sensor...")
        elif "Remove finger" in msg:
            self.message_label.config(text="Remove finger...")
        elif "Enrollment complete ID:" in msg:
            fid = msg.split(":")[-1].strip()
            messagebox.showinfo("Fingerprint", f"Enrollment complete for ID {fid}")
            self.message_label.config(text=f"Enrollment complete for ID {fid}")
        elif "Login success ID:" in msg:
            fid = msg.split(":")[-1].strip()
            self.user = f"FPUser{fid}"
            messagebox.showinfo("Fingerprint", f"Welcome {self.user}!")
            self.build_ui()

    # -------------------------------------------------------------
    # LOGIN PANEL
    # -------------------------------------------------------------
    def show_login_panel(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#800000", padx=60, pady=60)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="🔐 Smart Lab Login", bg="#800000", fg="white",
                 font=("Poppins", 32, "bold")).pack(pady=20)

        tk.Label(frame, text="Username:", bg="#800000", fg="white", font=("Poppins", 20)).pack()
        self.username_entry = tk.Entry(frame, font=("Poppins", 20))
        self.username_entry.pack(pady=10)
        self.username_entry.bind("<FocusIn>", lambda e: self.show_keyboard(self.username_entry))

        tk.Label(frame, text="Password:", bg="#800000", fg="white", font=("Poppins", 20)).pack()
        self.password_entry = tk.Entry(frame, show="*", font=("Poppins", 20))
        self.password_entry.pack(pady=10)
        self.password_entry.bind("<FocusIn>", lambda e: self.show_keyboard(self.password_entry))

        tk.Button(frame, text="Login", bg="#ffcc00", fg="#400000",
                  font=("Poppins", 20, "bold"), width=20, command=self.login_user).pack(pady=15)

        tk.Button(frame, text="Login via Fingerprint", bg="#ff6600", fg="white",
                  font=("Poppins", 20, "bold"), width=25).pack(pady=10)

        tk.Button(frame, text="Register", bg="#2ecc71", fg="white",
                  font=("Poppins", 20, "bold"), width=20, command=self.show_register_panel).pack(pady=15)

    # -------------------------------------------------------------
    # REGISTER PANEL
    # -------------------------------------------------------------
    def show_register_panel(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#800000", padx=60, pady=60)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="📝 Register New User", bg="#800000", fg="white",
                 font=("Poppins", 32, "bold")).pack(pady=20)

        self.reg_name_entry = self.create_entry(frame, "STUDENT NO.:")
        self.reg_username_entry = self.create_entry(frame, "Username:")
        self.reg_password_entry = self.create_entry(frame, "Password:", show="*")

        tk.Button(frame, text="Register Fingerprint", bg="#ff6600", fg="white",
                  font=("Poppins", 20, "bold"),
                  command=self.trigger_fingerprint_enroll).pack(pady=15)

        tk.Button(frame, text="Create Account", bg="#2ecc71", fg="white",
                  font=("Poppins", 20, "bold"), command=self.register_user).pack(pady=10)

        tk.Button(frame, text="Back", bg="#95a5a6", fg="white",
                  font=("Poppins", 20, "bold"), command=self.show_login_panel).pack(pady=10)

        self.message_label = tk.Label(frame, text="", bg="#800000", fg="yellow", font=("Poppins", 16))
        self.message_label.pack(pady=10)

    def create_entry(self, frame, label, show=None):
        tk.Label(frame, text=label, bg="#800000", fg="white", font=("Poppins", 20)).pack()
        entry = tk.Entry(frame, font=("Poppins", 20), show=show)
        entry.pack(pady=10)
        entry.bind("<FocusIn>", lambda e: self.show_keyboard(entry))
        return entry

    def show_keyboard(self, entry_widget):
        if self.keyboard:
            self.keyboard.destroy()
        self.keyboard = OnScreenKeyboard(self.root, entry_widget, hide_callback=self.hide_keyboard)

    def hide_keyboard(self):
        self.keyboard = None

    def trigger_fingerprint_enroll(self):
        username = self.reg_username_entry.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Enter username first.")
            return
        user_id = abs(hash(username)) % 1000
        self.fp_manager.send_command(f"ENROLL{user_id}")
        self.message_label.config(text=f"Enrolling Fingerprint ID {user_id}...")

    # -------------------------------------------------------------
    # LOGIN / REGISTER
    # -------------------------------------------------------------
    def login_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "123":
            self.user = "admin"
            self.build_ui()
            return

        conn = connect_db()
        if not conn:
            return

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            self.user = username
            self.build_ui()
        else:
            messagebox.showerror("Login Error", "Invalid username or password.")

    def register_user(self):
        name = self.reg_name_entry.get()
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()

        if not name or not username or not password:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        conn = connect_db()
        if not conn:
            return

        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, username, password) VALUES (%s, %s, %s)",
                       (name, username, password))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Account created successfully!")
        self.show_login_panel()

    # -------------------------------------------------------------
    # MAIN UI (QR SCANNER + IMAGES)
    # -------------------------------------------------------------
    def build_ui(self):
        self.clear_window()
        header = tk.Label(self.root, text=f"🔬 Smart Lab - Welcome {self.user}",
                          bg="#ffcc00", fg="#800000", font=("Poppins", 28, "bold"), pady=20)
        header.pack(fill="x")

        tk.Label(self.root, text="Scan QR Code or Click Image to Borrow/Return", bg="#400000",
                 fg="white", font=("Poppins", 24)).pack(fill="x")

        self.qr_entry = tk.Entry(self.root, font=("Poppins", 28))
        self.qr_entry.pack(pady=20)
        self.qr_entry.focus()
        self.qr_entry.bind("<Return>", self.handle_qr_scan_event)
        self.qr_entry.bind("<FocusIn>", lambda e: self.show_keyboard(self.qr_entry))

        self.image_frame = tk.Frame(self.root, bg="#400000")
        self.image_frame.pack(pady=10)
        self.load_images()

        self.image_label = tk.Label(self.root, image=self.placeholder_img, bg="#400000")
        self.image_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="", bg="#400000", fg="yellow",
                                     font=("Poppins", 20, "bold"))
        self.status_label.pack(pady=5)

        tk.Button(self.root, text="View History Logs", bg="#2980b9", fg="white",
                  font=("Poppins", 20, "bold"), command=self.show_history_logs).pack(pady=10)

        tk.Button(self.root, text="Logout", bg="#c0392b", fg="white",
                  font=("Poppins", 20, "bold"), command=self.logout).pack(pady=20)

    def load_images(self):
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        for code, info in self.qr_items.items():
            img_path = os.path.join(self.image_dir, info["img"])
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((150, 150))
                photo = ImageTk.PhotoImage(img)
                btn = tk.Button(
                    self.image_frame,
                    image=photo,
                    text=info["name"],
                    compound="top",
                    bg="white",
                    fg="black",
                    font=("Poppins", 11, "bold"),
                    command=lambda c=code: self.handle_qr_scan(c)
                )
                btn.image = photo
                btn.pack(side="left", padx=15, pady=10)
            else:
                tk.Label(self.image_frame, text=f"Missing {info['img']}", fg="red", bg="#400000").pack(side="left")

    # -------------------------------------------------------------
    # QR SCANNER HANDLER
    # -------------------------------------------------------------
    def handle_qr_scan_event(self, event):
        code = self.qr_entry.get().strip()
        self.qr_entry.delete(0, tk.END)
        self.handle_qr_scan(code)

    def handle_qr_scan(self, code):
        item = self.qr_items.get(code)
        if not item:
            messagebox.showerror("Error", f"Invalid QR Code: {code}")
            return

        img_path = os.path.join(self.image_dir, item["img"])
        if os.path.exists(img_path):
            img = Image.open(img_path).resize((300, 250))
            self.displayed_img = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.displayed_img)
        else:
            self.image_label.config(image=self.placeholder_img)

        is_borrowed = self.borrowed_items.get(code, False)
        action = "Borrowed" if not is_borrowed else "Returned"

        confirm = messagebox.askyesno("Confirm Action", f"{item['name']} detected.\nWould you like to {action} this item?")
        if not confirm:
            self.status_label.config(text="Action canceled.", fg="yellow")
            return

        self.borrowed_items[code] = not is_borrowed
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history_logs.append((timestamp, self.user, item["name"], action))

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (timestamp, user, item, action) VALUES (%s, %s, %s, %s)",
                           (timestamp, self.user, item["name"], action))
            conn.commit()
            conn.close()

        self.status_label.config(
            text=f"{item['name']} {action} at {timestamp}",
            fg="#2ecc71" if action == "Borrowed" else "#e74c3c"
        )

    # -------------------------------------------------------------
    # HISTORY LOGS WINDOW
    # -------------------------------------------------------------
    def show_history_logs(self):
        history_win = tk.Toplevel(self.root)
        history_win.title("📜 Borrowing History Logs")
        history_win.geometry("800x500")
        history_win.configure(bg="#800000")

        columns = ("timestamp", "user", "item", "action")
        tree = ttk.Treeview(history_win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=180)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for log in self.history_logs:
            tree.insert("", "end", values=log)

    # -------------------------------------------------------------
    # MISC
    # -------------------------------------------------------------
    def logout(self):
        self.user = None
        self.show_login_panel()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        if self.keyboard:
            self.keyboard.destroy()
            self.keyboard = None


# -------------------------------------------------------------
# RUN APP
# -------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartLabKiosk(root)
    root.mainloop()
