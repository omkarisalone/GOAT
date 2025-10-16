#!/usr/bin/env python3
import sys
import subprocess
import time
import os
import platform
import hashlib
import requests
import tempfile
import threading
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich import box

console = Console()

# --- Configuration ---
GIST_IDS = {
    "users": "995aff38a9bb55b8e4e84425e99be680",
    "main_script": "7d1fb739c586eaf358e345e041910d09"
}
GITHUB_TOKEN = "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"

# --- Global variable for preloaded script ---
main_script_content = None

# --- Secure Token Handling ---
def secure_token_handling():
    token = GITHUB_TOKEN
    if token.startswith('ghp_'):
        return token
    else:
        return token[::-1]

# --- STABLE HARDWARE-BASED HWID VERIFICATION ---
def get_stable_hardware_info():
    system = platform.system()
    
    try:
        if system == "Windows":
            try:
                # Use wmic for Windows
                uuid_output = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"],
                    capture_output=True, text=True, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                ).stdout.strip()
                uuid_lines = [line.strip() for line in uuid_output.split('\n') if line.strip() and line.strip() != 'UUID']
                motherboard_uuid = uuid_lines[0] if uuid_lines else "Unknown"
            except:
                motherboard_uuid = "Unknown"
            
            try:
                cpu_output = subprocess.run(
                    ["wmic", "cpu", "get", "ProcessorId"],
                    capture_output=True, text=True, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                ).stdout.strip()
                cpu_lines = [line.strip() for line in cpu_output.split('\n') if line.strip() and line.strip() != 'ProcessorId']
                cpu_id = cpu_lines[0] if cpu_lines else "Unknown"
            except:
                cpu_id = "Unknown"
            
            try:
                disk_output = subprocess.run(
                    ["wmic", "diskdrive", "get", "serialnumber"],
                    capture_output=True, text=True, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                ).stdout.strip()
                disk_lines = [line.strip() for line in disk_output.split('\n') if line.strip() and line.strip() != 'SerialNumber']
                disk_serial = disk_lines[0] if disk_lines else "Unknown"
            except:
                disk_serial = "Unknown"
            
            return {
                "Motherboard_UUID": motherboard_uuid,
                "CPU_ID": cpu_id,
                "Disk_Serial": disk_serial,
                "OS": "Windows"
            }
            
        elif system == "Linux":
            # Check if it's Android
            if os.path.exists("/system/build.prop"):
                try:
                    serialno = subprocess.run(
                        ["getprop", "ro.serialno"],
                        capture_output=True, text=True, timeout=2
                    ).stdout.strip()
                    if not serialno or serialno == "unknown":
                        serialno = subprocess.run(
                            ["getprop", "ro.boot.serialno"],
                            capture_output=True, text=True, timeout=2
                        ).stdout.strip()
                except:
                    serialno = "Unknown"
                
                try:
                    device = subprocess.run(
                        ["getprop", "ro.product.device"],
                        capture_output=True, text=True, timeout=2
                    ).stdout.strip()
                except:
                    device = "Unknown"
                
                try:
                    hardware = subprocess.run(
                        ["getprop", "ro.hardware"],
                        capture_output=True, text=True, timeout=2
                    ).stdout.strip()
                except:
                    hardware = "Unknown"
                
                return {
                    "Serial": serialno,
                    "Device": device,
                    "Hardware": hardware,
                    "OS": "Android"
                }
            else:
                # Regular Linux
                try:
                    with open("/etc/machine-id", "r") as f:
                        machine_id = f.read().strip()
                except:
                    machine_id = "Unknown"
                
                try:
                    with open("/sys/class/dmi/id/product_uuid", "r") as f:
                        product_uuid = f.read().strip()
                except:
                    product_uuid = "Unknown"
                
                return {
                    "Machine_ID": machine_id,
                    "Product_UUID": product_uuid,
                    "OS": "Linux"
                }
        
        elif system == "Darwin":
            try:
                mac_uuid = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True, text=True, timeout=3
                ).stdout
                for line in mac_uuid.split('\n'):
                    if 'IOPlatformUUID' in line:
                        mac_uuid = line.split('"')[3]
                        break
                else:
                    mac_uuid = "Unknown"
            except:
                mac_uuid = "Unknown"
            
            return {
                "UUID": mac_uuid,
                "OS": "macOS"
            }
        
        else:
            return {"OS": system, "Info": "Unsupported"}
            
    except Exception as e:
        return {"OS": "Error", "Info": str(e)}

def generate_hwid():
    try:
        info = get_stable_hardware_info()
        
        if info['OS'] == 'Windows':
            raw_data = f"{info['Motherboard_UUID']}{info['CPU_ID']}{info['Disk_Serial']}{info['OS']}"
        elif info['OS'] == 'Android':
            raw_data = f"{info['Serial']}{info['Device']}{info['Hardware']}{info['OS']}"
        elif info['OS'] == 'Linux':
            raw_data = f"{info['Machine_ID']}{info['Product_UUID']}{info['OS']}"
        elif info['OS'] == 'macOS':
            raw_data = f"{info['UUID']}{info['OS']}"
        else:
            raw_data = f"{info['OS']}{info.get('Info', 'Unknown')}"
        
        hwid = hashlib.sha256(raw_data.encode()).hexdigest()
        return hwid, info
    except Exception as e:
        return "ERROR", {}

# --- Secure Gist Fetching ---
def fetch_secure_gist(gist_id):
    token = secure_token_handling()
    api_url = f"https://api.github.com/gists/{gist_id}"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'OMNX-Auth-System'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        gist_data = response.json()
        first_file = next(iter(gist_data['files'].values()))
        return first_file['content']
    except Exception as e:
        return None

def fetch_users_data():
    gist_content = fetch_secure_gist(GIST_IDS["users"])
    if gist_content is None:
        return None
    
    try:
        users_data = {}
        lines = gist_content.strip().splitlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                name, hwid, license_key = parts[0], parts[1], ' '.join(parts[2:])
                users_data[hwid] = {"name": name, "license_key": license_key}
        return users_data
    except:
        return None

def preload_main_script():
    global main_script_content
    main_script_content = fetch_secure_gist(GIST_IDS["main_script"])

# --- Simple password input ---
def get_password():
    console.print("\n🔑 [bold yellow]Enter license key: [/bold yellow]", end="")
    password = input()
    return password

# --- Run main script ---
def run_main_script_instantly():
    global main_script_content
    
    if main_script_content:
        try:
            # Save to file and execute
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, delete_on_close=False) as f:
                f.write(main_script_content)
                temp_file = f.name
            
            # Set executable permissions only on Unix-like systems
            if os.name != 'nt':  # Not Windows
                os.chmod(temp_file, 0o755)
            
            console.print("\n✨ [bold green]Launching OMNX Application...[/bold green]\n")
            time.sleep(1)
            
            # Execute the script - platform-specific execution
            if os.name == 'nt':  # Windows
                os.system(f'python "{temp_file}"')
            else:  # Unix-like systems (Linux, Android, macOS)
                os.system(f'"{sys.executable}" "{temp_file}"')
                
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
                
        except Exception as e:
            console.print(f"❌ [red]Error launching main script: {str(e)}[/red]")
    else:
        console.print("❌ [red]Failed to load main script[/red]")

# --- Enhanced UI Components ---
def show_header():
    console.print("\n")
    console.print(Align.center("🔐 [bold cyan]OMNX SECURITY SYSTEM[/bold cyan]"))
    console.print(Align.center("[dim]Hardware-Based Authentication[/dim]"))
    console.print()

def show_hardware_info(hwid, device_info):
    """Show hardware info in a compact top-left panel"""
    info_text = ""
    for key, value in device_info.items():
        if value != "Unknown" and key != "OS":
            display_value = str(value)
            if len(display_value) > 20:
                display_value = display_value[:17] + "..."
            info_text += f"[bold yellow]{key}:[/bold yellow] {display_value}\n"
    
    info_text += f"[bold yellow]HWID:[/bold yellow] [white]{hwid}[/white]"
    
    panel = Panel(
        info_text.strip(),
        title="🖥️ Hardware Info",
        title_align="left",
        style="cyan",
        width=60
    )
    console.print(panel)

def create_auth_panel(steps):
    """Create authentication process panel"""
    process_text = ""
    for step in steps:
        if step["status"] == "loading":
            process_text += f"🔄 [cyan][{step['number']}] {step['message']}[/cyan]\n"
        elif step["status"] == "success":
            process_text += f"✅ [green][{step['number']}] {step['message']}[/green]\n"
        elif step["status"] == "error":
            process_text += f"❌ [red][{step['number']}] {step['message']}[/red]\n"
        else:
            process_text += f"🔹 [blue][{step['number']}] {step['message']}[/blue]\n"
    
    return Panel.fit(
        process_text.strip(),
        title="📋 Authentication Process",
        title_align="center",
        style="bright_blue",
        box=box.ROUNDED
    )

def show_success(username):
    """Show success message"""
    console.print("\n")
    console.print(Panel.fit(
        Align.center(f"🎉 [bold green]AUTHENTICATION SUCCESSFUL![/bold green]\n\n[dim]Welcome {username} to OMNX Premium[/dim]"),
        style="green",
        box=box.DOUBLE
    ))
    console.print()

# --- Main Authentication Flow ---
def verify_hwid_and_license():
    # Clear screen - platform specific
    os.system("cls" if os.name == 'nt' else "clear")
    show_header()
    
    # Generate HWID and show hardware info
    new_hwid, device_info = generate_hwid()
    
    if new_hwid == "ERROR":
        console.print("❌ [red]Failed to generate hardware ID[/red]")
        return False
    
    # Show hardware info in top-left with full HWID
    show_hardware_info(new_hwid, device_info)
    console.print()  # Add some space
    
    # Initialize steps
    steps = [
        {"number": "1", "message": "Generating hardware ID...", "status": "loading"},
        {"number": "2", "message": "Checking authorization...", "status": "pending"},
        {"number": "3", "message": "License verification", "status": "pending"}
    ]
    
    # Show initial authentication panel ONCE using Live for updates
    with Live(create_auth_panel(steps), console=console, refresh_per_second=4) as live:
        # Step 1: HWID Generation - FAST
        time.sleep(0.3)
        steps[0]["status"] = "success"
        live.update(create_auth_panel(steps))
        
        # Step 2: Authorization Check - FAST
        steps[1]["status"] = "loading"
        live.update(create_auth_panel(steps))
        
        # Fetch user data immediately without delay
        users_data = fetch_users_data()
        
        if not users_data:
            steps[1]["status"] = "error"
            steps[1]["message"] = "Network error - cannot verify"
            live.update(create_auth_panel(steps))
            time.sleep(1)
            return False
        
        # Check if HWID exists
        if new_hwid in users_data:
            steps[1]["status"] = "success"
            steps[1]["message"] = "Hardware verified"
            live.update(create_auth_panel(steps))
            time.sleep(0.5)
        else:
            steps[1]["status"] = "error"
            steps[1]["message"] = "Hardware not authorized"
            live.update(create_auth_panel(steps))
            time.sleep(1)
            console.print(f"\n📞 [yellow]Contact @OMNX3 with your HWID:[/yellow]")
            console.print(f"[bold white]{new_hwid}[/bold white]\n")
            return False
    
    # Only ask for license key after the Live context is closed
    if new_hwid in users_data:
        console.print("\n🔑 [bold yellow]Enter license key: [/bold yellow]", end="")
        license_key = input()
        
        if not license_key:
            console.print("❌ [red]No license key provided[/red]")
            return False
        
        # Verify license key immediately
        if license_key == users_data[new_hwid]["license_key"]:
            # Show success panel directly without showing the final auth panel
            show_success(users_data[new_hwid]["name"])
            return True
        else:
            console.print("❌ [red]Invalid license key[/red]")
            return False

def main():
    # Start preloading in background
    preload_thread = threading.Thread(target=preload_main_script)
    preload_thread.daemon = True
    preload_thread.start()
    
    # Verify authentication
    if verify_hwid_and_license():
        # Wait for preload
        preload_thread.join(timeout=3)
        
        # Launch main script
        run_main_script_instantly()
    else:
        console.print("\n❌ [red]Authentication failed. Exiting.[/red]\n")
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n⚠️  [yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n\n❌ [red]Unexpected error: {str(e)}[/red]")