#!/usr/bin/env python3
"""
Automated Video Repurposing Pipeline
Converts standard horizontal YouTube videos / podcasts into 9:16 vertical TikTok/Reels with Hormozi-style animated captions.
100% Free & Local (Python + Whisper + FFmpeg + Pillow).
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
FONT_PATH = "/System/Library/Fonts/Supplemental/Impact.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def run_cmd(cmd, check=True):
    res = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"[!] Command Error: {res.stderr}")
        raise RuntimeError(res.stderr)
    return res

def download_video(url, output_dir):
    """Downloads YouTube video using yt-dlp."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    template = str(output_dir / "source_%(id)s.%(ext)s")
    
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", template,
        url
    ]
    print(f"[*] Downloading {url}...")
    run_cmd(cmd)
    
    files = list(output_dir.glob("source_*.*"))
    if not files:
        raise FileNotFoundError("Downloaded video file not found.")
    print(f"[✓] Downloaded to {files[0]}")
    return files[0]

def transcribe_audio(video_path, model_name="base"):
    """Transcribes video using Whisper with word-level timestamps."""
    import whisper
    print(f"[*] Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    print(f"[*] Transcribing speech with word-level timestamps...")
    result = model.transcribe(str(video_path), word_timestamps=True, fp16=False)
    return result

def find_best_hook(segments, target_duration=30.0):
    """
    Finds the most engaging 30-45s window by looking for punchy hooks,
    question words, or peak speech density.
    """
    HOOK_KEYWORDS = {"why", "how", "secret", "never", "always", "money", "mistake", "stop", "million", "if you", "truth"}
    best_score = -1
    best_start = 0.0

    all_words = []
    for s in segments:
        all_words.extend(s.get("words", []))

    if not all_words:
        return 0.0

    total_time = all_words[-1]["end"]
    step = 5.0
    current = 0.0

    while current + target_duration <= total_time:
        score = 0
        window_words = [w for w in all_words if current <= w["start"] <= current + target_duration]
        score += len(window_words) # speech density
        
        # Check for hook words in the first 5 seconds of the window
        first_few = " ".join([w["word"].lower() for w in window_words if w["start"] <= current + 6.0])
        for kw in HOOK_KEYWORDS:
            if kw in first_few:
                score += 50
                
        if score > best_score:
            best_score = score
            best_start = current
        current += step

    print(f"[★] Auto-detected best hook starting at {best_start:.1f}s (score: {best_score})")
    return best_start

def group_words_into_cards(words, clip_start, chunk_size=3):
    """
    Groups words into short 3-word cards for fast reading on TikTok.
    """
    cards = []
    filtered = []
    for w in words:
        w_start = w["start"] - clip_start
        w_end = w["end"] - clip_start
        if w_start >= 0:
            filtered.append({
                "word": w["word"].strip().upper(),
                "start": max(0.0, w_start),
                "end": max(0.1, w_end)
            })

    for i in range(0, len(filtered), chunk_size):
        chunk = filtered[i:i + chunk_size]
        if not chunk:
            continue
        cards.append({
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"] + 0.1,
            "words": chunk
        })
    return cards

def draw_caption_frame(t, cards, width=1080, height=1920):
    """
    Draws the transparent overlay for the current timestamp `t`.
    Features:
      - Clean frosted pill background
      - Bold Impact font
      - Active spoken word in bright yellow (#FFE600), others in pure white (#FFFFFF)
      - Black stroke for contrast
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # Find active card
    active_card = None
    for card in cards:
        if card["start"] <= t <= card["end"]:
            active_card = card
            break

    if not active_card:
        return img

    draw = ImageDraw.Draw(img)
    font_size = 72
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Calculate widths for all words
    words = active_card["words"]
    space_w = draw.textbbox((0, 0), " ", font=font)[2]
    word_sizes = []
    total_w = 0
    for w in words:
        bbox = draw.textbbox((0, 0), w["word"], font=font)
        w_width = bbox[2] - bbox[0]
        word_sizes.append((w["word"], w_width))
        total_w += w_width
    total_w += space_w * (len(words) - 1)

    # Vertical position (lower-third: y=1300)
    y = 1300
    x = (width - total_w) // 2

    # Draw rounded dark pill container behind words
    pad_x = 35
    pad_y = 20
    pill_box = [x - pad_x, y - pad_y, x + total_w + pad_x, y + 80 + pad_y]
    draw.rounded_rectangle(pill_box, radius=25, fill=(0, 0, 0, 160))

    # Render each word
    curr_x = x
    for idx, (word_text, w_width) in enumerate(word_sizes):
        word_data = words[idx]
        is_active = word_data["start"] <= t <= word_data["end"]
        color = "#FFE600" if is_active else "#FFFFFF"
        
        draw.text(
            (curr_x, y),
            word_text,
            font=font,
            fill=color,
            stroke_width=6,
            stroke_fill="black"
        )
        curr_x += w_width + space_w

    return img

def render_short(input_video, start_time, duration, output_path, words):
    """
    Renders 9:16 vertical short with real-time piped captions.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cards = group_words_into_cards(words, clip_start=start_time, chunk_size=3)
    fps = 30
    total_frames = int(duration * fps)

    print(f"[*] Rendering {duration}s clip at {fps} fps ({total_frames} frames)...")

    # Step 1: Render video base with blurred background + foreground centered
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[0:v]scale=1080:-2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
        "[base][1:v]overlay=0:0"
    )

    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(input_video),
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", "1080x1920", "-pix_fmt", "rgba", "-r", str(fps),
        "-i", "-",
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", "loudnorm",
        str(output_path)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # Stream generated frames into ffmpeg
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        frame_img = draw_caption_frame(t, cards, 1080, 1920)
        proc.stdin.write(frame_img.tobytes())

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        err = proc.stderr.read().decode()
        raise RuntimeError(f"FFmpeg error: {err}")

    print(f"\n[✓] Video successfully rendered to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Automated 9:16 Shorts Generator with Animated Captions.")
    parser.add_argument("--input", required=True, help="YouTube URL or local MP4 path")
    parser.add_argument("--start", type=float, default=None, help="Clip start time in seconds (auto-detected if omitted)")
    parser.add_argument("--duration", type=float, default=30.0, help="Clip duration in seconds (default: 30s)")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--model", default="base", help="Whisper model (tiny, base, small)")

    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. Download or locate video
    if args.input.startswith("http://") or args.input.startswith("https://"):
        video_path = download_video(args.input, outdir / "raw")
    else:
        video_path = Path(args.input)
        if not video_path.exists():
            print(f"[!] Input file does not exist: {video_path}")
            sys.exit(1)

    # 2. Transcribe
    transcript = transcribe_audio(video_path, model_name=args.model)
    
    # Save transcript
    transcript_file = outdir / "transcript.json"
    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2)

    # 3. Hook Detection
    segments = transcript.get("segments", [])
    if args.start is not None:
        start_time = args.start
    else:
        start_time = find_best_hook(segments, target_duration=args.duration)

    # Collect words
    clip_end = start_time + args.duration
    all_words = []
    for s in segments:
        for w in s.get("words", []):
            if start_time <= w["start"] <= clip_end:
                all_words.append(w)

    # 4. Render
    output_video = outdir / f"short_{int(start_time)}s.mp4"
    render_short(video_path, start_time, args.duration, output_video, all_words)
    print(f"\n[DONE] Ready-to-post short: {output_video.resolve()}")

if __name__ == "__main__":
    main()
