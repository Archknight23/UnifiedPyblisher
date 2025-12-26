# Unified Publisher - Progress & Next Steps

## ✅ Completed (Session 1)
1. ✅ Cloned repo to `/Users/chaosuser/UnifiedPyblisher`
2. ✅ Deleted old main.py (browser automation approach)
3. ✅ Created `publisherlogic/main.py` with:
   - Imports (PyQt6, QWebChannel)
   - Bridge class (QObject with signals/slots)
   - operationFinished signal (Python→JS)
   - testConnection() method (@pyqtSlot)
   - handlePublishRequest() method (receives post data)
   - UnifiedWindow class (creates window, embeds browser, loads HTML)
   - main() function (app entry point)
4. ✅ Created `publisherlogic/__init__.py`
5. ✅ Created `requirements.txt`

## 🔄 Currently Working On
- Docked composer + safer X/YT flow (no paid API)

## 📋 Next Steps
1. **Test docked composer + external fallback**:
   - Ensure X opens in docked panel when enabled
   - Ensure YouTube forces external (Google blocks embedded login)
   - Verify “Composer Launched” panel shows URL + copy button

2. **Stability fixes**:
   - If X login fails embedded, auto-open external instead
   - Add clear UI hint when external composer opens

3. **Bluesky API**:
   - Install `atproto` dependency
   - Verify successful post + error handling

4. **Optional polish**:
   - Add X handle field for preview (no API)
   - Add tabs/switcher in docked composer

5. **Git commit and push**

## Key Architecture

### Python Backend (main.py)
```python
class Bridge(QObject):
    operationFinished = pyqtSignal(str, bool, str)  # Send TO JS
    
    @pyqtSlot(str)  # Receive FROM JS
    def handlePublishRequest(self, json_data):
        # Parse data, call APIs, emit results back
```

### HTML Frontend (index.html - TO CREATE)
```javascript
// Initialize QWebChannel
new QWebChannel(qt.webChannelTransport, function(channel) {
    window.pyBridge = channel.objects.pyBridge;
    
    // Call Python
    pyBridge.handlePublishRequest(JSON.stringify(data));
    
    // Listen for Python response
    pyBridge.operationFinished.connect(function(platform, success, msg) {
        showToast(`${platform}: ${msg}`, success ? 'success' : 'error');
    });
});
```

### Data Flow
1. User types in HTML UI
2. Clicks "Publish Now"
3. JS gathers: `{content, platforms[], image, credentials{}}`
4. JS calls: `pyBridge.handlePublishRequest(jsonString)`
5. Python receives, calls APIs
6. Python emits: `operationFinished.emit(platform, success, message)`
7. JS receives signal, updates UI

## File Structure
```
UnifiedPyblisher/
├── index.html                    # ← TO CREATE
├── AI_instructions.md            # This file
├── requirements.txt              # ✅ Done
├── publisherlogic/
│   ├── __init__.py              # ✅ Done
│   ├── main.py                  # ✅ Done
│   ├── api_bluesky.py           # To create
│   ├── api_twitter.py           # To create
│   └── api_youtube.py           # To create
├── LICENSE
└── README.md
```

## Token Usage
- Session start: 0/200000
- Current: ~94000/200000 (47% used)
- Remaining: ~106000 tokens

## Notes
- User: Roxy, using Zed editor
- Learning by writing code herself
- Keep explanations concise
- Update this file as we progress

## Testing Commands
```bash
cd ~/UnifiedPyblisher
python -m publisherlogic.main
```

## Known Constraints
- YouTube login often fails inside embedded webviews (Google/FedCM); force external browser.
- X can work embedded but may still require external fallback depending on login policies.
- YouTube Data API does not support Community posts; Studio paste flow is required.

## Recent Changes (Session 2)
- Added docked composer panel inside the main window (right side).
- Added persistent web profile for composer logins.
- Added Settings login buttons for X/YouTube.
- Added “Force YouTube to open external” setting (default on).
- Added “Composer Launched” panel with URL + copy button.
- Updated preview to reflect saved creds (Bluesky handle, YouTube channel ID).
