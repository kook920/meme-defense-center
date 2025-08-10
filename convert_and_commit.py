import pandas as pd
import os
from datetime import datetime

# 讀取 CSV（Google Sheets 轉出的）
CSV_URL = os.environ["SHEET_CSV_URL"]
df = pd.read_csv(CSV_URL)

# 過濾「狀態」為通過的行
df = df[df["Status"] == "通過"]

# 分組儲存 Markdown（依主題分類）
for topic, group in df.groupby("Theme"):
    md_lines = []

    for _, row in group.iterrows():
        date_str = datetime.strptime(row["Date"], "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
        tags = row["Tag"]
        content = row["Markdown"]

        md = f"""tags: {tags}
date: {row['Date']}
---
{content}
"""
        md_lines.append(md)

    # 寫入檔案，例如：馬文君-2025-08-09.md
    latest_date = max(group["Date"])
    latest_date = datetime.strptime(latest_date, "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
    filename = f"{topic}-{latest_date}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_lines))

# 將變更加進 Git 並推送
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add *.md")
os.system('git commit -m "Auto upload material" || echo "Nothing to commit"')
os.system("git push")
