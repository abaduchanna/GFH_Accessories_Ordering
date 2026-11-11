#!/usr/bin/env python3
"""
GFH Telecom LLC Accessories Ordering Automation (PySide6/Qt build)
=====================================================================
Same tool as the Tkinter build - dashboard for store selection, order
file assignment, CPWH Wireless login + automated checkout. Only the UI
toolkit differs; see GFH_Accessories_Ordering.py's module docstring for
the full feature description.
"""

from datetime import date
import time
from datetime import datetime
import os
import threading
import queue
import webbrowser
from pathlib import Path
import re
import sys
import traceback
import json

# ── LAZY heavy imports (opening-hang fix) ─────────────────────────────────
pd = None
webdriver = None
By = None
WebDriverWait = None
EC = None
Options = None
Service = None


def _ensure_heavy_imports():
    global pd, webdriver, By, WebDriverWait, EC, Options, Service
    if pd is None:
        import pandas as _pd_mod
        pd = _pd_mod
    if webdriver is None:
        from selenium import webdriver as _w
        from selenium.webdriver.common.by import By as _By
        from selenium.webdriver.support.ui import WebDriverWait as _W
        from selenium.webdriver.support import expected_conditions as _EC
        from selenium.webdriver.edge.options import Options as _O
        from selenium.webdriver.edge.service import Service as _S
        webdriver, By, WebDriverWait, EC, Options, Service = _w, _By, _W, _EC, _O, _S


import subprocess as _acc_sp
# --- 3SVerse runtime tamper guard (t197): frozen EXE main debugger = silent exit ---
import runtime_guard as _rguard3sv

_rguard3sv.enforce()

if getattr(sys, "frozen", False):
    _acc__run, _acc__popen = _acc_sp.run, _acc_sp.Popen
    def _acc__is_pip(cmd):
        try:
            return (isinstance(cmd, (list, tuple)) and len(cmd) >= 3
                    and str(cmd[0]) == sys.executable and cmd[1] == "-m"
                    and str(cmd[2]) == "pip")
        except Exception:
            return False
    def _acc_run(cmd, *a, **k):
        if _acc__is_pip(cmd):
            raise RuntimeError("pip install disabled in packaged app")
        return _acc__run(cmd, *a, **k)
    def _acc_popen(cmd, *a, **k):
        if _acc__is_pip(cmd):
            raise RuntimeError("pip install disabled in packaged app")
        return _acc__popen(cmd, *a, **k)
    _acc_sp.run = _acc_run
    _acc_sp.Popen = _acc_popen

# PDF reading support (pdfplumber preferred; pypdf as fallback)
try:
    import pdfplumber as _pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False

try:
    from pypdf import PdfReader as _PdfReader
    _HAS_PYPDF = True
except ImportError:
    _HAS_PYPDF = False

from theme_manager_qt import ThemeManagerQt

# -------------------------------------------------------------------
# HARDCODED PRODUCT DATABASE
# -------------------------------------------------------------------
PRODUCTS = {
    # ========== CABLES ==========
    "PD10FTRIV-BK": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "SHPD10FTRIV-BLK": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "PD10FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "SHPD10FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "PD10FTRIV-BRAD": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "SHPD10FTRIV-BRAD": {"type": "cable", "subtype": "c_to_c", "pack_size": 10, "price": 10.0},
    "PD3FTRIV-BK": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "SHPD3FTRIV-BLK": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "PD3FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "SHPD3FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "PD3FTRIV-BRAD": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "SHPD3FTRIV-BRAD": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "PD5FTRIV-BK": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "SHPD5FTRIV-BLK": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "PD5FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "SHPD5FTRIV-WHT": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "PD5FTRIV-BRAD": {"type": "cable", "subtype": "c_to_c", "pack_size": 20, "price": 10.0},
    "AMPUSB-TC-BK": {"type": "cable", "subtype": "a_to_c", "pack_size": 1, "price": 1.25},
    "AMPUSB-TC-WT": {"type": "cable", "subtype": "a_to_c", "pack_size": 1, "price": 1.25},
    "AMP-PD-BK": {"type": "cable", "subtype": "c_to_c", "pack_size": 1, "price": 1.25},
    "AMP-PD-WT": {"type": "cable", "subtype": "c_to_c", "pack_size": 1, "price": 1.25},
    "AUKEY-CBNCC2-29": {"type": "cable", "subtype": "c_to_c", "pack_size": 1, "price": 2.50},
    "10FTRIV-USB-BK": {"type": "cable", "subtype": "a_to_c", "pack_size": 10, "price": 5.0},
    "SH10FTRIV-USB-BLK": {"type": "cable", "subtype": "a_to_c", "pack_size": 10, "price": 5.0},
    "SH10FTRIV-USB-WHT": {"type": "cable", "subtype": "a_to_c", "pack_size": 10, "price": 5.0},
    "10FTRIV-USB-BRAD": {"type": "cable", "subtype": "a_to_c", "pack_size": 10, "price": 5.0},
    "3FTRIV-USB-BK": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 5.0},
    "SH3FTRIV-USB-BLK": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 5.0},
    "3FTRIV-USB-WHT": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 5.0},
    "SH3FTRIV-USB-WHT": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 5.0},
    "SH3FTRIV-USB-BRAD": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 5.0},
    "SH5FTRIV-USB-BLK": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 7.0},
    "5FTRIV-USB-WHT": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 7.0},
    "5FTRIV-USB-BRAD": {"type": "cable", "subtype": "a_to_c", "pack_size": 20, "price": 7.0},
    "BROOKBK13CLTB6-WHITE-35": {"type": "cable", "subtype": "c_to_l", "pack_size": 1, "price": 4.99},
    "EGC1284M-EGTECH10": {"type": "cable", "subtype": "a_to_c", "pack_size": 1, "price": 2.50},
    "EGC37-EGTECH11": {"type": "cable", "subtype": "c_to_c", "pack_size": 1, "price": 1.75},
    "ESEEKG12A-WHITE-38": {"type": "cable", "subtype": "a_to_c", "pack_size": 1, "price": 1.50},

    # ========== CAR CHARGERS ==========
    "AMPCAR20WT-BK": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 2.50},
    "AMPCAR20WT-WT": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 2.50},
    "AMPCMB-CAR-BK": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 3.75},
    "AMPCMB-CAR-WT": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 3.75},
    "ESEEKC15-WHITE-44": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 2.50},
    "ESEEKC15-BK-43": {"type": "charger", "charger_type": "car", "pack_size": 1, "price": 2.50},
    "ESEEKC10BS-BK-47": {"type": "charger", "charger_type": "car", "pack_size": 12, "price": 30.0},

    # ========== WALL CHARGERS ==========
    "AMPDUAL20WT-BK": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.45},
    "AMPDUAL20WT-WT": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.45},
    "BLING20WGG-BK-1": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.50},
    "BLING20WGG-GOLD-2": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.50},
    "BLING20WGG-SILVER-3": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.50},
    "BROOKBK112P20F-BLACK-15": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.99},
    "BROOKBK11PD20-BLACK-19": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.99},
    "BROOKBK11PD20-WHITE-20": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.99},
    "BROOKBK112P20F-WHITE-16": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.99},
    "BROOKBK11PD30-BLACK-17": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.99},
    "BROOKBK11PD30-WHITE-18": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.99},
    "BROOKBK112P30F-WHITE-14": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.99},
    "AMPCMB20WT-BK": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.95},
    "AMPCMB20WT-WT": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.95},
    "EGC08-EGTECH1": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 2.25},
    "EGC41F-EGTECH2": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 2.50},
    "PEANUT20W-WHITE-1": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.95},
    "PHONESUIT20W-WHITE-2": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.99},
    "PHONE30W-WHITE-15": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 6.99},
    "UPLUSHOME-WHITE-1": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.50},
    "UPLUS40WHOMEULTRA-WHITE-12": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.99},
    "ESEEKT32UC-WHITE-33": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.50},
    "ESEEKT45UC-WHITE-39": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.99},
    "ESEEKGOT32UB-WHITE-15": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 3.50},
    "ESEEKT45UB-WHITE-42": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 4.99},
    "VQT16-WHT": {"type": "charger", "charger_type": "wall", "pack_size": 1, "price": 5.45},
    "ESEEKT32US-WHITEBOX-48": {"type": "charger", "charger_type": "wall", "pack_size": 12, "price": 36.0},
}

# -------------------------------------------------------------------
# STORE ADDRESSES & MANAGEMENT
# -------------------------------------------------------------------
DEFAULT_ADDRESSES = {
    "MLK": "7111 Martin Luther King Blvd Ste B, Total Wireless, Houston, TEXAS, USA - 77033",
    "Tidwell": "8615 Tidwell Road Ste E, Total Wireless, Houston, TEXAS, USA - 77028",
    "Mississippi": "15062 E Mississippi Ave, Total Wireless , Aurora, COLORADO, USA - 80012",
    "E Iliff": "17150 E. Iliff Ave., Unit C1A, CO 80013 , Total Wireless , Aurora, COLORADO, USA - 80013",
    "Peoria": "4490 Peoria St Total Wireless, Denver, COLORADO, USA - 80239",
    "Bromley": "530 E Bromley Ln Suite 105 Total Wireless, Brighton, COLORADO, United States - 80601",
    "Wadsworth": "3214 S Wadsworth Blvd Total Wireless Suite A, Denver, CO 80227, Denver, COLORADO, United States - 80227",
    "FM1960": "4765 FM 1960 RD WEST SUITE B HOUSTON TEXAS 77069 (total wireless), Humble, TX, United States - 77069",
    "Rayford": "466 Rayford Rd Total Wireless (Suite 101) Spring, TX 77386, spring, TX, United States - 77386",
    "Melody": "12024 Melody Dr, Denver, CO 80234 Total Wireless , Denver, COLORADO, United States - 80234",
    "W88": "7641 W 88th Ave, Westminster, CO 80005 Total Wireless, westminster, COLORADO, United States - 80005",
    "Belleview": "2749 W Belleview Ave Littleton, CO 80123 Total Wireless, Littleton, COLORADO, United States - 80123",
    "Quebec": "2280 S Quebec St Denver, CO 80231 suite G2 , total wireless, Denver, COLORADO, United States - 80231",
    "Hollywood": "2508 Hollywood Ave total wireless, Shreveport, LA, United States - 71108",
    "Jewella": "4001 Jewella Ave Ste B total wireless, Shreveport, LA , United States - 71109",
    "Airline": "1131 Airline Drive Ste D total wireless, Bossier City, LA, United States - 71112",
    "Colfax": "7520 E. Colfax Ave, Total Wireless , Denver, COLORADO, UNITED STATES - 80220",
    "Englewood": "475 W Hampden Ave Suite B total wireless, ENGLEWOOD, COLORADO, UNITED STATES - 80110",
    "Lakewood": "98 Wadsworth Blvd unit #127 total wireless, LAKEWOOD, Colorado, United States - 80226",
    "Commerce City": "4952 E 62nd Ave Suite A6 Total Wireless, Commerce City, COLORADO, United States - 80022",
    "Boulder": "1676 30th Street Boulder total wireless, Boulder, COLORADO, United States - 80303",
    "Southwest": "8104 Southwest Fwy Suite F, total wireless, Houston, Texas, United States - 77074",
    "Phoenix": "8945 N 43rd Ave total wireless, PHOENIX, ARIZONA, USA - 85051",
    "Federal": "4344 N Federal Blvd, Total Wireless , Denver, Colorado, USA - 80211",
    "Kipling": "1550 Kipling St Total Wireless , Denver, Colorado, USA - 80215",
    "Gilbert": "323 N Gilbert Rd. #107 Total Wireless, Mesa, Arizona, USA - 85203",
    "Rural": "6323 S Rural Rd Total Wireless, Tempe, Arizona, USA - 85283",
    "Glendale": "6442 W Glendale Ave Total Wireless, Glendale, Arizona, USA - 85301",
    "Gulf": "5819 Gulf Freeway, Suite 400 Total Wireless, Houston, Texas, USA - 77023",
    "Thomas": "3517 E Thomas Rd Total Wireless, Phoenix, Arizona, USA - 85018",
    "Highway 6": "6608 Hwy 6 N Suite E Houston Total Wireless, Houston, Texas, USA - 77084",
    "New Colfax": "15355 E Colfax Ave, Unit F Total Wireless, Aurora, Colorado, USA - 80011",
    "South Central": "5233 South Central Ave, Unit A-09 Total Wireless, Phoenix, Arizona, USA - 85040",
    "Nolensville": "4702 Nolensville Pk Suite B Total Wireless, Nashville, Tennessee, USA - 37211",
    "Bethany": "2722 W Bethany Home Rd Total Wireless, Phoenix, Arizona, USA - 85017",
    "Elliot": "1320 W Elliot Rd Unit 103 Total Wireless, Tempe, Arizona, USA - 85284",
    "N 35": "4812 N 35th Ave Total Wireless, Phoenix, Arizona, USA - 85017",
    "McAllister": "2016 N McAllister Ave, Shehriyar Ali, Tempe, Arizona, USA - 85288",
    "N 51": "2828 N 51st Ave Suite 100 Total Wireless, Tempe, Arizona, USA - 85035",
    "N 19": "18631 N 19th Ave #170 Total Wireless, Phoenix, Arizona, USA - 85027",
    "Westheimer": "7529 Westheimer Rd Total Wireless, Houston, Texas, USA - 77063",
    "Windermere": "12149 FM-1960 W Total wireless, Houston, Texas, USA - 77065",
    "Crosstimbers": "20 E Crosstimbers Rd Total wireless, Houston, Texas, USA - 77022",
    "South Post Oak": "16101 S Post Oak Rd Total wireless, Houston, Texas, USA - 77053",
    "104 Tidwell": "104 Tidwell, Suite F Total Wireless, Houston, Texas, USA - 77022",
    "Fry Rd": "5502 N Fry Rd Suite D Total wireless, Katy, Texas, USA - 77449",
    "South Havana": "1155 S Havana St Suite 11 Total wireless, Aurora, Colorado, USA - 80012",
    "Federal Heights": "1886 W 92nd Ave Total wireless, Federal Heights, Colorado, USA - 80260",
    "Mount View": "5335 Mt View Rd 14 Total Wireless, Antioch, Tennessee, USA - 37013",
    "W Thomas": "7333 W Thomas Rd, 86 Total Wireless, Phoenix, Arizona, USA - 85033",
    "Main Store": "9150 S Main St Suite C Total Wireless, Houston, Texas, USA - 77025"
}

ADDRESSES = {}

def get_stores_file_path():
    try:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base_dir = os.getcwd()
    return os.path.join(base_dir, "stores.json")


def _acc_norm_addr(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _acc_addr_features(s):
    n = _acc_norm_addr(s)
    m = re.match(r"(\d+)", n)
    num = m.group(1) if m else ""
    zips = re.findall(r"\b(\d{5})\b", n)
    zipc = zips[-1] if zips else ""
    toks = set(t for t in n.split() if len(t) >= 3 and not t.isdigit())
    return num, zipc, toks


def _acc_address_score(store_addr, label):
    snum, szip, stoks = _acc_addr_features(store_addr)
    lnum, lzip, ltoks = _acc_addr_features(label)
    score = 0
    if snum and snum == lnum:
        score += 5
    if szip and szip == lzip:
        score += 3
    score += len(stoks & ltoks)
    return score

def load_stores():
    global ADDRESSES
    path = get_stores_file_path()
    loaded_successfully = False

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and len(data) > 0:
                    ADDRESSES = data
                    loaded_successfully = True
        except Exception:
            pass

    if not loaded_successfully:
        ADDRESSES = DEFAULT_ADDRESSES.copy()
        save_stores()

def save_stores():
    path = get_stores_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ADDRESSES, f, indent=4)
    except Exception:
        pass


LOG_CALLBACK = None
PROGRESS_CALLBACK = None

def set_log_callback(callback):
    global LOG_CALLBACK
    LOG_CALLBACK = callback

def set_progress_callback(callback):
    global PROGRESS_CALLBACK
    PROGRESS_CALLBACK = callback

def emit_progress(**payload):
    if PROGRESS_CALLBACK:
        try:
            PROGRESS_CALLBACK(payload)
        except Exception:
            pass

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    if LOG_CALLBACK:
        try:
            LOG_CALLBACK(line)
        except Exception:
            pass

def safe_int(value):
    _ensure_heavy_imports()
    if pd.isna(value) or value is None:
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0

# ── Edge automation profile + port ───────────────────────────────────────────
AUTOMATION_PROFILE_DIR = r"C:\GFH_Edge_Automation_Profile_AccessoriesOrdering"
REMOTE_DEBUGGING_PORT = 9227
ATTACH_TO_OPEN_EDGE = True


def get_edge_exe_path():
    """Find the Edge executable on Windows."""
    import shutil as _sh
    possible_paths = [
        _sh.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    return None


def is_port_open(host="127.0.0.1", port=REMOTE_DEBUGGING_PORT, timeout=1):
    """Check if the remote debugging port is open (Edge is running)."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def open_vpn_setup_browser(url="about:blank", log=print):
    """Launch a dedicated Edge process with our profile + port."""
    edge_path = get_edge_exe_path()
    if not edge_path:
        log("Microsoft Edge executable not found.")
        return False

    os.makedirs(AUTOMATION_PROFILE_DIR, exist_ok=True)

    args = [
        edge_path,
        f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
        f"--user-data-dir={AUTOMATION_PROFILE_DIR}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]

    try:
        _acc_sp.Popen(args)
        log("Opened dedicated Edge automation browser.")

        for _ in range(20):
            if is_port_open():
                log("Automation Edge remote connection is ready.")
                return True
            time.sleep(0.5)

        log("Edge opened, but remote debugging port is not ready yet.")
        return False
    except Exception as e:
        log(f"Failed to open Edge: {e}")
        return False


def create_edge_driver(log=print):
    """Create a Selenium Edge driver. If ATTACH_TO_OPEN_EDGE is True,
    attach to an already-running Edge on our debug port (launching it
    first if needed). Otherwise, create a standalone driver."""
    _ensure_heavy_imports()
    if ATTACH_TO_OPEN_EDGE:
        if not is_port_open():
            log("Automation Edge is not open.")
            log("Opening VPN Browser Setup now.")
            open_vpn_setup_browser(log=log)

        if not is_port_open():
            raise RuntimeError(
                "Automation Edge is not available on remote debugging port. "
                "Click Open VPN Browser Setup first and keep that Edge window open."
            )

        options = Options()
        options.add_experimental_option(
            "debuggerAddress",
            f"127.0.0.1:{REMOTE_DEBUGGING_PORT}"
        )

        driver = webdriver.Edge(options=options)
        return driver

    # Fallback: standalone driver
    options = Options()
    options.add_argument("--start-maximized")
    options.page_load_strategy = 'eager'
    driver = webdriver.Edge(options=options)
    return driver


class CPWHOrderAutomator:
    def __init__(self, username=None, password=None, stop_event=None):
        _ensure_heavy_imports()
        self.username = username or ""
        self.password = password or ""
        self.stop_event = stop_event or threading.Event()
        log("Setting up Microsoft Edge browser...")
        try:
            self.driver = create_edge_driver(log=log)
        except Exception as e1:
            log(f"Attach-to-open Edge failed: {e1}")
            log("Trying native system driver...")
            try:
                options = Options()
                options.add_argument("--start-maximized")
                options.page_load_strategy = 'eager'
                self.driver = webdriver.Edge(options=options)
            except Exception as e2:
                log("CRITICAL: Browser failed to launch.")
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    None, "Driver Error",
                    "Failed to start Microsoft Edge.\n\nPlease open your command prompt and run:\npip install --upgrade selenium webdriver-manager"
                )
                sys.exit()
        self.wait = WebDriverWait(self.driver, 10)
        log("Edge browser started successfully!")

        self.blacklist_colors = ['red']
        self.male_colors = ['black', 'blue', 'grey', 'gray', 'brown', 'silver', 'charcoal', 'navy']
        self.female_colors = ['pink', 'purple', 'rose', 'gold', 'clear', 'magenta', 'teal', 'mint', 'yellow', 'burgundy']
        self.female_keywords = [
            'diamond', 'butterfly', 'epoxy', 'glitter', 'shimmer', 'cute',
            'pearl', 'flower', 'floral', 'bling', 'rhinestone', 'women', 'girl',
            'jewel', 'crystal', 'leopard', 'daisy', 'lepoard'
        ]
        self.case_max_price = 3.00
        self.glass_max_price = 1.50
        self.soft_limit = 500.00
        self.hard_limit = 550.00
        self.current_limit = self.soft_limit
        self.camera_skip_keywords = [
            'camera', 'camera lens', 'camera glass', 'camera lense',
            'lense glass', 'lens glass', 'camera protector', 'lens protector'
        ]
        self.skip_excel_keywords = [
            'speaker', 'airpod', 'smart watch', 'watch',
            'other accessories', 'car phone holder'
        ]
        self.cable_charger_url = "https://www.cpwhwireless.com/latest-models?model=CABLE+CHARGER+POWERBANK&a=4"

    def handle_alerts(self, wait_time=0.5):
        try:
            WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.accept()
            return True
        except:
            return False

    def login(self):
        log("Navigating to login page...")
        self.driver.get("https://www.cpwhwireless.com/login")
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            email_input.clear()
            email_input.send_keys(self.username)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            password_input.submit()
            self.wait.until(EC.presence_of_element_located((By.ID, "search")))
            log("Login successful!")
            time.sleep(4)
            return True
        except Exception as e:
            log(f"Login failed: {e}")
            return False

    def normalize_model_name(self, name):
        n = name.lower()
        n = n.replace('sumsung', 'samsung')
        if 'g play' in n or ('moto g 5g' in n) or ('moto g (2026)' in n):
            return "Motorola Moto G 5G 2025 / 2026 / G Play 2026"
        if 'edge 2025' in n:
            return "Motorola Edge 2025"
        if 'a37' in n: return "Samsung Galaxy A37 5G"
        if 'stylus' in n: return "Motorola Moto G Stylus 5G 2025 2026"
        if 'power' in n: return "Motorola Moto G Power 5G 2025 2026"
        if 'razr' in n: return "Motorola Razr 2025 2024"
        if 'a17' in n: return "Samsung A17 5G"
        if 'a16' in n: return "Samsung A16 5G"
        if 'a36' in n or 'a56' in n: return "Samsung Galaxy A36 / A56"
        if 'a26' in n: return "Samsung Galaxy A26 5G"
        if 'a57' in n: return "Samsung Galaxy A57"
        if 's25 fe' in n: return "Samsung s25 FE"
        if 's26 ultra' in n: return "Samsung s26 Ultra"
        if 's26 plus' in n: return "Samsung s26 Plus"
        if 's26' in n and 'ultra' not in n and 'plus' not in n: return "Samsung s26"
        if '16e' in n or '17e' in n: return "Apple iPhone 16E / iPhone 17E"
        if '17 pro max' in n: return "Apple iPhone 17 Pro Max"
        if '17 pro' in n and 'max' not in n: return "Apple iPhone 17 Pro"
        if '17 air' in n: return "Apple iPhone 17 Air"
        if 'iphone 17' in n and 'pro' not in n and 'air' not in n and 'e' not in n: return "Apple iPhone 17"
        if '14' in n and '13' in n: return "Apple iPhone 14 / Apple iPhone 13"
        if '15' in n and 'plus' not in n and 'pro' not in n: return "Apple iPhone 15"
        if 'tab a9' in n or 'tab a11' in n: return "Samsung TAB A9 Plus / A11 Plus 5G 11 inch"
        return name.replace('Sumsung', 'Samsung').replace('sumsung', 'Samsung')

    def search_phone_model(self, raw_model_name):
        model_name = self.normalize_model_name(raw_model_name)
        for attempt in range(2):
            try:
                self.handle_alerts(0.1)
                if not self.driver.find_elements(By.ID, "search"):
                    self.driver.get("https://www.cpwhwireless.com/")
                    time.sleep(1)
                search_box = self.wait.until(EC.element_to_be_clickable((By.ID, "search")))
                search_box.clear()
                search_box.send_keys(model_name)
                search_box.submit()
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".col-md-3.pro-1")))
                    log(f"Searched: {model_name}. Loading all items...")
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    for i in range(8):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                    self.driver.execute_script("window.scrollTo(0, 0);")
                except:
                    return False
                return True
            except Exception as e:
                log(f"  Search attempt {attempt + 1} failed")
                self.driver.get("https://www.cpwhwireless.com/")
                time.sleep(1)
        return False

    def is_correct_model_exact(self, full_text, target_model):
        text_lower = full_text.lower()
        target_lower = target_model.lower()
        all_mods = ['pro', 'max', 'plus', 'ultra', 'fe', 'air', 'mini', 'stylus', 'power', 'play', 'edge', 'razr']
        required_mods = [m for m in all_mods if m in target_lower]
        for req in required_mods:
            if req not in text_lower:
                return False
        nums = re.findall(r'\b(?:[as]?\d{2})\b', target_lower)
        nums = [n for n in nums if n not in ['20', '24', '25', '26', '5g', '4g']]
        if not nums:
            return True
        forbidden_mods = [m for m in all_mods if m not in target_lower]
        needs_e = 'e' in target_lower.split() or '16e' in target_lower or '17e' in target_lower
        for num in nums:
            matches = list(re.finditer(r'(?:ip)?' + re.escape(num), text_lower))
            if not matches:
                continue
            for match in matches:
                end_pos = match.end()
                context_after = text_lower[end_pos:end_pos+15]
                is_dirty = False
                for f_mod in forbidden_mods:
                    if re.search(r'^[\s\-]*' + f_mod + r'\b', context_after):
                        is_dirty = True
                        break
                if not needs_e and re.search(r'^[\s\-]*e\b', context_after):
                    is_dirty = True
                if not is_dirty:
                    return True
        return False

    def has_camera_keyword(self, full_text):
        for keyword in self.camera_skip_keywords:
            if keyword in full_text:
                return True
        return False

    def is_screen_glass(self, full_text):
        if self.has_camera_keyword(full_text):
            return False
        if 'privacy' in full_text or 'tempered glass' in full_text or 'screen protector' in full_text:
            return True
        return False

    def is_phone_case(self, full_text):
        if self.has_camera_keyword(full_text):
            return False
        if self.is_screen_glass(full_text):
            return False
        case_indicators = ['case', 'hybrid', 'cover', 'bumper', 'wallet', 'folio',
                           'magnetic', 'ring', 'stand', 'kickstand', 'magsafe', 'tpu', 'pc']
        for indicator in case_indicators:
            if indicator in full_text:
                return True
        if 'iphone' in full_text or 'for iphone' in full_text or 'for ip' in full_text:
            return True
        return False

    def is_male_case_strict(self, full_text):
        text_lower = full_text.lower()
        for b_word in self.blacklist_colors:
            if re.search(r'\b' + b_word + r'\b', text_lower):
                return False
        for f_word in self.female_keywords:
            if f_word in text_lower:
                return False
        for color in self.male_colors:
            if re.search(r'\b' + color + r'\b', text_lower):
                return True
        return False

    def is_female_case(self, full_text):
        text_lower = full_text.lower()
        for b_word in self.blacklist_colors:
            if re.search(r'\b' + b_word + r'\b', text_lower):
                return False
        for f_word in self.female_keywords:
            if f_word in text_lower:
                return True
        for c in self.female_colors:
            if re.search(r'\b' + c + r'\b', text_lower):
                return True
        for color in self.male_colors:
            if re.search(r'\b' + color + r'\b', text_lower):
                return False
        return True

    def scrape_products_fast(self):
        js_script = """
        let data = [];
        let items = document.querySelectorAll('.col-md-3.pro-1');
        for(let i = 0; i < items.length; i++) {
            let div = items[i];
            let name = div.querySelector('h6 a') ? div.querySelector('h6 a').innerText : '';
            let desc = div.querySelector('.mid-2 p') ? div.querySelector('.mid-2 p').innerText : '';
            let priceTxt = div.querySelector('.item_price') ? div.querySelector('.item_price').innerText : '';
            let qtyInput = div.querySelector('.qty') ? div.querySelector('.qty').getAttribute('name') : '';
            let stockTxt = div.querySelector('.label-success') ? div.querySelector('.label-success').innerText : '';
            let img = div.querySelector('img') ? div.querySelector('img').src : '';
            data.push({name: name, desc: desc, price: priceTxt, qty_name: qtyInput, stock: stockTxt, img: img});
        }
        return data;
        """
        raw_items = self.driver.execute_script(js_script)
        products = []
        for item in raw_items:
            full_text = (item['name'] + ' ' + item['desc']).lower()
            if self.has_camera_keyword(full_text):
                continue
            price_str = item['price'].replace('$', '').strip()
            if not price_str or 'login' in price_str.lower():
                continue
            try:
                price = float(price_str)
            except:
                continue
            try:
                stock = int(item['stock'].split(':')[1].strip().split()[0])
            except:
                stock = 999
            products.append({
                'name': item['name'],
                'description': item['desc'],
                'full_text': full_text,
                'price': price,
                'qty_field': item['qty_name'],
                'stock': stock,
                'img_url': item['img']
            })
        return products

    def set_quantity(self, qty_field_name, quantity):
        if not qty_field_name:
            return False
        try:
            js_script = f"""
            var elem = document.getElementsByName("{qty_field_name}")[0];
            if(elem) {{
                elem.value = "{quantity}";
                elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                elem.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            """
            self.driver.execute_script(js_script)
            return True
        except:
            return False

    def add_to_cart(self):
        try:
            add_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "btnAddtoCart")))
            self.driver.execute_script("arguments[0].click();", add_btn)
            self.handle_alerts(2.0)
            log("  Added to cart")
            return True
        except Exception:
            log("  Failed to add to cart")
            return False

    def empty_cart(self):
        log("Preparing fresh cart...")
        try:
            self.driver.get("https://www.cpwhwireless.com/shopping-cart")
            time.sleep(3)
            try:
                empty_btn = self.driver.find_element(By.ID, "btnEmptyCart")
                log("Items found. Clicking Empty Cart...")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", empty_btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", empty_btn)
                self.handle_alerts(3.0)
                time.sleep(4)
                log("  Cart is now empty.")
            except:
                log("  Cart is already empty.")
        except Exception as e:
            log(f"  Failed to check/empty cart: {e}")
        finally:
            log("Returning to homepage to begin search...")
            self.driver.get("https://www.cpwhwireless.com/")
            time.sleep(2)

    def get_cart_total(self):
        try:
            self.driver.get("https://www.cpwhwireless.com/shopping-cart")
            time.sleep(2)
            total_elem = self.driver.find_element(By.XPATH, "//th[contains(@class, 'text-right') and contains(text(), '$')]")
            total_text = total_elem.text.replace('$', '').replace(',', '').strip()
            return float(total_text)
        except:
            return 0.0

    def trim_cart_to_limit(self, target_limit):
        log(f"Trimming cart to ${target_limit:.2f} limit...")
        max_attempts = 20
        for _ in range(max_attempts):
            current_total = self.get_cart_total()
            if current_total <= target_limit:
                log(f"  Cart total ${current_total:.2f} is within limit.")
                return True
            log(f"  Over limit (${current_total:.2f}). Removing 1 unit...")
            qty_inputs = self.driver.find_elements(By.XPATH, "//input[starts-with(@name, 'quantity_')]")
            if not qty_inputs:
                log("  No quantity inputs found, cannot trim.")
                return False
            target_input = None
            for inp in qty_inputs:
                try:
                    val = int(inp.get_attribute('value'))
                    if val > 0:
                        target_input = inp
                        break
                except:
                    pass
            if not target_input:
                log("  No product with quantity > 0 found.")
                return False
            curr_val = int(target_input.get_attribute('value'))
            new_val = max(0, curr_val - 1)
            target_input.clear()
            target_input.send_keys(str(new_val))
            update_btn = self.driver.find_element(By.ID, "btnUpdateCart")
            self.driver.execute_script("arguments[0].click();", update_btn)
            time.sleep(3)
        log(f"  Could not trim cart within {max_attempts} attempts.")
        return False

    def proceed_to_checkout_and_place(self, store_address):
        log("Proceeding to Checkout...")
        try:
            self.driver.get("https://www.cpwhwireless.com/checkout")
            self.wait.until(EC.presence_of_element_located((By.ID, "DivShippingAddresses")))
            time.sleep(2)
            log(f"Selecting store address: {store_address[:50]}...")
            addr_elements = self.driver.find_elements(By.XPATH, "//input[@name='shipping_addredd_id']")
            best_elem, best_score, best_label = None, -1, ""
            for elem in addr_elements:
                try:
                    label = elem.find_element(By.XPATH, "..").text
                except Exception:
                    label = ""
                sc = _acc_address_score(store_address, label)
                if sc > best_score:
                    best_elem, best_score, best_label = elem, sc, label
            if best_elem is not None and best_score >= 5:
                if not best_elem.is_selected():
                    self.driver.execute_script("arguments[0].click();", best_elem)
                log(f"  Matched store address (score {best_score}): {best_label[:60].strip()}")
            else:
                log(f"  No reliable address match (best score {best_score}). Skipping this store to avoid shipping to the wrong address.")
                return False
            log("Selecting Regular Ground Shipping...")
            ship_radio = self.driver.find_element(By.XPATH, "//input[@name='delivery_type' and @value='Regular Ground Shipping']")
            if not ship_radio.is_selected():
                self.driver.execute_script("arguments[0].click();", ship_radio)

            log("Placing Order...")
            place_btn = self.driver.find_element(By.ID, "btnCheckout")
            self.driver.execute_script("arguments[0].click();", place_btn)

            if self.handle_alerts(5.0):
                log("  Accepted checkout confirmation alert.")
            else:
                log("  No confirmation alert appeared.")

            time.sleep(4)
            log("ORDER PLACED SUCCESSFULLY!")
            return True
        except Exception as e:
            log(f"Failed during checkout phase: {e}")
            return False

    def add_cases_distributed(self, target_qty, case_type, target_model):
        products = self.scrape_products_fast()
        if not products:
            log(f"  No products scraped for {target_model}")
            return 0
        filtered = []
        for p in products:
            if self.is_phone_case(p['full_text']) and p['price'] <= self.case_max_price:
                if not self.is_correct_model_exact(p['full_text'], target_model):
                    continue
                if case_type == 'male' and self.is_male_case_strict(p['full_text']):
                    filtered.append(p)
                elif case_type == 'female' and self.is_female_case(p['full_text']):
                    filtered.append(p)
        if not filtered:
            log(f"  No {case_type} cases found for {target_model} under ${self.case_max_price}")
            return 0
        filtered.sort(key=lambda x: x['price'])
        remaining = target_qty
        total_cost = 0
        for product in filtered:
            if remaining <= 0:
                break
            take = min(remaining, 2, product['stock'])
            if take > 0:
                self.set_quantity(product['qty_field'], take)
                total_cost += product['price'] * take
                remaining -= take
                log(f"  {case_type.capitalize()} Case: {product['name'][:35]}... x{take} @ ${product['price']}")
        if remaining > 0:
            for product in filtered:
                if remaining <= 0:
                    break
                take = min(remaining, product['stock'])
                if take > 0:
                    self.set_quantity(product['qty_field'], take)
                    total_cost += product['price'] * take
                    remaining -= take
                    log(f"  {case_type.capitalize()} Case (extra): {product['name'][:35]}... x{take} @ ${product['price']}")
        if remaining > 0:
            log(f"  Only found {target_qty - remaining}/{target_qty} {case_type} cases")
        return total_cost

    def add_glass_exact(self, target_qty, glass_type, target_model):
        products = self.scrape_products_fast()
        if not products:
            return 0
        filtered = []
        for p in products:
            if self.is_screen_glass(p['full_text']) and p['price'] <= self.glass_max_price:
                if not self.is_correct_model_exact(p['full_text'], target_model):
                    continue
                is_priv = 'privacy' in p['full_text']
                if glass_type == 'privacy' and is_priv:
                    filtered.append(p)
                elif glass_type == 'clear' and not is_priv:
                    filtered.append(p)
        if not filtered:
            return 0
        filtered.sort(key=lambda x: x['price'])
        best = filtered[0]
        qty = min(target_qty, best['stock'])
        if qty > 0:
            self.set_quantity(best['qty_field'], qty)
            log(f"  {glass_type.capitalize()} Glass: {best['name'][:30]}... x{qty} @ ${best['price']:.2f}")
            return best['price'] * qty
        return 0

    def go_to_cable_charger_page(self):
        log("\nGoing to CABLE CHARGER POWERBANK page...")
        self.driver.get(self.cable_charger_url)
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".col-md-3.pro-1")))
            log("  Scrolling down to load ALL items...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(8):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            self.driver.execute_script("window.scrollTo(0, 0);")
            log("  On CABLE CHARGER POWERBANK page (Fully Loaded)")
            return True
        except:
            return False

    def add_hardcoded_items(self, target_qty, category, subtype):
        if target_qty <= 0:
            return 0

        if not self.go_to_cable_charger_page():
            return 0

        all_products = self.scrape_products_fast()
        sku_to_qty = {p['name'].strip(): p['qty_field'] for p in all_products}
        sku_to_stock = {p['name'].strip(): p['stock'] for p in all_products}

        available_items = []
        for sku, info in PRODUCTS.items():
            if info.get('type') != category:
                continue
            if category == 'cable' and info.get('subtype') != subtype:
                continue
            if category == 'charger' and info.get('charger_type') != subtype:
                continue
            if sku not in sku_to_qty:
                continue
            per_unit = info['price'] / info.get('pack_size', 1)
            if category == 'charger' and subtype == 'car':
                if per_unit > 3.00:
                    continue

            available_items.append({
                'sku': sku,
                'qty_field': sku_to_qty[sku],
                'price': info['price'],
                'pack_size': info.get('pack_size', 1),
                'stock': sku_to_stock[sku],
                'per_unit': per_unit
            })

        if not available_items:
            log(f"  No hardcoded SKUs found on page for {category} ({subtype})")
            return 0

        items_sorted = sorted(available_items, key=lambda x: x['per_unit'])
        best_cost = float('inf')
        best_counts = {}

        def dfs(current_target, item_idx, current_cost, current_counts):
            nonlocal best_cost, best_counts
            if current_target <= 0:
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_counts = current_counts.copy()
                return
            if item_idx >= len(items_sorted):
                return
            if current_cost + (current_target * items_sorted[item_idx]['per_unit']) >= best_cost:
                return

            item = items_sorted[item_idx]
            max_takes = min(item['stock'], (current_target + item['pack_size'] - 1) // item['pack_size'])

            for take in range(max_takes, -1, -1):
                new_counts = current_counts.copy()
                if take > 0:
                    new_counts[item['sku']] = take
                dfs(current_target - take * item['pack_size'], item_idx + 1, current_cost + take * item['price'], new_counts)

        dfs(target_qty, 0, 0, {})

        if best_cost < float('inf'):
            log(f"  Optimal combo found for {category} ({subtype}): ${best_cost:.2f}")
            total_units = 0
            for sku, take in best_counts.items():
                item = next(x for x in available_items if x['sku'] == sku)
                self.set_quantity(item['qty_field'], take)
                units = take * item['pack_size']
                total_units += units
                log(f"    {sku} x{take} (={units} units) @ ${item['price']} each")
            log(f"  Total units ordered: {total_units} (Target: {target_qty})")
            self.add_to_cart()
            return best_cost
        else:
            log(f"  Could not meet exact target. Buying what is available...")
            remaining = target_qty
            cost = 0
            for item in items_sorted:
                if remaining <= 0: break
                take = min(item['stock'], (remaining + item['pack_size'] - 1) // item['pack_size'])
                if take > 0:
                    self.set_quantity(item['qty_field'], take)
                    units = take * item['pack_size']
                    remaining -= units
                    cost += take * item['price']
                    log(f"    [Fallback] {item['sku']} x{take} (={units} units) @ ${item['price']} each")

            if cost > 0:
                self.add_to_cart()
            return cost

    def is_phone_model(self, model_name):
        model_lower = model_name.lower()
        for keyword in self.skip_excel_keywords:
            if keyword in model_lower:
                return False
        phone_indicators = ['iphone', 'samsung', 'motorola', 'google pixel', 'moto', 'galaxy',
                            'apple', 'edge', 'razr', 'a16', 'a17', 's26', 's25', '5g', 'tab', 'revvl']
        for indicator in phone_indicators:
            if indicator in model_lower:
                return True
        return False

    def read_pdf_orders(self, pdf_path):
        raw_text = ""

        if _HAS_PDFPLUMBER:
            try:
                with _pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            raw_text += t + "\n"
                log("PDF text extracted via pdfplumber.")
            except Exception as exc:
                log(f"pdfplumber failed ({exc}), trying pypdf...")

        if not raw_text.strip() and _HAS_PYPDF:
            try:
                reader = _PdfReader(pdf_path)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        raw_text += t + "\n"
                log("PDF text extracted via pypdf.")
            except Exception as exc:
                log(f"pypdf also failed: {exc}")

        if not raw_text.strip():
            log(f"Could not extract text from PDF: {pdf_path}")
            return None

        def split_trailing_numbers(line):
            tokens = line.split()
            n = len(tokens)

            raw_end = []
            for j in range(n - 1, -1, -1):
                tok = tokens[j]
                if re.fullmatch(r'\d+', tok):
                    val = int(tok)
                    if 1900 <= val <= 2099:
                        break
                    raw_end.insert(0, (j, val))
                else:
                    break

            if not raw_end:
                return line.strip(), []

            split_idx = raw_end[0][0]

            prefix_text = ' '.join(tokens[:split_idx])
            if '/' in prefix_text and split_idx > 0:
                prev_tok = tokens[split_idx - 1]
                prev_is_paren_year = bool(re.fullmatch(r'\(\d{4}\)', prev_tok))
                prev_is_digit      = bool(re.fullmatch(r'\d+', prev_tok))
                if not prev_is_digit and not prev_is_paren_year:
                    raw_end = raw_end[1:]
                    if not raw_end:
                        return line.strip(), []
                    split_idx = raw_end[0][0]

            if raw_end and split_idx > 0:
                prev_tok_lower = tokens[split_idx - 1].lower()
                first_val = raw_end[0][1]
                MODEL_SUFFIX_WORDS = ['iphone', 'pixel', 'revvl', 'galaxy', 'razr']
                if (any(prev_tok_lower.endswith(kw) for kw in MODEL_SUFFIX_WORDS)
                        and len(raw_end) == 1
                        and first_val <= 20):
                    return line.strip(), []

            model = ' '.join(tokens[:split_idx]).strip()
            nums  = [v for _, v in raw_end]
            return model, nums

        lines = [l.strip() for l in raw_text.splitlines()]

        orders         = []
        car_charger_qty  = 0
        wall_charger_qty = 0
        cable_qtys = {'c_to_c': 0, 'a_to_c': 0, 'c_to_l': 0, 'a_to_l': 0, 'unknown': 0}
        phone_map = {}

        SKIP_LINE_PHRASES = [
            'accessories order request',
            'phone cases model',
            'male cases quantity',
            'other accessories',
            'car phone holder',
        ]

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            line_lower = line.lower()

            if any(ph in line_lower for ph in SKIP_LINE_PHRASES):
                continue

            label, nums = split_trailing_numbers(line)
            label_lower = label.lower()

            if 'car charger' in label_lower:
                qty = nums[0] if nums else 0
                if qty > 0:
                    car_charger_qty += qty
                continue

            if ('charger' in label_lower or 'adaptor' in label_lower
                    or 'adapter' in label_lower or 'wall block' in label_lower
                    or 'wall adaptor' in label_lower or 'wall charger' in label_lower):
                qty = nums[0] if nums else 0
                if qty > 0:
                    wall_charger_qty += qty
                continue

            if ('cable' in label_lower or 'usb' in label_lower
                    or 'lightning' in label_lower or 'type-a' in label_lower
                    or 'type a' in label_lower or 'type-c' in label_lower
                    or 'type c' in label_lower):
                qty = nums[0] if nums else 0
                if qty <= 0:
                    continue
                if 'lightning' in label_lower or 'iphone' in label_lower:
                    if ('usb-c' in label_lower or 'type-c' in label_lower
                            or 'type c' in label_lower or 'pd' in label_lower
                            or 'c to' in label_lower):
                        cable_qtys['c_to_l'] += qty
                    else:
                        cable_qtys['a_to_l'] += qty
                elif (label_lower.count('usb-c') == 2 or 'c to c' in label_lower
                      or 'type c to type c' in label_lower or 'c-c' in label_lower):
                    cable_qtys['c_to_c'] += qty
                elif ('usb-c' in label_lower or 'type c' in label_lower
                      or 'type-c' in label_lower):
                    cable_qtys['a_to_c'] += qty
                else:
                    cable_qtys['unknown'] += qty
                continue

            if self.is_phone_model(label):
                if not nums:
                    continue

                male_q    = nums[0] if len(nums) > 0 else 0
                female_q  = nums[1] if len(nums) > 1 else 0
                privacy_q = nums[2] if len(nums) > 2 else 0
                clear_q   = nums[3] if len(nums) > 3 else 0

                if not any([male_q, female_q, privacy_q, clear_q]):
                    continue

                if label not in phone_map:
                    phone_map[label] = {'male': 0, 'female': 0, 'privacy': 0, 'clear': 0}
                phone_map[label]['male']    += male_q
                phone_map[label]['female']  += female_q
                phone_map[label]['privacy'] += privacy_q
                phone_map[label]['clear']   += clear_q
                continue

        for model, counts in phone_map.items():
            if any(v > 0 for v in counts.values()):
                orders.append({'type': 'phone', 'model': model, **counts})

        for c_type, qty in cable_qtys.items():
            if qty > 0:
                orders.append({
                    'type': 'cable',
                    'cable_type': c_type,
                    'model': f'Aggregated {c_type.replace("_", "-").upper()} Cables',
                    'qty': qty,
                })

        if car_charger_qty > 0:
            orders.append({'type': 'car_charger',  'model': 'Dual Port Car Charger (Combined)',   'qty': car_charger_qty})
        if wall_charger_qty > 0:
            orders.append({'type': 'wall_charger', 'model': 'Wall Adaptor/Charger (Combined)',     'qty': wall_charger_qty})

        if not orders:
            log(f"PDF parsed but no orderable lines found in: {pdf_path}")
            return None

        log(f"PDF parsed: {len(orders)} order group(s) found.")
        return orders

    def read_excel_orders(self, excel_path):
        _ensure_heavy_imports()
        if excel_path.lower().endswith('.pdf'):
            return self.read_pdf_orders(excel_path)

        try:
            if excel_path.lower().endswith('.csv'):
                df = pd.read_csv(excel_path, header=1).fillna(0)
            else:
                df = pd.read_excel(excel_path, sheet_name='Sheet1', header=1).fillna(0)

            orders = []
            car_charger_qty = 0
            wall_charger_qty = 0
            cable_qtys = {'c_to_c': 0, 'a_to_c': 0, 'c_to_l': 0, 'a_to_l': 0, 'unknown': 0}

            for index, row in df.iterrows():
                if len(row) < 2:
                    continue
                item_name = str(row.iloc[0]).strip()
                if not item_name or item_name == '0' or item_name == 'nan':
                    continue
                item_lower = item_name.lower()

                if 'car charger' in item_lower:
                    car_charger_qty += safe_int(row.iloc[1])
                elif 'charger' in item_lower or 'adapter' in item_lower or 'adaptor' in item_lower or 'wall block' in item_lower:
                    wall_charger_qty += safe_int(row.iloc[1])
                elif 'cable' in item_lower or 'type-a' in item_lower or 'type a' in item_lower or 'type-c' in item_lower or 'type c' in item_lower or 'usb' in item_lower or 'lightning' in item_lower:
                    qty = safe_int(row.iloc[1])
                    if qty > 0:
                        if 'lightning' in item_lower or 'iphone' in item_lower:
                            if 'usb-c' in item_lower or 'type-c' in item_lower or 'type c' in item_lower or 'pd' in item_lower or 'c to' in item_lower:
                                cable_qtys['c_to_l'] += qty
                            else:
                                cable_qtys['a_to_l'] += qty
                        elif item_lower.count('usb-c') == 2 or 'c to c' in item_lower or 'type c to type c' in item_lower or 'c-c' in item_lower:
                            cable_qtys['c_to_c'] += qty
                        elif 'usb-c' in item_lower or 'type c' in item_lower or 'type-c' in item_lower:
                            cable_qtys['a_to_c'] += qty
                        else:
                            cable_qtys['unknown'] += qty
                elif self.is_phone_model(item_name):
                    male_qty = safe_int(row.iloc[1]) if len(row) > 1 else 0
                    female_qty = safe_int(row.iloc[2]) if len(row) > 2 else 0
                    privacy_qty = safe_int(row.iloc[3]) if len(row) > 3 else 0
                    clear_qty = safe_int(row.iloc[4]) if len(row) > 4 else 0
                    if male_qty > 0 or female_qty > 0 or privacy_qty > 0 or clear_qty > 0:
                        orders.append({
                            'type': 'phone', 'model': item_name,
                            'male': male_qty, 'female': female_qty,
                            'privacy': privacy_qty, 'clear': clear_qty
                        })

            for c_type, qty in cable_qtys.items():
                if qty > 0:
                    orders.append({'type': 'cable', 'cable_type': c_type, 'model': f'Aggregated {c_type.replace("_", "-").upper()} Cables', 'qty': qty})

            if car_charger_qty > 0:
                orders.append({'type': 'car_charger', 'model': 'Dual Port Car Charger (Combined)', 'qty': car_charger_qty})
            if wall_charger_qty > 0:
                orders.append({'type': 'wall_charger', 'model': 'Wall Adaptor/Charger (Combined)', 'qty': wall_charger_qty})

            return orders
        except Exception as e:
            log(f"Error reading Excel file ({excel_path}): {e}")
            return None

    def process_store_order(self, orders):
        total_cost = 0
        self.current_limit = self.soft_limit
        last_processed_idx = -1

        for idx, order in enumerate(orders):
            if self.stop_event.is_set():
                log("Stop requested. Stopping before next item.")
                break
            log(f"\n--- {order['model']} ---")
            item_cost = 0

            if order['type'] == 'phone':
                if self.search_phone_model(order['model']):
                    if order.get('male', 0) > 0:
                        item_cost += self.add_cases_distributed(order['male'], 'male', order['model'])
                    if order.get('female', 0) > 0:
                        item_cost += self.add_cases_distributed(order['female'], 'female', order['model'])
                    if order.get('privacy', 0) > 0:
                        item_cost += self.add_glass_exact(order['privacy'], 'privacy', order['model'])
                    if order.get('clear', 0) > 0:
                        item_cost += self.add_glass_exact(order['clear'], 'clear', order['model'])

                    if item_cost > 0:
                        self.add_to_cart()
                    else:
                        log(f"  No valid products found for phone order")
                else:
                    log(f"  Could not search or no products for {order['model']}. Skipping.")
            else:
                if order['type'] == 'cable':
                    item_cost = self.add_hardcoded_items(order['qty'], 'cable', order['cable_type'])
                elif order['type'] == 'car_charger':
                    item_cost = self.add_hardcoded_items(order['qty'], 'charger', 'car')
                elif order['type'] == 'wall_charger':
                    item_cost = self.add_hardcoded_items(order['qty'], 'charger', 'wall')

            if item_cost > 0:
                total_cost += item_cost
                log(f"  Subtotal: ${item_cost:.2f}")

            if total_cost >= self.current_limit:
                log(f"\nReached ${self.current_limit:.2f} limit. Will attempt to add remaining items with extra budget if any left.")
                last_processed_idx = idx
                break
        else:
            return total_cost

        remaining_orders = orders[last_processed_idx+1:]
        if remaining_orders and total_cost < self.hard_limit:
            log(f"\nExtending budget to ${self.hard_limit:.2f} for remaining items...")
            self.current_limit = self.hard_limit
            for order in remaining_orders:
                if self.stop_event.is_set():
                    log("Stop requested. Stopping remaining items.")
                    break
                log(f"\n--- {order['model']} ---")
                item_cost = 0
                if order['type'] == 'phone':
                    if self.search_phone_model(order['model']):
                        if order.get('male', 0) > 0:
                            item_cost += self.add_cases_distributed(order['male'], 'male', order['model'])
                        if order.get('female', 0) > 0:
                            item_cost += self.add_cases_distributed(order['female'], 'female', order['model'])
                        if order.get('privacy', 0) > 0:
                            item_cost += self.add_glass_exact(order['privacy'], 'privacy', order['model'])
                        if order.get('clear', 0) > 0:
                            item_cost += self.add_glass_exact(order['clear'], 'clear', order['model'])
                        if item_cost > 0:
                            self.add_to_cart()
                else:
                    if order['type'] == 'cable':
                        item_cost = self.add_hardcoded_items(order['qty'], 'cable', order['cable_type'])
                    elif order['type'] == 'car_charger':
                        item_cost = self.add_hardcoded_items(order['qty'], 'charger', 'car')
                    elif order['type'] == 'wall_charger':
                        item_cost = self.add_hardcoded_items(order['qty'], 'charger', 'wall')

                if item_cost > 0:
                    total_cost += item_cost
                    log(f"  Subtotal: ${item_cost:.2f}")
                if total_cost >= self.hard_limit:
                    log(f"\nReached hard limit ${self.hard_limit:.2f}. Stopping.")
                    break
        return total_cost

    def run(self, stores=None):
        log("\n" + "="*60)
        log("GFH TELECOM LLC ACCESSORIES ORDERING AUTOMATION")
        log("="*60)

        missing = [s.get('alias', 'Unknown') for s in stores if not s.get('excel_path')]
        if missing:
            log(f"Missing order file (Excel/CSV/PDF) for: {', '.join(missing)}")
            return False

        total_stores = len(stores)
        processed_count = 0
        completed_count = 0
        emit_progress(total=total_stores, processed=0, completed=0, pending=total_stores)

        if self.stop_event.is_set():
            log("Automation cancelled before login.")
            return False

        if not self.login():
            return False

        for store in stores:
            if self.stop_event.is_set():
                log("Stop requested. Automation stopped before next store.")
                break

            log("\n" + "="*50)
            log(f"STARTING ORDER FOR STORE: {store['alias']}")
            log("="*50)
            orders = self.read_excel_orders(store['excel_path'])
            if not orders:
                log(f"No valid orders found in file for store {store['alias']}. Skipping.")
                processed_count += 1
                emit_progress(total=total_stores, processed=processed_count, completed=completed_count, pending=total_stores-processed_count)
                continue

            if self.stop_event.is_set():
                log("Stop requested. Store skipped before cart processing.")
                break

            self.empty_cart()
            total_cost = self.process_store_order(orders)
            self.trim_cart_to_limit(self.hard_limit)
            success = self.proceed_to_checkout_and_place(store['address'])
            processed_count += 1
            if success:
                completed_count += 1
                log(f"Finished processing store {store['alias']}\n")
            else:
                log(f"Aborted processing for store {store['alias']}\n")
            emit_progress(total=total_stores, processed=processed_count, completed=completed_count, pending=total_stores-processed_count)

        if self.stop_event.is_set():
            log("\nAUTOMATION STOPPED BY USER.")
            return False
        log("\nALL STORE ORDERS COMPLETED!")
        return True

    def close(self, ask=True):
        if ask:
            try:
                input("\nPress Enter to close browser...")
            except Exception:
                pass
        try:
            self.driver.quit()
        except Exception:
            pass


APP_TITLE = "GFH Telecom LLC Accessories Ordering Automation"

# ── Edge automation profile + port note ───────────────────────────────────
# Distinct from Extractor (9222), Ordering (9223), Transfer Bot (9224),
# Rebate Filing (9225), Scraper (9226) so running multiple GFH/VidaPay tools at
# once each gets its own Edge process/window instead of colliding.


# ==========================================================
# QT UI LAYER
# ==========================================================
from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar, QPlainTextEdit,
    QFileDialog, QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QInputDialog, QScrollArea, QFrame, QSizePolicy
)

from header_manager_qt import FixedHeaderManagerQt

EMBEDDED_ICON_B64 = (
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "embedded_icon_b64.txt"), "r").read().strip()
    if not getattr(sys, "frozen", False)
    else open(os.path.join(getattr(sys, "_MEIPASS", "."), "assets", "embedded_icon_b64.txt"), "r").read().strip()
)
ICON_ICO_NAME = "GFH_icon.ico"
LOGO_PNG_NAME = "GFH_Telecom_Logo.png"


def _extract_embedded_icon(b64, filename):
    try:
        if not b64:
            return None
        import base64 as _b64, tempfile
        target = os.path.join(tempfile.gettempdir(), filename)
        with open(target, "wb") as fh:
            fh.write(_b64.b64decode(b64))
        return target if os.path.isfile(target) else None
    except Exception:
        return None


def _set_window_icon_qt(window):
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        ico_path = os.path.join(meipass, ICON_ICO_NAME)
        if os.path.exists(ico_path):
            window.setWindowIcon(QIcon(ico_path))
            return
    base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
        else os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base_dir, ICON_ICO_NAME)
    if os.path.exists(ico_path):
        window.setWindowIcon(QIcon(ico_path))
        return
    try:
        ico_path = _extract_embedded_icon(EMBEDDED_ICON_B64, "gfh_app_icon.ico")
        if ico_path:
            window.setWindowIcon(QIcon(ico_path))
    except Exception:
        pass


class ManageStoresDialog(QDialog):
    """Add / edit / delete store aliases + addresses."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Manage Stores (Add / Edit / Delete)")
        self.resize(760, 480)

        outer = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Store Alias", "Store Address"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table, 1)
        self._refresh_table()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Store")
        add_btn.clicked.connect(self._add_store)
        btn_row.addWidget(add_btn)
        edit_btn = QPushButton("Edit Store")
        edit_btn.clicked.connect(self._edit_store)
        btn_row.addWidget(edit_btn)
        del_btn = QPushButton("Delete Store")
        del_btn.clicked.connect(self._delete_store)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        outer.addLayout(btn_row)

    def _refresh_table(self):
        self.table.setRowCount(0)
        for alias, addr in sorted(ADDRESSES.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(alias))
            self.table.setItem(row, 1, QTableWidgetItem(addr))

    def _add_store(self):
        alias, ok = QInputDialog.getText(self, "Add Store", "Enter new Store Alias:")
        if not ok or not alias:
            return
        if alias in ADDRESSES:
            QMessageBox.critical(self, "Error", "This store alias already exists!")
            return
        address, ok = QInputDialog.getText(
            self, "Add Store",
            f"Enter Full Address for '{alias}':\n(Format: Street, City, State, USA - Zip)")
        if not ok or not address:
            return
        ADDRESSES[alias] = address
        save_stores()
        self._refresh_table()
        self.main_window.refresh_store_list()

    def _edit_store(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Edit", "Please select a store to edit.")
            return
        old_alias = self.table.item(row, 0).text()
        old_address = self.table.item(row, 1).text()
        new_alias, ok = QInputDialog.getText(self, "Edit Store", "Edit Store Alias:", text=old_alias)
        if not ok or not new_alias:
            return
        new_address, ok = QInputDialog.getText(self, "Edit Store", "Edit Full Address:", text=old_address)
        if not ok or not new_address:
            return
        if new_alias != old_alias:
            del ADDRESSES[old_alias]
        ADDRESSES[new_alias] = new_address
        save_stores()
        self._refresh_table()
        self.main_window.refresh_store_list()

    def _delete_store(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Delete", "Please select a store to delete.")
            return
        alias = self.table.item(row, 0).text()
        resp = QMessageBox.question(self, "Confirm", f"Are you sure you want to delete '{alias}'?")
        if resp != QMessageBox.Yes:
            return
        del ADDRESSES[alias]
        save_stores()
        self._refresh_table()
        self.main_window.refresh_store_list()


class UIBridge(QObject):
    log = Signal(str)
    progress = Signal(int, int, int, int)  # total, processed, completed, pending
    done = Signal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        _set_window_icon_qt(self)
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.automator = None
        self.store_checks = {}   # alias -> QCheckBox
        self.file_map = {}       # alias -> path

        self.theme_manager = ThemeManagerQt(default="dark", app_name="VidaPay-GFH")

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header_mgr = FixedHeaderManagerQt(outer, title="GFH Accessories Ordering")
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOGO_PNG_NAME)
        if os.path.exists(logo_path):
            self.header_mgr.set_logo(logo_path=logo_path, text="GFH")
        self.header_mgr.add_theme_toggle(self.theme_manager, callback=self._apply_theme)

        body = QWidget()
        body_layout = QGridLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setColumnStretch(0, 4)
        body_layout.setColumnStretch(1, 5)
        body_layout.setColumnStretch(2, 4)
        body_layout.setRowStretch(0, 1)
        body_layout.setRowStretch(1, 1)
        outer.addWidget(body, 1)

        # 1. Store Selection
        store_box = QGroupBox("1. Store Selection")
        store_layout = QVBoxLayout(store_box)
        self.quick_edit = QLineEdit()
        self.quick_edit.setPlaceholderText("Quick Input or search store name")
        self.quick_edit.textChanged.connect(self.refresh_store_list)
        store_layout.addWidget(self.quick_edit)

        self.store_scroll = QScrollArea()
        self.store_scroll.setWidgetResizable(True)
        self.store_list_widget = QWidget()
        self.store_list_layout = QVBoxLayout(self.store_list_widget)
        self.store_list_layout.setAlignment(Qt.AlignTop)
        self.store_scroll.setWidget(self.store_list_widget)
        store_layout.addWidget(self.store_scroll, 1)

        self.selected_count_label = QLabel("0 stores selected")
        store_layout.addWidget(self.selected_count_label)
        manage_btn = QPushButton("Manage Stores")
        manage_btn.clicked.connect(self.open_manage_stores)
        store_layout.addWidget(manage_btn)
        store_btn_row = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_visible)
        store_btn_row.addWidget(select_all_btn)
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_stores)
        store_btn_row.addWidget(clear_all_btn)
        store_layout.addLayout(store_btn_row)
        body_layout.addWidget(store_box, 0, 0)

        # 2. Excel File Assignment
        file_box = QGroupBox("2. Excel File Assignment")
        file_layout = QVBoxLayout(file_box)
        self.file_table = QTableWidget(0, 2)
        self.file_table.setHorizontalHeaderLabels(["Store", "Order File"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_table.cellDoubleClicked.connect(lambda r, c: self.browse_selected_file())
        file_layout.addWidget(self.file_table, 1)
        self.files_assigned_label = QLabel("0 of 0 files assigned")
        file_layout.addWidget(self.files_assigned_label)
        one_for_all_btn = QPushButton("Use One File For All")
        one_for_all_btn.clicked.connect(self.browse_one_for_all)
        file_layout.addWidget(one_for_all_btn)
        browse_btn = QPushButton("Browse Selected")
        browse_btn.clicked.connect(self.browse_selected_file)
        file_layout.addWidget(browse_btn)
        body_layout.addWidget(file_box, 0, 1)

        # 3 + 4. Credentials / Controls (stacked in column 2)
        right_top = QWidget()
        right_top_layout = QVBoxLayout(right_top)
        right_top_layout.setContentsMargins(0, 0, 0, 0)

        cred_box = QGroupBox("3. Credentials")
        cred_layout = QVBoxLayout(cred_box)
        cred_layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        cred_layout.addWidget(self.username_edit)
        cred_layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        cred_layout.addWidget(self.password_edit)
        self.show_password_cb = QCheckBox("Show Password")
        self.show_password_cb.toggled.connect(self._toggle_password)
        cred_layout.addWidget(self.show_password_cb)
        right_top_layout.addWidget(cred_box)

        controls_box = QGroupBox("4. Automation Controls")
        controls_layout = QVBoxLayout(controls_box)
        self.start_btn = QPushButton("Start Automation")
        self.start_btn.clicked.connect(self.start_automation)
        controls_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_automation)
        controls_layout.addWidget(self.stop_btn)
        test_login_btn = QPushButton("Test Login")
        test_login_btn.clicked.connect(self.test_login)
        controls_layout.addWidget(test_login_btn)
        right_top_layout.addWidget(controls_box)
        body_layout.addWidget(right_top, 0, 2)

        # 5. Live Activity Log
        log_box = QGroupBox("5. Live Activity Log")
        log_layout = QVBoxLayout(log_box)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background: #020817; color: #E5E7EB; font-family: Consolas;")
        log_layout.addWidget(self.log_text, 1)
        log_btn_row = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_btn_row.addWidget(clear_log_btn)
        log_btn_row.addStretch(1)
        save_log_btn = QPushButton("Save Log")
        save_log_btn.clicked.connect(self.save_log)
        log_btn_row.addWidget(save_log_btn)
        log_layout.addLayout(log_btn_row)
        body_layout.addWidget(log_box, 1, 0, 1, 2)

        # 6. Order Summary
        summary_box = QGroupBox("6. Order Summary")
        summary_layout = QGridLayout(summary_box)
        self.summary_labels = {}
        cards = [("Total Selected", "total", 0, 0), ("Processed", "processed", 0, 1),
                 ("Pending", "pending", 1, 0), ("Completed", "completed", 1, 1)]
        for label, key, r, c in cards:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            fl = QVBoxLayout(frame)
            fl.addWidget(QLabel(label))
            val_lbl = QLabel("0")
            val_lbl.setStyleSheet("font-size: 21px; font-weight: bold; color: #e83030;")
            fl.addWidget(val_lbl)
            self.summary_labels[key] = val_lbl
            summary_layout.addWidget(frame, r, c)
        self.percent_label = QLabel("0%")
        summary_layout.addWidget(QLabel("Overall Progress"), 2, 0)
        summary_layout.addWidget(self.percent_label, 2, 1, Qt.AlignRight)
        self.overall_progress = QProgressBar()
        summary_layout.addWidget(self.overall_progress, 3, 0, 1, 2)
        body_layout.addWidget(summary_box, 1, 2)

        self.header_mgr.add_copyright(self.theme_manager, outer)

        self._bridge = UIBridge()
        self._bridge.log.connect(self._write_log)
        self._bridge.progress.connect(self.update_summary)
        self._bridge.done.connect(self._on_worker_done)

        set_log_callback(lambda line: self._bridge.log.emit(line))
        set_progress_callback(lambda payload: self._bridge.progress.emit(
            payload.get("total", 0), payload.get("processed", 0),
            payload.get("completed", 0), payload.get("pending", 0)))

        load_stores()
        self.refresh_store_list()
        self.refresh_file_table()
        self.update_summary(0, 0, 0, 0)

        self._apply_theme()
        self.resize(1500, 950)
        QTimer.singleShot(0, self.showMaximized)

    def _apply_theme(self):
        self.theme_manager.apply_theme_to_app(QApplication.instance())
        self.header_mgr.update_for_theme()

    def _toggle_password(self, checked):
        self.password_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    # ── Store list ──────────────────────────────────────────────────────
    def open_manage_stores(self):
        ManageStoresDialog(self, self).exec()

    def refresh_store_list(self):
        while self.store_list_layout.count():
            item = self.store_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        query = self.quick_edit.text().strip().lower()
        visible = []
        if query and "," in query:
            wanted = [p.strip().lower() for p in query.split(",") if p.strip()]
            for alias in ADDRESSES:
                if alias.lower() in wanted:
                    visible.append(alias)
        else:
            for alias in ADDRESSES:
                if not query or query in alias.lower() or query in ADDRESSES[alias].lower():
                    visible.append(alias)
        for alias in visible:
            cb = self.store_checks.get(alias)
            was_checked = cb.isChecked() if cb else False
            cb = QCheckBox(alias)
            cb.setChecked(was_checked)
            cb.toggled.connect(self.on_store_change)
            self.store_checks[alias] = cb
            self.store_list_layout.addWidget(cb)
        self.visible_stores = visible
        self.on_store_change()

    def selected_aliases(self):
        return [alias for alias, cb in self.store_checks.items() if cb.isChecked()]

    def on_store_change(self):
        count = len(self.selected_aliases())
        self.selected_count_label.setText(f"{count} stores selected")
        self.update_summary(count, 0, 0, count)
        self.refresh_file_table()

    def select_all_visible(self):
        for alias in getattr(self, "visible_stores", []):
            if alias in self.store_checks:
                self.store_checks[alias].setChecked(True)
        self.on_store_change()

    def clear_all_stores(self):
        for cb in self.store_checks.values():
            cb.setChecked(False)
        self.on_store_change()

    # ── File assignment ─────────────────────────────────────────────────
    def refresh_file_table(self):
        self.file_table.setRowCount(0)
        selected = self.selected_aliases()
        assigned = 0
        for alias in selected:
            path = self.file_map.get(alias, "")
            if path:
                assigned += 1
            display = os.path.basename(path) if path else "Not assigned"
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            self.file_table.setItem(row, 0, QTableWidgetItem(alias))
            self.file_table.setItem(row, 1, QTableWidgetItem(display))
        self.files_assigned_label.setText(f"{assigned} of {len(selected)} files assigned")

    def browse_selected_file(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Store", "Select a store row first.")
            return
        alias = self.file_table.item(row, 0).text()
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select order file for {alias}", "",
            "All supported (*.xlsx *.xls *.csv *.pdf);;Excel files (*.xlsx *.xls);;"
            "CSV files (*.csv);;PDF files (*.pdf);;All files (*.*)")
        if path:
            self.file_map[alias] = path
            self.refresh_file_table()

    def browse_one_for_all(self):
        selected = self.selected_aliases()
        if not selected:
            QMessageBox.warning(self, "No Stores", "Select at least one store first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select order file for all selected stores", "",
            "All supported (*.xlsx *.xls *.csv *.pdf);;Excel files (*.xlsx *.xls);;"
            "CSV files (*.csv);;PDF files (*.pdf);;All files (*.*)")
        if path:
            for alias in selected:
                self.file_map[alias] = path
            self.refresh_file_table()

    # ── Log / summary ────────────────────────────────────────────────────
    def _write_log(self, line):
        self.log_text.appendPlainText(line)

    def clear_log(self):
        self.log_text.setPlainText("")

    def save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save automation log", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.log_text.toPlainText())
        QMessageBox.information(self, "Saved", f"Log saved:\n{path}")

    def update_summary(self, total=None, processed=None, completed=None, pending=None):
        def cur(key):
            try:
                return int(self.summary_labels[key].text())
            except Exception:
                return 0
        if total is None:
            total = cur("total")
        if processed is None:
            processed = cur("processed")
        if completed is None:
            completed = cur("completed")
        if pending is None:
            pending = max(0, total - processed)
        self.summary_labels["total"].setText(str(total))
        self.summary_labels["processed"].setText(str(processed))
        self.summary_labels["pending"].setText(str(pending))
        self.summary_labels["completed"].setText(str(completed))
        percent = int((processed / total) * 100) if total else 0
        self.overall_progress.setValue(percent)
        self.percent_label.setText(f"{percent}%")

    # ── Automation control ───────────────────────────────────────────────
    def build_selected_stores(self):
        selected = self.selected_aliases()
        stores = []
        for alias in selected:
            stores.append({
                "alias": alias,
                "address": ADDRESSES[alias],
                "excel_path": self.file_map.get(alias, ""),
            })
        return stores

    def validate_before_run(self, stores):
        if self.worker_thread and self.worker_thread.is_alive():
            QMessageBox.warning(self, "Already Running", "Automation is already running.")
            return False
        if not stores:
            QMessageBox.warning(self, "No Store Selected", "Select at least one store.")
            return False
        missing = [s["alias"] for s in stores if not s.get("excel_path")]
        if missing:
            QMessageBox.warning(self, "Missing Files", "Assign an Excel order file for:\n" + "\n".join(missing))
            return False
        if not self.username_edit.text().strip() or not self.password_edit.text().strip():
            QMessageBox.warning(self, "Credentials Required", "Enter username and password.")
            return False
        return True

    def start_automation(self):
        stores = self.build_selected_stores()
        if not self.validate_before_run(stores):
            return
        self.stop_event.clear()
        self.start_btn.setEnabled(False)
        self.clear_log()
        self.update_summary(len(stores), 0, 0, len(stores))
        self.worker_thread = threading.Thread(target=self.automation_worker, args=(stores,), daemon=True)
        self.worker_thread.start()

    def automation_worker(self, stores):
        try:
            self.automator = CPWHOrderAutomator(
                username=self.username_edit.text().strip(),
                password=self.password_edit.text().strip(),
                stop_event=self.stop_event,
            )
            self.automator.run(stores)
            log("Browser will remain open until you stop automation or close the app.")
        except Exception:
            log("Automation crashed:")
            log(traceback.format_exc())
        finally:
            self._bridge.done.emit()

    def _on_worker_done(self):
        self.start_btn.setEnabled(True)

    def stop_automation(self):
        self.stop_event.set()
        log("Stop requested by user.")
        if self.automator:
            try:
                self.automator.close(ask=False)
                log("Browser closed.")
            except Exception as exc:
                log(f"Browser close failed: {exc}")

    def test_login(self):
        if self.worker_thread and self.worker_thread.is_alive():
            QMessageBox.warning(self, "Already Running", "Stop the current automation before testing login.")
            return
        if not self.username_edit.text().strip() or not self.password_edit.text().strip():
            QMessageBox.warning(self, "Credentials Required", "Enter username and password.")
            return
        self.stop_event.clear()
        self.start_btn.setEnabled(False)
        threading.Thread(target=self.test_login_worker, daemon=True).start()

    def test_login_worker(self):
        tester = None
        try:
            tester = CPWHOrderAutomator(username=self.username_edit.text().strip(),
                                         password=self.password_edit.text().strip(),
                                         stop_event=self.stop_event)
            if tester.login():
                log("Test login passed.")
            else:
                log("Test login failed.")
        except Exception:
            log("Test login crashed:")
            log(traceback.format_exc())
        finally:
            if tester:
                tester.close(ask=False)
            self._bridge.done.emit()

    def closeEvent(self, event):
        self.stop_event.set()
        set_log_callback(None)
        set_progress_callback(None)
        if self.automator:
            try:
                self.automator.close(ask=False)
            except Exception:
                pass
        event.accept()


# ==========================================================
# ENTRY POINT
# ==========================================================
def _enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _close_pyi_splash():
    try:
        import pyi_splash  # type: ignore
        pyi_splash.close()
    except Exception:
        pass


def main():
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GFHTelecom.AccessoriesOrdering")
    except Exception:
        pass
    _enable_dpi_awareness()
    app = QApplication(sys.argv)
    try:
        win = MainWindow()
        win.show()
        _close_pyi_splash()
        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()
        try:
            QMessageBox.critical(None, "GFH Accessories Ordering — Error",
                                  "The app hit an error during startup.\n\n" + traceback.format_exc())
        except Exception:
            pass


if __name__ == "__main__":
    main()
