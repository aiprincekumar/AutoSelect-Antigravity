#!/usr/bin/env node
/**
 * AutoSelect Antigravity - Universal NPM/NPX CLI Launcher
 * =======================================================
 * Subsystem: CLI Entrypoint & Autonomous Environment Harness (Root Bridge)
 * Author: Atul Verma (aiprincekumar / aiprincekumar010100@gmail.com)
 * Standard: Department 06 (Backend Engineering) & Department 12 (DevOps, Build & Release)
 * License: MIT
 *
 * Description:
 *   100% hands-free automatic launcher for the AutoSelect Antigravity automation suite.
 *   Provides instant single-command execution via:
 *     npx github:aiprincekumar/AutoSelect-Antigravity
 *   and global execution via:
 *     npm install -g github:aiprincekumar/AutoSelect-Antigravity
 *     autoselect-antigravity
 *
 * Architecture & Path Resolution:
 *   Dynamically bridges the root repository to the active subsystem:
 *     - WORKSPACE_DIR: Repository root containing Mouse & Keyboard automation suites
 *     - KEYBOARD_DIR : Primary Python automation subsystem (Keyboard Automation)
 *
 * 5-Step Automated Initialization Sequence:
 *   [1/5] Detect host Python 3.8+ (python, py -3, python3).
 *   [2/5] Validate / provision virtual environment (.venv) inside KEYBOARD_DIR.
 *   [3/5] Install / verify dependencies (pyautogui, psutil) from requirements.txt.
 *   [4/5] Configure silent Windows Auto-Start shortcut via step_4_reporting/autostart.py.
 *   [5/5] Launch headless background dashboard server on port 8501 and trigger default browser.
 *
 * Zero external npm dependencies (pure Node.js standard library).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const child_process = require('child_process');
const http = require('http');

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
// Subsystem-Aware Path Resolution
// ============================================================================

const WORKSPACE_DIR = path.resolve(__dirname, '..');
const KEYBOARD_DIR = fs.existsSync(path.join(WORKSPACE_DIR, 'Keyboard Automation'))
  ? path.join(WORKSPACE_DIR, 'Keyboard Automation')
  : WORKSPACE_DIR;

const IS_WINDOWS = process.platform === 'win32';
const IS_MACOS = process.platform === 'darwin';
const IS_LINUX = process.platform === 'linux';

// Default runtime configuration
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
// Step 1: Python Discovery & Environment Verification
// ============================================================================

/**
 * Searches for a valid Python 3.8+ executable on the host system.
 * Returns { cmd: string, args: string[], version: string, major: number, minor: number } or null.
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
      // Continue searching
    }
  }

  return null;
}

// ============================================================================
// Step 2: Virtual Environment (.venv) Path Resolution & Provisioning
// ============================================================================

/**
 * Resolves paths to Python executables inside the target virtual environment.
 * Prioritizes KEYBOARD_DIR/.venv, then falls back to WORKSPACE_DIR/.venv.
 */
function getVenvPaths(keyboardDir, workspaceDir) {
  let venvDir = path.join(keyboardDir, '.venv');
  if (!fs.existsSync(venvDir) && fs.existsSync(path.join(workspaceDir, '.venv'))) {
    venvDir = path.join(workspaceDir, '.venv');
  }

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
 * Ensures virtual environment exists; provisions it inside target directory if missing.
 */
function ensureVenv(systemPython, venvPaths, targetDir) {
  if (fs.existsSync(venvPaths.python)) {
    logSuccess(`Virtual environment already active: ${colors.dim}(${path.relative(WORKSPACE_DIR, venvPaths.venvDir)})${colors.reset}`);
    return true;
  }

  logInfo(`Provisioning virtual environment at ${venvPaths.venvDir}...`);
  const createArgs = [...systemPython.args, '-m', 'venv', venvPaths.venvDir];
  const res = child_process.spawnSync(systemPython.cmd, createArgs, {
    cwd: targetDir,
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
 * Ensures pip is functional inside the virtual environment.
 */
function ensurePip(venvPaths, targetDir) {
  if (fs.existsSync(venvPaths.pip)) {
    return true;
  }

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
    cwd: targetDir,
    encoding: 'utf8',
    timeout: 60000,
    windowsHide: true,
  });

  return ensureRes.status === 0;
}

// ============================================================================
// Step 3: Dependency Resolution & Verification
// ============================================================================

/**
 * Installs and verifies dependencies (pyautogui, psutil) from requirements.txt.
 */
function installDependencies(venvPaths, keyboardDir, workspaceDir) {
  const reqCandidates = [
    path.join(keyboardDir, 'requirements.txt'),
    path.join(workspaceDir, 'requirements.txt'),
  ];
  const reqFile = reqCandidates.find((p) => fs.existsSync(p));

  // Fast-path: check if core dependencies are already satisfied
  const verifyCheck = child_process.spawnSync(
    venvPaths.python,
    ['-c', 'import pyautogui, psutil; print("OK")'],
    { encoding: 'utf8', timeout: 5000, windowsHide: true }
  );

  if (verifyCheck.status === 0 && (verifyCheck.stdout || '').trim() === 'OK') {
    logSuccess(`All required dependencies satisfied: ${colors.dim}(pyautogui, psutil)${colors.reset}`);
    return true;
  }

  if (!reqFile) {
    logInfo(`No requirements.txt found; attempting direct dependency install...`);
    const pipDirect = child_process.spawnSync(
      venvPaths.python,
      ['-m', 'pip', 'install', 'pyautogui', 'psutil', '--disable-pip-version-check', '-q'],
      { cwd: keyboardDir, encoding: 'utf8', timeout: 120000, windowsHide: true }
    );
    if (pipDirect.status === 0) {
      logSuccess(`Direct dependencies installed successfully.`);
    } else {
      logWarn(`pip install reported warnings/errors: ${(pipDirect.stderr || '').trim()}`);
    }
    return true;
  }

  logInfo(`Installing dependencies from ${path.relative(WORKSPACE_DIR, reqFile)}...`);
  const pipArgs = ['-m', 'pip', 'install', '-r', reqFile, '--disable-pip-version-check', '-q'];

  const res = child_process.spawnSync(venvPaths.python, pipArgs, {
    cwd: path.dirname(reqFile),
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
// Step 4: Hands-Free Windows Auto-Start Subsystem
// ============================================================================

/**
 * Configures persistent Windows Auto-Start shortcut on user login.
 */
function configureAutoStart(venvPaths, keyboardDir) {
  if (!IS_WINDOWS) {
    logInfo(`Auto-Start startup registry is optimized for Windows; skipping on ${process.platform}.`);
    return true;
  }

  const autostartCandidates = [
    path.join(keyboardDir, 'step_4_reporting', 'autostart.py'),
    path.join(WORKSPACE_DIR, 'step_4_reporting', 'autostart.py'),
  ];
  const autostartScript = autostartCandidates.find((p) => fs.existsSync(p));

  if (autostartScript && fs.existsSync(venvPaths.python)) {
    const res = child_process.spawnSync(venvPaths.python, [autostartScript, '--enable'], {
      cwd: path.dirname(path.dirname(autostartScript)),
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
    logInfo(`Autostart script not found; skipping startup registry.`);
  }

  return true;
}

// ============================================================================
// Step 5: Server Readiness & Network Probes
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
async function waitForServer(host, port, maxAttempts = 18, intervalMs = 350) {
  for (let i = 0; i < maxAttempts; i++) {
    const isLive = await checkServerLive(host, port, 350);
    if (isLive) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

/**
 * Launches the Dashboard Server in the background as a detached headless daemon.
 */
async function launchDashboardServer(venvPaths, keyboardDir, workspaceDir, port, host) {
  const isAlreadyLive = await checkServerLive(host, port, 600);
  if (isAlreadyLive) {
    logSuccess(`Dashboard Server is already active on http://${host}:${port}/`);
    return true;
  }

  logInfo(`Starting background daemon on http://${host}:${port}/...`);

  const serverScriptCandidates = [
    path.join(keyboardDir, 'step_4_reporting', 'dashboard_server.py'),
    path.join(workspaceDir, 'step_4_reporting', 'dashboard_server.py'),
  ];
  const serverScript = serverScriptCandidates.find((p) => fs.existsSync(p));

  if (!serverScript) {
    logError(`Dashboard server script not found in ${keyboardDir} or ${workspaceDir}.`);
    return false;
  }

  const vbsCandidates = [
    path.join(workspaceDir, 'start_dashboard_background.vbs'),
    path.join(keyboardDir, 'launchers', 'start_dashboard_background.vbs'),
  ];
  const vbsLauncher = vbsCandidates.find((p) => fs.existsSync(p));

  if (IS_WINDOWS && vbsLauncher && port === DEFAULT_PORT && host === DEFAULT_HOST) {
    // Prefer VBS launcher on Windows for standard port for completely windowless execution
    const child = child_process.spawn('wscript.exe', [vbsLauncher, '--no-browser'], {
      cwd: keyboardDir,
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    child.unref();
  } else {
    // Direct detached Python server spawn
    const pyExe = IS_WINDOWS && fs.existsSync(venvPaths.pythonw) ? venvPaths.pythonw : venvPaths.python;
    const child = child_process.spawn(
      pyExe,
      [serverScript, '--port', String(port), '--host', host, '--no-browser'],
      {
        cwd: keyboardDir,
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
// Service Shutdown & Process Teardown (--stop)
// ============================================================================

/**
 * Stops running automation and gracefully terminates the dashboard server process.
 */
async function stopServer(port, host, keyboardDir) {
  printBanner();
  console.log(`${colors.bold}Stopping AutoSelect Antigravity Services...${colors.reset}\n`);

  let stoppedAutomation = false;
  let stoppedServer = false;

  // 1. Send stop request to the dashboard server API if alive
  const isLive = await checkServerLive(host, port, 1000);
  if (isLive) {
    try {
      await new Promise((resolve) => {
        const req = http.request(
          {
            host,
            port,
            path: '/api/automation/stop',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            timeout: 2500,
          },
          (res) => {
            stoppedAutomation = true;
            resolve();
          }
        );
        req.on('error', () => resolve());
        req.on('timeout', () => {
          req.destroy();
          resolve();
        });
        req.write(JSON.stringify({}));
        req.end();
      });
    } catch {
      // Ignore network errors
    }
  }

  // 2. Terminate the process listening on the dashboard port
  if (IS_WINDOWS) {
    try {
      const netstatRes = child_process.spawnSync('cmd.exe', ['/c', `netstat -ano | findstr :${port}`], {
        encoding: 'utf8',
        timeout: 5000,
        windowsHide: true,
      });
      if (netstatRes.status === 0 && netstatRes.stdout) {
        const lines = netstatRes.stdout.split(/\r?\n/);
        const pids = new Set();
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5 && parts[1].includes(`:${port}`) && parts[3] === 'LISTENING') {
            const pid = parseInt(parts[4], 10);
            if (!isNaN(pid) && pid > 0) pids.add(pid);
          }
        }
        for (const pid of pids) {
          logInfo(`Terminating dashboard process on port ${port} (PID: ${pid})...`);
          child_process.spawnSync('taskkill', ['/F', '/T', '/PID', String(pid)], {
            encoding: 'utf8',
            timeout: 5000,
            windowsHide: true,
          });
          stoppedServer = true;
        }
      }
    } catch (err) {
      logWarn(`Could not kill port process via netstat: ${err.message}`);
    }
  } else {
    try {
      const lsofRes = child_process.spawnSync('lsof', ['-ti', `:${port}`], {
        encoding: 'utf8',
        timeout: 5000,
      });
      if (lsofRes.status === 0 && lsofRes.stdout) {
        const pids = lsofRes.stdout.trim().split(/\s+/);
        for (const pid of pids) {
          if (pid) {
            child_process.spawnSync('kill', ['-9', pid], { timeout: 3000 });
            stoppedServer = true;
          }
        }
      }
    } catch {
      // Ignore
    }
  }

  // 3. Clean up automation PID tracking file
  const pidFile = path.join(keyboardDir, 'step_4_reporting', '.automation_process.json');
  if (fs.existsSync(pidFile)) {
    try {
      fs.unlinkSync(pidFile);
    } catch {
      // Ignore
    }
  }

  if (stoppedServer || stoppedAutomation) {
    logSuccess(`AutoSelect Antigravity services on port ${port} stopped successfully.`);
  } else if (!isLive) {
    logInfo(`No running AutoSelect Antigravity server found on http://${host}:${port}/.`);
  } else {
    logSuccess(`Sent stop signal to services on http://${host}:${port}/.`);
  }
}

// ============================================================================
// Status Query Subsystem (--status)
// ============================================================================

/**
 * Queries and displays comprehensive system and environment status.
 */
async function queryStatus(venvPaths, keyboardDir, workspaceDir, port, host) {
  printBanner();
  console.log(`${colors.bold}System Diagnostics & Service Status:${colors.reset}\n`);

  // 1. Workspace Resolution
  console.log(`  ${sym.bullet} Workspace Root    : ${colors.dim}${workspaceDir}${colors.reset}`);
  console.log(`  ${sym.bullet} Subsystem Target  : ${colors.dim}${keyboardDir}${colors.reset}`);

  // 2. Python Environment
  const sysPy = findSystemPython();
  console.log(`  ${sym.bullet} System Python     : ${sysPy ? `${colors.green}${sysPy.version}${colors.reset}` : `${colors.red}Not Found${colors.reset}`}`);

  // 3. Virtual Environment
  const hasVenv = fs.existsSync(venvPaths.python);
  console.log(`  ${sym.bullet} Virtual Env (.venv): ${hasVenv ? `${colors.green}Configured (${path.relative(workspaceDir, venvPaths.venvDir)})${colors.reset}` : `${colors.yellow}Missing${colors.reset}`}`);

  // 4. Dependency Verification
  let depsOk = false;
  if (hasVenv) {
    const chk = child_process.spawnSync(venvPaths.python, ['-c', 'import pyautogui, psutil; print("OK")'], {
      encoding: 'utf8',
      timeout: 5000,
      windowsHide: true,
    });
    depsOk = chk.status === 0 && (chk.stdout || '').trim() === 'OK';
  }
  console.log(`  ${sym.bullet} Dependencies      : ${depsOk ? `${colors.green}Satisfied (pyautogui, psutil)${colors.reset}` : `${colors.yellow}Pending Verification${colors.reset}`}`);

  // 5. Server Live Check
  const isServerLive = await checkServerLive(host, port);
  console.log(`  ${sym.bullet} Dashboard Server  : ${isServerLive ? `${colors.green}ONLINE (http://${host}:${port}/)${colors.reset}` : `${colors.yellow}OFFLINE${colors.reset}`}`);

  // 6. Windows Auto-Start
  if (IS_WINDOWS && hasVenv) {
    const autostartScript = path.join(keyboardDir, 'step_4_reporting', 'autostart.py');
    if (fs.existsSync(autostartScript)) {
      const res = child_process.spawnSync(venvPaths.python, [autostartScript, '--status'], {
        cwd: keyboardDir,
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

// ============================================================================
// CLI Argument Parsing & Help Screen
// ============================================================================

function parseCliArgs() {
  const args = process.argv.slice(2);
  const options = {
    help: false,
    noBrowser: false,
    statusOnly: false,
    stopService: false,
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
    } else if (arg === '--stop') {
      options.stopService = true;
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
  -s, --status          Query system diagnostics and service status without launching
  -n, --no-browser      Do not open the dashboard in the default browser
  -p, --port <port>     Set HTTP dashboard port (default: 8501)
      --host <host>     Set HTTP host interface (default: 127.0.0.1)
      --stop            Stop the running dashboard server and active automation tasks

${colors.bold}EXAMPLES:${colors.reset}
  ${colors.dim}# 1-Line Zero-Install Execution via NPX:${colors.reset}
  npx github:aiprincekumar/AutoSelect-Antigravity

  ${colors.dim}# Global NPM Installation & Run:${colors.reset}
  npm install -g github:aiprincekumar/AutoSelect-Antigravity
  autoselect-antigravity

  ${colors.dim}# Check Environment & Service Status:${colors.reset}
  autoselect-antigravity --status

  ${colors.dim}# Run Headless on Custom Port without Browser Popup:${colors.reset}
  autoselect-antigravity --port 8585 --no-browser

  ${colors.dim}# Stop Running Dashboard and Automation Services:${colors.reset}
  autoselect-antigravity --stop
`);
}

// ============================================================================
// Main Execution Lifecycle Orchestrator
// ============================================================================

async function main() {
  const options = parseCliArgs();

  if (options.help) {
    showHelp();
    process.exit(0);
  }

  if (options.stopService) {
    await stopServer(options.port, options.host, KEYBOARD_DIR);
    process.exit(0);
  }

  const venvPaths = getVenvPaths(KEYBOARD_DIR, WORKSPACE_DIR);

  if (options.statusOnly) {
    await queryStatus(venvPaths, KEYBOARD_DIR, WORKSPACE_DIR, options.port, options.host);
    process.exit(0);
  }

  printBanner();

  const TOTAL_STEPS = 5;

  // [1/5] Detecting Python Environment
  logStep(1, TOTAL_STEPS, 'Detecting Python Environment...');
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

  // [2/5] Validating / Provisioning Virtual Environment (.venv)
  logStep(2, TOTAL_STEPS, 'Validating / Provisioning Virtual Environment (.venv)...');
  const venvOk = ensureVenv(systemPython, venvPaths, KEYBOARD_DIR);
  if (!venvOk) {
    logError('Could not set up virtual environment. Aborting.');
    process.exit(1);
  }
  ensurePip(venvPaths, KEYBOARD_DIR);

  // [3/5] Installing & Verifying Dependencies
  logStep(3, TOTAL_STEPS, 'Installing & Verifying Dependencies...');
  installDependencies(venvPaths, KEYBOARD_DIR, WORKSPACE_DIR);

  // [4/5] Configuring Hands-Free Windows Auto-Start
  logStep(4, TOTAL_STEPS, 'Configuring Hands-Free Windows Auto-Start...');
  configureAutoStart(venvPaths, KEYBOARD_DIR);

  // [5/5] Launching Headless Dashboard Server & Opening Browser
  logStep(5, TOTAL_STEPS, 'Launching Headless Dashboard Server & Opening Browser...');
  await launchDashboardServer(venvPaths, KEYBOARD_DIR, WORKSPACE_DIR, options.port, options.host);

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
