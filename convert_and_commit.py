import pandas as pd
import os
import urllib.parse
import csv
import shutil
from dateutil import parser
from datetime import datetime


def parse_datetime(raw_date):
    try:
        return datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
    except:
        try:
            return parser.parse(raw_date)
        except:
            print(f"❌ 無法解析日期：{raw_date}")
            return None

import html


def make_preview_by_chars(text: str, max_chars: int = 120) -> str:
    s = " ".join((text or "").split())
    return s[:max_chars] + ("…" if len(s) > max_chars else "")


def seems_risky_for_details(content: str) -> bool:
    c = content or ""

    # 1️⃣ 內容本身含 HTML 標籤 → 不包 details
    for tag in ["<details", "</details", "<summary", "</summary", "<div", "</div", "<span", "</span"]:
        if tag in c:
            return True

    # 2️⃣ 使用 ~~~ fence（GitBook 高風險）
    if "~~~" in c:
        return True

    # 3️⃣ 單一 code block 很長（就算每行不長）
    if len(c) > 1200:
        return True

    # 4️⃣ 超長單行（保險）
    if any(len(line) > 800 for line in c.splitlines()):
        return True

    return False



def render_block(content: str, title: str, lang: str = "text") -> str:
    safe = (content or "").strip()

    if seems_risky_for_details(safe):
        # 🚑 降級模式：不包 <details>，避免 GitBook 500
        return f"""## {title}

```{lang}
{safe}
```""".strip()

    preview = make_preview_by_chars(safe, max_chars=120)
    preview = html.escape(preview, quote=False)

    return f"""## {title}

<details>
<summary>

📄 預覽（約 120 字）：<br>
{preview}

</summary>

```{lang}
{safe}
```

</details>""".strip()


    return md


    
# 📥 讀取 Google Sheets
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]
encoded_sheet_name = urllib.parse.quote(sheet_name)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)
df = df[df["Status"] == "通過"]

# 📁 建立暫存目錄
temp_root = "temp_output"
if os.path.exists(temp_root):
    shutil.rmtree(temp_root)
os.makedirs(temp_root)

zone_map = {}

# 📂 寫入 Zone/Theme/Topic 結構到 temp_output/
for (zone_raw, theme, topic), group in df.groupby(["Zone", "Theme", "Topic"]):
    zone = (str(zone_raw) or "未分類").strip()
    theme = theme.strip()
    topic = topic.strip()

    # Topic 底下：Zone/Theme/Topic/index.md
    folder_path = os.path.join(temp_root, zone, theme, topic)
    os.makedirs(folder_path, exist_ok=True)

    md_lines = []
    for _, row in group.iterrows():
        raw_date = str(row["Date"]).strip()
        content = str(row["Markdown"]).strip()
        tags = str(row["Tag"]).strip()

        date_obj = parse_datetime(raw_date)
        display_date = date_obj.strftime("%Y/%m/%d %H:%M") if date_obj else raw_date or "未提供日期"
        section_title = tags or display_date
        md_lines.append(render_block(content, section_title, lang="text"))


    with open(os.path.join(folder_path, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"# {theme}/{topic}\n\n" + "\n\n---\n\n".join(md_lines))

    zone_map.setdefault(zone, {}).setdefault(theme, [])
    if topic not in zone_map[zone][theme]:
        zone_map[zone][theme].append(topic)


# 🔧 為每個 Zone / Theme 建 README 結構
for zone, themes in zone_map.items():
    # Zone 資料夾
    zone_dir = os.path.join(temp_root, zone)
    os.makedirs(zone_dir, exist_ok=True)

    # Zone level：Zone/README.md
    zone_readme = os.path.join(zone_dir, "README.md")
    if not os.path.exists(zone_readme):
        with open(zone_readme, "w", encoding="utf-8") as f:
            f.write(f"# {zone}\n\n")

    # Theme level：Zone/Theme/README.md
    for theme, topics in themes.items():
        theme_dir = os.path.join(zone_dir, theme)
        os.makedirs(theme_dir, exist_ok=True)

        theme_readme = os.path.join(theme_dir, "README.md")
        if not os.path.exists(theme_readme):
            # 留白，讓 GitBook 自己在這頁列出底下 Topic 的按鈕
            open(theme_readme, "w", encoding="utf-8").close()

# 🏠 首頁：網站地圖 Site Map
with open(os.path.join(temp_root, "README.md"), "w", encoding="utf-8") as f:
    f.write("# 文字素材庫（網站地圖）\n\n")
    f.write("[回到入口頁 ➡](https://taipai-1.gitbook.io/l-ke-fu-wu-zhong-xin/)\n\n")
    f.write("🚧 本頁面由自動化腳本產生，內容依據 Google Sheets 即時更新。\n\n")
    f.write("## 網站地圖 Site Map\n\n")

    for zone, themes in sorted(zone_map.items()):
        f.write(f"### {zone}\n\n")
        for theme, topics in sorted(themes.items()):
            f.write(f"- **{theme}**\n")
            for topic in sorted(topics):
                f.write(f"  - {topic}\n")
            f.write("\n")

# 📖 寫入 SUMMARY.md 到 temp_output/
# ✅ 關鍵修改：移除所有 urllib.parse.quote()，直接使用中文路徑
with open(os.path.join(temp_root, "SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for zone, themes in sorted(zone_map.items()):
        # ✅ 直接使用中文，不編碼
        f.write(f"- [{zone}]({zone}/README.md)\n")

        for theme, topics in sorted(themes.items()):
            # ✅ 直接使用中文路徑
            theme_path = f"{zone}/{theme}"
            f.write(f"  - [{theme}]({theme_path}/README.md)\n")

            # Topic level：Zone/Theme/Topic/index.md
            for topic in sorted(topics):
                # ✅ 直接使用中文路徑
                topic_path = f"{theme_path}/{topic}"
                f.write(f"    - [{topic}]({topic_path}/index.md)\n")

# 🪄 一次性替換原始資料夾
for name in os.listdir():
    if name in [".git", ".github", temp_root]:
        continue
    if os.path.isdir(name) or name in ["README.md", "SUMMARY.md"]:
        shutil.rmtree(name) if os.path.isdir(name) else os.remove(name)

for item in os.listdir(temp_root):
    shutil.move(os.path.join(temp_root, item), item)
shutil.rmtree(temp_root)

# 🌀 Git 自動提交
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
