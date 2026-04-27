# Changelog

## V1.0.0 — 2026-04-27

**新增** — 初始化 bgm-gen BGM 生成 CLI。

- 路线:MIDI + SoundFont (FluidR3_GM, 148MB) → fluidsynth → wav,本地合成,无 GPU、无网络。
- 入口:`generate.py "<描述>" -d 30 -o out/x.wav`。
- 8 个 mood 预设:`calm / tense / sad / happy / epic / mystery / funny / cozy`。中英关键词字典自动匹配,未命中默认 `calm`。
- 每 mood 含 tempo / 调式根音 / 音阶 / 4 个和弦循环 / lead 乐器 / pad 乐器 / drum kit(可空)。
- pretty_midi 按 mood 模板铺三轨:**pad**(整 bar 持续和弦)、**lead**(8 分音符旋律,60% 命中和弦音 / 40% 走音阶,主旋律比根音高一个八度)、**drum**(可选;chase/pop/epic/shaker 四种节奏型)。
- fluidsynth subprocess 离线渲染:`-ni -F out.wav -r 44100 -g 0.7 <sf2> <mid>`。
- 输出默认 `out/<ns_ts>_<mood>_<dur>s.wav`(纳秒 + mood + 时长,避免并发撞名)。
- CLI 选项:`--mood` 强制覆盖、`--seed` 可重现、`--keep-mid` 保留 MIDI、`--list-moods` 列预设。
- 退出码:`0` 成功 / `1` 环境缺失或 prompt 缺失 / `2` MIDI 写入或 fluidsynth 渲染失败。
- 工程:`requirements.txt`、`.gitignore`、`out/.gitkeep`、`README.md`。

**已知限制(留给 V2)**

- GM 音色对"电子 / lo-fi / 氛围"风格弱;命中此类关键词仍走最近的 GM 预设,但不假装能复制氛围乐质感。
- 无响度归一化,BGM 配旁白可能过响或过柔;后续考虑 `ffmpeg -filter:a loudnorm`。
- 关键词字典处理不了细粒度场景("80 年代日剧风温馨晚餐"会落到 `cozy` 但丢失年代/场景细节)。
- `prompt → mood` 是规则匹配;V2 可改 LLM 输出 `spec`(tempo/key/instruments/structure)再展开成 MIDI,精度上限会高很多。
- MIDI 末尾仅靠 `n_bars` 内缩 1.5s 给 reverb tail;若 SoundFont 默认 reverb 短可能仍被切尾。

**为什么** — 用户授权"本地合成"路线;选 MIDI + fluidsynth 因为依赖轻(150MB)、CPU 秒级渲染、Claude 输出 MIDI 比让 AI 黑盒解释自然语言更可控可调试。AI 模型路线(MusicGen / AudioLDM)留作 V2 backend,接口预留但 V1 不预抽象。
