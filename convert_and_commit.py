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
# 🔧 重點 1：不再建立「topic 資料夾 + index.md」
#           改成 theme 資料夾裡面直接放「Topic.md」
for (zone_raw, theme, topic), group in df.groupby(["Zone", "Theme", "Topic"]):
    zone = (str(zone_raw) or "未分類").strip()
    theme = theme.strip()
    topic = topic.strip()

    # Theme 資料夾
    theme_folder = os.path.join(temp_root, zone, theme)
    os.makedirs(theme_folder, exist_ok=True)

    # 如果有特殊字元再處理檔名，暫時先用原 Topic 當檔名
    topic_filename = f"{topic}.md"
    topic_filepath = os.path.join(theme_folder, topic_filename)

    md_lines = []
    for _, row in group.iterrows():
        raw_date = str(row["Date"]).strip()
        content = str(row["Markdown"]).strip()
        tags = str(row["Tag"]).strip()

        date_obj = parse_datetime(raw_date)
        display_date = date_obj.strftime("%Y/%m/%d %H:%M") if date_obj else raw_date or "未提供日期"
        section_title = tags or display_date
        wrapped_content = f"```\n{content}\n```"
        md_lines.append(f"## {section_title}\n\n{wrapped_content}")

    # 🔧 每個 Topic 一個獨立檔案：<Theme>/<Topic>.md
    with open(topic_filepath, "w", encoding="utf-8") as f:
        f.write(f"# {theme}/{topic}\n\n" + "\n\n---\n\n".join(md_lines))

    zone_map.setdefault(zone, {}).setdefault(theme, []).append(topic)

# 🔧 額外補上 Zone 層級 README 與 Theme 層級 index.md（SUMMARY 有連結）
for zone, themes in zone_map.items():
    zone_dir = os.path.join(temp_root, zone)
    os.makedirs(zone_dir, exist_ok=True)
    zone_readme = os.path.join(zone_dir, "README.md")
    if not os.path.exists(zone_readme):
        with open(zone_readme, "w", encoding="utf-8") as f:
            f.write(f"# {zone}\n\n")
            for theme in themes.keys():
                f.write(f"- {theme}\n")

    for theme in themes.keys():
        theme_dir = os.path.join(zone_dir, theme)
        os.makedirs(theme_dir, exist_ok=True)
        theme_index = os.path.join(theme_dir, "index.md")
        if not os.path.exists(theme_index):
            with open(theme_index, "w", encoding="utf-8") as f:
                f.write(f"# {theme}\n\n")

# 🏠 寫入 README.md 到 temp_output/
with open(os.path.join(temp_root, "README.md"), "w", encoding="utf-8") as f:
    f.write("# 文字素材庫\n\n")
    f.write("[回到入口頁 ➡](https://taipai-1.gitbook.io/l-ke-fu-wu-zhong-xin/)\n\n")
    f.write("🚧 本頁面由自動化腳本產生，內容依據 Google Sheets 即時更新。\n\n")
    f.write("## 分類一覽\n\n")
    for zone, themes in zone_map.items():
        f.write(f"### {zone}\n")
        for theme in themes:
            f.write(f"- {theme}\n")   # ← 保留純文字
        f.write("\n")

# 📖 寫入 SUMMARY.md 到 temp_output/
with open(os.path.join(temp_root, "SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for zone, themes in sorted(zone_map.items()):
        zone_enc = urllib.parse.quote(zone)
        f.write(f"- [{zone}]({zone_enc}/README.md)\n")
        for theme, topics in sorted(themes.items()):
            theme_enc = urllib.parse.quote(theme)
            theme_path = f"{zone_enc}/{theme_enc}"
            f.write(f"  - [{theme}]({theme_path}/index.md)\n")
            for topic in sorted(topics):
                topic_enc = urllib.parse.quote(topic)
                # 🔧 這裡連到 <Theme>/<Topic>.md
                f.write(f"    - [{topic}]({theme_path}/{topic_enc}.md)\n")

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
