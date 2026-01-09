# 项目迭代记录 / Changelog 📘

## 概要 ✨

此项目为一个基于 HMM 的中文拼音输入法原型，经过若干阶段的迭代，覆盖核心算法实现、模型训练、GUI 从 Tkinter 到 PyQt5 的迁移、知识库（成语/歇后语/词典/Emoji）集成，以及最近加入的语音输入功能与非阻塞多线程处理。文档按主要版本阶段归纳变更与要点，便于开发者和贡献者快速把握项目进化历程。

---

## 版本历程（精华摘录）

### 第一阶段：核心算法构建 (v1.0 - v1.2) 🧠

- **v1.0 — HMM 基础模型实现**
  - 实现 `HMM_Model`，加载发射概率（`pinyin.txt`）、转移概率（`Bigram.txt`）、初始概率（`CharFreq.txt`）。
  - 实现 Viterbi 算法，用于拼音到汉字序列的解码。
  - 支持命令行交互与批量测试（`input.txt` -> `output.txt`）。

- **v1.1 — 算法优化与平滑处理**
  - 引入回退平滑策略：当二元概率缺失时回退使用一元概率并施加惩罚系数（示例：-8.0），显著改善未登录词识别。

- **v1.2 — 模型训练模块**
  - 增加 `train.py`，实现从原始语料（人民日报）统计并生成 `CharFreq.txt` 与 `Bigram.txt`。

---

### 第二阶段：功能扩展与 GUI 原型 (v2.0 - v2.3) 🧩

- **v2.0 — Tkinter GUI 原型**
  - 实现基础界面（输入框 + 候选条），支持实时拼音监听与前 5 候选显示。

- **v2.1 — 多源知识库**
  - 新增 `knowledge.py`，加载 `idiom.json`、`xiehouyu.json`、`ci.json` 等，支持：
    - 成语速录（缩写匹配）
    - 歇后语补全
    - 鼠标悬停显示词义百科

- **v2.2 — Emoji 支持**
  - 增加 `emoji.json`，并将 Emoji 优先插入候选（例如输入 `haha` 更容易得到 😂）。

- **v2.3 — 交互与兼容性修复**
  - 修复界面与知识库接口不匹配的崩溃问题；修复编码（GBK/UTF-8）兼容性；释放空格键支持带空格的拼音输入；改进回车/快捷键行为。

---

### 第三阶段：架构重构与体验升级 (v3.0 - v3.2) 🚀

- **v3.0 — 框架迁移（Tkinter → PyQt5）**
  - 迁移到 PyQt5，使用 `Segoe UI Emoji` 完整支持 Windows 彩色 Emoji，并用 QSS 美化界面。界面更现代，支持更丰富的交互样式。

- **v3.1 — 交互优化**
  - 数字选词（1-5）、翻页（→ / ← 或 = / -）、更好的释义滚动（QTextEdit）和页码提示等体验改进。

- **v3.2 — 语音交互增强（新增） 🎤**
  - 集成 `speech_recognition` 与 Google Web Speech API，实现麦克风实时语音转中文文本。
  - 通过 PyQt5 多线程（`VoiceThread`）实现非阻塞监听，支持“点击开始 / 点击暂停”切换，并提供界面视觉反馈（按钮变色、状态栏提示）。

---

## 重要文件一览 🔎

- `main.py` — HMM 模型与候选生成（Beam Search、get_top_candidates 等）。
- `train.py` — 语料清洗与模型参数（`CharFreq.txt` / `Bigram.txt`）生成脚本。
- `knowledge.py` — 知识库：成语、歇后语、词典、Emoji 查询接口。
- `voice.py` — 语音识别封装，提供 `VoiceRecognizer.listen_and_convert()`。
- `gui.py` — PyQt5 GUI（输入、候选、语音控制、词义面板与翻页逻辑）。
- `data/` — 存放 `pinyin.txt`、`CharFreq.txt`、`Bigram.txt` 与 JSON 词库（`idiom.json`、`emoji.json` 等）。

---

## 安装与运行（精简）⚙️

1. 推荐 Python 3.9+，建议使用虚拟环境。

2. 安装核心依赖：

```bash
pip install PyQt5 SpeechRecognition pyaudio
```

- Windows 用户若直接安装 `pyaudio` 失败：
  - ```bash
    pip install pipwin
    pipwin install pyaudio
    ```
  - 或从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载对应 wheel 并 `pip install <whl>`。

3. 运行 GUI：

```bash
python gui.py
```

4. 语音输入使用：点击 **🎤 开始识别** 按钮开始持续监听，识别到的中文文本会插入编辑区。若按钮显示“语音不可用”，请检查 `SpeechRecognition` / `pyaudio` 是否安装、麦克风权限与网络连接是否可用（Google API 需联网）。

---

## 已知限制与注意事项 ⚠️

- HMM 对生僻词和长上下文仍有局限；混合词典能在很多场景下改善表现。
- 语音识别依赖 Google 免费接口，受网络与配额限制，识别质量会受噪声和麦克风影响。
- Windows 下 `pyaudio` 安装可能需要使用 `pipwin` 或手动安装 wheel。
- 项目中部分老语料使用 `gb18030` 编码，替换为 UTF-8 时请注意同步修改读取代码。

---

## 贡献与联系方式 🤝

欢迎提交 Issue 或 Pull Request：

- 若要扩充语料（成语/歇后语/词典/Emoji），请把 JSON 文件放入 `data/` 并在 `knowledge.py` 中加入加载逻辑。
- 有界面/交互优化或准确率提升建议，请在 PR 中说明评估方法与示例对比。

---