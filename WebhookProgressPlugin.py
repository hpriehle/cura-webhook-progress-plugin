import json
import threading
import time
from typing import Optional, Dict, Any
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.i18n import i18nCatalog

try:
    from PyQt6.QtCore import QTimer, QObject, pyqtSignal
except ImportError:
    try:
        from PyQt5.QtCore import QTimer, QObject, pyqtSignal
    except ImportError:
        from UM.Qt.QtCore import QTimer, QObject, pyqtSignal

from cura.CuraApplication import CuraApplication

i18n_catalog = i18nCatalog("cura")


@signalemitter
class WebhookProgressPlugin(Extension, QObject):
    def __init__(self) -> None:
        super().__init__()
        
        self._application = CuraApplication.getInstance()
        self._webhook_url = ""
        self._last_progress = -1
        self._is_printing = False
        self._current_job_name = ""
        self._print_start_time = 0
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_print_progress)
        self._check_timer.setSingleShot(False)
        
        # Settings for webhook URL (you can extend this to use Cura's preferences system)
        self._load_settings()
        
        # Connect to printer output device manager
        self._application.getMachineManager().printerOutputDevicesChanged.connect(self._on_printer_output_devices_changed)
        
        # Start monitoring timer (check every 5 seconds)
        self._check_timer.start(5000)
        
        Logger.log("i", "WebhookProgressPlugin initialized")

    def _load_settings(self) -> None:
        """Load plugin settings. For now, we'll use a hardcoded URL.
        You can extend this to use Cura's preference system."""
        # TODO: Implement proper settings dialog
        # For now, set your webhook URL here:
        self._webhook_url = "https://your-webhook-url.com/progress"
        
        if not self._webhook_url or self._webhook_url == "https://your-webhook-url.com/progress":
            Logger.log("w", "No webhook URL configured for WebhookProgressPlugin. Please update the URL in WebhookProgressPlugin.py")

    def _on_printer_output_devices_changed(self) -> None:
        """Called when printer output devices change."""
        output_devices = self._application.getMachineManager().printerOutputDevices
        
        for device in output_devices:
            try:
                if hasattr(device, 'printJobChanged'):
                    device.printJobChanged.connect(self._on_print_job_changed)
                if hasattr(device, 'printProgressChanged'):
                    device.printProgressChanged.connect(self._on_print_progress_changed)
                if hasattr(device, 'connectionStateChanged'):
                    device.connectionStateChanged.connect(self._on_connection_state_changed)
            except Exception as e:
                Logger.log("w", f"Could not connect to device signals: {e}")

    def _on_connection_state_changed(self, connection_state) -> None:
        """Called when printer connection state changes."""
        Logger.log("d", f"Printer connection state changed: {connection_state}")

    def _on_print_job_changed(self, job) -> None:
        """Called when print job changes."""
        if job is None:
            self._is_printing = False
            self._current_job_name = ""
            self._last_progress = -1
            self._send_webhook_update("print_ended", {
                "message": "Print job ended or cancelled",
                "timestamp": time.time()
            })
        else:
            self._is_printing = True
            self._current_job_name = job.getName() if hasattr(job, 'getName') else "Unknown"
            self._print_start_time = time.time()
            self._last_progress = 0
            
            self._send_webhook_update("print_started", {
                "job_name": self._current_job_name,
                "start_time": self._print_start_time
            })

    def _on_print_progress_changed(self, progress: float) -> None:
        """Called when print progress changes."""
        if not self._is_printing:
            return
            
        # Convert to percentage and round to nearest integer
        progress_percent = int(progress * 100)
        
        # Only send update if progress has increased by at least 1%
        if progress_percent > self._last_progress:
            self._last_progress = progress_percent
            
            elapsed_time = time.time() - self._print_start_time
            estimated_total = elapsed_time / (progress if progress > 0 else 0.01)
            estimated_remaining = estimated_total - elapsed_time
            
            self._send_webhook_update("progress_update", {
                "job_name": self._current_job_name,
                "progress_percent": progress_percent,
                "elapsed_time_seconds": elapsed_time,
                "estimated_remaining_seconds": estimated_remaining,
                "timestamp": time.time()
            })

    def _check_print_progress(self) -> None:
        """Periodically check print progress from connected devices."""
        if not self._webhook_url or self._webhook_url == "https://your-webhook-url.com/progress":
            return
            
        try:
            output_devices = self._application.getMachineManager().printerOutputDevices
            
            for device in output_devices:
                if hasattr(device, 'activePrintJob'):
                    job = device.activePrintJob
                    if job is not None:
                        if not self._is_printing:
                            # New print job detected
                            self._on_print_job_changed(job)
                        
                        # Get progress
                        progress = 0.0
                        if hasattr(job, 'getProgress'):
                            progress = job.getProgress()
                        elif hasattr(device, 'printProgress'):
                            progress = device.printProgress
                        
                        if progress is not None:
                            self._on_print_progress_changed(progress)
                    elif self._is_printing:
                        # Print job ended
                        self._on_print_job_changed(None)
        except Exception as e:
            Logger.log("e", f"Error checking print progress: {e}")

    def _send_webhook_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send update to webhook URL."""
        if not self._webhook_url or self._webhook_url == "https://your-webhook-url.com/progress":
            Logger.log("w", "Webhook URL not configured, skipping update")
            return
            
        payload = {
            "event_type": event_type,
            "data": data,
            "plugin_version": "1.0.0"
        }
        
        # Send in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._send_webhook_request, args=(payload,))
        thread.daemon = True
        thread.start()

    def _send_webhook_request(self, payload: Dict[str, Any]) -> None:
        """Send HTTP request to webhook URL."""
        try:
            json_data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                self._webhook_url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Cura-WebhookProgressPlugin/1.0.0'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    Logger.log("d", f"Webhook update sent successfully: {payload['event_type']}")
                else:
                    Logger.log("w", f"Webhook returned status {response.getcode()}")
                    
        except HTTPError as e:
            Logger.log("e", f"HTTP error sending webhook: {e.code} - {e.reason}")
        except URLError as e:
            Logger.log("e", f"URL error sending webhook: {e.reason}")
        except Exception as e:
            Logger.log("e", f"Unexpected error sending webhook: {str(e)}")

    def setWebhookUrl(self, url: str) -> None:
        """Set the webhook URL (for future settings dialog)."""
        self._webhook_url = url
        Logger.log("i", f"Webhook URL set to: {url}")
