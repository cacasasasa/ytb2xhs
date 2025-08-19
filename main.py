# main.py
import os, re, sys, time, requests, yt_dlp
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# 价格
WHISPER_PRICE_PER_MIN = 0.006
GPT_INPUT_PER_MTOK = 0.15
GPT_OUTPUT_PER_MTOK = 0.60

# 可调参数与可外部覆盖的 prompt
def load_prompt(path: str, default_text: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default_text

TRANSLATE_SYS = load_prompt(
    "prompt_translate.txt",
    "你是专业中英翻译。逐句准确翻译英文为中文，保留专有名词，首次出现的缩写补充全称，禁止编造与省略。"
)

XHS_SYS = load_prompt(
    "prompt_xhs.txt",
    """你是一名小红书爆款写手，目标是把英文内容转化为适合小红书的中文笔记。  
写作要求：  
1. 开头用一句有冲击力的话抛出问题或观点，最好配合 emoji。  
2. 用生活化、形象的比喻解释复杂概念，让人秒懂。  
3. 引用视频/播客/观点时，加上“我觉得很赞同/一下子击中了我”这种共鸣感。  
4. 结合工作、生活或当下趋势，把抽象的知识贴近读者的处境。  
5. 分点说明时,每点1-2句,简短有力,避免大段解释。  
6. 结尾加上互动问题或号召，比如“你怎么看？”、“欢迎留言讨论”。  
7. 保持语气轻松、有分享感，避免生硬或学术化。  
8. 标签精简、相关即可，不要太多。  
输出格式：  
### 标题  
正文(带emoji、分段、分点)  
#标签1 #标签2 #标签3  
"""
)

MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMP", "0.6"))
FALLBACK_SUBTITLE_ONLY = os.getenv("FALLBACK_TO_SUBTITLE_ONLY", "false").lower() == "true"

class CostMeter:
    def __init__(self):
        self.whisper_minutes = 0.0
        self.gpt_in = 0
        self.gpt_out = 0
    def add_whisper_minutes(self, m): self.whisper_minutes += float(m or 0)
    def add_usage(self, usage):
        if usage:
            self.gpt_in += int(getattr(usage, "prompt_tokens", 0) or 0)
            self.gpt_out += int(getattr(usage, "completion_tokens", 0) or 0)
    def totals(self):
        c_whisper = self.whisper_minutes * WHISPER_PRICE_PER_MIN
        c_in = (self.gpt_in / 1_000_000) * GPT_INPUT_PER_MTOK
        c_out = (self.gpt_out / 1_000_000) * GPT_OUTPUT_PER_MTOK
        return round(c_whisper + c_in + c_out, 6), round(c_whisper, 6), round(c_in, 6), round(c_out, 6)

meter = CostMeter()

def slugify(s: str) -> str:
    return ("".join(c if c.isalnum() else "_" for c in s) or "video")[:50]

def get_info(url):
    with yt_dlp.YoutubeDL({"skip_download": True, "quiet": True}) as ydl:
        return ydl.extract_info(url, download=False)

def pick_caption_track(info):
    prefer = ["en", "en-US", "zh", "zh-Hans", "zh-Hant"]
    subs = info.get("subtitles") or {}
    autos = info.get("automatic_captions") or {}
    def pick(d):
        for code in prefer:
            if code in d and d[code]:
                tracks = d[code]
                for t in tracks:
                    if t.get("ext") == "vtt":
                        return t.get("url")
                return tracks[0].get("url")
        return None
    url = pick(subs)
    if url: return url, "human"
    url = pick(autos)
    if url: return url, "auto"
    return None, None

def vtt_to_text(vtt: str) -> str:
    lines = []
    for line in vtt.splitlines():
        if "-->" in line: continue
        if re.match(r"^\d+\s*$", line): continue
        line = re.sub(r"<[^>]+>", "", line.strip())
        if line: lines.append(line)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()

def fetch_captions_text(url) -> str:
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    t = r.text
    if t.lstrip().lower().startswith("webvtt"):
        return vtt_to_text(t)
    text = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", text).strip()

def download_audio(url, title_slug):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{title_slug}.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return f"{title_slug}.mp3"

def transcribe_audio(file_path, minutes_hint):
    meter.add_whisper_minutes(minutes_hint)
    with open(file_path, "rb") as f:
        resp = client.audio.transcriptions.create(model="whisper-1", file=f)
    return resp.text

def llm_chat(messages, model=MODEL, temperature=TEMPERATURE, retries=3):
    for i in range(retries):
        try:
            resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
            meter.add_usage(resp.usage)
            return resp.choices[0].message.content
        except RateLimitError:
            time.sleep(2 ** i)
        except APIError:
            if i == retries - 1: raise
            time.sleep(2 ** i)

def translate_text(text_en):
    return llm_chat([
        {"role": "system", "content": TRANSLATE_SYS},
        {"role": "user", "content": text_en}
    ], temperature=0.3)

def xhs_style(chinese_text):
    user = (
        "基于以下中文内容生成小红书成品文案。"
        "结构为 标题两行开头 主体分点 结尾行动号召与互动问题 并生成三到五个中文话题标签。"
        f"\n\n内容如下\n{chinese_text}"
    )
    return llm_chat([
        {"role": "system", "content": XHS_SYS},
        {"role": "user", "content": user}
    ], temperature=TEMPERATURE)

def save_result(title, url, post_text):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"result_{ts}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"原视频标题  {title}\n原链接  {url}\n\n小红书成品文案\n\n{post_text}\n")
    return fname

if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else input("请输入 YouTube 视频链接  ")
    url = raw.strip().strip('"').strip("'").strip("“”‘’")
    info = get_info(url)
    title = info.get("title") or "yt_video"
    duration = info.get("duration") or 0
    minutes = round(duration / 60.0, 2)
    title_slug = slugify(title)

    print(f"视频  {title}  时长约  {minutes} 分钟")
    cap_url, cap_type = pick_caption_track(info)

    if cap_url:
        print(f"检测到字幕  类型  {cap_type}  优先使用字幕")
        english_text = fetch_captions_text(cap_url)
        if FALLBACK_SUBTITLE_ONLY:
            with open("subtitle_en.txt", "w", encoding="utf-8") as f:
                f.write(english_text)
            print("已保存字幕到 subtitle_en.txt")
            sys.exit(0)
    else:
        print("无可用字幕  下载音频并使用 Whisper 转写")
        audio_file = download_audio(url, title_slug)
        english_text = transcribe_audio(audio_file, minutes)

    print("开始翻译")
    chinese_text = translate_text(english_text)

    print("开始小红书改写")
    xhs_post = xhs_style(chinese_text)

    out = save_result(title, url, xhs_post)
    total, c_whisper, c_in, c_out = meter.totals()

    print("\n已写入文件  ", out)
    print("\n费用预估")
    print(f"Whisper USD {c_whisper}")
    print(f"LLM 输入 token {meter.gpt_in} 费用 USD {c_in}")
    print(f"LLM 输出 token {meter.gpt_out} 费用 USD {c_out}")
    print(f"合计 USD {total}")
