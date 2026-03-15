"""
🔬 Advanced Research Tools Automation System
Automated launching, interaction, and integration with MATLAB, SPSS, AMOS, and NVivo
"""

import os
import sys
import subprocess
import psutil
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import threading
from dataclasses import dataclass
import win32gui
import win32con
import win32process
import pyautogui
import pygetwindow as gw

logger = logging.getLogger(__name__)

@dataclass
class ApplicationInfo:
    """Information about installed research applications"""
    name: str
    version: str
    path: str
    executable: str
    is_running: bool
    process_id: Optional[int] = None
    window_handle: Optional[int] = None

class ResearchToolsAutomation:
    """Main class for automating research tools"""
    
    def __init__(self):
        self.applications = {}
        self.discover_applications()
        self.setup_automation()
        
    def discover_applications(self):
        """Discover installed research applications"""
        print("🔍 Discovering installed research applications...")
        
        # MATLAB detection
        matlab_info = self._detect_matlab()
        if matlab_info:
            self.applications['matlab'] = matlab_info
            
        # SPSS detection
        spss_info = self._detect_spss()
        if spss_info:
            self.applications['spss'] = spss_info
            
        # AMOS detection
        amos_info = self._detect_amos()
        if amos_info:
            self.applications['amos'] = amos_info
            
        # NVivo detection
        nvivo_info = self._detect_nvivo()
        if nvivo_info:
            self.applications['nvivo'] = nvivo_info
            
        print(f"✅ Found {len(self.applications)} research applications")
        
    def _detect_matlab(self) -> Optional[ApplicationInfo]:
        """Detect MATLAB installation"""
        matlab_paths = [
            r"C:\Program Files\MATLAB",
            r"C:\Program Files (x86)\MATLAB"
        ]
        
        for base_path in matlab_paths:
            if os.path.exists(base_path):
                # Find latest version
                versions = [d for d in os.listdir(base_path) if d.startswith('R')]
                if versions:
                    latest_version = sorted(versions)[-1]
                    matlab_path = os.path.join(base_path, latest_version)
                    matlab_exe = os.path.join(matlab_path, "bin", "matlab.exe")
                    
                    if os.path.exists(matlab_exe):
                        print(f"✅ MATLAB {latest_version} found at: {matlab_path}")
                        return ApplicationInfo(
                            name="MATLAB",
                            version=latest_version,
                            path=matlab_path,
                            executable=matlab_exe,
                            is_running=self._is_process_running("MATLAB.exe")
                        )
        
        print("❌ MATLAB not found")
        return None
    
    def _detect_spss(self) -> Optional[ApplicationInfo]:
        """Detect SPSS installation"""
        spss_paths = [
            r"C:\Program Files\IBM\SPSS\Statistics",
            r"C:\Program Files (x86)\IBM\SPSS\Statistics"
        ]
        
        for base_path in spss_paths:
            if os.path.exists(base_path):
                # Find latest version
                versions = [d for d in os.listdir(base_path) if d.isdigit()]
                if versions:
                    latest_version = sorted(versions, key=int)[-1]
                    spss_path = os.path.join(base_path, latest_version)
                    spss_exe = os.path.join(spss_path, "statistics.exe")
                    
                    if os.path.exists(spss_exe):
                        print(f"✅ SPSS {latest_version} found at: {spss_path}")
                        return ApplicationInfo(
                            name="SPSS",
                            version=latest_version,
                            path=spss_path,
                            executable=spss_exe,
                            is_running=self._is_process_running("statistics.exe")
                        )
        
        print("❌ SPSS not found")
        return None
    
    def _detect_amos(self) -> Optional[ApplicationInfo]:
        """Detect SPSS Amos installation"""
        amos_paths = [
            r"C:\Program Files\IBM\SPSS\Amos",
            r"C:\Program Files (x86)\IBM\SPSS\Amos"
        ]
        
        for base_path in amos_paths:
            if os.path.exists(base_path):
                # Find latest version
                versions = [d for d in os.listdir(base_path) if d.isdigit()]
                if versions:
                    latest_version = sorted(versions, key=int)[-1]
                    amos_path = os.path.join(base_path, latest_version)
                    amos_exe = os.path.join(amos_path, "Amos.exe")
                    
                    if os.path.exists(amos_exe):
                        print(f"✅ SPSS Amos {latest_version} found at: {amos_path}")
                        return ApplicationInfo(
                            name="AMOS",
                            version=latest_version,
                            path=amos_path,
                            executable=amos_exe,
                            is_running=self._is_process_running("Amos.exe")
                        )
        
        print("❌ SPSS Amos not found")
        return None
    
    def _detect_nvivo(self) -> Optional[ApplicationInfo]:
        """Detect NVivo installation"""
        nvivo_paths = [
            r"C:\Program Files\QSR",
            r"C:\Program Files (x86)\QSR"
        ]
        
        for base_path in nvivo_paths:
            if os.path.exists(base_path):
                # Find NVivo installations
                nvivo_dirs = [d for d in os.listdir(base_path) if d.startswith('NVivo')]
                if nvivo_dirs:
                    latest_nvivo = sorted(nvivo_dirs)[-1]
                    nvivo_path = os.path.join(base_path, latest_nvivo)
                    nvivo_exe = os.path.join(nvivo_path, "NVivo.exe")
                    
                    if os.path.exists(nvivo_exe):
                        version = latest_nvivo.split(' ')[-1] if ' ' in latest_nvivo else "Unknown"
                        print(f"✅ NVivo {version} found at: {nvivo_path}")
                        return ApplicationInfo(
                            name="NVivo",
                            version=version,
                            path=nvivo_path,
                            executable=nvivo_exe,
                            is_running=self._is_process_running("NVivo.exe")
                        )
        
        print("❌ NVivo not found")
        return None
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    def setup_automation(self):
        """Setup automation environment"""
        print("🔧 Setting up automation environment...")
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Create automation scripts directory
        scripts_dir = Path("research_automation_scripts")
        scripts_dir.mkdir(exist_ok=True)
        
        print("✅ Automation environment ready")

class MATLABAutomation:
    """MATLAB-specific automation"""
    
    def __init__(self, app_info: ApplicationInfo):
        self.app_info = app_info
        self.process = None
        self.window = None
        
    async def launch(self, options: Dict[str, Any] = None) -> bool:
        """Launch MATLAB with specified options"""
        try:
            print("🚀 Launching MATLAB...")
            
            # Build command
            cmd = [self.app_info.executable]
            
            if options:
                if options.get('no_splash'):
                    cmd.append('-nosplash')
                if options.get('no_desktop'):
                    cmd.append('-nodesktop')
                if options.get('minimize'):
                    cmd.append('-minimize')
                if options.get('automation'):
                    cmd.append('-automation')
                    
            # Launch process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Wait for window to appear
            await self._wait_for_window("MATLAB")
            
            print("✅ MATLAB launched successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch MATLAB: {e}")
            return False
    
    async def execute_command(self, command: str) -> str:
        """Execute MATLAB command"""
        try:
            if not self.window:
                await self._find_window()
            
            # Bring MATLAB to foreground
            self.window.activate()
            time.sleep(1)
            
            # Type command
            pyautogui.typewrite(command)
            pyautogui.press('enter')
            
            # Wait for execution
            time.sleep(2)
            
            return f"Executed: {command}"
            
        except Exception as e:
            return f"Error executing command: {e}"
    
    async def run_script(self, script_path: str) -> str:
        """Run MATLAB script file"""
        try:
            script_name = Path(script_path).stem
            command = f"run('{script_path}')"
            return await self.execute_command(command)
        except Exception as e:
            return f"Error running script: {e}"
    
    async def open_file(self, file_path: str) -> bool:
        """Open file in MATLAB"""
        try:
            command = f"open('{file_path}')"
            await self.execute_command(command)
            return True
        except Exception as e:
            print(f"Error opening file: {e}")
            return False
    
    async def _wait_for_window(self, title_contains: str, timeout: int = 30):
        """Wait for window to appear"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = gw.getWindowsWithTitle(title_contains)
            if windows:
                self.window = windows[0]
                return
            await asyncio.sleep(1)
        raise TimeoutError(f"Window containing '{title_contains}' not found")
    
    async def _find_window(self):
        """Find MATLAB window"""
        windows = gw.getWindowsWithTitle("MATLAB")
        if windows:
            self.window = windows[0]
        else:
            raise Exception("MATLAB window not found")

class SPSSAutomation:
    """SPSS-specific automation"""
    
    def __init__(self, app_info: ApplicationInfo):
        self.app_info = app_info
        self.process = None
        self.window = None
        
    async def launch(self, options: Dict[str, Any] = None) -> bool:
        """Launch SPSS"""
        try:
            print("🚀 Launching SPSS...")
            
            cmd = [self.app_info.executable]
            
            if options and options.get('production_mode'):
                cmd.append('-production')
                
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await self._wait_for_window("IBM SPSS Statistics")
            
            print("✅ SPSS launched successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch SPSS: {e}")
            return False
    
    async def open_dataset(self, file_path: str) -> bool:
        """Open dataset in SPSS"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(1)
            
            # Use Ctrl+O to open file
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(2)
            
            # Type file path
            pyautogui.typewrite(file_path)
            pyautogui.press('enter')
            
            return True
        except Exception as e:
            print(f"Error opening dataset: {e}")
            return False
    
    async def run_syntax(self, syntax: str) -> str:
        """Run SPSS syntax"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(1)
            
            # Open syntax window (Ctrl+Shift+S)
            pyautogui.hotkey('ctrl', 'shift', 's')
            time.sleep(2)
            
            # Type syntax
            pyautogui.typewrite(syntax)
            
            # Run syntax (Ctrl+A, then Ctrl+R)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'r')
            
            return f"Executed SPSS syntax: {syntax[:50]}..."
            
        except Exception as e:
            return f"Error running syntax: {e}"
    
    async def _wait_for_window(self, title_contains: str, timeout: int = 30):
        """Wait for SPSS window"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = gw.getWindowsWithTitle(title_contains)
            if windows:
                self.window = windows[0]
                return
            await asyncio.sleep(1)
        raise TimeoutError(f"SPSS window not found")
    
    async def _find_window(self):
        """Find SPSS window"""
        windows = gw.getWindowsWithTitle("IBM SPSS Statistics")
        if windows:
            self.window = windows[0]
        else:
            raise Exception("SPSS window not found")

class AMOSAutomation:
    """SPSS Amos-specific automation"""
    
    def __init__(self, app_info: ApplicationInfo):
        self.app_info = app_info
        self.process = None
        self.window = None
        
    async def launch(self) -> bool:
        """Launch SPSS Amos"""
        try:
            print("🚀 Launching SPSS Amos...")
            
            self.process = subprocess.Popen(
                [self.app_info.executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await self._wait_for_window("Amos")
            
            print("✅ SPSS Amos launched successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch SPSS Amos: {e}")
            return False
    
    async def open_model(self, model_path: str) -> bool:
        """Open Amos model file"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(1)
            
            # Use Ctrl+O to open file
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(2)
            
            pyautogui.typewrite(model_path)
            pyautogui.press('enter')
            
            return True
        except Exception as e:
            print(f"Error opening model: {e}")
            return False
    
    async def run_analysis(self) -> str:
        """Run Amos analysis"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(1)
            
            # Press F5 to run analysis
            pyautogui.press('f5')
            
            return "Amos analysis started"
            
        except Exception as e:
            return f"Error running analysis: {e}"
    
    async def _wait_for_window(self, title_contains: str, timeout: int = 30):
        """Wait for Amos window"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = gw.getWindowsWithTitle(title_contains)
            if windows:
                self.window = windows[0]
                return
            await asyncio.sleep(1)
        raise TimeoutError(f"Amos window not found")
    
    async def _find_window(self):
        """Find Amos window"""
        windows = gw.getWindowsWithTitle("Amos")
        if windows:
            self.window = windows[0]
        else:
            raise Exception("Amos window not found")

class NVivoAutomation:
    """NVivo-specific automation"""
    
    def __init__(self, app_info: ApplicationInfo):
        self.app_info = app_info
        self.process = None
        self.window = None
        
    async def launch(self) -> bool:
        """Launch NVivo"""
        try:
            print("🚀 Launching NVivo...")
            
            self.process = subprocess.Popen(
                [self.app_info.executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await self._wait_for_window("NVivo")
            
            print("✅ NVivo launched successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch NVivo: {e}")
            return False
    
    async def open_project(self, project_path: str) -> bool:
        """Open NVivo project"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(2)
            
            # Use Ctrl+O to open project
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(2)
            
            pyautogui.typewrite(project_path)
            pyautogui.press('enter')
            
            return True
        except Exception as e:
            print(f"Error opening project: {e}")
            return False
    
    async def import_data(self, data_path: str) -> str:
        """Import data into NVivo"""
        try:
            if not self.window:
                await self._find_window()
            
            self.window.activate()
            time.sleep(1)
            
            # Use Ctrl+Shift+I for import
            pyautogui.hotkey('ctrl', 'shift', 'i')
            time.sleep(2)
            
            pyautogui.typewrite(data_path)
            pyautogui.press('enter')
            
            return f"Imported data from: {data_path}"
            
        except Exception as e:
            return f"Error importing data: {e}"
    
    async def _wait_for_window(self, title_contains: str, timeout: int = 30):
        """Wait for NVivo window"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = gw.getWindowsWithTitle(title_contains)
            if windows:
                self.window = windows[0]
                return
            await asyncio.sleep(1)
        raise TimeoutError(f"NVivo window not found")
    
    async def _find_window(self):
        """Find NVivo window"""
        windows = gw.getWindowsWithTitle("NVivo")
        if windows:
            self.window = windows[0]
        else:
            raise Exception("NVivo window not found")

class ResearchToolsManager:
    """Main manager for all research tools automation"""
    
    def __init__(self):
        self.automation = ResearchToolsAutomation()
        self.active_tools = {}
        
    async def launch_tool(self, tool_name: str, options: Dict[str, Any] = None) -> bool:
        """Launch a specific research tool"""
        tool_name = tool_name.lower()
        
        if tool_name not in self.automation.applications:
            print(f"❌ {tool_name.upper()} not installed")
            return False
        
        app_info = self.automation.applications[tool_name]
        
        if tool_name == 'matlab':
            automation_class = MATLABAutomation(app_info)
        elif tool_name == 'spss':
            automation_class = SPSSAutomation(app_info)
        elif tool_name == 'amos':
            automation_class = AMOSAutomation(app_info)
        elif tool_name == 'nvivo':
            automation_class = NVivoAutomation(app_info)
        else:
            print(f"❌ Automation not implemented for {tool_name}")
            return False
        
        success = await automation_class.launch(options)
        if success:
            self.active_tools[tool_name] = automation_class
        
        return success
    
    async def execute_command(self, tool_name: str, command: str, **kwargs) -> str:
        """Execute command in specific tool"""
        tool_name = tool_name.lower()
        
        if tool_name not in self.active_tools:
            await self.launch_tool(tool_name)
        
        if tool_name not in self.active_tools:
            return f"Failed to launch {tool_name}"
        
        tool = self.active_tools[tool_name]
        
        if tool_name == 'matlab':
            if command.startswith('run_script:'):
                script_path = command.split(':', 1)[1]
                return await tool.run_script(script_path)
            elif command.startswith('open:'):
                file_path = command.split(':', 1)[1]
                await tool.open_file(file_path)
                return f"Opened {file_path}"
            else:
                return await tool.execute_command(command)
                
        elif tool_name == 'spss':
            if command.startswith('open_dataset:'):
                file_path = command.split(':', 1)[1]
                success = await tool.open_dataset(file_path)
                return f"Dataset opened: {success}"
            elif command.startswith('syntax:'):
                syntax = command.split(':', 1)[1]
                return await tool.run_syntax(syntax)
                
        elif tool_name == 'amos':
            if command.startswith('open_model:'):
                model_path = command.split(':', 1)[1]
                success = await tool.open_model(model_path)
                return f"Model opened: {success}"
            elif command == 'run_analysis':
                return await tool.run_analysis()
                
        elif tool_name == 'nvivo':
            if command.startswith('open_project:'):
                project_path = command.split(':', 1)[1]
                success = await tool.open_project(project_path)
                return f"Project opened: {success}"
            elif command.startswith('import:'):
                data_path = command.split(':', 1)[1]
                return await tool.import_data(data_path)
        
        return f"Unknown command for {tool_name}: {command}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.automation.applications.keys())
    
    def get_tool_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tools"""
        status = {}
        for name, app_info in self.automation.applications.items():
            status[name] = {
                "installed": True,
                "version": app_info.version,
                "running": app_info.is_running,
                "active": name in self.active_tools
            }
        return status
    
    async def close_tool(self, tool_name: str) -> bool:
        """Close a specific tool"""
        tool_name = tool_name.lower()
        
        if tool_name in self.active_tools:
            tool = self.active_tools[tool_name]
            if hasattr(tool, 'process') and tool.process:
                tool.process.terminate()
            del self.active_tools[tool_name]
            return True
        
        return False
    
    async def close_all_tools(self):
        """Close all active tools"""
        for tool_name in list(self.active_tools.keys()):
            await self.close_tool(tool_name)

# Integration with Artemis AI Core
async def handle_research_tool_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle research tool requests from Artemis AI"""
    manager = ResearchToolsManager()
    
    action = request.get('action')
    tool = request.get('tool')
    
    try:
        if action == 'launch':
            options = request.get('options', {})
            success = await manager.launch_tool(tool, options)
            return {
                "success": success,
                "message": f"{'Launched' if success else 'Failed to launch'} {tool.upper()}"
            }
            
        elif action == 'execute':
            command = request.get('command')
            result = await manager.execute_command(tool, command)
            return {
                "success": True,
                "result": result
            }
            
        elif action == 'status':
            status = manager.get_tool_status()
            return {
                "success": True,
                "status": status
            }
            
        elif action == 'available':
            tools = manager.get_available_tools()
            return {
                "success": True,
                "tools": tools
            }
            
        elif action == 'close':
            success = await manager.close_tool(tool)
            return {
                "success": success,
                "message": f"{'Closed' if success else 'Failed to close'} {tool.upper()}"
            }
            
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the automation system
    async def test_automation():
        manager = ResearchToolsManager()
        
        print("Available tools:", manager.get_available_tools())
        print("Tool status:", manager.get_tool_status())
        
        # Test launching MATLAB
        if 'matlab' in manager.get_available_tools():
            await manager.launch_tool('matlab', {'no_splash': True})
            result = await manager.execute_command('matlab', 'disp("Hello from Python!")')
            print("MATLAB result:", result)
    
    asyncio.run(test_automation())
