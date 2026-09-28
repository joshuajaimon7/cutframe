const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow = null;
let currentChildProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1240,
    height: 860,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: "#0d0f14",
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 18, y: 18 },
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile("index.html");
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// File selector dialog
ipcMain.handle("select-video-file", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [{ name: "Videos", extensions: ["mp4", "mov", "mkv", "webm", "avi"] }]
  });
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

// Reveal in Finder
ipcMain.on("reveal-in-finder", (_event, filePath) => {
  if (filePath) {
    shell.showItemInFolder(filePath);
  }
});

// Open Documents Export Folder
ipcMain.on("open-documents-folder", () => {
  const dir = path.join(app.getPath("documents"), "AI_Shorts_Studio");
  shell.openPath(dir);
});

// Cancel clipping
ipcMain.on("cancel-clipping", () => {
  if (currentChildProcess) {
    currentChildProcess.kill();
    currentChildProcess = null;
  }
});

// Start clipping
ipcMain.on("start-clipping", (event, params) => {
  if (currentChildProcess) {
    currentChildProcess.kill();
  }

  const pythonBin = path.join(__dirname, "venv", "bin", "python");
  const engineScript = path.join(__dirname, "engine.py");
  const outputDir = path.join(app.getPath("documents"), "AI_Shorts_Studio");

  const args = [
    engineScript,
    "--input", params.input,
    "--num_clips", String(params.numClips || 3),
    "--duration", String(params.duration || 30),
    "--mode", params.mode || "full_bleed",
    "--style", params.style || "luxury_doc",
    "--lang_mode", params.langMode || "auto",
    "--outdir", outputDir
  ];

  if (params.zoomCuts) {
    args.push("--zoom-cuts");
  } else {
    args.push("--no-zoom-cuts");
  }

  if (params.broll) {
    args.push("--broll");
  } else {
    args.push("--no-broll");
  }

  if (params.sfx) {
    args.push("--sfx");
  } else {
    args.push("--no-sfx");
  }

  console.log("Spawning Python:", pythonBin, args);

  currentChildProcess = spawn(pythonBin, args, {
    cwd: __dirname,
    env: { ...process.env, PATH: `/opt/homebrew/bin:/usr/local/bin:${process.env.PATH}` }
  });

  currentChildProcess.stdout.on("data", (data) => {
    const lines = data.toString().split("\n");
    for (const line of lines) {
      if (line.startsWith("__IPC_EVENT__")) {
        try {
          const jsonStr = line.replace("__IPC_EVENT__", "").trim();
          const parsed = JSON.parse(jsonStr);
          mainWindow.webContents.send("clipper-progress", parsed);
        } catch (err) {
          console.error("IPC Parse error:", err);
        }
      } else if (line.trim()) {
        console.log("[Python Stdout]:", line);
      }
    }
  });

  currentChildProcess.stderr.on("data", (data) => {
    console.error("[Python Stderr]:", data.toString());
  });

  currentChildProcess.on("close", (code) => {
    currentChildProcess = null;
    if (code !== 0) {
      mainWindow.webContents.send("clipper-error", { message: `Engine process exited with code ${code}` });
    }
  });
});
