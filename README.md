# Python HMM 输入法

> 简体中文说明 — 本项目基于隐马尔可夫模型（HMM）实现了一个拼音到汉字的输入法原型，并集成了成语速录、歇后语补全、Emoji 映射与词义百科等特色资源。

---

## ✅ 项目功能概览

- 拼音输入 -> 候选汉字/词组（支持连续拼音无空格/有空格输入）
- HMM + Beam Search 候选生成（支持多候选、翻页显示）
- 成语速录：支持缩写（例如 `szdt` -> `守株待兔`）优先匹配
- Emoji 映射：输入常见表情拼音可直接上屏 Emoji（如 `haha` -> 😂）
- 歇后语支持：输入成语/词后可自动给出歇后语谜底（若命中）
- 词义百科：鼠标悬停候选词显示解释 / 字典信息
- 联想功能：根据已上屏词的末字给出后续候选（基于二元统计）
- 语音输入：支持麦克风实时语音转文本（基于 `SpeechRecognition` + Google API，需联网），点击 GUI 中的语音按钮开始/停止识别。
- GUI：基于 PyQt5，支持键盘快捷选词、翻页与候选点击

## 🔧 使用的算法与技术

- 隐马尔可夫模型 (HMM)：
  - 发射（emit）由 `pinyin.txt` 映射：拼音 -> 候选汉字集合
  - 初始概率（start）由字符词频（`CharFreq.txt`）计算（取对数概率）
  - 转移概率（trans）由二元词频（`Bigram.txt`）计算（取对数概率）
- Beam Search：对拼音序列进行宽度受限的搜索以找到高概率字序列（代码中 BEAM_WIDTH=30，可修改）
- 知识库检索：使用 JSON 语料（成语、歇后语、词典、Emoji 数据）做快速查表优先匹配
- GUI 框架：PyQt5（实现候选页、鼠标悬停显示词义、键盘操作映射）

## ⭐ 项目特色

- 成语速录优先策略：当用户输入像 `szdt` 这样的缩写时，优先返回整词成语
- Emoji 内置映射与展示（便于聊天场景快速输入）
- 翻页机制（按 →/= 下一页，←/- 上一页）方便查看大量候选
- 词义百科展示（鼠标悬停时展示来自 `data` 的详尽解释）
- 既有统计模型（HMM）又能利用规则/词典提升体验（混合式设计）

## 🚀 快速上手

1. 环境准备
   - 推荐 Python 3.9+
   - 安装依赖（建议在虚拟环境中）：
     ```bash
     pip install PyQt5 SpeechRecognition pyaudio
     ```
   - Windows 用户：若直接安装 `pyaudio` 失败，可先安装 `pipwin`：
     ```bash
     pip install pipwin
     pipwin install pyaudio
     ```
     或从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载对应的 wheel 并用 `pip install <whl>` 安装。
   - 需要麦克风权限和网络访问（语音识别使用 Google 免费接口）。

2. 运行 GUI
   - 进入 `plus` 目录后运行：
     ```bash
     python gui.py
     ```
   - 在输入框输入拼音（支持带空格或不带空格），使用数字键 `1-5` 或 鼠标 点击候选词上屏。
   - 翻页：使用右箭头 或 `=` 翻页，左箭头 或 `-` 返回上一页。
   - 语音输入：点击界面右侧的 **🎤 开始识别** 按钮开启持续监听，识别到的文字会插入到文本编辑器并继续监听。再次点击或点击 **⏸️ 停止识别** 可暂停识别。若按钮显示 **语音不可用**，请参考安装依赖并确保麦克风可用与网络连接正常。

3. 可选：命令行 / 调试
   - `main.py` 中的 `HMM_Model` 可被单独导入/测试，提供 `get_top_candidates()`、`beam_search()` 等接口。

## 📁 文件说明

- `gui.py` 🔧
  - PyQt5 GUI 主程序；实现输入框、候选栏、翻页、鼠标悬停显示解释、键盘快捷操作等逻辑。

- `main.py` 🧠
  - HMM 模型实现：加载语料、计算初始/转移概率、拼音切分、Beam Search、候选合并（包含成语优先逻辑）和联想接口。

- `knowledge.py` 📚
  - 知识库实现：加载 `data` 下的 JSON（`idiom.json`, `xiehouyu.json`, `ci.json`, `word.json`, `emoji.json`）并提供查询接口（成语、歇后语、词/字释义、Emoji 映射）。

- `voice.py` 🎧
  - 语音识别模块：封装了基于 `speech_recognition` 的 `VoiceRecognizer`，提供 `listen_and_convert()` 方法；GUI 使用 `VoiceThread` 调用该模块以非阻塞方式监听麦克风并把识别结果上屏。注意：识别依赖 Google 的免费接口，需要联网与麦克风权限。
- `input.txt`、`pinyin.txt`、`CharFreq.txt`、`Bigram.txt` 等（位于 `plus/data/`）
  - 数据源/示例语料。注意：项目中对部分文件使用 `gb18030` 编码读取（基于原始数据），修改或替换时请注意编码一致性。

- `data/` 文件夹
  - 放置各种 JSON 数据：成语、歇后语、词典、Emoji 等（UTF-8 编码）。

## ⚙️ 可配置项与扩展点

- Beam 宽度：在 `main.py` 的 `beam_search()` 中调节 `BEAM_WIDTH`
- 候选页大小：在 `gui.py` 中 `PAGE_SIZE` 控制每页显示多少候选（默认 5）
- 数据扩充：向 `plus/data/` 添加或修改 JSON 文件可补充成语/歇后语/Emoji/词库
- 算法替换：`HMM_Model` 是模块化的，可以替换为更复杂的语言模型（如 tri-gram 或神经模型）

## ⚠️ 已知限制与注意事项

- 基于统计的 HMM 对生僻词和长上下文理解有限，混合词典帮助缓解部分问题
- 拼音切分对多音/歧义拼写的处理依赖 `pinyin.txt` 的覆盖范围
- 语音识别依赖 Google 的免费识别接口，需联网且可能受配额/网络质量影响，识别质量受噪声和麦克风质量影响。
- 在 Windows 上 `pyaudio` 安装可能需要特殊步骤（可使用 `pipwin` 或下载安装对应的 wheel）。
- 部分老语料使用 `gb18030` 编码，若替换为 UTF-8 请同步修改读取方式

---

## 联系与贡献

- 欢迎补充更多语料（成语、歇后语、二元/字频表），或将界面改成更接近 IME 的交互（上屏替代行为等）。

---
