const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  selectVideoFile: () => ipcRenderer.invoke("select-video-file"),
  startClipping: (params) => ipcRenderer.send("start-clipping", params),
  cancelClipping: () => ipcRenderer.send("cancel-clipping"),
  revealInFinder: (filePath) => ipcRenderer.send("reveal-in-finder", filePath),
  openDocumentsFolder: () => ipcRenderer.send("open-documents-folder"),
  onProgress: (callback) => ipcRenderer.on("clipper-progress", (_event, value) => callback(value)),
  onError: (callback) => ipcRenderer.on("clipper-error", (_event, value) => callback(value)),
  onFinished: (callback) => ipcRenderer.on("clipper-finished", (_event, value) => callback(value))
});
