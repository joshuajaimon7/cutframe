# Cutframe Studio

> **Professional 9:16 Vertical Repurposing Engine for macOS**  
> Transform long podcasts, interviews, and talks into viral vertical shorts with hardware-accelerated face tracking and native CoreText typography.

---

## Overview

Cutframe is a desktop production studio engineered for video editors and creators. Inspired by the minimalist, high-contrast aesthetics of **DaVinci Resolve** and **Premiere Pro**, Cutframe strips away gimmicky automated overlays to focus strictly on what drives retention: **flawless framing, natural dialogue pacing, and pristine captions**.

- **$0 Processing Cost**: 100% local execution on Apple Silicon (M1/M2/M3/M4) Metal & Neural Engine.
- **Native Typography Engine**: Powered by Apple CoreText and AppKit text layout managers, ensuring **zero dotted circle (`◌`) errors** in complex scripts (Malayalam, Hindi, Tamil, Arabic).
- **Intelligent Camera Framing**: Hardware-accelerated single-speaker detection and dual-speaker split-screen adaptive framing via Apple's Vision framework (`VNDetectFaceRectanglesRequest`).
- **Dynamic Pacing**: 8% punch-in camera zoom cuts synchronized to key narrative sentence shifts.
- **Direct Export**: Renders production-ready 1080x1920 MP4s directly to `~/Documents/AI_Shorts_Studio`.

---

## Architecture & Local Model Distribution

### How Local AI Models Work in Cutframe
Cutframe relies on local offline models to ensure privacy, zero recurring cloud costs, and high-speed transcription:

1. **Transcription & Word Alignment**:
   - Uses OpenAI's **Whisper** engine running locally on device via PyTorch / Metal MPS.
   - **Model Storage**: Model weights (`base` ~140MB or `small` ~460MB) are stored locally in the standard macOS cache (`~/.cache/whisper` or `~/Library/Application Support/Cutframe/models`).
   - **First Launch**: When a user runs Cutframe on a new Mac, the engine checks for cached weights. If not found, it downloads the model once. Subsequent runs are **100% offline**.

2. **Native Vision & CoreText Pipelines**:
   - `tools/face_tracker`: Compiled Swift binary utilizing Apple's `Vision.framework`. Operates at 60+ FPS on Apple Silicon with zero external model weights required.
   - `tools/card_renderer`: Compiled Swift binary utilizing Apple's `AppKit` and `CoreText` shaping engines to generate pixel-perfect subtitle cards with subpixel anti-aliasing.

3. **Audio-Video Multiplexing**:
   - Leverages `ffmpeg` hardware encoding (`h264_videotoolbox` / `libx264`) for lightning-fast vertical exports.

---

## Editorial Styles

Cutframe includes four curated editorial presets:

- **Documentary**: Frosted obsidian pill with subtle amber border, native CoreText typography, lower-third chest placement.
- **Kinetic**: High-contrast black pill with electric yellow active word highlights and dynamic camera punch-in cuts.
- **Clean Editorial**: Ultra-clean neutral white typography, translucent card, natural interview framing.
- **High-Contrast**: Crisp white text on matte black, maximum legibility, zero distractions.

---

## Development & Building

### Prerequisites
- macOS 13+ (Apple Silicon recommended)
- Node.js 18+
- Python 3.10+
- Xcode Command Line Tools (`swiftc`)
- FFmpeg (`brew install ffmpeg`)

### Installation
```bash
git clone https://github.com/joshuajaimon7/cutframe.git
cd cutframe
npm install
```

### Running Locally
```bash
npm start
```

### Packaging into a macOS DMG
To build a standalone installer DMG:
```bash
npm run dist
```
The output `.dmg` will be generated in the `dist/` directory.

---

## License
MIT License. Created by Joshua Jaimon.
