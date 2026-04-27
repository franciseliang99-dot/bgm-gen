# bgm-gen

按自然语言描述生成 BGM(.wav)。本地合成,无网络、无 GPU。

路线:`prompt` → mood 关键词匹配 → `pretty_midi` 模板生成 MIDI → `fluidsynth` 用 GM SoundFont 渲染 wav。

## 安装

```bash
sudo apt install -y fluidsynth fluid-soundfont-gm
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 用法

```bash
.venv/bin/python generate.py "30 秒紧张追逐戏 BGM" -d 30
.venv/bin/python generate.py "温馨咖啡馆背景音乐" -d 60 -o out/cafe.wav
.venv/bin/python generate.py "悲伤" --seed 42        # 同 seed 可复现
.venv/bin/python generate.py "..." -m epic           # 强制 mood
.venv/bin/python generate.py --list-moods            # 看预设
```

输出默认落在 `out/<纳秒时间戳>_<mood>_<时长>s.wav`。

## 支持的 mood

`calm / tense / sad / happy / epic / mystery / funny / cozy`,各有中英关键词触发(如"紧张/追逐/chase" → `tense`)。未命中关键词默认 `calm`。完整关键词见 `generate.py` 的 `KEYWORDS` 表。

## 已知限制

GM 音色对电子 / lo-fi / 氛围乐风格弱;无响度归一化;复杂语义("80 年代日剧风晚餐")会丢细节。详见 `CHANGELOG.md`。
