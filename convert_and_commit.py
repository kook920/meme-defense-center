import pandas as pd
import os
import urllib.parse
import csv
from datetime import datetime

# 讀取 Google Sheets 的基本資訊
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]
encoded_sheet_name = urllib.parse.quote(sheet_name)

# 組出 Google Sheet CSV 匯出網址
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 讀取 CSV 並保留原始換行
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)

# 顯示欄位名稱以利除錯
print("欄位名稱：", df.columns.tolist())

# 過濾 Status 為 "通過"
df = df[df["Status"] == "通過"]

# 按主題分組處理
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []  # 用來寫入 index.md 的段落

    for _, row in group.iterrows():
        raw_date = row["Date"]
        if not raw_date.strip():
            continue  # 跳過空白日期的列

        try:
            date_obj = datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
        except ValueError:
            print(f"❌ 無法解析日期：{raw_date}")
            continue

        # 格式化檔名與標題用的日期
        file_friendly_date = date_obj.strftime("%Y-%m-%d-%H%M")
        display_date = date_obj.strftime("%Y/%m/%d %H:%M")

        tags = row.get("Tag", "").strip()
        content = row.get("Markdown", "").replace("\r\n", "\n").replace("\n", "\n\n")

        # 寫入單篇 markdown
        post_filename = f"{file_friendly_date}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""tags: {tags}
date: {raw_date}
---
{content}
""")

        # 整合進 index.md
        md_lines.append(f"## {display_date}\n\n{content}")

    # 寫入主題首頁 index.md（讓 GitBook 顯示）
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic} 歷史貼文\n\n" + "\n\n---\n\n".join(md_lines))

# 🔹 自動產生 GitBook 的 SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")

for folder in sorted(os.listdir()):
        index_path = os.path.join(folder, "index.md")
        if os.path.isdir(folder) and os.path.exists(index_path):
            f.write(f"- [{folder}]({urllib.parse.quote(folder)}/index.md)\n")

        # 加入該主題底下所有貼文
        md_files = [f for f in os.listdir(folder) if f.endswith(".md") and f != "index.md"]
        for md in sorted(md_files):
            f.write(f"  - [{md}]({urllib.parse.quote(folder)}/{md})\n")


# 🔹 Git 操作
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
