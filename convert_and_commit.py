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

# 🧾 讀取 Google Sheets 設定
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]
encoded_sheet_name = urllib.parse.quote(sheet_name)

CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 📥 載入資料
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)
print("欄位名稱：", df.columns.tolist())

# 🎯 篩選「Status = 通過」
df = df[df["Status"] == "通過"]

# 🗂️ 依主題分組處理
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []

    for _, row in group.iterrows():
        raw_date = row["Date"]
        if not raw_date.strip():
            continue

        try:
            date_obj = parse_datetime(raw_date)
            if not date_obj:
                continue
        except ValueError:
            print(f"❌ 無法解析日期：{raw_date}")
            continue

        display_date = date_obj.strftime("%Y/%m/%d %H:%M")
        content = row.get("Markdown", "").replace("\r\n", "\n")

        # 🔸 包裝成 code block
        wrapped_content = f"```\n{content}\n```"

        # 🔹 集中寫入 index.md
        md_lines.append(f"## {display_date}\n\n{wrapped_content}")

    # ✨ 寫入主題首頁
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic} 歷史貼文\n\n" + "\n\n---\n\n".join(md_lines))

# 🧭 自動產生 GitBook SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")

    for folder in sorted(os.listdir()):
        index_path = os.path.join(folder, "index.md")
        if os.path.isdir(folder) and os.path.exists(index_path):
            f.write(f"- [{folder}]({urllib.parse.quote(folder)}/index.md)\n")

# 🌀 Git 自動提交
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
