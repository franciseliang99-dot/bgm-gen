#!/usr/bin/env python3
"""BGM generator: prompt -> MIDI (pretty_midi) -> wav (fluidsynth).

V1: keyword-matched mood presets (8 moods); single-file CLI.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

__version__ = "1.0.3"

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "out"
SOUNDFONT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"


def _health_dict() -> dict:
    deps, checks, reasons = [], [], []
    # python deps
    try:
        import pretty_midi as _pm
        ver = getattr(_pm, "__version__", "unknown")
        deps.append({"name": "pretty_midi", "kind": "python", "ok": True,
                     "found": ver, "required": "any"})
    except ImportError as e:
        deps.append({"name": "pretty_midi", "kind": "python", "ok": False, "error": str(e)})
        reasons.append("pretty_midi not installed (critical)")
    # binary deps
    fp = shutil.which("fluidsynth")
    deps.append({"name": "fluidsynth", "kind": "binary", "ok": fp is not None,
                 "found": fp or "", "required": "any"})
    if fp is None:
        reasons.append("fluidsynth not on PATH (critical)")
    # data file deps
    sf_ok = Path(SOUNDFONT).exists()
    deps.append({"name": "FluidR3_GM.sf2", "kind": "file", "ok": sf_ok,
                 "found": SOUNDFONT if sf_ok else "", "required": SOUNDFONT})
    if not sf_ok:
        reasons.append(f"SoundFont missing: {SOUNDFONT} (critical)")

    crit = [d for d in deps if not d["ok"]]
    healthy = not crit
    severity = "ok" if healthy else "broken"
    return {
        "name": "bgm-gen", "version": __version__,
        "healthy": healthy,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "deps": deps, "env": [], "checks": checks, "reasons": reasons,
        "extra": {
            "runtime": f"python{sys.version_info.major}.{sys.version_info.minor}",
            "venv": str(Path(sys.executable).parent.parent),
            "severity": severity,
        },
    }


def _emit_health_or_version() -> None:
    if "--version" in sys.argv and "--json" in sys.argv:
        h = _health_dict()
        print(json.dumps(h, indent=2, ensure_ascii=False))
        sys.exit(0 if h["healthy"] else (1 if h["extra"]["severity"] == "degraded" else 2))

# GM drum map (channel 10) pitches used by drum kits below.
KICK, SNARE, HAT, LOW_TOM, MARACAS = 36, 38, 42, 41, 70

# Each preset: tempo (BPM); root (MIDI pitch of tonic, ~C4=60);
# scale (semitone offsets from root, melodic pool);
# chords (list of (offsets) chord tones, looped per bar);
# lead/pad: GM program numbers; drum_kit: pattern name or None.
PRESETS = {
    "calm":    {"tempo": 70,  "root": 60, "scale": [0,2,4,5,7,9,11],
                "chords": [[0,4,7], [-3,0,4], [-7,-3,0], [-5,-1,2]],
                "lead": 73, "pad": 89, "drum_kit": None},               # flute + warm pad
    "tense":   {"tempo": 150, "root": 62, "scale": [0,2,3,5,7,8,10],
                "chords": [[0,3,7], [-4,0,3], [-2,1,5], [0,3,7]],
                "lead": 44, "pad": 48, "drum_kit": "chase"},            # tremolo + strings + chase kit
    "sad":     {"tempo": 60,  "root": 57, "scale": [0,2,3,5,7,8,10],
                "chords": [[0,3,7], [-2,1,5], [-5,-1,2], [-7,-4,0]],
                "lead": 42, "pad": 48, "drum_kit": None},               # cello + strings
    "happy":   {"tempo": 128, "root": 67, "scale": [0,2,4,5,7,9,11],
                "chords": [[0,4,7], [5,9,12], [-3,0,4], [-5,-1,2]],
                "lead": 56, "pad": 24, "drum_kit": "pop"},              # trumpet + nylon gtr + pop kit
    "epic":    {"tempo": 100, "root": 60, "scale": [0,2,3,5,7,8,11],
                "chords": [[0,3,7], [-5,0,3], [-3,0,4], [0,3,7]],
                "lead": 60, "pad": 48, "drum_kit": "epic"},             # french horn + strings + taiko
    "mystery": {"tempo": 80,  "root": 61, "scale": [0,1,4,5,7,8,11],
                "chords": [[0,4,7], [-1,3,7], [0,4,8], [-1,3,7]],
                "lead": 11, "pad": 95, "drum_kit": None},               # vibraphone + halo pad
    "funny":   {"tempo": 140, "root": 64, "scale": [0,2,4,5,7,9,11],
                "chords": [[0,4,7], [5,9,12], [0,4,7], [5,9,12]],
                "lead": 70, "pad": 22, "drum_kit": "shaker"},           # bassoon + harmonica
    "cozy":    {"tempo": 90,  "root": 65, "scale": [0,2,4,5,7,9,11],
                "chords": [[0,4,7], [-5,-1,2], [-3,0,4], [-7,-3,0]],
                "lead": 24, "pad": 0,  "drum_kit": None},               # nylon gtr + acoustic piano
}

KEYWORDS = {
    "calm":    ["平静", "安静", "宁静", "舒缓", "calm", "peaceful", "ambient", "relax"],
    "tense":   ["紧张", "追逐", "战斗", "急促", "焦虑", "tense", "chase", "battle", "thriller"],
    "sad":     ["悲伤", "忧郁", "难过", "哀伤", "孤独", "sad", "melancholy", "sorrow", "lonely"],
    "happy":   ["欢快", "快乐", "明亮", "活泼", "happy", "cheerful", "uplifting", "bright"],
    "epic":    ["史诗", "壮丽", "宏大", "英雄", "庄严", "epic", "heroic", "grand", "cinematic"],
    "mystery": ["神秘", "悬疑", "诡异", "暗黑", "mystery", "mysterious", "eerie", "dark"],
    "funny":   ["搞笑", "滑稽", "幽默", "卡通", "funny", "comic", "silly", "cartoon"],
    "cozy":    ["温馨", "温暖", "治愈", "舒适", "cozy", "warm", "healing", "comfort"],
}


def detect_mood(prompt: str) -> str:
    text = prompt.lower()
    scores = {mood: sum(kw in text for kw in kws) for mood, kws in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "calm"


def _add_drums(drum: "pretty_midi.Instrument", kit: str, t: float, beat: int,
               sub: float) -> None:
    import pretty_midi  # V1.0.3: also imported here (V1.0.2 health-check refactor moved import to build_midi but missed _add_drums; same regression class as picture-gen V0.2.0→V0.2.1)
    if kit == "chase":  # 16ths hat + kick on 1/3, snare on 2/4
        for s in range(4):
            drum.notes.append(pretty_midi.Note(velocity=70, pitch=HAT,
                                               start=t + s*sub/2, end=t + s*sub/2 + 0.05))
        pitch = KICK if beat in (0, 2) else SNARE
        vel = 100 if beat in (0, 2) else 95
        drum.notes.append(pretty_midi.Note(velocity=vel, pitch=pitch, start=t, end=t + 0.1))
    elif kit == "pop":  # backbeat
        drum.notes.append(pretty_midi.Note(velocity=60, pitch=HAT, start=t, end=t + 0.05))
        if beat in (0, 2):
            drum.notes.append(pretty_midi.Note(velocity=95, pitch=KICK, start=t, end=t + 0.1))
        else:
            drum.notes.append(pretty_midi.Note(velocity=85, pitch=SNARE, start=t, end=t + 0.1))
    elif kit == "epic":  # half-time taiko-style
        if beat == 0:
            drum.notes.append(pretty_midi.Note(velocity=110, pitch=KICK, start=t, end=t + 0.2))
        elif beat == 2:
            drum.notes.append(pretty_midi.Note(velocity=100, pitch=LOW_TOM, start=t, end=t + 0.2))
    elif kit == "shaker":
        drum.notes.append(pretty_midi.Note(velocity=50, pitch=MARACAS, start=t, end=t + 0.05))
        drum.notes.append(pretty_midi.Note(velocity=50, pitch=MARACAS,
                                           start=t + sub, end=t + sub + 0.05))


def build_midi(mood: str, duration: float, seed: int | None):
    import pretty_midi  # imported here so --version --json works without pretty_midi installed
    p = PRESETS[mood]
    rng = random.Random(seed)
    pm = pretty_midi.PrettyMIDI(initial_tempo=p["tempo"])
    bar_sec = 60.0 / p["tempo"] * 4
    n_bars = max(2, int((duration - 1.5) / bar_sec))  # leave ~1.5s reverb tail

    # Pad: hold each chord for one bar
    pad = pretty_midi.Instrument(program=p["pad"], name="pad")
    for i in range(n_bars):
        chord = p["chords"][i % len(p["chords"])]
        start, end = i * bar_sec, (i + 1) * bar_sec
        for offset in chord:
            pad.notes.append(pretty_midi.Note(velocity=55, pitch=p["root"] + offset,
                                              start=start, end=end))
    pm.instruments.append(pad)

    # Lead: 8th-note melody, 60% chord tones / 40% scale tones, octave above root
    lead = pretty_midi.Instrument(program=p["lead"], name="lead")
    beat_sec = bar_sec / 4
    sub = beat_sec / 2
    t = bar_sec  # let pad establish for one bar before lead enters
    end_t = n_bars * bar_sec
    scale_pool = [p["root"] + 12 + o for o in p["scale"]]
    chord_pools = [[p["root"] + 12 + o for o in c] for c in p["chords"]]
    while t < end_t - 0.05:
        chord_tones = chord_pools[int(t / bar_sec) % len(chord_pools)]
        pitch = rng.choice(chord_tones if rng.random() < 0.6 else scale_pool)
        dur = sub if rng.random() < 0.7 else beat_sec
        lead.notes.append(pretty_midi.Note(velocity=rng.randint(70, 95), pitch=pitch,
                                           start=t, end=min(t + dur, end_t)))
        t += dur
    pm.instruments.append(lead)

    # Drums (optional)
    if p["drum_kit"]:
        drum = pretty_midi.Instrument(program=0, is_drum=True, name="drums")
        for i in range(n_bars):
            for beat in range(4):
                _add_drums(drum, p["drum_kit"], i*bar_sec + beat*beat_sec, beat, sub)
        pm.instruments.append(drum)

    return pm


def render_wav(midi_path: Path, wav_path: Path) -> None:
    cmd = ["fluidsynth", "-ni", "-F", str(wav_path), "-r", "44100", "-g", "0.7",
           SOUNDFONT, str(midi_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"fluidsynth failed (rc={res.returncode}): {res.stderr.strip()[:300]}")
    if not wav_path.exists() or wav_path.stat().st_size == 0:
        raise RuntimeError("fluidsynth produced empty wav")


def main() -> int:
    _emit_health_or_version()
    p = argparse.ArgumentParser(prog="generate.py",
                                description="Generate BGM via MIDI + fluidsynth (local, no network).")
    p.add_argument("prompt", nargs="?", help="自然语言描述,例如 '30秒紧张追逐戏'")
    p.add_argument("-d", "--duration", type=float, default=30.0, help="总时长(秒),默认 30")
    p.add_argument("-m", "--mood", choices=list(PRESETS),
                   help="强制 mood(默认从 prompt 关键词推断)")
    p.add_argument("-o", "--out", help="输出 wav 路径(默认 out/<ns_ts>_<mood>_<dur>s.wav)")
    p.add_argument("--seed", type=int, help="随机种子(可重现)")
    p.add_argument("--keep-mid", action="store_true", help="保留中间 .mid")
    p.add_argument("--list-moods", action="store_true", help="列出 mood 预设")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args()

    if args.list_moods:
        for m, conf in PRESETS.items():
            kws = ", ".join(KEYWORDS[m][:3])
            print(f"  {m:8s} tempo={conf['tempo']:3d}  关键词: {kws}")
        return 0

    if not args.prompt:
        print("ERROR: 需要 prompt(或用 --list-moods)", file=sys.stderr)
        return 1
    if shutil.which("fluidsynth") is None:
        print("ERROR: fluidsynth 未安装", file=sys.stderr)
        return 1
    if not Path(SOUNDFONT).exists():
        print(f"ERROR: SoundFont 缺失: {SOUNDFONT}", file=sys.stderr)
        return 1

    mood = args.mood or detect_mood(args.prompt)
    pm = build_midi(mood, args.duration, args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else OUT_DIR / f"{time.time_ns()}_{mood}_{int(args.duration)}s.wav"

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tf:
        mid_path = Path(tf.name)
    try:
        pm.write(str(mid_path))
        render_wav(mid_path, out)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        mid_path.unlink(missing_ok=True)
        return 2

    if args.keep_mid:
        kept = out.with_suffix(".mid")
        shutil.move(str(mid_path), kept)
        print(f"  kept midi: {kept}")
    else:
        mid_path.unlink(missing_ok=True)

    print(f"[v{__version__}] saved {out}  ({out.stat().st_size} bytes, mood={mood}, dur={args.duration}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
