## cd forecasting_web
pip install -r requirements.txt
python app.py

pip install --upgrade Flask-Session
pip show Flask-Session



forecasting_web/README.md

Perfect 👌 — we’ll make this **professional and self-contained** so anyone (including you) can launch the forecasting web app easily.

Here’s the plan:

---

## 🧩 Step 1: Create a single PowerShell launcher

Rename your `.bat` file to **`Launch_ForecastingWeb.ps1`**, and replace its content with this **full, improved version**:

```powershell
<#
Launch_ForecastingWeb.ps1
----------------------------------------
This script:
1. Ensures all required packages are installed
2. Launches the Flask forecasting web app
3. Waits until Flask is running
4. Launches ngrok once Flask is ready
5. Copies the public URL to clipboard
----------------------------------------
#>

Write-Host "🚀 Starting Forecasting Web Application..." -ForegroundColor Cyan

# === Allow PowerShell scripts to run (safe for current user) ===
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force | Out-Null

# === Define paths ===
$condaHook = "C:\Users\gshk0\anaconda3\shell\condabin\conda-hook.ps1"
$projectDir = "C:\Users\gshk0\Downloads\forecasting_web"
$ngrokPath = "C:\Users\gshk0\Downloads\ngrok.exe"

# === Step 1: Ensure dependencies are installed ===
Write-Host "📦 Installing required Python packages..." -ForegroundColor Yellow

$requirementsFile = Join-Path $projectDir "requirements.txt"

# Create requirements.txt if it doesn’t exist
if (-not (Test-Path $requirementsFile)) {
    Write-Host "Creating requirements.txt automatically..." -ForegroundColor DarkGray
    $requirements = @(
        "flask",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn"
    )
    $requirements | Out-File $requirementsFile -Encoding utf8
}

# Run pip install
& $condaHook
conda activate base
pip install -r $requirementsFile

# === Step 2: Start Flask app in a new PowerShell window ===
Write-Host "🧠 Launching Flask web app..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "& '$condaHook'; conda activate base; cd '$projectDir'; python app.py"
) -WindowStyle Normal

# === Step 3: Wait until Flask is running ===
Write-Host "⏳ Waiting for Flask to start (checking port 5000)..." -ForegroundColor Yellow

$flaskReady = $false
for ($i = 0; $i -lt 30; $i++) { # check for up to ~30 seconds
    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port 5000 -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            $flaskReady = $true
            break
        }
    } catch { }
    Start-Sleep -Seconds 2
}

if (-not $flaskReady) {
    Write-Host "❌ Flask did not start within the expected time." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Flask is running on http://127.0.0.1:5000" -ForegroundColor Green

# === Step 4: Start ngrok and copy the public URL to clipboard ===
Write-Host "🌐 Launching ngrok tunnel..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd 'C:\Users\gshk0\Downloads'; " +
    ".\ngrok http 5000 --log=stdout | " +
    "Select-String -Pattern 'https://[a-z0-9.-]+\.ngrok-free\.app' -AllMatches | " +
    "ForEach-Object { $_.Matches } | ForEach-Object { $_.Value } | Set-Clipboard; " +
    "Write-Host 'Public ngrok URL copied to clipboard!' -ForegroundColor Green; " +
    ".\ngrok http 5000"
) -WindowStyle Normal

Write-Host "🌟 All systems running. Flask + ngrok ready!" -ForegroundColor Green
```

---

## 🧩 Step 2: Create a `requirements.txt`

If you don’t already have one in your `forecasting_web` folder, create:

📄 **forecasting_web/requirements.txt**

```
flask
pandas
numpy
matplotlib
seaborn
scikit-learn
```

You can add more packages later if your app needs them (like `requests` or `openpyxl`).

---

## 🧩 Step 3: Create a professional README.md

📄 **forecasting_web/README.md**

```markdown
# Forecasting Web Application

A Flask-based web app for forecasting and participant data visualization.

---

## 🚀 Quick Start

### 1. Requirements
- Windows
- [Anaconda](https://www.anaconda.com/download)
- [ngrok](https://ngrok.com/download)

### 2. Folder Structure
```

forecasting_web/
│
├── app.py
├── requirements.txt
├── data/
├── static/
├── templates/
└── flask_session/

````

### 3. Launch Instructions

#### Option A — Automatic setup
Run the PowerShell launcher:
```powershell
powershell -ExecutionPolicy Bypass -File .\Launch_ForecastingWeb.ps1
````

This will:

1. Install all required packages (`pip install -r requirements.txt`)
2. Start the Flask web app
3. Wait until Flask is online
4. Start ngrok
5. Copy the public URL to your clipboard

#### Option B — Manual setup

```bash
conda activate base
cd forecasting_web
pip install -r requirements.txt
python app.py
```

Then in another terminal:

```bash
ngrok http 5000
```

---

## 🌐 Output

Once running, visit:

* Local: [http://127.0.0.1:5000](http://127.0.0.1:5000)
* Public (via ngrok): copied automatically to your clipboard

---

## 🧩 Notes

* The launcher script auto-creates `requirements.txt` if missing.
* Flask must run before ngrok can establish a tunnel.
* You can customize ports by editing `app.py` and updating the script accordingly.

```

---

### ✅ What this setup gives you
- Fully automated environment setup.
- Automatic dependency installation.
- Intelligent wait-for-Flask before ngrok.
- Clipboard-ready public URL.
- Clear, professional documentation.

---

Would you like me to make the README include **troubleshooting and FAQ** (e.g., “ngrok not found”, “port already in use”, “PowerShell permission error”)? It’d make it even more polished and classroom-ready.
```
