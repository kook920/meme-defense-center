import pandas as pd
import os
import urllib.parse
import csv
from dateutil import parser
from datetime import datetime

def parse_datetime(raw_date):
    try:
        return datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
    except:
        try:
            return parser.parse(raw_date)
        except:
            print(f"\u274c \u7121\u6cd5\u89e3\u6790\u65e5\u671f\uff1a{raw_date}")
            return None

# 🧓️ 讀取 Google Sheets 設定
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]
encoded_sheet_name = urllib.parse.quote(sheet_name)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 📅 載入資料
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)
print("欄位名稱：", df.columns.tolist())

# 🌟 篩選「Status = 通過」
df = df[df["Status"] == "通過"]

# 🗂️ 依 Theme/Topic 集一分類
for (theme, topic), group in df.groupby(["Theme", "Topic"]):
    folder = os.path.join(theme.strip(), topic.strip())
    os.makedirs(folder, exist_ok=True)

    md_lines = []
    for _, row in group.iterrows():
        raw_date = str(row["Date"]).strip()
        content = str(row["Markdown"]).strip()
        tags = str(row["Tag"]).strip()

        try:
            date_obj = parse_datetime(raw_date)
            display_date = date_obj.strftime("%Y/%m/%d %H:%M") if date_obj else raw_date
        except:
            display_date = raw_date or "未提供日期"

        section_title = tags or display_date
        wrapped_content = f"```\n{content}\n```"
        md_lines.append(f"## {section_title}\n\n{wrapped_content}")

    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {theme}/{topic}\n\n" + "\n\n---\n\n".join(md_lines))

# 🧭 自動產生 GitBook SUMMARY.md（依照 Google Sheets 出現順序）
seen_themes = set()
ordered_themes = []

for theme in df["Theme"]:
    if theme not in seen_themes:
        seen_themes.add(theme)
        ordered_themes.append(theme.strip())

with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")

    for theme in sorted(os.listdir()):
        if not os.path.isdir(theme) or theme.startswith("."):
            continue
        f.write(f"- [{theme}]({urllib.parse.quote(theme)}/index.md)\n")

        for topic in sorted(os.listdir(theme)):
            topic_folder = os.path.join(theme, topic)
            index_path = os.path.join(topic_folder, "index.md")
            if os.path.exists(index_path):
                f.write(f"  - [{topic}]({urllib.parse.quote(theme)}/{urllib.parse.quote(topic)}/index.md)\n")

# 📀 Git 自動 commit/push
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
