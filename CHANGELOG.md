# Changelog

## V1.0.4 — 2026-04-30

**Docs** — Translate README from Chinese to English for OSS visibility (other sibling tools in the director suite are already English; bgm-gen was the lone outlier). Content unchanged: same install steps, same usage examples, same mood table, same known-limits section. CN keyword examples preserved (`紧张 / 追逐` → `tense`) since the keyword matcher itself accepts both EN and CN tokens. `__version__` 1.0.3 → 1.0.4.

## V1.0.3 — 2026-04-27

**Bug fix** — `_add_drums()` 也加 `import pretty_midi`(与 `build_midi()` 同 pattern)。

V1.0.2 (`1f1f3c9`) 加 `--version --json` 健康自检时,把 `import pretty_midi` 从模块顶层下沉到 `build_midi()` 内部,让健康自检在 pretty_midi 缺失时仍能输出 broken JSON。**漏改了 `_add_drums()`** —— `_add_drums` 也直接引用 `pretty_midi.Note` / `pretty_midi.Instrument`,在 `build_midi → _add_drums` 调用链中触发 `NameError: name 'pretty_midi' is not defined`(任何走 drum_kit 的 mood 即:`tense / happy / epic / funny`)。

director toothbrush-monsters 项目用 `funny` mood(drum_kit=shaker)直接撞上,bgm-gen 输出 0 bytes wav。

**Fix**: `_add_drums()` 顶部加 `import pretty_midi`(同 `build_midi()` pattern,Python module cache 让重复 import 实质零开销)。type annotation 改为 string-form `"pretty_midi.Instrument"` 避免 module-load-time evaluation(`from __future__ import annotations` 已经在顶部,但显式更稳)。`__version__` 1.0.2 → 1.0.3。

**回归测试**: `--version` plain ✓ / `--version --json` 仍正常输出健康 JSON ✓ / 实际 5s funny BGM 生成 ✓ / toothbrush 122s funny BGM 重生成 ✓。

**Lesson** (同 picture-gen V0.2.0→V0.2.1 + maintainer.md §6.1 §6.7): **health-check refactor 要 grep 整个 module 找所有 use site,不只是 main()/dispatch entry**。这次错误模式跟 picture-gen V0.2.0 相同(import 下沉漏一处),证明 §6.1 自警在 maintainer 实战中 **第二次复发**。下次 director patch 应增加 §6.8 「import-decoupling refactor checklist」具体到 grep 命令模板。

## V1.0.2 — 2026-04-27

**新增** — `--version --json` 健康自检接口(对齐 director maintainer 协议)。

- `--version` 单独走 plain 输出(向后兼容)。
- `--version --json`:输出健康 JSON,字段对齐 director 协议(`name / version / healthy / ts / deps[] / env[] / checks[] / reasons[] / extra{runtime, venv, severity}`)。退出码 `0=healthy / 1=degraded / 2=broken`。
- 探测项:`pretty_midi` (python, critical) / `fluidsynth` (binary, PATH 上) / `FluidR3_GM.sf2` (file at `/usr/share/sounds/sf2/`)。任一缺失 → `healthy=false / severity=broken`(bgm-gen 没有降级模式,缺一不可)。
- `pretty_midi` 顶层 import 下沉到 `build_midi()` 内部,让 `--version --json` 在 pretty_midi 缺失时仍能输出 broken JSON 而非 ImportError 直接挂。

**为什么** — director (V0.3.0+) 引入统一健康自检机制。本 patch 是该协议在 bgm-gen 的实现。

## V1.0.1 — 2026-04-27

**元数据补登** — V1.0.1 已合入代码 (`__version__` 已是 1.0.1) 但 CHANGELOG 漏更,本段补记。

- 代码顶部 `__version__ = "1.0.1"` 与 `--version` 输出 `bgm-gen 1.0.1` 已同步。
- 实质行为相对 V1.0.0 暂未追加新功能,本次升级是"对齐代号 / CHANGELOG 补登",非行为变更。
- 后续小修复 (mood 关键词扩展、loudnorm 归一化) 计划走 V1.1.0+。

**为什么** — 总导演 (director, V0.2.2) 接入 bgm-gen 时检测到 `tool_versions.bgm-gen` 与 `--version` 不一致 (CHANGELOG 顶 1.0.0 vs 代码 1.0.1)。补登避免后续 director smoke test 校验失败。

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
