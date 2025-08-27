# Cura Webhook Progress Plugin

A Cura plugin that monitors 3D print progress and sends real-time updates to a webhook URL every 1% of completion.

## 🚀 Features

- **Real-time Progress Monitoring**: Tracks print progress from Cura and sends updates every 1%
- **Comprehensive Event Tracking**: Monitors print start, progress updates, and completion/cancellation
- **Detailed Progress Information**: Includes elapsed time, estimated remaining time, and job details
- **Thread-safe Operations**: Non-blocking webhook requests that don't interfere with Cura's UI
- **Network Printer Support**: Works best with OctoPrint, Ultimaker, and other networked printers
- **Easy Configuration**: Simple webhook URL configuration

## 📋 Requirements

- **Cura**: Version 5.0 or later
- **Printer Connection**: Works best with networked printers (OctoPrint, Ultimaker, etc.)
- **Webhook Endpoint**: An accessible HTTP endpoint to receive progress updates

## 🔧 Installation

1. **Download the Plugin**:
   - Download or clone this repository
   - Extract the files if needed

2. **Locate Cura Plugins Directory**:
   - Open Cura
   - Go to `Help` → `Show Configuration Folder`
   - Navigate to the `plugins` folder (create it if it doesn't exist)

3. **Install the Plugin**:
   - Copy the entire repository folder to the `plugins` directory
   - Rename the folder to `WebhookProgressPlugin` (must match the class name)

4. **Configure Webhook URL**:
   - Open `WebhookProgressPlugin.py` in a text editor
   - Find this line: `self._webhook_url = "https://your-webhook-url.com/progress"`
   - Replace with your actual webhook URL

5. **Restart Cura**

## ⚙️ Configuration

Before using the plugin, you **must** configure your webhook URL:

1. Open `WebhookProgressPlugin.py`
2. Locate the `_load_settings` method
3. Update this line with your webhook URL:
```python
self._webhook_url = "https://your-webhook-url.com/progress"
```

### Cura Version Compatibility

Update the `supported_sdk_versions` in `plugin.json` based on your Cura version:

- **Cura 5.0-5.2**: `["8.0.0"]`
- **Cura 5.3-5.4**: `["8.1.0"]`
- **Cura 5.5+**: `["8.2.0"]`

## 📡 Webhook API

The plugin sends HTTP POST requests with JSON payloads to your configured webhook URL.

### Event Types

#### 1. Print Started
```json
{
    "event_type": "print_started",
    "data": {
        "job_name": "MyModel.gcode",
        "start_time": 1640995200.123
    },
    "plugin_version": "1.0.0"
}
```

#### 2. Progress Update (every 1%)
```json
{
    "event_type": "progress_update",
    "data": {
        "job_name": "MyModel.gcode",
        "progress_percent": 25,
        "elapsed_time_seconds": 1800.5,
        "estimated_remaining_seconds": 5400.0,
        "timestamp": 1640997000.456
    },
    "plugin_version": "1.0.0"
}
```

#### 3. Print Ended
```json
{
    "event_type": "print_ended",
    "data": {
        "message": "Print job ended or cancelled",
        "timestamp": 1641002400.789
    },
    "plugin_version": "1.0.0"
}
```

## 🔍 Troubleshooting

### Plugin Not Loading
1. Check that all files are in the correct directory structure
2. Verify `plugin.json` has the correct SDK versions for your Cura version
3. Check Cura logs: `Help` → `Show Configuration Folder` → `cura.log`

### No Webhook Updates
1. Verify your webhook URL is correctly configured
2. Test your webhook endpoint with a tool like curl or Postman
3. Check Cura logs for HTTP errors
4. Ensure your printer is connected and recognized by Cura

## 📝 License

This project is licensed under the MIT License.

## 🤝 Acknowledgments

- Built for the [Ultimaker Cura](https://github.com/Ultimaker/Cura) 3D printing software
- Inspired by existing Cura monitoring plugins like the OctoPrint Connection plugin

---

**Note**: This plugin monitors print progress from Cura's perspective and requires an active printer connection. It works best with networked printers that provide regular progress updates to Cura.
