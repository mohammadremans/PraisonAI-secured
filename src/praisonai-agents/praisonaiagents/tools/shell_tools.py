"""Tools for executing shell commands safely.

This module provides a safe interface for executing shell commands with:
- Timeout control
- Output capture
- Error handling
- Resource limits
"""

import subprocess
import shlex
import logging
import os
import time
import platform
# psutil is imported lazily inside methods that need it
# to avoid hard failure when the package is not installed
from typing import Dict, List, Optional, Union
from ..approval import require_approval

class ShellTools:
    """Tools for executing shell commands safely."""

    # Allowlist of permitted command binaries
    ALLOWED_COMMANDS = frozenset({
        # Navigation & inspection
        "ls", "dir", "pwd", "cd", "cat", "head", "tail", "less", "more",
        "wc", "file", "stat", "du", "df", "which", "whereis", "type",
        # Search
        "find", "grep", "rg", "ag", "ack", "locate",
        # Text processing
        "echo", "printf", "sort", "uniq", "cut", "tr", "sed", "awk",
        "diff", "patch", "jq", "yq", "xargs",
        # Dev tools
        "python", "python3", "pip", "pip3", "node", "npm", "npx",
        "git", "gh", "cargo", "rustc", "go", "make", "cmake",
        "docker", "docker-compose", "kubectl",
        # Package managers
        "brew", "apt", "apt-get", "yum", "dnf", "pacman",
        # Network (read-only)
        "curl", "wget", "ping", "dig", "nslookup", "host",
        # Archive
        "tar", "zip", "unzip", "gzip", "gunzip",
        # Misc safe
        "date", "cal", "env", "printenv", "uname", "hostname", "whoami",
        "touch", "mkdir", "cp", "mv", "ln", "chmod", "chown",
        "tee", "xargs", "basename", "dirname", "realpath", "readlink",
    })

    # Dangerous command patterns that are always blocked
    BLOCKED_PATTERNS = frozenset({
        "rm -rf /", "rm -rf /*", "rm -rf ~",
        "dd if=", "mkfs", "fdisk", "parted",
        "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
        ":(){ :|:& };:", "fork bomb",
        "> /dev/sda", "> /dev/null",
        "chmod -R 777 /", "chown -R",
    })

    def __init__(self) -> None:
        """Initialize ShellTools."""
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check if required packages are installed (lazy - no hard failure)."""
        pass

    @staticmethod
    def _is_command_allowed(command_parts: List[str]) -> bool:
        """Check if a command binary is in the allowlist.

        Args:
            command_parts: The split command as a list of strings.

        Returns:
            True if the command binary is allowed, False otherwise.
        """
        if not command_parts:
            return False
        binary = os.path.basename(command_parts[0])
        return binary in ShellTools.ALLOWED_COMMANDS

    @staticmethod
    def _is_blocked_pattern(raw_command: str) -> bool:
        """Check if raw command matches a dangerous pattern.

        Args:
            raw_command: The original unsplit command string.

        Returns:
            True if the command matches a blocked pattern.
        """
        normalized = raw_command.strip().lower()
        return any(pattern in normalized for pattern in ShellTools.BLOCKED_PATTERNS)

    @require_approval(risk_level="critical")
    def execute_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None,
        max_output_size: int = 10000,
    ) -> Dict[str, Union[str, int, bool]]:
        """Execute a shell command safely.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Maximum execution time in seconds
            env: Environment variables
            max_output_size: Maximum output size in bytes

        Returns:
            Dictionary with execution results
        """
        try:
            # Block dangerous patterns before any processing
            if self._is_blocked_pattern(command):
                return {
                    'stdout': '',
                    'stderr': f'Command blocked: matches a dangerous pattern',
                    'exit_code': -1,
                    'success': False,
                    'execution_time': 0,
                }

            # Always split command for safety (no shell execution)
            # Use shlex.split with appropriate posix flag
            if platform.system() == 'Windows':
                command = shlex.split(command, posix=False)
            else:
                command = shlex.split(command)

            # Validate command against allowlist
            if not self._is_command_allowed(command):
                binary = os.path.basename(command[0]) if command else "<empty>"
                return {
                    'stdout': '',
                    'stderr': f'Command blocked: "{binary}" is not in the allowed commands list',
                    'exit_code': -1,
                    'success': False,
                    'execution_time': 0,
                }
            
            # Expand tilde and environment variables in command arguments
            # (shell=False means the shell won't do this for us)
            command = [os.path.expanduser(os.path.expandvars(arg)) for arg in command]
            
            # Expand tilde in cwd (subprocess doesn't do this)
            if cwd:
                cwd = os.path.expanduser(cwd)
                cwd = os.path.expandvars(cwd)  # Also expand $HOME, $USER, etc.
                if not os.path.isdir(cwd):
                    # Fallback: try home directory, then current working directory
                    fallback = os.path.expanduser("~") if os.path.isdir(os.path.expanduser("~")) else os.getcwd()
                    logging.warning(f"Working directory '{cwd}' does not exist, using '{fallback}'")
                    cwd = fallback
            
            # Set up process environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start process
            start_time = time.time()
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                shell=False,  # Always use shell=False for security
                env=process_env,
                text=True
            )
            
            try:
                # Wait for process with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Truncate output if too large (use smart format)
                if len(stdout) > max_output_size:
                    tail_size = min(max_output_size // 5, 500)
                    stdout = stdout[:max_output_size - tail_size] + f"\n...[{len(stdout):,} chars, showing first/last portions]...\n" + stdout[-tail_size:]
                if len(stderr) > max_output_size:
                    tail_size = min(max_output_size // 5, 500)
                    stderr = stderr[:max_output_size - tail_size] + f"\n...[{len(stderr):,} chars, showing first/last portions]...\n" + stderr[-tail_size:]
                
                return {
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': process.returncode,
                    'success': process.returncode == 0,
                    'execution_time': time.time() - start_time
                }
            
            except subprocess.TimeoutExpired:
                # Kill process on timeout
                try:
                    import psutil
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.kill()
                    parent.kill()
                except ImportError:
                    # Fallback: kill without psutil
                    process.kill()
                
                return {
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                    'exit_code': -1,
                    'success': False,
                    'execution_time': timeout
                }
                
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logging.error(error_msg)
            return {
                'stdout': '',
                'stderr': error_msg,
                'exit_code': -1,
                'success': False,
                'execution_time': 0
            }
    
    def list_processes(self) -> List[Dict[str, Union[int, str, float]]]:
        """List running processes with their details.
        
        Returns:
            List of process information dictionaries
        """
        try:
            import psutil
        except ImportError:
            return [{"error": "psutil is required for list_processes. Install with: pip install psutil"}]
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    # Handle None values for memory_percent and cpu_percent
                    # These can be None for system processes or zombie processes
                    mem_pct = pinfo['memory_percent']
                    cpu_pct = pinfo['cpu_percent']
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'username': pinfo['username'],
                        'memory_percent': round(mem_pct, 2) if mem_pct is not None else 0.0,
                        'cpu_percent': round(cpu_pct, 2) if cpu_pct is not None else 0.0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return processes
        except Exception as e:
            error_msg = f"Error listing processes: {str(e)}"
            logging.error(error_msg)
            return []
    
    @require_approval(risk_level="critical")
    def kill_process(
        self,
        pid: int,
        force: bool = False
    ) -> Dict[str, Union[bool, str]]:
        """Kill a process by its PID.
        
        Args:
            pid: Process ID to kill
            force: Whether to force kill (-9)
            
        Returns:
            Dictionary with operation results
        """
        try:
            import psutil
        except ImportError:
            return {
                'success': False,
                'message': 'psutil is required for kill_process. Install with: pip install psutil'
            }
        try:
            process = psutil.Process(pid)
            if force:
                process.kill()  # SIGKILL
            else:
                process.terminate()  # SIGTERM
            
            return {
                'success': True,
                'message': f'Process {pid} killed successfully'
            }
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'message': f'No process found with PID {pid}'
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'message': f'Access denied to kill process {pid}'
            }
        except Exception as e:
            error_msg = f"Error killing process: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def get_system_info(self) -> Dict[str, Union[float, int, str, Dict]]:
        """Get system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            import psutil
        except ImportError:
            return {"error": "psutil is required for get_system_info. Install with: pip install psutil"}
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            # Use appropriate root path for the OS
            root_path = os.path.abspath(os.sep)
            disk = psutil.disk_usage(root_path)
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count(),
                    'physical_cores': psutil.cpu_count(logical=False)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'boot_time': psutil.boot_time(),
                'platform': platform.system()
            }
        except Exception as e:
            error_msg = f"Error getting system info: {str(e)}"
            logging.error(error_msg)
            return {}

_shell_tools = ShellTools()
execute_command = _shell_tools.execute_command
list_processes = _shell_tools.list_processes
kill_process = _shell_tools.kill_process
get_system_info = _shell_tools.get_system_info

if __name__ == "__main__":
    # Example usage
    print("\n==================================================")
    print("ShellTools Demonstration")
    print("==================================================\n")
    
    # 1. Execute command
    print("1. Command Execution")
    print("------------------------------")
    # Cross-platform directory listing
    if platform.system() == 'Windows':
        result = execute_command("dir")
    else:
        result = execute_command("ls -la")
    print(f"Success: {result['success']}")
    print(f"Output:\n{result['stdout']}")
    if result['stderr']:
        print(f"Errors:\n{result['stderr']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
    print()
    
    # 2. System Information
    print("2. System Information")
    print("------------------------------")
    info = get_system_info()
    print(f"CPU Usage: {info['cpu']['percent']}%")
    print(f"Memory Usage: {info['memory']['percent']}%")
    print(f"Disk Usage: {info['disk']['percent']}%")
    print(f"Platform: {info['platform']}")
    print()
    
    # 3. Process List
    print("3. Process List (top 5 by CPU)")
    print("------------------------------")
    processes = sorted(
        list_processes(),
        key=lambda x: x['cpu_percent'],
        reverse=True
    )[:5]
    for proc in processes:
        print(f"PID: {proc['pid']}, Name: {proc['name']}, CPU: {proc['cpu_percent']}%")
    print()
    
    print("\n==================================================")
    print("Demonstration Complete")
    print("==================================================")
