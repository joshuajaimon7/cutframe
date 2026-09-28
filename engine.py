#!/usr/bin/env python3
"""
Production AI Video Repurposing Studio - Multi-Language & B-Roll Engine
Features:
- Native Multi-Language Transcription (Malayalam, Hindi, Tamil, Telugu, Global)
- Auto-Translation Engine (e.g. Malayalam/Hindi Speech -> English Subtitles)
- Regional Slang & Colloquial Idioms Adapter
- Smart Font Resolver (Malayalam Sangam, Devanagari Sangam, Tamil Sangam, Impact)
- Automated Cinematic B-Roll Inserts
- Dynamic Per-Shot Face Tracking & Podcast Split-Screen
- Auto-Emoji Badges & AI Viral Hook Scoring
"""

import os
import sys
import json
import argparse
import subprocess
import wave
import tempfile
import uuid
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
ASSETS_DIR = Path(__file__).parent / "assets" / "broll"
SFX_DIR = Path(__file__).parent / "assets" / "sfx"

# System Fonts for Multilingual Typography
FONTS = {
    "default": "/System/Library/Fonts/Supplemental/Impact.ttf" if os.path.exists("/System/Library/Fonts/Supplemental/Impact.ttf") else "/System/Library/Fonts/Helvetica.ttc",
    "malayalam": "/System/Library/Fonts/Supplemental/Malayalam Sangam MN.ttc",
    "devanagari": "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
    "tamil": "/System/Library/Fonts/Supplemental/Tamil Sangam MN.ttc",
    "telugu": "/System/Library/Fonts/Supplemental/Telugu Sangam MN.ttc",
    "kannada": "/System/Library/Fonts/Supplemental/Kannada Sangam MN.ttc"
}

# Indian Regional Slang Dictionary (Malayalam, Hindi, Pan-Indian)
SLANG_TRANSLATIONS = {
    # Malayalam Slangs & Idioms
    "machane": "bro",
    "macha": "bro",
    "aliyan": "bro",
    "pwoli": "awesome",
    "adipoli": "insane",
    "polichu": "killed it",
    "scene": "chaotic",
    "kidu": "fire",
    "mass": "epic",
    "shaddi": "mess",
    "chumma": "simply",
    "vibe": "atmosphere",
    "oru rakshayum illa": "no comparison",
    "level": "tier",
    # Hindi Slangs & Idioms
    "jugaad": "hack",
    "bhai": "bro",
    "yaar": "friend",
    "bindaas": "carefree",
    "funda": "concept",
    "bhasad": "chaos",
    "jhakaas": "fantastic",
    "chindi": "cheap",
    "locha": "trouble",
    "kat gaya": "scammed",
    "faad": "mindblowing"
}

EMOJI_MAP = {
    "MONEY": "💰", "CASH": "💵", "RICH": "🤑", "BOOK": "📖",
    "SECRET": "🤫", "MIND": "🧠", "BRAIN": "🧠", "THINK": "💡",
    "IDEA": "💡", "FIRE": "🔥", "TRUTH": "🎯", "STOP": "🛑",
    "GROW": "📈", "SCALE": "🚀", "TIME": "⏳", "WORK": "⚡",
    "LIFE": "🌱", "HARD": "💪", "WIN": "🏆", "NEVER": "🚫",
    "PEOPLE": "👥", "BUSINESS": "💼", "MILLION": "💎",
    "സത്യം": "🎯", "പണം": "💰", "വിജയം": "🏆", "കൂട്ടുകാർ": "👥",
    "पैसा": "💰", "सफलता": "🏆", "काम": "⚡", "जिंदगी": "🌱"
}

BROLL_TRIGGERS = {
    # Money / Wealth / Finance (English + Malayalam + Hindi + Manglish)
    "money": "money.mp4", "cash": "money.mp4", "rich": "money.mp4", "dollar": "money.mp4", "million": "money.mp4",
    "wealth": "money.mp4", "panam": "money.mp4", "kaash": "money.mp4", "duddu": "money.mp4", "profit": "money.mp4",
    "invest": "money.mp4", "salary": "money.mp4", "crypto": "money.mp4", "bitcoin": "money.mp4", "laabham": "money.mp4",
    "labham": "money.mp4", "varumanam": "money.mp4", "crore": "money.mp4", "lakh": "money.mp4",
    "പണം": "money.mp4", "പണ": "money.mp4", "കാശു": "money.mp4", "കാശ്": "money.mp4", "കാശ": "money.mp4",
    "സമ്പത്ത്": "money.mp4", "സമ്പ": "money.mp4", "ലാഭം": "money.mp4", "ലാഭ": "money.mp4",
    "നിക്ഷേപം": "money.mp4", "വരുമാനം": "money.mp4", "പൈസ": "money.mp4",
    "पैसा": "money.mp4", "धन": "money.mp4", "रुपया": "money.mp4", "मुनाफा": "money.mp4", "निवेश": "money.mp4",

    # Tech / AI / Coding / Digital
    "code": "tech.mp4", "tech": "tech.mp4", "ai": "tech.mp4", "computer": "tech.mp4", "software": "tech.mp4",
    "coding": "tech.mp4", "laptop": "tech.mp4", "mobile": "tech.mp4", "phone": "tech.mp4", "app": "tech.mp4",
    "robot": "tech.mp4", "internet": "tech.mp4", "digital": "tech.mp4", "algorithm": "tech.mp4",
    "കമ്പ്യൂട്ടർ": "tech.mp4", "ഫോൺ": "tech.mp4", "ടെക്": "tech.mp4", "കോഡിംഗ്": "tech.mp4", "ആപ്പ്": "tech.mp4",
    "ഡിജിറ്റൽ": "tech.mp4", "ഇൻ്റർനെറ്റ്": "tech.mp4",
    "कंप्यूटर": "tech.mp4", "तकनीक": "tech.mp4", "इंटरनेट": "tech.mp4",

    # Growth / Success / Business / Career
    "growth": "growth.mp4", "grow": "growth.mp4", "scale": "growth.mp4", "business": "growth.mp4", "success": "growth.mp4",
    "vijayam": "growth.mp4", "valarcha": "growth.mp4", "safal": "growth.mp4", "kaamyabi": "growth.mp4",
    "startup": "growth.mp4", "leader": "growth.mp4", "win": "growth.mp4", "goal": "growth.mp4", "target": "growth.mp4",
    "വിജയം": "growth.mp4", "വിജയ": "growth.mp4", "വളർച്ച": "growth.mp4", "ബിസിനസ്": "growth.mp4", "ജയം": "growth.mp4",
    "ലക്ഷ്യം": "growth.mp4", "സ്റ്റാർട്ടപ്പ്": "growth.mp4", "വിജയി": "growth.mp4", "സഫല": "growth.mp4",
    "सफलता": "growth.mp4", "विकास": "growth.mp4", "व्यापार": "growth.mp4", "जीत": "growth.mp4", "लक्ष्य": "growth.mp4"
}

# Tone & Context-Aware Sound FX Triggers
TONE_SFX_TRIGGERS = {
    # Wealth / Money / Finance -> Ka-Ching (English, Malayalam, Hindi, Manglish)
    "money": "kaching.wav", "cash": "kaching.wav", "profit": "kaching.wav", "rich": "kaching.wav",
    "dollar": "kaching.wav", "crypto": "kaching.wav", "invest": "kaching.wav", "crore": "kaching.wav",
    "lakh": "kaching.wav", "salary": "kaching.wav", "million": "kaching.wav",
    "panam": "kaching.wav", "kaash": "kaching.wav", "laabham": "kaching.wav", "varumanam": "kaching.wav",
    "പണം": "kaching.wav", "പണ": "kaching.wav", "കാശു": "kaching.wav", "കാശ്": "kaching.wav", "കാശ": "kaching.wav",
    "ലാഭം": "kaching.wav", "നിക്ഷേപം": "kaching.wav", "സമ്പത്ത്": "kaching.wav",
    "पैसा": "kaching.wav", "मुनाफा": "kaching.wav", "धन": "kaching.wav",

    # Knowledge / Insight / Idea -> Crystal Ding / Bell
    "idea": "ding.wav", "secret": "ding.wav", "mindset": "ding.wav", "learn": "ding.wav",
    "lesson": "ding.wav", "think": "ding.wav", "tip": "ding.wav", "smart": "ding.wav",
    "padikkan": "ding.wav", "kariam": "ding.wav", "chintha": "ding.wav",
    "കാര്യം": "ding.wav", "രഹസ്യം": "ding.wav", "ചിന്ത": "ding.wav", "പഠി": "ding.wav", "ബുദ്ധി": "ding.wav",
    "സീഖ": "ding.wav", "रहस्य": "ding.wav", "सोच": "ding.wav",

    # High Energy / Pop / Visual Burst
    "boom": "pop.wav", "crazy": "pop.wav", "viral": "pop.wav", "start": "pop.wav", "magic": "pop.wav",
    "തീ": "pop.wav", "പൊളി": "pop.wav"
}

def resolve_font_for_text(text, font_size=74):
    """Auto-detects unicode script to pick the native font for zero tofu errors."""
    for char in text:
        cp = ord(char)
        if 0x0D00 <= cp <= 0x0D7F and os.path.exists(FONTS["malayalam"]):
            return ImageFont.truetype(FONTS["malayalam"], font_size - 6)
        elif 0x0900 <= cp <= 0x097F and os.path.exists(FONTS["devanagari"]):
            return ImageFont.truetype(FONTS["devanagari"], font_size - 6)
        elif 0x0B80 <= cp <= 0x0BFF and os.path.exists(FONTS["tamil"]):
            return ImageFont.truetype(FONTS["tamil"], font_size - 6)
        elif 0x0C00 <= cp <= 0x0C7F and os.path.exists(FONTS["telugu"]):
            return ImageFont.truetype(FONTS["telugu"], font_size - 6)
    return ImageFont.truetype(FONTS["default"], font_size)

def emit_status(step, percent, message, data=None):
    payload = {
        "step": step,
        "percent": percent,
        "message": message,
        "data": data or {}
    }
    print(f"__IPC_EVENT__{json.dumps(payload)}", flush=True)

def run_cmd(cmd, check=True):
    res = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(res.stderr)
    return res

def download_video(url, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    template = str(output_dir / "source_%(id)s.%(ext)s")
    
    emit_status("download", 10, "Downloading highest resolution video...")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--js-runtimes", "node:/opt/homebrew/bin/node",
        "--remote-components", "ejs:github",
        "--extractor-args", "youtube:player_client=android,web",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", template,
        url
    ]
    
    cookies_file = Path(__file__).parent / "cookies.txt"
    if cookies_file.exists():
        cmd.extend(["--cookies", str(cookies_file)])
    run_cmd(cmd)
    
    files = list(output_dir.glob("source_*.*"))
    if not files:
        raise FileNotFoundError("Downloaded video file not found.")
    emit_status("download", 25, "Download complete!")
    return files[0]

def translate_text(text, target_lang="ml"):
    import urllib.request
    import urllib.parse
    clean_text = text.strip()
    if not clean_text:
        return text
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + target_lang + "&dt=t&q=" + urllib.parse.quote(clean_text)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res = json.loads(response.read().decode("utf-8"))
            translated = "".join([part[0] for part in res[0] if part[0]])
            return translated
    except Exception as e:
        print(f"[!] Translation fallback error: {e}", file=sys.stderr)
        return text

def transcribe_multilingual(video_path, model_name="tiny", lang_mode="auto"):
    """
    Multilingual transcription & translation using Whisper.
    - auto: Keeps native language (Malayalam, Hindi, Tamil, English, etc.)
    - to_en: Translates any spoken language into English subtitles.
    - to_ml, to_hi, to_es, etc.: Translates any spoken audio into the specified target language subtitles.
    """
    import whisper
    emit_status("transcribe", 30, f"Loading Multilingual Whisper ({model_name}) AI model...")
    model = whisper.load_model(model_name)
    
    task = "translate" if lang_mode == "to_en" else "transcribe"
    emit_status("transcribe", 45, f"Running AI speech transcription ({task})...")
    
    result = model.transcribe(str(video_path), task=task, word_timestamps=True, fp16=False)
    detected_lang = result.get("language", "en")
    
    # Target Language Translation (e.g. English audio -> Malayalam/Hindi/Spanish subtitles)
    if lang_mode.startswith("to_") and lang_mode != "to_en":
        target_code = lang_mode.replace("to_", "").lower()
        emit_status("transcribe", 55, f"Translating subtitles to {target_code.upper()}...")
        for seg in result.get("segments", []):
            orig_text = seg.get("text", "")
            if not orig_text.strip():
                continue
            translated = translate_text(orig_text, target_lang=target_code)
            words = translated.strip().split()
            if words:
                seg_dur = max(0.2, seg["end"] - seg["start"])
                step = seg_dur / len(words)
                new_words = []
                for i, tw in enumerate(words):
                    new_words.append({
                        "word": tw,
                        "start": seg["start"] + i * step,
                        "end": seg["start"] + (i + 1) * step
                    })
                seg["words"] = new_words
                seg["text"] = translated
        detected_lang = target_code

    emit_status("transcribe", 60, f"Speech processed! (Language: {detected_lang.upper()})")
    return result, detected_lang

def apply_slang_cleaning(word):
    """Refines Indian regional colloquialisms for natural English translations."""
    clean = word.lower().strip(",.!?\"'")
    if clean in SLANG_TRANSLATIONS:
        return SLANG_TRANSLATIONS[clean].upper()
    return word

def calculate_viral_score(text, duration):
    HOOK_KEYWORDS = {"why", "how", "secret", "never", "always", "money", "mistake", "stop", "million", "truth", "brain", "book", "life"}
    words = text.lower().split()
    score = 82
    for w in words:
        if w in HOOK_KEYWORDS:
            score += 4
    wpm = len(words) / max(duration / 60.0, 0.1)
    if 110 <= wpm <= 180:
        score += 8
    score = min(98, score)
    
    title_words = [w.capitalize() for w in words[:6] if len(w) > 2]
    title = " ".join(title_words) if title_words else "Viral Insight"
    hashtags = "#podcast #viral #mindset #motivation #growth #shorts"
    return score, title, hashtags

def find_top_hooks(segments, num_clips=3, target_duration=30.0):
    HOOK_KEYWORDS = {"why", "how", "secret", "never", "always", "money", "mistake", "stop", "million", "if you", "truth", "people", "future", "book"}
    all_words = []
    for s in segments:
        all_words.extend(s.get("words", []))

    if not all_words:
        return [0.0]

    total_time = all_words[-1]["end"]
    step = 4.0
    candidates = []

    current = 0.0
    while current + target_duration <= total_time:
        score = 0
        window_words = [w for w in all_words if current <= w["start"] <= current + target_duration]
        score += len(window_words)
        
        first_few = " ".join([w["word"].lower() for w in window_words if w["start"] <= current + 8.0])
        for kw in HOOK_KEYWORDS:
            if kw in first_few:
                score += 45
                
        candidates.append((score, current))
        current += step

    candidates.sort(key=lambda x: x[0], reverse=True)

    selected = []
    min_gap = target_duration * 1.5
    for score, start_t in candidates:
        if all(abs(start_t - s) > min_gap for s in selected):
            selected.append(start_t)
            if len(selected) >= num_clips:
                break

    selected.sort()
    return selected

def analyze_shot_timeline(video_path, start_time, duration):
    face_tracker_bin = Path(__file__).parent / "tools" / "face_tracker"
    if face_tracker_bin.exists():
        try:
            res = subprocess.run([str(face_tracker_bin), str(video_path), str(start_time), str(duration)], capture_output=True, text=True, check=True)
            data = json.loads(res.stdout.strip())
            if data:
                positions = [(item["time"], item["cropX"], item.get("faceCount", 1)) for item in data]
                merged = []
                cur_start, cur_x, cur_fc = positions[0]
                for t, x, fc in positions[1:]:
                    if abs(x - cur_x) > 60:
                        merged.append((cur_start, t, cur_x, cur_fc))
                        cur_start, cur_x, cur_fc = t, x, fc
                merged.append((cur_start, duration, cur_x, cur_fc))
                return merged
        except Exception as e:
            print(f"[!] Face tracker fallback due to: {e}", file=sys.stderr)

    return [(0.0, duration, 480, 1)]

def build_dynamic_crop_expr(timeline):
    if len(timeline) <= 1:
        return str(timeline[0][2])
    expr = str(timeline[-1][2])
    for start, end, x, *rest in reversed(timeline[:-1]):
        expr = f"if(between(t,{start:.1f},{end:.1f}),{x},{expr})"
    return expr

def detect_broll_trigger(words, clip_start, duration):
    """Finds if any visual keywords occur to drop a 2.5s B-roll overlay with smart stem and inflection matching."""
    is_already_relative = len(words) > 0 and words[0]["start"] < clip_start and clip_start > 60
    offset = 0.0 if is_already_relative else clip_start

    for w in words:
        clean = w["word"].lower().strip(",.!?\"' \t\n")
        if not clean:
            continue
        
        matched_file = None
        # 1. Direct dictionary match
        if clean in BROLL_TRIGGERS:
            matched_file = ASSETS_DIR / BROLL_TRIGGERS[clean]
        else:
            # 2. Substring & inflection match (handles Malayalam inflections like 'പണത്തെ', 'കാശുകൾ', English 'growing')
            for trigger, broll_name in BROLL_TRIGGERS.items():
                min_len = 2 if any(ord(c) > 127 for c in trigger) else 3
                if len(trigger) >= min_len and (trigger in clean or clean.startswith(trigger)):
                    matched_file = ASSETS_DIR / broll_name
                    break

        if matched_file and matched_file.exists():
            start_rel = max(0.5, w["start"] - offset)
            end_rel = min(duration - 0.5, start_rel + 2.5)
            return str(matched_file), start_rel, end_rel

    return None, 0.0, 0.0

def build_tone_sfx_timeline(words, clip_start, duration, broll_start=None):
    """Detects tone and timestamps to build a non-colliding audio SFX timeline."""
    events = []
    # 1. Opening hook punch at 0.1s
    events.append((0.1, "impact.wav", 0.45))

    # 2. B-Roll transition whoosh
    if broll_start is not None and broll_start > 0:
        whoosh_time = max(0.2, broll_start - 0.1)
        events.append((whoosh_time, "whoosh.wav", 0.35))

    # 3. Tone words detection (debounced with min 2.0s gap between tone cues)
    is_already_relative = len(words) > 0 and words[0]["start"] < clip_start and clip_start > 60
    offset = 0.0 if is_already_relative else clip_start

    last_tone_time = -10.0
    for w in words:
        w_rel = w["start"] - offset
        if w_rel < 0.6 or w_rel > duration - 0.8:
            continue
        
        # Debounce: avoid sound spamming
        if abs(w_rel - last_tone_time) < 2.0:
            continue

        clean = w["word"].lower().strip(",.!?\"' \t\n")
        matched_sfx = None
        if clean in TONE_SFX_TRIGGERS:
            matched_sfx = TONE_SFX_TRIGGERS[clean]
        else:
            for trigger, sfx_name in TONE_SFX_TRIGGERS.items():
                min_len = 2 if any(ord(c) > 127 for c in trigger) else 3
                if len(trigger) >= min_len and (trigger in clean or clean.startswith(trigger)):
                    matched_sfx = sfx_name
                    break

        if matched_sfx:
            vol = 0.35 if matched_sfx == "pop.wav" else 0.4
            events.append((w_rel, matched_sfx, vol))
            last_tone_time = w_rel

    return sorted(events, key=lambda x: x[0])

def create_composite_sfx_track(events, duration, output_wav):
    """Renders all timed sound effects into a single 44.1kHz audio track with zero digital distortion."""
    sr = 44100
    total_samples = int(duration * sr)
    track = np.zeros(total_samples, dtype=np.float32)

    for time_s, sfx_name, vol in events:
        sfx_path = SFX_DIR / sfx_name
        if not sfx_path.exists():
            continue
        try:
            with wave.open(str(sfx_path), 'r') as wf:
                frames = wf.readframes(wf.getnframes())
                data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            start_sample = int(time_s * sr)
            if start_sample >= total_samples:
                continue
            end_sample = min(total_samples, start_sample + len(data))
            length = end_sample - start_sample
            track[start_sample:end_sample] += data[:length] * vol
        except Exception:
            continue

    peak = np.max(np.abs(track))
    if peak > 0.95:
        track = track * (0.95 / peak)

    out_16 = (track * 32767).astype(np.int16)
    with wave.open(str(output_wav), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out_16.tobytes())


def group_words_into_cards(words, clip_start, chunk_size=3, enable_slang=True):
    cards = []
    filtered = []
    has_indic = False
    is_already_relative = len(words) > 0 and words[0]["start"] < clip_start and clip_start > 60
    offset = 0.0 if is_already_relative else clip_start

    for w in words:
        w_start = w["start"] - offset
        w_end = w["end"] - offset
        if w_start >= 0:
            raw_word = w["word"].strip()
            if any(0x0900 <= ord(c) <= 0x0D7F for c in raw_word):
                has_indic = True
            if enable_slang:
                raw_word = apply_slang_cleaning(raw_word)
            
            clean_word = raw_word if has_indic else raw_word.upper()
            emoji = EMOJI_MAP.get(clean_word, "")
            display_word = f"{emoji} {clean_word}".strip() if emoji else clean_word
            
            filtered.append({
                "word": display_word,
                "start": max(0.0, w_start),
                "end": max(0.1, w_end)
            })

    effective_chunk_size = 2 if has_indic else chunk_size
    for i in range(0, len(filtered), effective_chunk_size):
        chunk = filtered[i:i + effective_chunk_size]
        if not chunk:
            continue
        cards.append({
            "card_idx": i // effective_chunk_size,
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"] + 0.1,
            "words": chunk
        })
    return cards

def draw_caption_frame(t, cards, width=1080, height=1920, y_pos=1350):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    active_card = None
    for card in cards:
        if card["start"] <= t <= card["end"]:
            active_card = card
            break

    if not active_card:
        return img

    draw = ImageDraw.Draw(img)
    words = active_card["words"]
    combined_sample = " ".join([w["word"] for w in words])
    
    base_size = 58 if any(0x0900 <= ord(c) <= 0x0D7F for c in combined_sample) else 74
    font = resolve_font_for_text(combined_sample, font_size=base_size)

    space_w = draw.textbbox((0, 0), " ", font=font)[2]
    word_sizes = []
    total_w = 0
    for w in words:
        bbox = draw.textbbox((0, 0), w["word"], font=font)
        w_width = bbox[2] - bbox[0]
        word_sizes.append((w["word"], w_width))
        total_w += w_width
    total_w += space_w * (len(words) - 1)

    # Auto-fit scaling if text exceeds screen margins
    max_w = width - 160
    if total_w > max_w:
        ratio = max_w / total_w
        new_size = max(38, int(base_size * ratio))
        font = resolve_font_for_text(combined_sample, font_size=new_size)
        space_w = draw.textbbox((0, 0), " ", font=font)[2]
        word_sizes = []
        total_w = 0
        for w in words:
            bbox = draw.textbbox((0, 0), w["word"], font=font)
            w_width = bbox[2] - bbox[0]
            word_sizes.append((w["word"], w_width))
            total_w += w_width
        total_w += space_w * (len(words) - 1)

    y = y_pos
    x = (width - total_w) // 2

    pad_x, pad_y = 35, 20
    pill_box = [x - pad_x, y - pad_y, x + total_w + pad_x, y + 85 + pad_y]
    draw.rounded_rectangle(pill_box, radius=28, fill=(0, 0, 0, 180))

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

def render_clip(input_video, start_time, duration, output_path, words, mode="full_bleed", style="luxury_doc", enable_zoom_cuts=True, enable_broll=True, enable_sfx=True):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cards = group_words_into_cards(words, clip_start=start_time, chunk_size=3)
    fps = 30
    total_frames = int(duration * fps)

    # 1. Native CoreText Card Pre-rendering (zero runtime Pillow lag, 100% textbook ligatures)
    card_renderer_bin = Path(__file__).parent / "tools" / "card_renderer"
    cards_temp_dir = Path(tempfile.gettempdir()) / f"cards_{uuid.uuid4().hex[:8]}"
    cards_temp_dir.mkdir(parents=True, exist_ok=True)
    cards_json_path = cards_temp_dir / "cards.json"

    cards_spec = []
    card_map = {}
    for c in cards:
        c_idx = c["card_idx"]
        words_in_card = c["words"]
        for active_idx in range(len(words_in_card)):
            png_file = cards_temp_dir / f"card_{c_idx}_{active_idx}.png"
            cards_spec.append({
                "cardIdx": c_idx,
                "words": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words_in_card],
                "activeIdx": active_idx,
                "outPath": str(png_file),
                "style": style
            })
            card_map[(c_idx, active_idx)] = png_file

    with open(cards_json_path, "w") as f:
        json.dump(cards_spec, f)

    if card_renderer_bin.exists():
        subprocess.run([str(card_renderer_bin), str(cards_json_path)], check=True)

    # Preload PNG RGBA byte buffers into memory
    card_buffers = {}
    for key, png_p in card_map.items():
        if png_p.exists():
            im = Image.open(png_p).convert("RGBA")
            if im.size != (1080, 1920):
                im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
            card_buffers[key] = im.tobytes()

    empty_frame_buffer = bytes(1080 * 1920 * 4)

    # 2. Check for B-Roll trigger
    broll_path, broll_s, broll_e = (None, 0, 0)
    if enable_broll:
        broll_path, broll_s, broll_e = detect_broll_trigger(words, start_time, duration)

    # 3. Tone & Context Sound FX
    sfx_temp_file = None
    if enable_sfx:
        sfx_events = build_tone_sfx_timeline(words, clip_start=start_time, duration=duration, broll_start=broll_s if broll_path else None)
        if sfx_events:
            sfx_temp_file = Path(tempfile.gettempdir()) / f"sfx_{uuid.uuid4().hex[:8]}.wav"
            create_composite_sfx_track(sfx_events, duration, sfx_temp_file)

    # 4. Smart Camera Face Tracking & Single-Speaker Protection
    timeline = analyze_shot_timeline(input_video, start_time, duration)
    face_counts = [item[3] for item in timeline if len(item) > 3]
    is_single_speaker = len(face_counts) > 0 and max(face_counts) <= 1

    if mode == "split_screen" and is_single_speaker:
        print("[SMART CAMERA] Single-speaker close-up detected! Auto-upgrading to Full-Bleed 9:16 Centered Face-Tracking to avoid empty desk split-screen.", file=sys.stderr)
        mode = "full_bleed"

    curr_input_idx = 1
    broll_idx = None
    if broll_path:
        broll_idx = curr_input_idx
        curr_input_idx += 1

    pipe_idx = curr_input_idx
    curr_input_idx += 1

    sfx_idx = None
    if sfx_temp_file and sfx_temp_file.exists():
        sfx_idx = curr_input_idx
        curr_input_idx += 1

    if mode == "split_screen":
        vf_base = (
            "[0:v]crop=820:960:150:60,scale=1080:960[top];"
            "[0:v]crop=820:960:950:60,scale=1080:960[bot];"
            "[top][bot]vstack[stacked];"
            "[stacked]drawbox=y=958:h=4:color=white@0.35:t=fill[base];"
        )
    elif mode == "full_bleed":
        crop_expr = build_dynamic_crop_expr(timeline)
        if enable_zoom_cuts and style != "minimal_story":
            vf_base = (
                f"[0:v]crop=608:1080:'{crop_expr}':0,"
                "split[norm][punch];"
                "[punch]crop=550:980:29:50,scale=1080:1920[zoomed];"
                "[norm]scale=1080:1920[regular];"
                "[regular][zoomed]blend=all_expr='if(lt(mod(T,7),3.5),A,B)'[base];"
            )
        else:
            vf_base = f"[0:v]crop=608:1080:'{crop_expr}':0,scale=1080:1920[base];"
    else: # blur mode
        vf_base = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            "[0:v]scale=1080:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
        )

    # Add B-roll layer if triggered
    if broll_idx is not None:
        slide_in_end = broll_s + 0.3
        slide_out_start = broll_e - 0.3
        broll_x_expr = (
            f"if(lt(t,{slide_in_end:.2f}),-W+W*(t-{broll_s:.2f})/0.3,"
            f"if(gt(t,{slide_out_start:.2f}),W*(t-{slide_out_start:.2f})/0.3,0))"
        )
        vf_base += (
            f"[{broll_idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[broll_scaled];"
            f"[base][broll_scaled]overlay=x='{broll_x_expr}':y=0:enable='between(t,{broll_s:.2f},{broll_e:.2f})'[with_broll];"
            f"[with_broll][{pipe_idx}:v]overlay=0:0[vout]"
        )
    else:
        vf_base += f"[base][{pipe_idx}:v]overlay=0:0[vout]"

    # Audio filter graph
    filter_complex = vf_base
    map_args = ["-map", "[vout]"]

    if sfx_idx is not None:
        sfx_gain = 0.85 if style == "luxury_doc" else 0.70
        filter_complex += f"; [{sfx_idx}:a]volume={sfx_gain}[sfx_vol]; [0:a][sfx_vol]amix=inputs=2:duration=first:normalize=0,loudnorm[aout]"
        map_args.extend(["-map", "[aout]"])
    else:
        filter_complex += "; [0:a]loudnorm[aout]"
        map_args.extend(["-map", "[aout]"])

    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(input_video)
    ]

    if broll_path:
        cmd.extend(["-t", str(duration), "-stream_loop", "-1", "-i", broll_path])

    cmd.extend([
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", "1080x1920", "-pix_fmt", "rgba", "-r", str(fps),
        "-i", "-"
    ])

    if sfx_temp_file and sfx_temp_file.exists():
        cmd.extend(["-i", str(sfx_temp_file)])

    cmd.extend([
        "-filter_complex", filter_complex,
        *map_args,
        "-t", str(duration),
        "-shortest",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path)
    ])

    err_log = Path(tempfile.gettempdir()) / f"ffmpeg_err_{uuid.uuid4().hex[:8]}.log"
    try:
        with open(err_log, "wb") as err_file:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err_file)

            try:
                for frame_idx in range(total_frames):
                    t = frame_idx / fps
                    active_card = None
                    for c in cards:
                        if c["start"] <= t <= c["end"]:
                            active_card = c
                            break

                    frame_bytes = empty_frame_buffer
                    if active_card:
                        c_idx = active_card["card_idx"]
                        for a_idx, w in enumerate(active_card["words"]):
                            if w["start"] <= t <= w["end"]:
                                frame_bytes = card_buffers.get((c_idx, a_idx), empty_frame_buffer)
                                break
                        else:
                            frame_bytes = card_buffers.get((c_idx, 0), empty_frame_buffer)

                    proc.stdin.write(frame_bytes)
            except (BrokenPipeError, IOError):
                pass

            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.wait()

            if proc.returncode != 0:
                err = err_log.read_text(errors="replace")
                raise RuntimeError(f"FFmpeg render error:\n{err}")
    finally:
        if err_log.exists():
            try:
                err_log.unlink(missing_ok=True)
            except Exception:
                pass
        if sfx_temp_file and sfx_temp_file.exists():
            try:
                sfx_temp_file.unlink(missing_ok=True)
            except Exception:
                pass
        # Clean up card temp files
        for p in cards_temp_dir.glob("*"):
            p.unlink(missing_ok=True)
        try:
            cards_temp_dir.rmdir()
        except Exception:
            pass

    return str(output_path.resolve())

def main():
    parser = argparse.ArgumentParser(description="AI Shorts Studio Engine")
    parser.add_argument("--input", required=True, help="YouTube URL or local video path")
    parser.add_argument("--num_clips", type=int, default=3, help="Number of viral clips to generate")
    parser.add_argument("--duration", type=float, default=30.0, help="Clip duration in seconds")
    parser.add_argument("--mode", default="full_bleed", choices=["full_bleed", "split_screen", "blur"], help="Framing mode")
    parser.add_argument("--style", default="luxury_doc", choices=["luxury_doc", "kinetic_punch", "minimal_story", "hyper_neon"], help="Editing style preset")
    parser.add_argument("--lang_mode", default="auto", help="Language & Translation mode (auto, to_en, to_ml, to_hi, to_es, to_ta, to_ar)")
    parser.add_argument("--zoom-cuts", action=argparse.BooleanOptionalAction, default=True, help="Enable dynamic punch-in zoom cuts")
    parser.add_argument("--broll", action=argparse.BooleanOptionalAction, default=False, help="Enable automated cinematic B-roll inserts")
    parser.add_argument("--sfx", action=argparse.BooleanOptionalAction, default=False, help="Enable tone and context-aware sound effects")
    parser.add_argument("--outdir", default="output", help="Output directory")

    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. Acquire video
    if args.input.startswith("http://") or args.input.startswith("https://"):
        video_path = download_video(args.input, outdir / "raw")
    else:
        video_path = Path(args.input)
        if not video_path.exists():
            emit_status("error", 0, f"File not found: {video_path}")
            sys.exit(1)

    # 2. Multilingual Transcription
    transcript, detected_lang = transcribe_multilingual(video_path, lang_mode=args.lang_mode)
    segments = transcript.get("segments", [])

    # 3. Detect Top N Hooks
    emit_status("hooks", 65, f"AI detecting top {args.num_clips} viral moments ({detected_lang.upper()})...")
    hook_starts = find_top_hooks(segments, num_clips=args.num_clips, target_duration=args.duration)

    # 4. Render All Clips
    rendered_clips = []
    for idx, start_t in enumerate(hook_starts):
        percent = int(70 + (idx / args.num_clips) * 28)
        emit_status("render", percent, f"Rendering Clip #{idx+1} of {args.num_clips} (Multi-Cam + B-Roll)...")
        
        clip_end = start_t + args.duration
        words = []
        clip_text = []
        for s in segments:
            for w in s.get("words", []):
                if start_t <= w["start"] <= clip_end:
                    words.append(w)
                    clip_text.append(w["word"])

        full_text = " ".join(clip_text)
        viral_score, title, hashtags = calculate_viral_score(full_text, args.duration)

        output_path = outdir / f"clip_{idx+1}_{int(start_t)}s.mp4"
        final_file = render_clip(
            input_video=video_path,
            start_time=start_t,
            duration=args.duration,
            output_path=output_path,
            words=words,
            mode=args.mode,
            style=args.style,
            enable_zoom_cuts=args.zoom_cuts,
            enable_broll=args.broll,
            enable_sfx=args.sfx
        )
        rendered_clips.append({
            "index": idx + 1,
            "title": title,
            "score": viral_score,
            "lang": detected_lang.upper(),
            "hashtags": hashtags,
            "start": int(start_t),
            "duration": int(args.duration),
            "path": final_file
        })

    emit_status("finished", 100, "All viral clips successfully generated!", {"clips": rendered_clips})
    print("\n[SUCCESS] Multilingual Batch Processing Complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        emit_status("error", 0, f"Error: {str(e)}")
        print(f"[!] Error in engine: {e}", file=sys.stderr)
        sys.exit(1)
