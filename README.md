# bgm-gen

Generate background music (`.wav`) from a natural-language description. Local synthesis — no network, no GPU.

Pipeline: `prompt` → mood keyword match → `pretty_midi` template → `fluidsynth` rendering with a GM SoundFont.

## Install

```bash
sudo apt install -y fluidsynth fluid-soundfont-gm
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/python generate.py "30s tense chase scene BGM" -d 30
.venv/bin/python generate.py "cozy cafe background music" -d 60 -o out/cafe.wav
.venv/bin/python generate.py "sad" --seed 42        # same seed → reproducible
.venv/bin/python generate.py "..." -m epic           # force a mood
.venv/bin/python generate.py --list-moods            # list presets
```

Output defaults to `out/<nano-timestamp>_<mood>_<duration>s.wav`.

## Supported moods

`calm / tense / sad / happy / epic / mystery / funny / cozy` — each triggered by EN/CN keywords (e.g. `chase / 紧张 / 追逐` → `tense`). No keyword match falls back to `calm`. Full keyword table in `generate.py`'s `KEYWORDS` dict.

## Known limits

GM soundfonts are weak for electronic / lo-fi / ambient styles; no loudness normalization; complex semantics ("80s Japanese drama dinner scene") lose nuance. See `CHANGELOG.md`.

## License

MIT — see [LICENSE](LICENSE).
