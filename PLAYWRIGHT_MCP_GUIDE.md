# 🎭 Playwright MCP Setup Guide

## ✅ What's Installed

- **@playwright/mcp@0.0.40** - Official Microsoft Playwright MCP Server
- **Playwright Browsers** - Chromium, Firefox, WebKit
- **VS Code Configuration** - Ready for MCP client integration

## 🚀 How to Use Playwright MCP

### Option 1: With Claude Dev Extension

1. Install **Claude Dev** extension in VS Code
2. Configure Claude to use the MCP server
3. Use natural language commands like:

   ```
   Navigate to http://localhost:8000/patients/cda/1472807983/L3/
   Click on "Extended Patient Information" tab
   Click on "Clinical Information" tab
   Take a screenshot of the clinical sections
   Verify that all accordion sections are visible
   Check if the "History of Medication use Narrative" section has good contrast
   ```

### Option 2: Direct MCP Server

Start the server manually:

```bash
mcp-server-playwright --host localhost --port 3001 --browser chrome
```

### Option 3: HTTP Server Mode

For web-based access:

```bash
mcp-server-playwright --host 0.0.0.0 --port 3001 --browser chrome
```

## 📋 Common Playwright MCP Commands

### Navigation

- `Navigate to [URL]`
- `Go back to previous page`
- `Refresh the current page`
- `Close the current tab`

### Interaction

- `Click on [element]`
- `Type "[text]" in [field]`
- `Select "[option]" from [dropdown]`
- `Upload file [path] to [upload field]`

### Verification

- `Take a screenshot`
- `Verify that [element] is visible`
- `Check if [text] exists on the page`
- `Wait for [element] to appear`

### Clinical Sections Specific

- `Click on the Clinical Information tab`
- `Expand the medication section`
- `Check if all 13 clinical sections are present`
- `Verify contrast in clinical headers`
- `Test accordion expand/collapse functionality`

## 🔧 Configuration Files

### `.vscode/mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "C:\\Users\\Duncan\\AppData\\Roaming\\npm\\mcp-server-playwright.cmd",
      "args": [
        "--host", "localhost",
        "--port", "3001",
        "--browser", "chrome",
        "--headless", "false",
        "--viewport-size", "1920x1080"
      ]
    }
  }
}
```

## 🎯 Testing Your Clinical Sections

Perfect commands for testing our clinical interface:

1. **Navigate to Patient Data:**

   ```
   Navigate to http://localhost:8000/patients/cda/1472807983/L3/
   ```

2. **Access Clinical Sections:**

   ```
   Click on "Extended Patient Information" tab
   Wait for the tab content to load
   Click on "Clinical Information" tab
   ```

3. **Test Interface:**

   ```
   Take a screenshot of the clinical sections
   Verify that "History of Medication use Narrative" is visible
   Check if the header has good contrast (dark text on light background)
   Expand the first clinical section
   Verify no content spillover outside the Clinical Information tab
   ```

4. **Test All Sections:**

   ```
   Count the number of clinical sections (should be 13)
   Test expand/collapse on each section
   Verify all section headers are readable
   Check for any content appearing in wrong tabs
   ```

## 🐛 Troubleshooting

### Server Won't Start

```bash
# Check if port is available
netstat -an | findstr 3001

# Try different port
mcp-server-playwright --port 3002
```

### Browser Issues

```bash
# Reinstall browsers
npx playwright install

# Use different browser
mcp-server-playwright --browser firefox
```

### VS Code Integration

1. Make sure MCP-compatible extension is installed
2. Check `.vscode/mcp.json` configuration
3. Restart VS Code after configuration changes

## 🎉 Benefits for Your Project

- **Natural Language Testing**: "Check if clinical sections display properly"
- **Visual Verification**: Screenshots and element inspection
- **Interactive Debugging**: Real-time browser control
- **Accessibility Testing**: Verify contrast and readability
- **Cross-browser Testing**: Test in Chrome, Firefox, Safari
- **No Code Required**: Just describe what you want to test

Perfect for validating all the clinical sections work we've done! 🚀
