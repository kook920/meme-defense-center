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
df = df[df.get("Status", "") == "通過"].copy()

# 📁 建立暫存目錄
temp_root = "temp_output"
if os.path.exists(temp_root):
    shutil.rmtree(temp_root)
os.makedirs(temp_root, exist_ok=True)

# 用 dict 收集結構：{zone: {theme: [topics...]}}
zone_map: dict[str, dict[str, list[str]]] = {}

# 📂 寫入 Zone/Theme/Topic 結構到 temp_output/
for (zone_key, theme_key, topic_key), group in df.groupby(["Zone", "Theme", "Topic"], dropna=False):
    zone = (str(zone_key) or "未分類").strip()
    theme = (str(theme_key) or "").strip()
    topic = (str(topic_key) or "").strip()

    folder_path = os.path.join(temp_root, zone, theme, topic)
    os.makedirs(folder_path, exist_ok=True)

    md_lines = []
    # 盡量依時間排序（新到舊）
    def _sort_key(row):
        dt = parse_datetime(str(row.get("Date", "")).strip())
        return (dt is None, dt if dt else datetime.min)
    group_sorted = sorted(group.to_dict("records"), key=_sort_key, reverse=True)

    for row in group_sorted:
        raw_date = str(row.get("Date", "")).strip()
        content = str(row.get("Markdown", "")).replace("\r\n", "\n")  # 保留換行
        tags = str(row.get("Tag", "")).strip()

        dt = parse_datetime(raw_date)
        display_date = dt.strftime("%Y/%m/%d %H:%M") if dt else (raw_date or "未提供日期")
        section_title = tags or display_date
        wrapped_content = f"```\n{content}\n```"
        md_lines.append(f"## {section_title}\n\n{wrapped_content}")

    # Topic 頁
    with open(os.path.join(folder_path, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"# {theme}/{topic}\n\n" + "\n\n---\n\n".join(md_lines))

    # 建立 Theme → Topics 清單
    zone_map.setdefault(zone, {}).setdefault(theme, [])
    if topic not in zone_map[zone][theme]:
        zone_map[zone][theme].append(topic)

# 🗂️ 產生 Theme 索引頁（列出底下所有 Topic）
for zone, themes in zone_map.items():
    for theme, topics in themes.items():
        theme_dir = os.path.join(temp_root, zone, theme)
        os.makedirs(theme_dir, exist_ok=True)
        with open(os.path.join(theme_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(f"# {theme}\n\n")
            for topic in topics:
                f.write(f"- [{topic}]({urllib.parse.quote(topic)}/index.md)\n")

# 🏠 寫入 README.md（純文字目錄）到 temp_output/
with open(os.path.join(temp_root, "README.md"), "w", encoding="utf-8") as f:
    f.write("# 文字素材庫\n\n")
    f.write("🎯 本頁面由自動化腳本產生，內容依據 Google Sheets 即時更新。\n\n")
    f.write("## 分類一覽\n\n")
    for zone, themes in zone_map.items():
        f.write(f"### {zone}\n")
        for theme in themes.keys():
            f.write(f"- {theme}\n")  # 純文字，不放連結
        f.write("\n")

# 📖 寫入 SUMMARY.md 到 temp_output/
with open(os.path.join(temp_root, "SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    # Zone 層不放連結（避免死連結）；Theme/Topic 才放
    for zone, themes in zone_map.items():
        f.write(f"- {zone}\n")
        for theme, topics in themes.items():
            theme_path = f"{urllib.parse.quote(zone)}/{urllib.parse.quote(theme)}"
            f.write(f"  - [{theme}]({theme_path}/index.md)\n")
            for topic in topics:
                topic_path = f"{theme_path}/{urllib.parse.quote(topic)}"
                f.write(f"    - [{topic}]({topic_path}/index.md)\n")

# 🪄 一次性替換原始資料夾（保留 .git、.github、工作流程）
for name in os.listdir():
    if name in [".git", ".github", temp_root]:
        continue
    if os.path.isdir(name):
        shutil.rmtree(name)
    elif name in ["README.md", "SUMMARY.md"]:
        os.remove(name)

for item in os.listdir(temp_root):
    shutil.move(os.path.join(temp_root, item), item)
shutil.rmtree(temp_root)

# 🌀 Git 自動提交
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
