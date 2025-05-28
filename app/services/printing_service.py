import os
import subprocess
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PrintingService:
    """
    Service for handling PDF printing to local printers.
    Supports Windows, macOS, and Linux printing.
    """
    
    def __init__(self):
        self.system = platform.system()
        
    def get_available_printers(self) -> List[Dict[str, str]]:
        """
        Get list of available printers on the system.
        """
        printers = []
        
        try:
            if self.system == "Windows":
                printers = self._get_windows_printers()
            elif self.system == "Darwin":  # macOS
                printers = self._get_macos_printers()
            elif self.system == "Linux":
                printers = self._get_linux_printers()
        except Exception as e:
            logger.error(f"Error getting printers: {e}")
            
        return printers
    
    def _get_windows_printers(self) -> List[Dict[str, str]]:
        """Get Windows printers using PowerShell."""
        try:
            cmd = ["powershell", "-Command", "Get-Printer | Select-Object Name, DriverName, PortName | ConvertTo-Json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            import json
            printers_data = json.loads(result.stdout)
            
            # Handle single printer case
            if isinstance(printers_data, dict):
                printers_data = [printers_data]
            
            printers = []
            for printer in printers_data:
                printers.append({
                    "name": printer.get("Name", ""),
                    "driver": printer.get("DriverName", ""),
                    "port": printer.get("PortName", ""),
                    "status": "available"
                })
            
            return printers
        except Exception as e:
            logger.error(f"Error getting Windows printers: {e}")
            return []
    
    def _get_macos_printers(self) -> List[Dict[str, str]]:
        """Get macOS printers using lpstat."""
        try:
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, check=True)
            printers = []
            
            for line in result.stdout.split('\n'):
                if line.startswith('printer '):
                    parts = line.split()
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        status = "available" if "idle" in line else "busy"
                        printers.append({
                            "name": printer_name,
                            "driver": "Unknown",
                            "port": "Unknown",
                            "status": status
                        })
            
            return printers
        except Exception as e:
            logger.error(f"Error getting macOS printers: {e}")
            return []
    
    def _get_linux_printers(self) -> List[Dict[str, str]]:
        """Get Linux printers using lpstat."""
        try:
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, check=True)
            printers = []
            
            for line in result.stdout.split('\n'):
                if line.startswith('printer '):
                    parts = line.split()
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        status = "available" if "idle" in line else "busy"
                        printers.append({
                            "name": printer_name,
                            "driver": "Unknown",
                            "port": "Unknown",
                            "status": status
                        })
            
            return printers
        except Exception as e:
            logger.error(f"Error getting Linux printers: {e}")
            return []
    
    def print_pdf(self, pdf_path: str, printer_name: Optional[str] = None, copies: int = 1) -> Dict[str, Any]:
        """
        Print a PDF file to the specified printer.
        
        Args:
            pdf_path: Path to the PDF file
            printer_name: Name of the printer (None for default)
            copies: Number of copies to print
            
        Returns:
            Dict with success status and details
        """
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        try:
            if self.system == "Windows":
                return self._print_windows(pdf_path, printer_name, copies)
            elif self.system == "Darwin":  # macOS
                return self._print_macos(pdf_path, printer_name, copies)
            elif self.system == "Linux":
                return self._print_linux(pdf_path, printer_name, copies)
            else:
                return {
                    "success": False,
                    "error": f"Printing not supported on {self.system}"
                }
        except Exception as e:
            logger.error(f"Error printing PDF: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _print_windows(self, pdf_path: str, printer_name: Optional[str], copies: int) -> Dict[str, Any]:
        """Print PDF on Windows using PowerShell."""
        try:
            # Use PowerShell to print PDF
            cmd = ["powershell", "-Command"]
            
            if printer_name:
                ps_script = f"""
                $printer = Get-Printer -Name '{printer_name}'
                if ($printer) {{
                    Start-Process -FilePath '{pdf_path}' -Verb Print -ArgumentList '/t','{printer_name}' -Wait
                }} else {{
                    Write-Error 'Printer not found'
                }}
                """
            else:
                ps_script = f"Start-Process -FilePath '{pdf_path}' -Verb Print -Wait"
            
            cmd.append(ps_script)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "message": f"PDF printed successfully to {printer_name or 'default printer'}",
                "copies": copies,
                "printer": printer_name
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Print command failed: {e.stderr}"
            }
    
    def _print_macos(self, pdf_path: str, printer_name: Optional[str], copies: int) -> Dict[str, Any]:
        """Print PDF on macOS using lpr."""
        try:
            cmd = ["lpr"]
            
            if printer_name:
                cmd.extend(["-P", printer_name])
            
            if copies > 1:
                cmd.extend(["-#", str(copies)])
            
            cmd.append(pdf_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "message": f"PDF printed successfully to {printer_name or 'default printer'}",
                "copies": copies,
                "printer": printer_name
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Print command failed: {e.stderr}"
            }
    
    def _print_linux(self, pdf_path: str, printer_name: Optional[str], copies: int) -> Dict[str, Any]:
        """Print PDF on Linux using lpr."""
        try:
            cmd = ["lpr"]
            
            if printer_name:
                cmd.extend(["-P", printer_name])
            
            if copies > 1:
                cmd.extend(["-#", str(copies)])
            
            cmd.append(pdf_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "message": f"PDF printed successfully to {printer_name or 'default printer'}",
                "copies": copies,
                "printer": printer_name
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Print command failed: {e.stderr}"
            }
    
    def print_license_card(self, front_pdf: str, back_pdf: str, combined_pdf: Optional[str] = None, 
                          printer_name: Optional[str] = None, copies: int = 1) -> Dict[str, Any]:
        """
        Print a complete license card (front, back, and optional combined).
        
        Args:
            front_pdf: Path to front PDF
            back_pdf: Path to back PDF  
            combined_pdf: Path to combined PDF (optional)
            printer_name: Printer name
            copies: Number of copies
            
        Returns:
            Dict with print results
        """
        results = {
            "success": True,
            "front_result": None,
            "back_result": None,
            "combined_result": None,
            "total_copies": copies
        }
        
        # Print combined PDF if available, otherwise print front and back separately
        if combined_pdf and os.path.exists(combined_pdf):
            logger.info(f"Printing combined license card: {combined_pdf}")
            combined_result = self.print_pdf(combined_pdf, printer_name, copies)
            results["combined_result"] = combined_result
            
            if not combined_result["success"]:
                results["success"] = False
        else:
            # Print front
            logger.info(f"Printing front of license card: {front_pdf}")
            front_result = self.print_pdf(front_pdf, printer_name, copies)
            results["front_result"] = front_result
            
            if not front_result["success"]:
                results["success"] = False
            
            # Print back
            logger.info(f"Printing back of license card: {back_pdf}")
            back_result = self.print_pdf(back_pdf, printer_name, copies)
            results["back_result"] = back_result
            
            if not back_result["success"]:
                results["success"] = False
        
        return results
    
    def get_default_printer(self) -> Optional[str]:
        """Get the default printer name."""
        try:
            if self.system == "Windows":
                cmd = ["powershell", "-Command", "Get-WmiObject -Query 'SELECT * FROM Win32_Printer WHERE Default=$true' | Select-Object Name"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 3:  # Header, separator, data
                    return lines[2].strip()
            elif self.system in ["Darwin", "Linux"]:
                cmd = ["lpstat", "-d"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                for line in result.stdout.split('\n'):
                    if 'system default destination:' in line:
                        return line.split(':')[1].strip()
        except Exception as e:
            logger.error(f"Error getting default printer: {e}")
        
        return None


# Global printing service instance
printing_service = PrintingService() 