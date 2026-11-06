#!/usr/bin/env node
/**
 * AutoSelect Antigravity - Universal NPM/NPX CLI Launcher
 * =======================================================
 * Subsystem: CLI Entrypoint & Autonomous Environment Harness
 * Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
 * Standard: Department 04 (Automation & Tooling) & Department 06 (Backend Engineering)
 * License: MIT
 *
 * Description:
 *   100% hands-free automatic launcher for AutoSelect Antigravity automation suite.
 *   Supports instant 1-line execution via:
 *     npx github:aiprincekumar/AutoSelect-Antigravity
 *   and global execution via:
 *     npm install -g github:aiprincekumar/AutoSelect-Antigravity
 *     autoselect-antigravity
 *
 * Responsibilities:
 *   1. Cross-platform OS detection (Windows, macOS, Linux).
 *   2. Python 3 detection & minimum version verification (>= 3.8).
 *   3. Automatic virtual environment (.venv) creation & path resolution.
 *   4. Automatic pip package installation from requirements.txt.
 *   5. Hands-free Windows Auto-Start registration on user login.
 *   6. Detached headless background dashboard server launch on port 8501.
 *   7. Automatic default web browser launch to http://127.0.0.1:8501/.
 *   8. Zero external npm dependencies (pure Node.js standard library).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const child_process = require('child_process');
const http = require('http');
const net = require('net');

// ============================================================================
// ANSI Color & Styling Constants
// ============================================================================

const isColorSupported = !process.env.NO_COLOR && (process.stdout.isTTY || process.env.FORCE_COLOR);

const colors = {
  reset: isColorSupported ? '\x1b[0m' : '',
  bold: isColorSupported ? '\x1b[1m' : '',
  dim: isColorSupported ? '\x1b[2m' : '',
  cyan: isColorSupported ? '\x1b[36m' : '',
  green: isColorSupported ? '\x1b[32m' : '',
  yellow: isColorSupported ? '\x1b[33m' : '',
  blue: isColorSupported ? '\x1b[34m' : '',
  magenta: isColorSupported ? '\x1b[35m' : '',
  red: isColorSupported ? '\x1b[31m' : '',
  white: isColorSupported ? '\x1b[37m' : '',
};

const sym = {
  check: isColorSupported ? `${colors.green}✓${colors.reset}` : '[OK]',
  cross: isColorSupported ? `${colors.red}✗${colors.reset}` : '[ERR]',
  info: isColorSupported ? `${colors.cyan}ℹ${colors.reset}` : '[INFO]',
  bullet: isColorSupported ? `${colors.magenta}◆${colors.reset}` : '*',
  arrow: isColorSupported ? `${colors.cyan}→${colors.reset}` : '->',
};

// ============================================================================
// Workspace & Path Resolution
// ============================================================================

const WORKSPACE_DIR = path.resolve(__dirname, '..');
const IS_WINDOWS = process.platform === 'win32';
const IS_MACOS = process.platform === 'darwin';
const IS_LINUX = process.platform === 'linux';

// Default configuration
const DEFAULT_PORT = 8501;
const DEFAULT_HOST = '127.0.0.1';

// ============================================================================
// Banner & Logging Utilities
// ============================================================================

function printBanner() {
  console.log(`
${colors.cyan}┌────────────────────────────────────────────────────────────────────────┐
│ ${colors.bold}${colors.white}           AutoSelect Antigravity - Autonomous CLI Launcher             ${colors.reset}${colors.cyan}│
│ ${colors.dim}       100% Hands-Free NPM/NPX Execution & Visual Dashboard             ${colors.reset}${colors.cyan}│
└────────────────────────────────────────────────────────────────────────┘${colors.reset}
`);
}

function logStep(stepNum, totalSteps, title) {
  console.log(`${colors.cyan}[${stepNum}/${totalSteps}]${colors.reset} ${colors.bold}${title}${colors.reset}`);
}

function logSuccess(message) {
  console.log(`    ${sym.check} ${message}`);
}

function logInfo(message) {
  console.log(`    ${sym.info} ${colors.dim}${message}${colors.reset}`);
}

function logWarn(message) {
  console.log(`    ${colors.yellow}!${colors.reset} ${colors.yellow}${message}${colors.reset}`);
}

function logError(message) {
  console.error(`    ${sym.cross} ${colors.red}${message}${colors.reset}`);
}

// ============================================================================
// Python Discovery & Environment Verification
// ============================================================================

/**
 * Searches for a valid Python 3.8+ executable on the host system.
 * Returns { cmd: string, args: string[], version: string } or null.
 */
function findSystemPython() {
  const candidates = IS_WINDOWS
    ? [
        { cmd: 'python', args: [] },
        { cmd: 'py', args: ['-3'] },
        { cmd: 'python3', args: [] },
      ]
    : [
        { cmd: 'python3', args: [] },
        { cmd: 'python', args: [] },
      ];

  for (const candidate of candidates) {
    try {
      const res = child_process.spawnSync(candidate.cmd, [...candidate.args, '--version'], {
        encoding: 'utf8',
        timeout: 5000,
        windowsHide: true,
      });

      if (res.status === 0) {
        const output = (res.stdout || res.stderr || '').trim();
        const match = output.match(/Python\s+(\d+)\.(\d+)(?:\.(\d+))?/i);
        if (match) {
          const major = parseInt(match[1], 10);
          const minor = parseInt(match[2], 10);
          if (major === 3 && minor >= 8) {
            return {
              cmd: candidate.cmd,
              args: candidate.args,
              version: output,
              major,
              minor,
            };
          }
        }
      }
    } catch {
      // Continue to next candidate
    }
  }

  return null;
}

/**
 * Resolves paths to Python executables inside the virtual environment (.venv).
 */
function getVenvPaths(workspace) {
  const venvDir = path.join(workspace, '.venv');
  if (IS_WINDOWS) {
    return {
      venvDir,
      python: path.join(venvDir, 'Scripts', 'python.exe'),
      pythonw: path.join(venvDir, 'Scripts', 'pythonw.exe'),
      pip: path.join(venvDir, 'Scripts', 'pip.exe'),
    };
  } else {
    return {
      venvDir,
      python: path.join(venvDir, 'bin', 'python'),
      pythonw: path.join(venvDir, 'bin', 'python'),
      pip: path.join(venvDir, 'bin', 'pip'),
    };
  }
}

/**
 * Ensures virtual environment exists; creates it if missing.
 */
function ensureVenv(systemPython, venvPaths, workspace) {
  if (fs.existsSync(venvPaths.python)) {
    logSuccess(`Virtual environment already active: ${colors.dim}(.venv)${colors.reset}`);
    return true;
  }

  logInfo(`Creating virtual environment at ${venvPaths.venvDir}...`);
  const createArgs = [...systemPython.args, '-m', 'venv', '.venv'];
  const res = child_process.spawnSync(systemPython.cmd, createArgs, {
    cwd: workspace,
    encoding: 'utf8',
    timeout: 60000,
    windowsHide: true,
  });

  if (res.status !== 0 || !fs.existsSync(venvPaths.python)) {
    logError(`Failed to create virtual environment: ${res.stderr || res.stdout}`);
    return false;
  }

  logSuccess(`Virtual environment created successfully.`);
  return true;
}

/**
 * Ensures pip is functional inside .venv, running ensurepip if necessary.
 */
function ensurePip(venvPaths, workspace) {
  if (fs.existsSync(venvPaths.pip)) {
    return true;
  }

  // Check if python -m pip works
  const pipCheck = child_process.spawnSync(venvPaths.python, ['-m', 'pip', '--version'], {
    encoding: 'utf8',
    timeout: 10000,
    windowsHide: true,
  });

  if (pipCheck.status === 0) {
    return true;
  }

  logInfo(`Bootstrapping pip via ensurepip...`);
  const ensureRes = child_process.spawnSync(venvPaths.python, ['-m', 'ensurepip', '--upgrade'], {
    cwd: workspace,
    encoding: 'utf8',
    timeout: 60000,
    windowsHide: true,
  });

  return ensureRes.status === 0;
}

/**
 * Installs dependencies from requirements.txt if present.
 */
function installDependencies(venvPaths, workspace) {
  const reqFile = path.join(workspace, 'requirements.txt');
  if (!fs.existsSync(reqFile)) {
    logInfo(`No requirements.txt found. Skipping pip install.`);
    return true;
  }

  // Quick check if core dependencies are already satisfied to save time
  const verifyCheck = child_process.spawnSync(
    venvPaths.python,
    ['-c', 'import pyautogui, psutil; print("OK")'],
    { encoding: 'utf8', timeout: 5000, windowsHide: true }
  );

  if (verifyCheck.status === 0 && (verifyCheck.stdout || '').trim() === 'OK') {
    logSuccess(`All required dependencies satisfied: ${colors.dim}(pyautogui, psutil)${colors.reset}`);
    return true;
  }

  logInfo(`Installing dependencies from requirements.txt...`);
  const pipCmd = venvPaths.python;
  const pipArgs = ['-m', 'pip', 'install', '-r', 'requirements.txt', '--disable-pip-version-check', '-q'];

  const res = child_process.spawnSync(pipCmd, pipArgs, {
    cwd: workspace,
    encoding: 'utf8',
    timeout: 120000,
    windowsHide: true,
  });

  if (res.status !== 0) {
    logWarn(`pip install reported warnings/errors: ${(res.stderr || '').trim()}`);
  } else {
    logSuccess(`Dependencies verified & up to date.`);
  }

  return true;
}

// ============================================================================
// Hands-Free Auto-Start Subsystem
// ============================================================================

/**
 * Configures persistent Windows Auto-Start on user login.
 */
function configureAutoStart(venvPaths, workspace) {
  if (!IS_WINDOWS) {
    logInfo(`Auto-Start startup registry is optimized for Windows; skipping on ${process.platform}.`);
    return true;
  }

  const autostartScript = path.join(workspace, 'step_4_reporting', 'autostart.py');
  if (fs.existsSync(autostartScript)) {
    const res = child_process.spawnSync(venvPaths.python, [autostartScript, '--enable'], {
      cwd: workspace,
      encoding: 'utf8',
      timeout: 15000,
      windowsHide: true,
    });

    if (res.status === 0) {
      logSuccess(`Windows Auto-Start registered in user Startup folder.`);
      return true;
    } else {
      logWarn(`Auto-Start registration returned non-zero code; proceeding.`);
    }
  } else {
    logInfo(`Autostart script not found at ${autostartScript}. Skipping.`);
  }

  return true;
}

// ============================================================================
// Server Readiness & Network Probes
// ============================================================================

/**
 * Tests if an HTTP port is listening and responsive.
 */
function checkServerLive(host, port, timeoutMs = 800) {
  return new Promise((resolve) => {
    const req = http.get(
      {
        host,
        port,
        path: '/api/automation/status',
        timeout: timeoutMs,
      },
      (res) => {
        resolve(res.statusCode === 200);
      }
    );

    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.on('error', () => {
      resolve(false);
    });
  });
}

/**
 * Polls server URL until it responds or timeout expires.
 */
async function waitForServer(host, port, maxAttempts = 15, intervalMs = 400) {
  for (let i = 0; i < maxAttempts; i++) {
    const isLive = await checkServerLive(host, port, 400);
    if (isLive) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

// ============================================================================
// Server Background Launch & Web Browser Trigger
// ============================================================================

/**
 * Launches the Dashboard Server in the background as a detached daemon.
 */
async function launchDashboardServer(venvPaths, workspace, port, host) {
  const isAlreadyLive = await checkServerLive(host, port, 600);
  if (isAlreadyLive) {
    logSuccess(`Dashboard Server is already active on http://${host}:${port}/`);
    return true;
  }

  logInfo(`Starting background daemon on http://${host}:${port}/...`);

  const serverScript = path.join(workspace, 'step_4_reporting', 'dashboard_server.py');
  const vbsLauncher = path.join(workspace, 'launchers', 'start_dashboard_background.vbs');

  if (IS_WINDOWS && fs.existsSync(vbsLauncher)) {
    // Prefer VBS launcher on Windows for completely windowless execution
    const child = child_process.spawn('wscript.exe', [vbsLauncher, '--no-browser'], {
      cwd: workspace,
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    child.unref();
  } else {
    // Spawn detached Python server
    const pyExe = IS_WINDOWS && fs.existsSync(venvPaths.pythonw) ? venvPaths.pythonw : venvPaths.python;
    const child = child_process.spawn(
      pyExe,
      [serverScript, '--port', String(port), '--host', host, '--no-browser'],
      {
        cwd: workspace,
        detached: true,
        stdio: 'ignore',
        windowsHide: true,
      }
    );
    child.unref();
  }

  // Await server readiness
  const isReady = await waitForServer(host, port, 20, 350);
  if (isReady) {
    logSuccess(`Dashboard Server successfully initialized & bound to port ${port}.`);
  } else {
    logWarn(`Dashboard Server spawned; awaiting socket bind on http://${host}:${port}/`);
  }

  return true;
}

/**
 * Opens the target URL in the user's default web browser cross-platform.
 */
function openBrowser(url) {
  try {
    if (IS_WINDOWS) {
      child_process.exec(`start "" "${url}"`);
    } else if (IS_MACOS) {
      const child = child_process.spawn('open', [url], { detached: true, stdio: 'ignore' });
      child.unref();
    } else {
      const child = child_process.spawn('xdg-open', [url], { detached: true, stdio: 'ignore' });
      child.unref();
    }
    logSuccess(`Opened default browser at ${colors.cyan}${url}${colors.reset}`);
  } catch (err) {
    logWarn(`Could not open web browser automatically: ${err.message}`);
    console.log(`    ${colors.bold}Open URL manually:${colors.reset} ${url}`);
  }
}

// ============================================================================
// CLI Command Handlers & Main Pipeline
// ============================================================================

function parseCliArgs() {
  const args = process.argv.slice(2);
  const options = {
    help: false,
    noBrowser: false,
    statusOnly: false,
    port: DEFAULT_PORT,
    host: DEFAULT_HOST,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--no-browser' || arg === '-n') {
      options.noBrowser = true;
    } else if (arg === '--status' || arg === '-s') {
      options.statusOnly = true;
    } else if (arg === '--port' || arg === '-p') {
      const p = parseInt(args[++i], 10);
      if (!isNaN(p)) options.port = p;
    } else if (arg === '--host') {
      options.host = args[++i] || DEFAULT_HOST;
    }
  }

  return options;
}

function showHelp() {
  printBanner();
  console.log(`
${colors.bold}USAGE:${colors.reset}
  npx github:aiprincekumar/AutoSelect-Antigravity [OPTIONS]
  autoselect-antigravity [OPTIONS]

${colors.bold}OPTIONS:${colors.reset}
  -h, --help            Show this help documentation
  -n, --no-browser      Do not open the dashboard in default browser
  -s, --status          Query server and auto-start status without launching
  -p, --port <port>     Set HTTP dashboard port (default: 8501)
      --host <host>     Set HTTP host interface (default: 127.0.0.1)

${colors.bold}EXAMPLES:${colors.reset}
  ${colors.dim}# 1-Line Zero-Install Execution via NPX:${colors.reset}
  npx github:aiprincekumar/AutoSelect-Antigravity

  ${colors.dim}# Global NPM Installation:${colors.reset}
  npm install -g github:aiprincekumar/AutoSelect-Antigravity
  autoselect-antigravity

  ${colors.dim}# Run Headless without Browser Popup:${colors.reset}
  npx github:aiprincekumar/AutoSelect-Antigravity --no-browser
`);
}

async function queryStatus(venvPaths, workspace, port, host) {
  printBanner();
  console.log(`${colors.bold}System Status Check:${colors.reset}\n`);

  // 1. Python Environment
  const sysPy = findSystemPython();
  console.log(`  ${sym.bullet} System Python     : ${sysPy ? `${colors.green}${sysPy.version}${colors.reset}` : `${colors.red}Not Found${colors.reset}`}`);

  // 2. Virtual Environment
  const hasVenv = fs.existsSync(venvPaths.python);
  console.log(`  ${sym.bullet} Virtual Env (.venv): ${hasVenv ? `${colors.green}Configured & Ready${colors.reset}` : `${colors.yellow}Missing${colors.reset}`}`);

  // 3. Server Live Check
  const isServerLive = await checkServerLive(host, port);
  console.log(`  ${sym.bullet} Dashboard Server  : ${isServerLive ? `${colors.green}ONLINE (http://${host}:${port}/)${colors.reset}` : `${colors.yellow}OFFLINE${colors.reset}`}`);

  // 4. Windows Auto-Start
  if (IS_WINDOWS && hasVenv) {
    const autostartScript = path.join(workspace, 'step_4_reporting', 'autostart.py');
    if (fs.existsSync(autostartScript)) {
      const res = child_process.spawnSync(venvPaths.python, [autostartScript, '--status'], {
        cwd: workspace,
        encoding: 'utf8',
        timeout: 5000,
        windowsHide: true,
      });
      const isEnabled = (res.stdout || '').includes('[ENABLED]');
      console.log(`  ${sym.bullet} Windows Auto-Start: ${isEnabled ? `${colors.green}ENABLED${colors.reset}` : `${colors.dim}DISABLED${colors.reset}`}`);
    }
  }

  console.log('\n');
}

/**
 * Main execution lifecycle coordinating the 5-step launch sequence.
 */
async function main() {
  const options = parseCliArgs();

  if (options.help) {
    showHelp();
    process.exit(0);
  }

  const venvPaths = getVenvPaths(WORKSPACE_DIR);

  if (options.statusOnly) {
    await queryStatus(venvPaths, WORKSPACE_DIR, options.port, options.host);
    process.exit(0);
  }

  printBanner();

  const TOTAL_STEPS = 5;

  // [1/5] Checking Python Environment
  logStep(1, TOTAL_STEPS, 'Checking Python Environment...');
  const systemPython = findSystemPython();
  if (!systemPython && !fs.existsSync(venvPaths.python)) {
    logError('Python 3.8 or higher was not detected on this machine.');
    console.error(`\n    Please install Python 3.8+ from https://www.python.org/downloads/ and ensure it is added to PATH.\n`);
    process.exit(1);
  }
  if (systemPython) {
    logSuccess(`Found ${systemPython.version} (${systemPython.cmd})`);
  } else {
    logSuccess(`Using existing virtual environment Python.`);
  }

  // [2/5] Setting up Virtual Environment (.venv)
  logStep(2, TOTAL_STEPS, 'Setting up Virtual Environment (.venv)...');
  const venvOk = ensureVenv(systemPython, venvPaths, WORKSPACE_DIR);
  if (!venvOk) {
    logError('Could not set up virtual environment. Aborting.');
    process.exit(1);
  }
  ensurePip(venvPaths, WORKSPACE_DIR);

  // [3/5] Installing Dependencies
  logStep(3, TOTAL_STEPS, 'Installing Dependencies...');
  installDependencies(venvPaths, WORKSPACE_DIR);

  // [4/5] Configuring Auto-Start
  logStep(4, TOTAL_STEPS, 'Configuring Hands-Free Auto-Start...');
  configureAutoStart(venvPaths, WORKSPACE_DIR);

  // [5/5] Launching Dashboard Server & Opening Browser
  logStep(5, TOTAL_STEPS, 'Launching Dashboard Server & Opening Browser...');
  await launchDashboardServer(venvPaths, WORKSPACE_DIR, options.port, options.host);

  const dashboardUrl = `http://${options.host}:${options.port}/`;

  if (!options.noBrowser) {
    openBrowser(dashboardUrl);
  } else {
    logInfo(`Browser launch bypassed by --no-browser flag.`);
  }

  console.log(`
${colors.green}✔ AutoSelect Antigravity is active and operational!${colors.reset}
  ${colors.bold}Dashboard URL:${colors.reset} ${colors.cyan}${dashboardUrl}${colors.reset}
  ${colors.bold}API Endpoint :${colors.reset} ${colors.cyan}${dashboardUrl}api/automation/status${colors.reset}
`);

  process.exit(0);
}

// Execute main entrypoint
main().catch((err) => {
  logError(`Fatal CLI execution error: ${err.message}`);
  process.exit(1);
});
