import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import subprocess
import db
import settings
import intent
import mic_manager
import system_actions
import time
from threading import Thread
import psutil
from datetime import datetime

def run_notification_listener(gui_ref):
    cmd = (
        '[void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
        '$wshell = New-Object -ComObject Wscript.Shell; '
        '$res = $wshell.Popup("Chinni is listening in the background. Click Cancel to stop voice service.", 0, "Chinni AI OS", 1 + 64); '
        'exit $res'
    )
    try:
        proc = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if proc.returncode == 2:
            print("Background notification 'Cancel' clicked. Stopping mic listener.")
            gui_ref.stop_listening()
    except Exception as e:
        print(f"PowerShell notification error: {e}")

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CHINNI AI OS - Futuristic HUD Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#050811")
        self.root.resizable(False, False)

        # Style colors
        self.bg_color = "#050811"
        self.panel_color = "#0d1527"
        self.sidebar_color = "#03050a"
        self.border_color = "#1e3b5e"
        self.text_color = "#ffffff"
        self.subtext_color = "#8a9ba8"
        
        self.cyan_color = "#00e5ff"
        self.purple_color = "#7c4dff"
        self.green_color = "#00e676"
        self.red_color = "#ff3d00"
        self.yellow_color = "#ffea00"
        self.blue_color = "#2979ff"

        # States
        self.visualizer_state = "idle"
        self.vis_phase = 0.0
        self.is_listening = True
        self.current_page = ""
        self.wifi_state = True
        self.bluetooth_state = True
        self.dark_mode_state = True

        # Callbacks
        self.on_confirm_callback = None
        self.on_cancel_callback = None
        self.on_manual_submit_callback = None
        self.on_toggle_listening_callback = None

        # Build UI layout
        self.create_layouts()
        
        # Load details
        self.load_settings_ui()
        self.refresh_custom_commands_ui()
        self.refresh_history_ui()
        self.refresh_notes_ui()
        self.refresh_tasks_ui()
        self.refresh_projects_ui()

        # Open Dashboard Tab
        self.show_page("dashboard")
        
        # Start animations & background threads
        self.animate_visualizer()
        self.start_metrics_thread()

        # Bind minimize event to background notification
        self.root.bind("<Unmap>", self.on_minimize)

        # Run startup check for OS access permission after 1s
        self.root.after(1000, self.check_os_access_on_startup)

    def create_layouts(self):
        # Left Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.sidebar_color, width=200, height=800)
        self.sidebar.pack_propagate(False)
        self.sidebar.pack(side="left", fill="y")

        # Brand header
        lbl_brand = tk.Label(self.sidebar, text="CHINNI AI OS", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.sidebar_color)
        lbl_brand.pack(pady=(30, 30))

        # Nav Buttons Creator
        def add_nav_btn(text, page_name):
            btn = tk.Button(
                self.sidebar, 
                text=text, 
                font=("Consolas", 9, "bold"), 
                bg=self.sidebar_color, 
                fg=self.subtext_color,
                activebackground=self.panel_color,
                activeforeground=self.cyan_color,
                bd=0,
                pady=14,
                anchor="w",
                padx=20,
                command=lambda: self.show_page(page_name)
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e: btn.config(fg=self.cyan_color))
            btn.bind("<Leave>", lambda e: btn.config(fg=self.subtext_color if self.current_page != page_name else self.cyan_color))
            return btn

        self.nav_btns = {
            "dashboard": add_nav_btn("📊 DASHBOARD", "dashboard"),
            "commands": add_nav_btn("📜 CUSTOM MACROS", "commands"),
            "notes": add_nav_btn("📝 NOTES MANAGER", "notes"),
            "tasks": add_nav_btn("📋 TASK PLANNER", "tasks"),
            "projects": add_nav_btn("💼 PROJECT PORTFOLIO", "projects"),
            "settings": add_nav_btn("⚙ PREFERENCES", "settings")
        }

        # Main pages viewport container
        self.pages_container = tk.Frame(self.root, bg=self.bg_color, width=1000, height=800)
        self.pages_container.pack_propagate(False)
        self.pages_container.pack(side="right", fill="both", expand=True)

        # Instances of pages
        self.pages = {
            "dashboard": tk.Frame(self.pages_container, bg=self.bg_color),
            "commands": tk.Frame(self.pages_container, bg=self.bg_color),
            "notes": tk.Frame(self.pages_container, bg=self.bg_color),
            "tasks": tk.Frame(self.pages_container, bg=self.bg_color),
            "projects": tk.Frame(self.pages_container, bg=self.bg_color),
            "settings": tk.Frame(self.pages_container, bg=self.bg_color)
        }

        self.setup_dashboard_page()
        self.setup_commands_page()
        self.setup_notes_page()
        self.setup_tasks_page()
        self.setup_projects_page()
        self.setup_settings_page()

    def show_page(self, page_name):
        self.current_page = page_name
        for p in self.pages.values():
            p.pack_forget()

        for name, btn in self.nav_btns.items():
            if name == page_name:
                btn.config(bg=self.panel_color, fg=self.cyan_color)
            else:
                btn.config(bg=self.sidebar_color, fg=self.subtext_color)

        self.pages[page_name].pack(fill="both", expand=True, padx=20, pady=20)
        
        # Refresh bindings
        if page_name == "dashboard":
            self.refresh_history_ui()
            self.sync_dashboard_mic_info()
        elif page_name == "commands":
            self.refresh_custom_commands_ui()
        elif page_name == "notes":
            self.refresh_notes_ui()
        elif page_name == "tasks":
            self.refresh_tasks_ui()
        elif page_name == "projects":
            self.refresh_projects_ui()
        elif page_name == "settings":
            self.load_settings_ui()

    # ----------------- PAGE 1: DASHBOARD -----------------
    def setup_dashboard_page(self):
        page = self.pages["dashboard"]

        # TOP BAR
        top_bar = tk.Frame(page, bg=self.panel_color, height=60, bd=1, highlightbackground=self.border_color, highlightthickness=1)
        top_bar.pack(fill="x", pady=(0, 15))
        top_bar.pack_propagate(False)

        # Status indicator
        self.status_indicator = tk.Canvas(top_bar, width=15, height=15, bg=self.panel_color, highlightthickness=0)
        self.status_indicator.pack(side="left", padx=(15, 5))
        self.status_indicator.create_oval(2, 2, 13, 13, fill=self.green_color, tags="dot")

        self.lbl_status_core = tk.Label(top_bar, text="CHINNI CORE: ONLINE", font=("Consolas", 10, "bold"), fg=self.green_color, bg=self.panel_color)
        self.lbl_status_core.pack(side="left", padx=(0, 15))

        # Search Bar
        tk.Label(top_bar, text="🔍 SYSTEM SEARCH:", font=("Consolas", 9, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(side="left", padx=(15, 5))
        self.top_search = tk.Entry(top_bar, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightcolor=self.cyan_color, highlightbackground="#37474f", width=25)
        self.top_search.pack(side="left", ipady=3)
        self.top_search.bind("<Return>", lambda e: self.run_top_search())

        btn_search = tk.Button(top_bar, text="RUN", font=("Consolas", 8, "bold"), bg=self.cyan_color, fg="#050811", bd=0, padx=10, command=self.run_top_search)
        btn_search.pack(side="left", padx=5, ipady=1)

        # System controls (Toggles)
        btn_wifi = tk.Button(top_bar, text="📶 WIFI: ON", font=("Consolas", 8, "bold"), bg="#1c1f2b", fg=self.text_color, bd=0, padx=10, command=self.toggle_wifi)
        btn_wifi.pack(side="right", padx=(5, 15), ipady=3)
        self.btn_wifi = btn_wifi

        btn_bt = tk.Button(top_bar, text="🔵 BT: ON", font=("Consolas", 8, "bold"), bg="#1c1f2b", fg=self.text_color, bd=0, padx=10, command=self.toggle_bluetooth)
        btn_bt.pack(side="right", padx=5, ipady=3)
        self.btn_bt = btn_bt

        btn_dark = tk.Button(top_bar, text="🌙 DARK MODE", font=("Consolas", 8, "bold"), bg="#1c1f2b", fg=self.text_color, bd=0, padx=10, command=self.toggle_dark_theme)
        btn_dark.pack(side="right", padx=5, ipady=3)
        self.btn_dark = btn_dark

        # 3 COLUMN MID CONTAINER
        mid_container = tk.Frame(page, bg=self.bg_color)
        mid_container.pack(fill="both", expand=True)

        # LEFT COLUMN: MODES & QUICK ACTIONS (260px)
        left_col = tk.Frame(mid_container, bg=self.bg_color, width=250)
        left_col.pack_propagate(False)
        left_col.pack(side="left", fill="y", padx=(0, 10))

        # Mode Activations
        mode_panel = tk.Frame(left_col, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, pady=10, padx=10)
        mode_panel.pack(fill="x", pady=(0, 10))

        tk.Label(mode_panel, text="OPERATING SYSTEM MODES", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 8))
        
        def make_mode_btn(text, mode_cmd, color):
            btn = tk.Button(mode_panel, text=text, font=("Consolas", 9, "bold"), bg="#101a30", fg=color, bd=1, highlightthickness=1, highlightbackground=self.border_color, pady=6, command=lambda: self.inject_command(mode_cmd))
            btn.pack(fill="x", pady=4)
            btn.bind("<Enter>", lambda e: btn.config(bg=color, fg="#050811"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#101a30", fg=color))

        make_mode_btn("📖 STUDY MODE", "study mode", self.blue_color)
        make_mode_btn("💻 CODING MOOD", "coding mood", self.purple_color)
        make_mode_btn("🎓 PLACEMENT MODE", "placement mode", self.green_color)
        make_mode_btn("💼 PROJECT MODE", "project mode", self.yellow_color)

        # Quick System Tools
        tools_panel = tk.Frame(left_col, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, pady=10, padx=10)
        tools_panel.pack(fill="both", expand=True)

        tk.Label(tools_panel, text="QUICK UTILITIES", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 8))

        def add_tool_btn(text, cmd, bg_col):
            btn = tk.Button(tools_panel, text=text, font=("Consolas", 8, "bold"), bg=bg_col, fg=self.text_color if bg_col != self.cyan_color else "#050811", bd=0, pady=5, command=cmd)
            btn.pack(fill="x", pady=3)
            self.make_btn_hoverable(btn, "#455a64", bg_col)

        add_tool_btn("📷 TAKE SCREENSHOT", self.trigger_screenshot, "#1a2a4a")
        add_tool_btn("📹 START SCREEN RECORD", self.trigger_record, "#1a2a4a")
        add_tool_btn("🎙 TEST MICROPHONE", self.test_microphone, "#1a2a4a")
        add_tool_btn("🔇 MUTE ASSISTANT", self.stop_listening, self.red_color)
        add_tool_btn("🔊 UNMUTE ASSISTANT", self.start_listening, self.green_color)
        add_tool_btn("🚪 EXIT SERVICES", self.quit_app, "#37474f")

        # CENTER COLUMN: VISUALIZER CORE & ACTIONS ROUTER (width=auto, wraps)
        center_col = tk.Frame(mid_container, bg=self.bg_color)
        center_col.pack(side="left", fill="both", expand=True, padx=10)

        # Visualizer Frame
        vis_panel = tk.Frame(center_col, bg=self.panel_color, height=270, bd=1, highlightbackground=self.purple_color, highlightthickness=1)
        vis_panel.pack(fill="x", pady=(0, 10))
        vis_panel.pack_propagate(False)

        tk.Label(vis_panel, text="CHINNI AI NEURAL CORE", font=("Consolas", 8, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", padx=10, pady=(10, 0))

        self.canvas = tk.Canvas(vis_panel, width=220, height=220, bg=self.panel_color, highlightthickness=0)
        self.canvas.pack(pady=(0, 10))

        self.status = tk.Label(vis_panel, text="Status: Online & Idle", font=("Consolas", 10, "bold"), fg=self.text_color, bg=self.panel_color)
        self.status.place(x=15, y=235)

        # Action Router details
        router_panel = tk.Frame(center_col, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=10, pady=10)
        router_panel.pack(fill="both", expand=True)

        tk.Label(router_panel, text="ACTION INTENT DECODER", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", padx=15, pady=(10, 5))

        grid_frame = tk.Frame(router_panel, bg=self.panel_color)
        grid_frame.pack(fill="x", padx=15, pady=2)
        grid_frame.columnconfigure(1, weight=1)

        def add_info_row(row_idx, label_text, color=None):
            tk.Label(grid_frame, text=label_text, font=("Consolas", 8), fg=self.subtext_color, bg=self.panel_color, anchor="w").grid(row=row_idx, column=0, sticky="w", pady=2)
            lbl_val = tk.Label(grid_frame, text="-", font=("Segoe UI", 9, "bold"), fg=color or self.text_color, bg=self.panel_color, anchor="w", wraplength=320, justify="left")
            lbl_val.grid(row=row_idx, column=1, sticky="w", padx=(10, 0), pady=2)
            return lbl_val

        self.val_heard = add_info_row(0, "Heard phrase:")
        self.val_intent = add_info_row(1, "Parsed Intent:", self.cyan_color)
        self.val_target = add_info_row(2, "Parameter target:")
        self.val_confidence = add_info_row(3, "Confidence rating:", self.purple_color)
        self.val_preview = add_info_row(4, "Action routing:", self.yellow_color)

        btn_frame = tk.Frame(router_panel, bg=self.panel_color)
        btn_frame.pack(fill="x", padx=15, pady=(10, 10))

        self.btn_confirm = tk.Button(
            btn_frame, text="CONFIRM ROUTE", font=("Consolas", 9, "bold"), bg=self.green_color, fg="#050811", 
            activebackground="#00c853", activeforeground="#050811", bd=0, padx=10, pady=5, command=self.trigger_confirm, state="disabled"
        )
        self.btn_confirm.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.make_btn_hoverable(self.btn_confirm, "#00c853", self.green_color, True)

        self.btn_cancel = tk.Button(
            btn_frame, text="CANCEL ROUTE", font=("Consolas", 9, "bold"), bg=self.red_color, fg=self.text_color, 
            activebackground="#d50000", activeforeground=self.text_color, bd=0, padx=10, pady=5, command=self.trigger_cancel, state="disabled"
        )
        self.btn_cancel.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.make_btn_hoverable(self.btn_cancel, "#d50000", self.red_color, True)

        # RIGHT COLUMN: SYSTEM METRIC GRAPH/BARS (260px)
        right_col = tk.Frame(mid_container, bg=self.bg_color, width=250)
        right_col.pack_propagate(False)
        right_col.pack(side="right", fill="y", padx=(10, 0))

        metrics_panel = tk.Frame(right_col, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, pady=10, padx=15)
        metrics_panel.pack(fill="both", expand=True)

        tk.Label(metrics_panel, text="SYSTEM METRICS MONITOR", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 15))

        def add_metric_bar(title, fg_color):
            tk.Label(metrics_panel, text=title, font=("Consolas", 8, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
            info_frame = tk.Frame(metrics_panel, bg=self.panel_color)
            info_frame.pack(fill="x", pady=(2, 4))
            
            p_bar = ttk.Progressbar(info_frame, orient="horizontal", mode="determinate", length=200)
            p_bar.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            lbl_val = tk.Label(info_frame, text="0%", font=("Segoe UI", 9, "bold"), fg=fg_color, bg=self.panel_color, width=5)
            lbl_val.pack(side="right")
            return p_bar, lbl_val

        self.cpu_bar, self.cpu_lbl = add_metric_bar("CPU UTILIATION", self.cyan_color)
        self.ram_bar, self.ram_lbl = add_metric_bar("RAM SATURATION", self.purple_color)
        self.gpu_bar, self.gpu_lbl = add_metric_bar("GPU ESTIMATED LOAD", self.yellow_color)
        self.bat_bar, self.bat_lbl = add_metric_bar("BATTERY CAPACITY", self.green_color)

        tk.Label(metrics_panel, text="BATTERY STATE:", font=("Consolas", 8, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(10, 0))
        self.lbl_bat_status = tk.Label(metrics_panel, text="Discharging", font=("Segoe UI", 9, "bold"), fg=self.text_color, bg=self.panel_color)
        self.lbl_bat_status.pack(anchor="w", pady=(0, 15))

        tk.Label(metrics_panel, text="NETWORK IO TRAFFIC:", font=("Consolas", 8, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.lbl_net_down = tk.Label(metrics_panel, text="Download: 0.0 KB/s", font=("Segoe UI", 9), fg=self.cyan_color, bg=self.panel_color)
        self.lbl_net_down.pack(anchor="w")
        self.lbl_net_up = tk.Label(metrics_panel, text="Upload: 0.0 KB/s", font=("Segoe UI", 9), fg=self.purple_color, bg=self.panel_color)
        self.lbl_net_up.pack(anchor="w", pady=(0, 20))

        # Bottom parameters info card row
        cards_frame = tk.Frame(metrics_panel, bg=self.panel_color)
        cards_frame.pack(fill="x")
        
        def add_sub_card(title, color):
            f = tk.Frame(cards_frame, bg="#101a30", bd=1, highlightbackground=self.border_color, highlightthickness=1, pady=3, padx=5)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=title, font=("Consolas", 7), fg=color, bg="#101a30").pack(anchor="w")
            val = tk.Label(f, text="-", font=("Segoe UI", 8, "bold"), fg=self.text_color, bg="#101a30")
            val.pack(anchor="w")
            return val

        self.card_mic = add_sub_card("MIC AUDIO CAPTURE", self.cyan_color)
        self.card_status = add_sub_card("SPEECH RECOGNIZER STATE", self.green_color)
        self.val_os_access = add_sub_card("SYSTEM OS PERMISSION", self.purple_color)

        self.card_status.config(text="Active")

        # BOTTOM CONVERSATION LOGS (Height=160)
        bottom_frame = tk.Frame(page, bg=self.bg_color, height=160)
        bottom_frame.pack_propagate(False)
        bottom_frame.pack(fill="x", pady=(15, 0))

        left_bottom = tk.Frame(bottom_frame, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=8)
        left_bottom.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left_bottom, text="MANUAL INSTRUCTION INPUT CORE", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 4))
        
        me_frame = tk.Frame(left_bottom, bg=self.panel_color)
        me_frame.pack(fill="x", pady=(0, 5))

        self.manual_entry = tk.Entry(me_frame, font=("Segoe UI", 10), bg="#1c1f2b", fg=self.text_color, insertbackground=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f", highlightcolor=self.cyan_color)
        self.manual_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=3)
        self.manual_entry.bind("<Return>", lambda e: self.submit_manual_command())

        btn_run = tk.Button(me_frame, text="EXECUTE", font=("Consolas", 9, "bold"), bg=self.cyan_color, fg="#050811", bd=0, padx=15, command=self.submit_manual_command)
        btn_run.pack(side="right", ipady=2)
        self.make_btn_hoverable(btn_run, "#00b2cc", self.cyan_color)

        tk.Label(left_bottom, text="Notifications: System is ready.", font=("Segoe UI", 8, "italic"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")

        # Logs panel
        logs_panel = tk.Frame(bottom_frame, bg=self.panel_color, width=450, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=8)
        logs_panel.pack_propagate(False)
        logs_panel.pack(side="right", fill="y", padx=(10, 0))

        tk.Label(logs_panel, text="SESSION ACTION AUDIT LOG", font=("Consolas", 8, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(0, 2))

        logs_container = tk.Frame(logs_panel, bg=self.panel_color)
        logs_container.pack(fill="both", expand=True)

        scr = tk.Scrollbar(logs_container)
        scr.pack(side="right", fill="y")

        self.history_listbox = tk.Listbox(
            logs_container, font=("Segoe UI", 8), bg="#050811", fg=self.subtext_color,
            selectbackground=self.purple_color, selectforeground=self.text_color, bd=0, highlightthickness=0, yscrollcommand=scr.set
        )
        self.history_listbox.pack(fill="both", expand=True)
        scr.config(command=self.history_listbox.yview)

    # ----------------- PAGE 2: CUSTOM COMMANDS -----------------
    def setup_commands_page(self):
        page = self.pages["commands"]

        hdr_frame = tk.Frame(page, bg=self.bg_color)
        hdr_frame.pack(fill="x", pady=(0, 15))

        tk.Label(hdr_frame, text="CUSTOM COMMAND SEQUENCE MACROS", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.bg_color).pack(side="left")

        btn_add = tk.Button(hdr_frame, text="➕ CREATE NEW MACRO", font=("Consolas", 9, "bold"), bg=self.purple_color, fg=self.text_color, bd=0, padx=12, pady=6, command=self.open_add_macro_dialog)
        btn_add.pack(side="right")
        self.make_btn_hoverable(btn_add, "#5e35b1", self.purple_color)

        list_panel = tk.Frame(page, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1)
        list_panel.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#0c1527", fieldbackground="#0c1527", foreground=self.text_color, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#101a30", foreground=self.cyan_color, borderwidth=0, font=("Consolas", 9, "bold"))
        style.map("Treeview", background=[("selected", self.purple_color)], foreground=[("selected", self.text_color)])

        self.tree_scroll = tk.Scrollbar(list_panel)
        self.tree_scroll.pack(side="right", fill="y")

        self.macro_tree = ttk.Treeview(list_panel, columns=("trigger", "aliases", "actions", "enabled"), show="headings", yscrollcommand=self.tree_scroll.set)
        self.macro_tree.heading("trigger", text="TRIGGER KEYWORD")
        self.macro_tree.heading("aliases", text="SYNONYM ALIASES")
        self.macro_tree.heading("actions", text="MACRO ACTIONS SEQUENCE")
        self.macro_tree.heading("enabled", text="STATUS")
        
        self.macro_tree.column("trigger", width=150, anchor="w")
        self.macro_tree.column("aliases", width=200, anchor="w")
        self.macro_tree.column("actions", width=350, anchor="w")
        self.macro_tree.column("enabled", width=80, anchor="center")
        
        self.macro_tree.pack(fill="both", expand=True)
        self.tree_scroll.config(command=self.macro_tree.yview)

        ctrl_frame = tk.Frame(page, bg=self.bg_color)
        ctrl_frame.pack(fill="x", pady=(15, 0))

        btn_toggle = tk.Button(ctrl_frame, text="ENABLE / DISABLE", font=("Consolas", 8, "bold"), bg="#1a2a4a", fg=self.text_color, bd=0, padx=12, pady=7, command=self.toggle_macro_status)
        btn_toggle.pack(side="left", padx=(0, 10))
        self.make_btn_hoverable(btn_toggle, "#455a64", "#1a2a4a")

        btn_edit = tk.Button(ctrl_frame, text="✏ EDIT SELECTED", font=("Consolas", 8, "bold"), bg=self.cyan_color, fg="#050811", bd=0, padx=12, pady=7, command=self.open_edit_macro_dialog)
        btn_edit.pack(side="left", padx=10)
        self.make_btn_hoverable(btn_edit, "#00b2cc", self.cyan_color)

        btn_del = tk.Button(ctrl_frame, text="❌ DELETE SELECTED", font=("Consolas", 8, "bold"), bg=self.red_color, fg=self.text_color, bd=0, padx=12, pady=7, command=self.delete_macro)
        btn_del.pack(side="right")
        self.make_btn_hoverable(btn_del, "#d50000", self.red_color)

    # ----------------- PAGE 3: NOTES MANAGER -----------------
    def setup_notes_page(self):
        page = self.pages["notes"]

        tk.Label(page, text="PERSISTENT SYSTEM MEMORY NOTES", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.bg_color).pack(anchor="w", pady=(0, 15))

        notes_container = tk.Frame(page, bg=self.bg_color)
        notes_container.pack(fill="both", expand=True)

        # Form (Left side)
        form_panel = tk.Frame(notes_container, bg=self.panel_color, width=280, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        form_panel.pack_propagate(False)
        form_panel.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(form_panel, text="CREATE NEW NOTE", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))
        
        tk.Label(form_panel, text="Title:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.note_title_entry = tk.Entry(form_panel, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.note_title_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(form_panel, text="Content Details:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.note_content_text = tk.Text(form_panel, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f", height=12)
        self.note_content_text.pack(fill="x", pady=(2, 15))

        btn_save_note = tk.Button(form_panel, text="💾 SAVE NOTE", font=("Consolas", 9, "bold"), bg=self.green_color, fg="#050811", bd=0, pady=7, command=self.save_note_ui)
        btn_save_note.pack(fill="x")
        self.make_btn_hoverable(btn_save_note, "#00c853", self.green_color)

        # List (Right side)
        list_panel = tk.Frame(notes_container, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        list_panel.pack(side="right", fill="both", expand=True)

        tk.Label(list_panel, text="SAVED NOTES DATABASE", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))

        scr = tk.Scrollbar(list_panel)
        scr.pack(side="right", fill="y")

        self.notes_list = ttk.Treeview(list_panel, columns=("id", "title", "content", "date"), show="headings", yscrollcommand=scr.set)
        self.notes_list.heading("id", text="ID")
        self.notes_list.heading("title", text="TITLE")
        self.notes_list.heading("content", text="DETAILS")
        self.notes_list.heading("date", text="DATE RECORDED")
        
        self.notes_list.column("id", width=40, anchor="center")
        self.notes_list.column("title", width=120, anchor="w")
        self.notes_list.column("content", width=250, anchor="w")
        self.notes_list.column("date", width=110, anchor="center")

        self.notes_list.pack(fill="both", expand=True)
        scr.config(command=self.notes_list.yview)

        btn_del_note = tk.Button(list_panel, text="❌ DELETE SELECTED NOTE", font=("Consolas", 8, "bold"), bg=self.red_color, fg=self.text_color, bd=0, pady=6, padx=12, command=self.delete_note_ui)
        btn_del_note.pack(anchor="e", pady=(10, 0))
        self.make_btn_hoverable(btn_del_note, "#d50000", self.red_color)

    # ----------------- PAGE 4: TASK PLANNER -----------------
    def setup_tasks_page(self):
        page = self.pages["tasks"]

        tk.Label(page, text="STUDY PLANNER & TASK SCHEDULER", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.bg_color).pack(anchor="w", pady=(0, 15))

        tasks_container = tk.Frame(page, bg=self.bg_color)
        tasks_container.pack(fill="both", expand=True)

        # Form panel
        form = tk.Frame(tasks_container, bg=self.panel_color, width=280, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        form.pack_propagate(False)
        form.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(form, text="SCHEDULE NEW TASK", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="Task Name:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.task_name_entry = tk.Entry(form, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.task_name_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(form, text="Deadline Date (YYYY-MM-DD):", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.task_deadline_entry = tk.Entry(form, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.task_deadline_entry.pack(fill="x", pady=(2, 10), ipady=3)
        self.task_deadline_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(form, text="Initial Status:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.task_status_combo = ttk.Combobox(form, font=("Segoe UI", 9), values=("Pending", "In Progress", "Completed"), state="readonly")
        self.task_status_combo.set("Pending")
        self.task_status_combo.pack(fill="x", pady=(2, 20), ipady=2)

        btn_add_t = tk.Button(form, text="📋 CREATE TASK", font=("Consolas", 9, "bold"), bg=self.green_color, fg="#050811", bd=0, pady=7, command=self.save_task_ui)
        btn_add_t.pack(fill="x")
        self.make_btn_hoverable(btn_add_t, "#00c853", self.green_color)

        # List panel
        list_p = tk.Frame(tasks_container, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        list_p.pack(side="right", fill="both", expand=True)

        tk.Label(list_p, text="ACTIVE SCHEDULER BOARD", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))

        scr = tk.Scrollbar(list_p)
        scr.pack(side="right", fill="y")

        self.tasks_tree = ttk.Treeview(list_p, columns=("id", "name", "status", "deadline"), show="headings", yscrollcommand=scr.set)
        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("name", text="TASK DESCRIPTION")
        self.tasks_tree.heading("status", text="STATUS")
        self.tasks_tree.heading("deadline", text="DEADLINE TARGET")
        
        self.tasks_tree.column("id", width=40, anchor="center")
        self.tasks_tree.column("name", width=250, anchor="w")
        self.tasks_tree.column("status", width=90, anchor="center")
        self.tasks_tree.column("deadline", width=100, anchor="center")

        self.tasks_tree.pack(fill="both", expand=True)
        scr.config(command=self.tasks_tree.yview)

        ctrls = tk.Frame(list_p, bg=self.panel_color)
        ctrls.pack(fill="x", pady=(10, 0))

        btn_prog = tk.Button(ctrls, text="IN PROGRESS", font=("Consolas", 8, "bold"), bg=self.purple_color, fg=self.text_color, bd=0, pady=6, padx=10, command=lambda: self.update_task_status_ui("In Progress"))
        btn_prog.pack(side="left", padx=(0, 5))
        self.make_btn_hoverable(btn_prog, "#5e35b1", self.purple_color)

        btn_comp = tk.Button(ctrls, text="MARK COMPLETE", font=("Consolas", 8, "bold"), bg=self.green_color, fg="#050811", bd=0, pady=6, padx=10, command=lambda: self.update_task_status_ui("Completed"))
        btn_comp.pack(side="left", padx=5)
        self.make_btn_hoverable(btn_comp, "#00c853", self.green_color)

        btn_del_t = tk.Button(ctrls, text="DELETE TASK", font=("Consolas", 8, "bold"), bg=self.red_color, fg=self.text_color, bd=0, pady=6, padx=10, command=self.delete_task_ui)
        btn_del_t.pack(side="right")
        self.make_btn_hoverable(btn_del_t, "#d50000", self.red_color)

    # ----------------- PAGE 5: PROJECTS PORTFOLIO -----------------
    def setup_projects_page(self):
        page = self.pages["projects"]

        tk.Label(page, text="PLACEMENT TRACKER & PROJECTS PORTFOLIO", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.bg_color).pack(anchor="w", pady=(0, 15))

        proj_container = tk.Frame(page, bg=self.bg_color)
        proj_container.pack(fill="both", expand=True)

        # Form
        form = tk.Frame(proj_container, bg=self.panel_color, width=280, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        form.pack_propagate(False)
        form.pack(side="left", fill="y", padx=(0, 15))

        tk.Label(form, text="RECORD NEW PROJECT / TASK", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="Project Name / Area:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.proj_name_entry = tk.Entry(form, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.proj_name_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(form, text="Focus / Details:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.proj_details_entry = tk.Entry(form, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.proj_details_entry.pack(fill="x", pady=(2, 10), ipady=3)

        tk.Label(form, text="Target Date (YYYY-MM-DD):", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.proj_deadline_entry = tk.Entry(form, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f")
        self.proj_deadline_entry.pack(fill="x", pady=(2, 10), ipady=3)
        self.proj_deadline_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(form, text="Status:", font=("Segoe UI", 9), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w")
        self.proj_status_combo = ttk.Combobox(form, font=("Segoe UI", 9), values=("In Progress", "Completed", "Review Stage"), state="readonly")
        self.proj_status_combo.set("In Progress")
        self.proj_status_combo.pack(fill="x", pady=(2, 20), ipady=2)

        btn_add_p = tk.Button(form, text="💼 SAVE PORTFOLIO", font=("Consolas", 9, "bold"), bg=self.green_color, fg="#050811", bd=0, pady=7, command=self.save_project_ui)
        btn_add_p.pack(fill="x")
        self.make_btn_hoverable(btn_add_p, "#00c853", self.green_color)

        # List
        list_p = tk.Frame(proj_container, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=15, pady=15)
        list_p.pack(side="right", fill="both", expand=True)

        tk.Label(list_p, text="PLACEMENT PORTFOLIO TRACKER", font=("Consolas", 9, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", pady=(0, 10))

        scr = tk.Scrollbar(list_p)
        scr.pack(side="right", fill="y")

        self.proj_tree = ttk.Treeview(list_p, columns=("id", "name", "details", "status", "deadline", "countdown"), show="headings", yscrollcommand=scr.set)
        self.proj_tree.heading("id", text="ID")
        self.proj_tree.heading("name", text="PROJECT / PLACEMENT WORK")
        self.proj_tree.heading("details", text="DESCRIPTION")
        self.proj_tree.heading("status", text="STATUS")
        self.proj_tree.heading("deadline", text="DEADLINE")
        self.proj_tree.heading("countdown", text="DAYS LEFT")
        
        self.proj_tree.column("id", width=30, anchor="center")
        self.proj_tree.column("name", width=150, anchor="w")
        self.proj_tree.column("details", width=180, anchor="w")
        self.proj_tree.column("status", width=90, anchor="center")
        self.proj_tree.column("deadline", width=80, anchor="center")
        self.proj_tree.column("countdown", width=80, anchor="center")

        self.proj_tree.pack(fill="both", expand=True)
        scr.config(command=self.proj_tree.yview)

        btn_del_p = tk.Button(list_p, text="❌ DELETE PORTFOLIO ENTRY", font=("Consolas", 8, "bold"), bg=self.red_color, fg=self.text_color, bd=0, pady=6, padx=12, command=self.delete_project_ui)
        btn_del_p.pack(anchor="e", pady=(10, 0))
        self.make_btn_hoverable(btn_del_p, "#d50000", self.red_color)

    # ----------------- PAGE 6: SETTINGS -----------------
    def setup_settings_page(self):
        page = self.pages["settings"]

        tk.Label(page, text="PREFERENCES & OS ACCESS CONTROL", font=("Consolas", 15, "bold"), fg=self.cyan_color, bg=self.bg_color).pack(anchor="w", pady=(0, 15))

        form_panel = tk.Frame(page, bg=self.panel_color, bd=1, highlightbackground=self.border_color, highlightthickness=1, padx=25, pady=25)
        form_panel.pack(fill="both", expand=True)

        # 1. Microphone Selection Dropdown
        tk.Label(form_panel, text="Preferred Voice Microphone Input:", font=("Consolas", 9, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(0, 4))
        
        mic_frame = tk.Frame(form_panel, bg=self.panel_color)
        mic_frame.pack(fill="x", pady=(0, 15))

        self.combo_mic = ttk.Combobox(mic_frame, font=("Segoe UI", 9), state="readonly")
        self.combo_mic.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=3)
        self.populate_mics_dropdown()

        btn_test_mic = tk.Button(mic_frame, text="🎤 TEST MIC", font=("Consolas", 9, "bold"), bg="#101a30", fg=self.text_color, bd=1, highlightthickness=1, highlightbackground=self.border_color, padx=15, command=self.test_microphone)
        btn_test_mic.pack(side="right", ipady=2)
        self.make_btn_hoverable(btn_test_mic, "#455a64", "#101a30")

        # 2. Antigravity IDE custom path
        tk.Label(form_panel, text="Antigravity IDE Executable Path:", font=("Consolas", 9, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(0, 4))

        path_frame = tk.Frame(form_panel, bg=self.panel_color)
        path_frame.pack(fill="x", pady=(0, 15))

        self.entry_ide_path = tk.Entry(path_frame, font=("Segoe UI", 9), bg="#1c1f2b", fg=self.text_color, insertbackground=self.text_color, bd=0, highlightthickness=1, highlightbackground="#37474f", highlightcolor=self.cyan_color)
        self.entry_ide_path.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=4)

        btn_browse = tk.Button(path_frame, text="BROWSE...", font=("Consolas", 9, "bold"), bg="#101a30", fg=self.text_color, bd=1, highlightthickness=1, highlightbackground=self.border_color, padx=15, command=self.browse_ide_path)
        btn_browse.pack(side="right", ipady=2)
        self.make_btn_hoverable(btn_browse, "#455a64", "#101a30")

        # 3. Browser Preferences
        tk.Label(form_panel, text="Preferred Web Browser Behavior:", font=("Consolas", 9, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(0, 4))

        self.combo_browser = ttk.Combobox(form_panel, font=("Segoe UI", 9), state="readonly")
        self.combo_browser["values"] = ("Default Browser", "Chrome", "Edge")
        self.combo_browser.pack(anchor="w", fill="x", pady=(0, 15), ipady=3)

        # 4. Startup shortcuts
        tk.Label(form_panel, text="Startup Integration Controls:", font=("Consolas", 9, "bold"), fg=self.subtext_color, bg=self.panel_color).pack(anchor="w", pady=(0, 4))
        self.chk_startup_var = tk.BooleanVar(value=False)
        self.chk_startup = tk.Checkbutton(form_panel, text="Launch Chinni AI automatically when Windows starts", font=("Segoe UI", 9), variable=self.chk_startup_var, bg=self.panel_color, fg=self.text_color, selectcolor="#050811", activebackground=self.panel_color, activeforeground=self.text_color, command=self.toggle_windows_startup)
        self.chk_startup.pack(anchor="w", pady=(0, 15))

        # Checkboxes
        self.chk_bg = tk.BooleanVar(value=True)
        self.chk_bg_listener = tk.Checkbutton(form_panel, text="Enable background listening when app is minimized", font=("Segoe UI", 9), variable=self.chk_bg, bg=self.panel_color, fg=self.text_color, selectcolor="#050811", bd=0, activebackground=self.panel_color, activeforeground=self.text_color)
        self.chk_bg_listener.pack(anchor="w", pady=2)

        self.chk_wake = tk.BooleanVar(value=False)
        self.chk_wake_cmd = tk.Checkbutton(form_panel, text="Enable wake words filtering ('Hey Chinni' or 'Chinni')", font=("Segoe UI", 9), variable=self.chk_wake, bg=self.panel_color, fg=self.text_color, selectcolor="#050811", bd=0, activebackground=self.panel_color, activeforeground=self.text_color)
        self.chk_wake_cmd.pack(anchor="w", pady=2)

        self.chk_auto = tk.BooleanVar(value=True)
        self.chk_auto_safe = tk.Checkbutton(form_panel, text="Auto-execute safe commands directly without confirming", font=("Segoe UI", 9), variable=self.chk_auto, bg=self.panel_color, fg=self.text_color, selectcolor="#050811", bd=0, activebackground=self.panel_color, activeforeground=self.text_color)
        self.chk_auto_safe.pack(anchor="w", pady=(2, 20))

        # Save Button
        btn_save = tk.Button(form_panel, text="💾 SAVE SYSTEM SETTINGS", font=("Consolas", 10, "bold"), bg=self.cyan_color, fg="#050811", bd=0, pady=8, command=self.save_settings_ui)
        btn_save.pack(fill="x")
        self.make_btn_hoverable(btn_save, "#00b2cc", self.cyan_color)

    # ----------------- POPUPS & METADATA MANAGERS -----------------
    def check_os_access_on_startup(self):
        allowed = db.get_setting("os_access_allowed", "0")
        if allowed == "0":
            confirm = messagebox.askyesno(
                "Chinni AI OS Access Permission Required",
                "Do you want to allow Chinni to control your system operations?"
            )
            if confirm:
                db.set_setting("os_access_allowed", "1")
                self.val_os_access.config(text="ALLOWED", fg=self.green_color)
            else:
                db.set_setting("os_access_allowed", "0")
                self.val_os_access.config(text="BLOCKED", fg=self.red_color)
        else:
            self.val_os_access.config(text="ALLOWED", fg=self.green_color)

    def toggle_windows_startup(self):
        import tray_service
        if self.chk_startup_var.get():
            if tray_service.add_to_startup():
                messagebox.showinfo("Startup Registered", "Chinni AI will now run automatically on Windows startup.")
            else:
                self.chk_startup_var.set(False)
        else:
            if tray_service.remove_from_startup():
                messagebox.showinfo("Startup Removed", "Chinni AI will no longer launch on Windows startup.")
            else:
                self.chk_startup_var.set(True)

    def run_top_search(self):
        query = self.top_search.get().strip()
        if query:
            self.top_search.delete(0, tk.END)
            self.inject_command("search " + query)

    def toggle_wifi(self):
        self.wifi_state = not self.wifi_state
        if system_actions.set_wifi_state(self.wifi_state):
            self.btn_wifi.config(text="📶 WIFI: ON" if self.wifi_state else "📶 WIFI: OFF")
            messagebox.showinfo("WiFi Command", f"WiFi interface set to {'ENABLED' if self.wifi_state else 'DISABLED'}.")
        else:
            self.wifi_state = not self.wifi_state
            messagebox.showwarning("WiFi Command", "WiFi command failed (requires Admin privileges).")

    def toggle_bluetooth(self):
        self.bluetooth_state = not self.bluetooth_state
        state_str = "on" if self.bluetooth_state else "off"
        # Run process trigger
        self.inject_command(f"turn {state_str} bluetooth")
        self.btn_bt.config(text=f"🔵 BT: ON" if self.bluetooth_state else "🔵 BT: OFF")

    def toggle_dark_theme(self):
        self.dark_mode_state = not self.dark_mode_state
        if system_actions.set_dark_mode(self.dark_mode_state):
            self.btn_dark.config(text="🌙 DARK MODE" if self.dark_mode_state else "☀️ LIGHT MODE")
            messagebox.showinfo("Theme Command", f"System Apps theme set to {'DARK' if self.dark_mode_state else 'LIGHT'}.")
        else:
            self.dark_mode_state = not self.dark_mode_state

    # ----------------- DB BINDINGS NOTES -----------------
    def refresh_notes_ui(self):
        for item in self.notes_list.get_children():
            self.notes_list.delete(item)
        notes = db.get_all_notes()
        for n in notes:
            self.notes_list.insert("", "end", values=(n["id"], n["title"], n["content"][:60], n["created_at"]))

    def save_note_ui(self):
        title = self.note_title_entry.get().strip()
        content = self.note_content_text.get("1.0", tk.END).strip()
        if not title or not content:
            messagebox.showwarning("Incomplete Form", "Both note title and content description are required.")
            return
        db.add_note(title, content)
        self.note_title_entry.delete(0, tk.END)
        self.note_content_text.delete("1.0", tk.END)
        self.refresh_notes_ui()
        messagebox.showinfo("Success", "System note saved successfully.")

    def delete_note_ui(self):
        selected = self.notes_list.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a note from the tree view to delete.")
            return
        note_id = self.notes_list.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete note ID {note_id}?"):
            db.delete_note(note_id)
            self.refresh_notes_ui()

    # ----------------- DB BINDINGS TASKS -----------------
    def refresh_tasks_ui(self):
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        tasks = db.get_all_tasks()
        for t in tasks:
            self.tasks_tree.insert("", "end", values=(t["id"], t["task_name"], t["status"], t["deadline"]))

    def save_task_ui(self):
        name = self.task_name_entry.get().strip()
        deadline = self.task_deadline_entry.get().strip()
        status = self.task_status_combo.get()
        if not name:
            messagebox.showwarning("Incomplete Form", "Task Description is required.")
            return
        db.add_task(name, status, deadline)
        self.task_name_entry.delete(0, tk.END)
        self.refresh_tasks_ui()
        messagebox.showinfo("Success", "Task scheduled successfully.")

    def update_task_status_ui(self, status):
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a task from the list.")
            return
        task_id = self.tasks_tree.item(selected[0])["values"][0]
        db.update_task_status(task_id, status)
        self.refresh_tasks_ui()

    def delete_task_ui(self):
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a task to delete.")
            return
        task_id = self.tasks_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to cancel/delete task ID {task_id}?"):
            db.delete_task(task_id)
            self.refresh_tasks_ui()

    # ----------------- DB BINDINGS PROJECTS -----------------
    def refresh_projects_ui(self):
        for item in self.proj_tree.get_children():
            self.proj_tree.delete(item)
        projects = db.get_all_projects()
        for p in projects:
            det = p["details"].get("info", "-")
            deadline_str = p["deadline"]
            days_left = "-"
            if deadline_str:
                try:
                    target_dt = datetime.strptime(deadline_str, "%Y-%m-%d")
                    diff = target_dt - datetime.now()
                    days_left = str(max(0, diff.days + 1))
                except Exception:
                    pass
            self.proj_tree.insert("", "end", values=(p["id"], p["project_name"], det, p["status"], deadline_str, days_left))

    def save_project_ui(self):
        name = self.proj_name_entry.get().strip()
        details = {"info": self.proj_details_entry.get().strip()}
        deadline = self.proj_deadline_entry.get().strip()
        status = self.proj_status_combo.get()
        if not name:
            messagebox.showwarning("Incomplete Form", "Project Name is required.")
            return
        db.add_project(name, details, deadline, status)
        self.proj_name_entry.delete(0, tk.END)
        self.proj_details_entry.delete(0, tk.END)
        self.refresh_projects_ui()
        messagebox.showinfo("Success", "Portfolio item saved successfully.")

    def delete_project_ui(self):
        selected = self.proj_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a project to delete.")
            return
        project_id = self.proj_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete portfolio entry ID {project_id}?"):
            db.delete_project(project_id)
            self.refresh_projects_ui()

    # ----------------- METRICS THREAD -----------------
    def start_metrics_thread(self):
        def run():
            last_net = psutil.net_io_counters()
            last_time = time.time()
            while True:
                if not self.root.winfo_exists():
                    break
                time.sleep(1.0)
                try:
                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    
                    battery = psutil.sensors_battery()
                    bat_percent = battery.percent if battery else 100
                    bat_status = "Charging" if (battery and battery.power_plugged) else "Discharging"
                    
                    gpu_load = max(0, min(100, int(cpu * 0.4 + (ram * 0.1))))
                    
                    curr_net = psutil.net_io_counters()
                    curr_time = time.time()
                    dt = curr_time - last_time
                    if dt > 0:
                        down_speed = (curr_net.bytes_recv - last_net.bytes_recv) / dt / 1024.0
                        up_speed = (curr_net.bytes_sent - last_net.bytes_sent) / dt / 1024.0
                    else:
                        down_speed, up_speed = 0.0, 0.0
                    
                    last_net = curr_net
                    last_time = curr_time
                    
                    if self.root.winfo_exists():
                        self.root.after(0, self.update_metrics_labels, cpu, ram, bat_percent, bat_status, gpu_load, down_speed, up_speed)
                except Exception as e:
                    print(f"Metrics update error: {e}")
        Thread(target=run, daemon=True).start()

    def update_metrics_labels(self, cpu, ram, bat_p, bat_s, gpu, down, up):
        self.cpu_bar["value"] = cpu
        self.cpu_lbl.config(text=f"{int(cpu)}%")
        
        self.ram_bar["value"] = ram
        self.ram_lbl.config(text=f"{int(ram)}%")
        
        self.gpu_bar["value"] = gpu
        self.gpu_lbl.config(text=f"{int(gpu)}%")
        
        self.bat_bar["value"] = bat_p
        self.bat_lbl.config(text=f"{int(bat_p)}%")
        
        self.lbl_bat_status.config(text=bat_s)
        self.lbl_net_down.config(text=f"Download: {down:.1f} KB/s")
        self.lbl_net_up.config(text=f"Upload: {up:.1f} KB/s")

    # ----------------- TRAY & MINIMIZE RESTORE -----------------
    def on_minimize(self, event):
        if event.widget == self.root:
            is_bg_enabled = db.get_setting("background_listening", "1") == "1"
            if is_bg_enabled:
                Thread(target=run_notification_listener, args=(self,), daemon=True).start()

    def start_listening(self):
        self.is_listening = True
        self.card_status.config(text="Active Listening", fg=self.green_color)
        self.lbl_status_core.config(text="CHINNI CORE: ONLINE", fg=self.green_color)
        self.status_indicator.delete("dot")
        self.status_indicator.create_oval(2, 2, 13, 13, fill=self.green_color, tags="dot")
        if self.on_toggle_listening_callback:
            self.on_toggle_listening_callback(True)
        self.update_status("Online & Listening")

    def stop_listening(self):
        self.is_listening = False
        self.card_status.config(text="Muted / Suspended", fg=self.red_color)
        self.lbl_status_core.config(text="CHINNI CORE: MUTED", fg=self.red_color)
        self.status_indicator.delete("dot")
        self.status_indicator.create_oval(2, 2, 13, 13, fill=self.red_color, tags="dot")
        if self.on_toggle_listening_callback:
            self.on_toggle_listening_callback(False)
        self.update_status("Online & Muted")

    def quit_app(self):
        if messagebox.askyesno("Exit Chinni AI", "Are you sure you want to stop Chinni AI services?"):
            self.root.quit()

    # ----------------- MICROPHONE CONTROLS -----------------
    def populate_mics_dropdown(self):
        devices = mic_manager.get_input_devices()
        device_names = [d["name"] for d in devices]
        self.combo_mic["values"] = device_names
        
        active_name = mic_manager.get_active_mic_name()
        if active_name in device_names:
            self.combo_mic.set(active_name)
        elif device_names:
            self.combo_mic.set(device_names[0])

    def test_microphone(self):
        self.update_status("Testing Microphone...")
        def run_test():
            import pyaudio
            p = pyaudio.PyAudio()
            try:
                index = mic_manager.get_active_mic_index()
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=index,
                    frames_per_buffer=1024
                )
                data = stream.read(1024, exception_on_overflow=False)
                stream.stop_stream()
                stream.close()
                if len(data) > 0:
                    messagebox.showinfo("Mic Sandbox Test", f"Microphone Sandbox Test successful! Data packets captured from {mic_manager.get_active_mic_name()}.")
                else:
                    messagebox.showwarning("Mic Sandbox Test", "No audio packets captured. Check device driver.")
            except Exception as e:
                messagebox.showerror("Mic Sandbox Test", f"Microphone Sandbox Test failed: {e}")
            finally:
                p.terminate()
                self.update_status("Online & Idle")
        Thread(target=run_test, daemon=True).start()

    # ----------------- CUSTOM MACROS DIALOGS -----------------
    def open_add_macro_dialog(self):
        self.macro_dialog("Add Custom Macro", mode="add")

    def open_edit_macro_dialog(self):
        selected = self.macro_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a macro from the list.")
            return
        trigger_phrase = self.macro_tree.item(selected[0])["values"][0]
        commands = db.get_all_custom_commands()
        target_cmd = None
        for cmd in commands:
            if cmd["trigger_phrase"] == trigger_phrase:
                target_cmd = cmd
                break
        if target_cmd:
            self.macro_dialog("Edit Custom Macro", mode="edit", macro=target_cmd)

    def macro_dialog(self, title, mode="add", macro=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("460x320")
        dialog.configure(bg=self.panel_color)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Voice Trigger Phrase:", font=("Consolas", 10, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", padx=20, pady=(15, 2))
        entry_trig = tk.Entry(dialog, font=("Segoe UI", 10), bg="#050811", fg=self.text_color, bd=1, highlightthickness=0, insertbackground=self.text_color)
        entry_trig.pack(fill="x", padx=20, ipady=3)
        if mode == "edit":
            entry_trig.insert(0, macro["trigger_phrase"])
            entry_trig.config(state="disabled")

        tk.Label(dialog, text="Aliases / Similar Phrases (comma-separated):", font=("Consolas", 10, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", padx=20, pady=(12, 2))
        entry_aliases = tk.Entry(dialog, font=("Segoe UI", 10), bg="#050811", fg=self.text_color, bd=1, highlightthickness=0, insertbackground=self.text_color)
        entry_aliases.pack(fill="x", padx=20, ipady=3)
        if mode == "edit" and macro["aliases"]:
            entry_aliases.insert(0, ", ".join(macro["aliases"]))

        tk.Label(dialog, text="Execute Action Sequence (comma-separated):", font=("Consolas", 10, "bold"), fg=self.cyan_color, bg=self.panel_color).pack(anchor="w", padx=20, pady=(12, 2))
        entry_acts = tk.Entry(dialog, font=("Segoe UI", 10), bg="#050811", fg=self.text_color, bd=1, highlightthickness=0, insertbackground=self.text_color)
        entry_acts.pack(fill="x", padx=20, ipady=3)
        if mode == "edit":
            entry_acts.insert(0, ", ".join(macro["actions"]))

        btn_frame = tk.Frame(dialog, bg=self.panel_color)
        btn_frame.pack(fill="x", padx=20, pady=20)

        def save_macro():
            trig = entry_trig.get().strip() if mode == "add" else macro["trigger_phrase"]
            aliases_raw = entry_aliases.get().strip()
            acts_raw = entry_acts.get().strip()
            
            if not trig or not acts_raw:
                messagebox.showwarning("Incomplete Form", "Trigger Phrase and Actions list are required.")
                return
                
            aliases_list = [a.strip() for a in aliases_raw.split(",") if a.strip()]
            actions_list = [a.strip() for a in acts_raw.split(",") if a.strip()]
            
            if mode == "add":
                success = db.add_custom_command(trig, actions_list, aliases_list)
            else:
                success = db.update_custom_command(macro["id"], trig, actions_list, aliases_list, 1 if macro["enabled"] else 0)
                
            if success:
                messagebox.showinfo("Success", "Custom Command Macro saved successfully!")
                dialog.destroy()
                self.refresh_custom_commands_ui()
            else:
                messagebox.showerror("Error", "Could not save custom macro. Trigger phrases must be unique.")

        btn_save = tk.Button(btn_frame, text="SAVE MACRO", font=("Consolas", 9, "bold"), bg=self.cyan_color, fg="#050811", bd=0, padx=15, pady=6, command=save_macro)
        btn_save.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.make_btn_hoverable(btn_save, "#00b2cc", self.cyan_color)

        btn_cancel = tk.Button(btn_frame, text="CANCEL", font=("Consolas", 9, "bold"), bg=self.red_color, fg=self.text_color, bd=0, padx=15, pady=6, command=dialog.destroy)
        btn_cancel.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.make_btn_hoverable(btn_cancel, "#d50000", self.red_color)

    # ----------------- UI CONTROLS SYNC -----------------
    def browse_ide_path(self):
        path = filedialog.askopenfilename(title="Select Antigravity IDE Executable", filetypes=(("Executable Files", "*.exe"), ("All Files", "*.*")))
        if path:
            self.entry_ide_path.delete(0, tk.END)
            self.entry_ide_path.insert(0, path)

    def load_settings_ui(self):
        path_info = db.get_app_path("Antigravity IDE")
        path = path_info["executable_path"] if path_info else ""
        self.entry_ide_path.delete(0, tk.END)
        self.entry_ide_path.insert(0, path)
        
        br = db.get_setting("browser_pref", "default")
        br_map = {"default": "Default Browser", "chrome": "Chrome", "edge": "Edge"}
        self.combo_browser.set(br_map.get(br, "Default Browser"))
        
        self.chk_bg.set(db.get_setting("background_listening", "1") == "1")
        self.chk_wake.set(db.get_setting("wake_command_enabled", "0") == "1")
        self.chk_auto.set(db.get_setting("auto_execute_safe", "1") == "1")

        import tray_service
        self.chk_startup_var.set(tray_service.is_startup_enabled())

        self.populate_mics_dropdown()

    def save_settings_ui(self):
        ide_path = self.entry_ide_path.get().strip()
        db.set_app_path("Antigravity IDE", ide_path, "")
        
        br_val_map = {"Default Browser": "default", "Chrome": "chrome", "Edge": "edge"}
        db.set_setting("browser_pref", br_val_map.get(self.combo_browser.get(), "default"))
        
        db.set_setting("background_listening", "1" if self.chk_bg.get() else "0")
        db.set_setting("wake_command_enabled", "1" if self.chk_wake.get() else "0")
        db.set_setting("auto_execute_safe", "1" if self.chk_auto.get() else "0")
        
        selected_mic = self.combo_mic.get()
        if selected_mic:
            mic_manager.select_device_by_name(selected_mic)
            
        messagebox.showinfo("Saved Settings", "Chinni AI preferences saved successfully.")
        self.sync_dashboard_mic_info()

    def refresh_custom_commands_ui(self):
        for item in self.macro_tree.get_children():
            self.macro_tree.delete(item)
        commands = db.get_all_custom_commands()
        for cmd in commands:
            status_text = "ENABLED" if cmd["enabled"] else "DISABLED"
            self.macro_tree.insert("", "end", values=(
                cmd["trigger_phrase"],
                ", ".join(cmd["aliases"]),
                ", ".join(cmd["actions"]),
                status_text
            ))

    def refresh_history_ui(self):
        self.history_listbox.delete(0, tk.END)
        logs = db.get_action_logs(25)
        for log in logs:
            status_icon = "✔" if log["status"] == "executed" else ("引导" if log["status"] == "confirming" else ("✘" if log["status"] == "cancelled" else "❓"))
            self.history_listbox.insert(
                tk.END,
                f"[{log['timestamp']}] {status_icon} {log['phrase']} ({log['intent']}) -> {log['action']}"
            )

    def sync_dashboard_mic_info(self):
        mic_name = mic_manager.get_active_mic_name()
        self.card_mic.config(text=mic_name[:20] + "..." if len(mic_name) > 20 else mic_name)
        
        allowed = db.get_setting("os_access_allowed", "0")
        self.val_os_access.config(text="ALLOWED" if allowed == "1" else "BLOCKED", fg=self.green_color if allowed == "1" else self.red_color)

    def toggle_macro_status(self):
        selected = self.macro_tree.selection()
        if not selected:
            messagebox.showwarning("Select Macro", "Please select a custom command from the list.")
            return
        trigger = self.macro_tree.item(selected[0])["values"][0]
        commands = db.get_all_custom_commands()
        for cmd in commands:
            if cmd["trigger_phrase"] == trigger:
                new_state = 0 if cmd["enabled"] else 1
                db.toggle_custom_command(cmd["id"], new_state)
                break
        self.refresh_custom_commands_ui()

    def delete_macro(self):
        selected = self.macro_tree.selection()
        if not selected:
            messagebox.showwarning("Select Macro", "Please select a custom command to delete.")
            return
        trigger = self.macro_tree.item(selected[0])["values"][0]
        commands = db.get_all_custom_commands()
        for cmd in commands:
            if cmd["trigger_phrase"] == trigger:
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete custom macro: '{trigger}'?"):
                    db.delete_custom_command_by_id(cmd["id"])
                break
        self.refresh_custom_commands_ui()

    def submit_manual_command(self):
        text = self.manual_entry.get().strip()
        if text:
            self.manual_entry.delete(0, tk.END)
            self.inject_command(text)

    def inject_command(self, text):
        if self.on_manual_submit_callback:
            self.on_manual_submit_callback(text)

    def trigger_confirm(self):
        if self.on_confirm_callback:
            self.on_confirm_callback()

    def trigger_cancel(self):
        if self.on_cancel_callback:
            self.on_cancel_callback()

    def trigger_screenshot(self):
        path = system_actions.take_screenshot()
        messagebox.showinfo("Screenshot", f"Screenshot saved at: {path}")

    def trigger_record(self):
        system_actions.trigger_screen_recording()

    def update_status(self, text):
        self.status.config(text=f"Status: {text}")
        status_lower = text.lower()
        if "listening" in status_lower:
            self.set_visualizer_state("listening")
        elif "thinking" in status_lower or "processing" in status_lower:
            self.set_visualizer_state("thinking")
        elif "speak" in status_lower:
            self.set_visualizer_state("speaking")
        elif "confirm" in status_lower or "heard" in status_lower or "clarif" in status_lower:
            self.set_visualizer_state("confirming")
        else:
            self.set_visualizer_state("idle")
        self.root.update()

    def set_visualizer_state(self, state_name):
        self.visualizer_state = state_name

    def update_intent_details(self, details):
        heard = details.get("heard", "-")
        intent_name = details.get("intent", "-")
        target = details.get("target", "-")
        conf = f"{details.get('confidence', 0)}%"
        preview = details.get("preview", "-")

        self.val_heard.config(text=heard)
        self.val_intent.config(text=intent_name)
        self.val_target.config(text=target)
        self.val_confidence.config(text=conf)
        self.val_preview.config(text=preview)

    def set_waiting_for_confirmation(self, waiting: bool):
        if waiting:
            self.btn_confirm.config(state="normal")
            self.btn_cancel.config(state="normal")
            self.set_visualizer_state("confirming")
        else:
            self.btn_confirm.config(state="disabled")
            self.btn_cancel.config(state="disabled")
            self.set_visualizer_state("idle")

    def make_btn_hoverable(self, btn, hover_bg, normal_bg, check_state=False):
        def on_enter(e):
            if not check_state or btn["state"] != "disabled":
                btn.config(bg=hover_bg)
        def on_leave(e):
            if not check_state or btn["state"] != "disabled":
                btn.config(bg=normal_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def animate_visualizer(self):
        self.canvas.delete("vis")
        cx, cy = 110, 110
        self.vis_phase += 0.05
        
        # Outer blueprint ring
        self.canvas.create_oval(cx-90, cy-90, cx+90, cy+90, outline="#122538", width=1, tags="vis")
        
        if self.visualizer_state == "idle":
            r_core = 45 + 3 * math.sin(self.vis_phase * 2)
            self.canvas.create_oval(cx-r_core, cy-r_core, cx+r_core, cy+r_core, outline=self.cyan_color, width=3, tags="vis")
            
            # Concentric slow-spinning ring
            r_ring = 65
            ang = (self.vis_phase * 15) % 360
            self.canvas.create_arc(cx-r_ring, cy-r_ring, cx+r_ring, cy+r_ring, start=ang, extent=80, outline=self.purple_color, width=2, style="arc", tags="vis")
            self.canvas.create_arc(cx-r_ring, cy-r_ring, cx+r_ring, cy+r_ring, start=ang+180, extent=80, outline=self.purple_color, width=2, style="arc", tags="vis")
            
            r_ring2 = 80
            ang2 = (-self.vis_phase * 10) % 360
            self.canvas.create_arc(cx-r_ring2, cy-r_ring2, cx+r_ring2, cy+r_ring2, start=ang2, extent=120, outline=self.blue_color, width=1, style="arc", tags="vis")
            self.canvas.create_arc(cx-r_ring2, cy-r_ring2, cx+r_ring2, cy+r_ring2, start=ang2+180, extent=120, outline=self.blue_color, width=1, style="arc", tags="vis")
            
        elif self.visualizer_state == "listening":
            for i in range(4):
                r = (25 + i * 16 + 12 * math.sin(self.vis_phase * 3.5 - i * 0.8)) % 95
                if r < 10:
                    continue
                color = [self.green_color, self.cyan_color, self.blue_color][i % 3]
                w = max(1, int(4 - (r / 28.0)))
                self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=w, tags="vis")
            
            r_core = 22 + 4 * math.sin(self.vis_phase * 5)
            self.canvas.create_oval(cx-r_core, cy-r_core, cx+r_core, cy+r_core, fill=self.green_color, outline="", tags="vis")
            
        elif self.visualizer_state == "thinking":
            angle = int(self.vis_phase * 140) % 360
            r = 55
            self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=angle, extent=120, outline=self.purple_color, width=4, style="arc", tags="vis")
            self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=angle+180, extent=120, outline=self.cyan_color, width=4, style="arc", tags="vis")
            self.canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill=self.purple_color, outline="", tags="vis")
            
        elif self.visualizer_state == "speaking":
            r_core = 35 + 18 * abs(math.sin(self.vis_phase * 4))
            self.canvas.create_oval(cx-r_core, cy-r_core, cx+r_core, cy+r_core, outline=self.cyan_color, width=4, tags="vis")
            
            # Draw radiating waveform rods
            for deg in range(0, 360, 30):
                rad = math.radians(deg + self.vis_phase * 8)
                length = 15 + 12 * math.sin(self.vis_phase * 6 + deg)
                x1 = cx + (r_core + 4) * math.cos(rad)
                y1 = cy + (r_core + 4) * math.sin(rad)
                x2 = cx + (r_core + 4 + length) * math.cos(rad)
                y2 = cy + (r_core + 4 + length) * math.sin(rad)
                self.canvas.create_line(x1, y1, x2, y2, fill=self.cyan_color, width=2, tags="vis")
                
        elif self.visualizer_state == "confirming":
            r = 50 + 6 * math.sin(self.vis_phase * 4)
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=self.yellow_color, width=3, tags="vis")
            inner_r = 12 + 4 * math.sin(self.vis_phase * 4)
            self.canvas.create_oval(cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r, fill=self.yellow_color, outline="", tags="vis")
            
        self.root.after(40, self.animate_visualizer)

    def run(self):
        self.root.mainloop()

