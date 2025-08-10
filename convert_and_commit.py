import pandas as pd
import os
import urllib.parse
import csv
from datetime import datetime

# 讀取環境變數
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]

# 組出 Google Sheet CSV 匯出網址
encoded_sheet_name = urllib.parse.quote(sheet_name)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 讀取 CSV，保留換行（Markdown 欄位可能有多行）
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)

# Debug：顯示欄位名稱
print("欄位名稱：", df.columns.tolist())

# 過濾 Status 為通過
df = df[df["Status"] == "通過"]

# 🔸 建立主題資料夾、index.md
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []

    for _, row in group.iterrows():
        raw_date = row["Date"]
        try:
            date_obj = datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
        except ValueError:
            print(f"❗ 無法解析日期：{raw_date}，跳過此列")
            continue

        date_str = date_obj.strftime("%Y-%m-%d %H:%M")
        tags = row["Tag"]
        content = row["Markdown"]

        # 修正 Markdown 換行符號（還原為 GitBook 可解析格式）
        formatted_content = content.replace("\\n", "\n\n")

        # 單篇 index.md：GitBook 可抓到
        with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
            f.write(f"""---
tags: {tags}
date: {raw_date}
---

{formatted_content}
""")

        # 整合 index 頁用的區塊
        md_lines.append(f"## {date_str}\n\n{formatted_content}")

    # 🔸 寫入整合頁 index.md（供檢視歷史）
    with open(f"{folder}/all_posts.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic} 歷史貼文\n\n" + "\n\n---\n\n".join(md_lines))

# 🔸 自動產出 GitBook 導覽頁 SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for folder in sorted(os.listdir()):
        if os.path.isdir(folder) and not folder.startswith("."):
            f.write(f"- [{folder}]({folder}/index.md)\n")

# 🔸 Git 自動推送
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
