import pandas as pd
import os
from datetime import datetime
import urllib.parse
import csv

# 從 GitHub Actions 的環境變數讀取 ID 與表單名稱
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ["SPREADSHEET_ID"]

# URL encode 表單名稱
encoded_sheet_name = urllib.parse.quote(sheet_name)

# 組出 Google Sheet CSV 匯出網址
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

# 讀取 Google Sheet CSV，保留換行與原格式
df = pd.read_csv(CSV_URL, quoting=csv.QUOTE_ALL, keep_default_na=False)

# Debug：顯示欄位名稱
print("欄位名稱：", df.columns.tolist())

# 過濾 Status 為「通過」
df = df[df["Status"] == "通過"]

# 依 Theme 分類資料夾
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []
    for _, row in group.iterrows():
        raw_date = row["Date"]
        date_obj = datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
        date_str = date_obj.strftime("%Y-%m-%d")

        tags = row["Tag"]
        content = row["Markdown"].replace("\\n", "\n")  # 👈 保留換行！

        # 單篇文章
        post_filename = f"{date_str}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""tags: {tags}
date: {raw_date}
---
{content}
""")

        # 整合段落給 index.md 用
        md_lines.append(f"## {raw_date}\n\n{content.replace(chr(10), '\n\n')}")

    # 寫入主題頁 index.md
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n" + "\n\n---\n\n".join(md_lines))

# 更新 GitBook 的 SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for folder in sorted(os.listdir()):
        if os.path.isdir(folder) and not folder.startswith("."):
            f.write(f"- [{folder}]({folder}/index.md)\n")

# Git commit & push
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "Nothing to commit"')
os.system("git push")
