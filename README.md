ytb2xhs

把 YouTube 视频 转成 中文小红书风格文案。
支持优先使用视频字幕；无字幕时自动下载音频并转写（可选）。

1️⃣ 快速开始
# 克隆并进入项目
git clone https://github.com/你的用户名/ytb2xhs.git
cd ytb2xhs

# 建议使用虚拟环境
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

2️⃣ 配置环境变量（.env）

在项目根目录创建 .env 文件（只有一行）：

OPENAI_API_KEY=sk-你的key


不要把 .env 提交到 GitHub（.gitignore 已忽略）。

3️⃣ 运行
python main.py


按提示粘贴一个 YouTube 链接，例如：

https://www.youtube.com/watch?v=V-_O7nl0Ii0


运行结束后，会在当前目录生成 result_时间戳.txt，内容为小红书文案。

4️⃣ 可选配置

在 .env 中可增加以下可选项（没有就使用默认值）：

MODEL_NAME=gpt-4o-mini   # 默认 gpt-4o-mini
TEMP=0.6                 # 生成的发散度，0~1
FALLBACK_TO_SUBTITLE_ONLY=false  # true 时只保存英文字幕，不做翻译与改写


还可以通过编辑同目录的提示词文件定制风格（不存在则用内置默认）：

prompt_translate.txt：翻译风格

prompt_xhs.txt：小红书文案风格

5️⃣ 依赖与说明

项目使用的主要库（已在 requirements.txt）：

openai：调用语言模型

python-dotenv：读取 .env

yt-dlp：抓取 YouTube 信息/字幕/音频

（可选）ffmpeg：用于音频处理，某些系统需单独安装

macOS: brew install ffmpeg

Ubuntu: sudo apt install -y ffmpeg

6️⃣ 常见问题（FAQ）

Q1：运行报 ModuleNotFoundError: No module named 'XXX'？
A：依赖未安装，执行 pip install -r requirements.txt。

Q2：python 命令不存在？
A：用 python3 运行；或在 Windows 直接 python。

Q3：提示 insufficient_quota 或 rate limit？
A：OpenAI 额度不足或速率受限。到 OpenAI 控制台开通/充值，或稍后重试。

Q4：下载/转码报 ffmpeg not found？
A：安装 ffmpeg（见上方依赖说明）。

Q5：生成结果“太 AI 味儿”怎么办？
A：编辑 prompt_xhs.txt，加入更生活化的风格要求（如“痛点开头、比喻、分点、互动问题、少术语”）。

7️⃣ 示例提示词（可放入文件）

prompt_xhs.txt（示例）：

你是一名小红书爆款写手。
写作要求：
- 开头用一句有冲击力的话抛出问题或观点，并配合 emoji
- 用生活化比喻解释复杂概念，让人秒懂
- 分点表达，每点1–2句，短句有力，少术语
- 引用视频/观点时加入“我觉得很赞同/一下子击中了我”等共鸣
- 结合工作或日常场景，贴近读者处境
- 结尾加互动问题或轻量号召
- 生成 3–5 个中文话题标签（#效率 等），不要堆砌
输出格式：
标题一行
正文若干段（可含分点与 emoji）
3–5 个话题标签


prompt_translate.txt（示例）：

你是专业中英翻译。逐句准确翻译英文为中文，保留专有名词，
首次出现的缩写补充全称，禁止编造与省略。

8️⃣ 目录建议
ytb2xhs/
  main.py
  requirements.txt
  .env                # 本地自建，勿提交
  prompt_xhs.txt      # 可选：自定义风格
  prompt_translate.txt# 可选：自定义翻译
  venv/               # 本地虚拟环境（已在 .gitignore）
  result_*.txt        # 运行产物
