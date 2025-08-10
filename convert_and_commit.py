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
            print(f"❌ 無法解析日期：{raw_date}")
            return None

# 讀取 Google Sheets 的基本資訊
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]
encoded_sheet_name = urllib.parse.quote(sheet_name)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 讀取 CSV 並保留原始換行
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)
print("欄位名稱：", df.columns.tolist())

df = df[df["Status"] == "通過"]

# 每個主題建資料夾並處理貼文
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)
    md_lines = []

    for _, row in group.iterrows():
        raw_date = row["Date"]
        if not raw_date.strip():
            continue

        date_obj = parse_datetime(raw_date)
        if not date_obj:
            continue

        file_friendly_date = date_obj.strftime("%Y-%m-%d-%H%M")
        display_date = date_obj.strftime("%Y/%m/%d %H:%M")

        tags = row.get("Tag", "").strip()
        content = row.get("Markdown", "").replace("\r\n", "\n")

        # 將內文包進 code block，讓 GitBook 顯示複製按鈕
        wrapped_content = f"```\n{content}\n```"

        # 寫入單篇 markdown
        post_filename = f"{file_friendly_date}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""tags: {tags}
date: {raw_date}
---
{wrapped_content}
""")

        # 匯入主題 index.md 的段落（加上 code block）
        md_lines.append(f"""## {display_date}

```text
{content}
""")

# 寫入 index.md
with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
    f.write(f"# {topic} 歷史貼文\n\n" + "\n\n---\n\n".join(md_lines))

# ✅ 產生 SUMMARY.md（包含貼文連結）
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")

    for folder in sorted(os.listdir()):
        if not os.path.isdir(folder):
            continue

        index_path = os.path.join(folder, "index.md")
        if os.path.exists(index_path):
            f.write(f"- [{folder}]({urllib.parse.quote(folder)}/index.md)\n")

            md_files = [
                md for md in os.listdir(folder)
                if md.endswith(".md") and md != "index.md"
            ]
            for md in sorted(md_files):
                f.write(f"  - [{md}]({urllib.parse.quote(folder)}/{md})\n")

# ✅ Git 操作
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
