import pandas as pd
import os
import urllib.parse
import csv
from datetime import datetime

# 環境變數設定
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]

# 組出 Google Sheet CSV 匯出網址
encoded_sheet_name = urllib.parse.quote(sheet_name)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 讀取 CSV，保留換行符號
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)

# 🔍 Debug：顯示欄位
print("欄位名稱：", df.columns.tolist())

# 過濾狀態為「通過」
df = df[df["Status"] == "通過"]

# 建立主題資料夾，輸出 .md 檔案
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []

    for _, row in group.iterrows():
        raw_date = row["Date"]

        # 🛡️ 避免空白日期造成錯誤
        if not raw_date.strip():
            print(f"⚠️ 跳過空日期的資料：{row.to_dict()}")
            continue

        date_obj = datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
        date_str = date_obj.strftime("%Y-%m-%d-%H-%M")

        tags = row.get("Tag", "")
        content = row["Markdown"].replace('\r\n', '\n').replace('\r', '\n')

        post_filename = f"{date_str}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""---
tags: [{tags}]
date: {raw_date}
---

{content}
""")

        # ➤ index.md 裡的段落
        md_lines.append(f"## {raw_date}\n\n{content}")

    # ➤ 每主題的 index.md
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n" + "\n\n---\n\n".join(md_lines))

# ➤ SUMMARY.md 自動產出
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for folder in sorted(os.listdir()):
        if os.path.isdir(folder) and not folder.startswith("."):
            f.write(f"- [{folder}]({folder}/index.md)\n")
