import pandas as pd
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ✅ 用 Google Sheets API 開啟網址（來自 GitHub Secret）
CSV_URL = os.environ["SHEET_CSV_URL"]

# ✅ 驗證 credentials（Make sure credentials.json 已放入 repo 中或 Actions 跑得過）
gc = gspread.service_account(filename='credentials.json')

# ✅ 開啟 Google Sheet 並指定工作表名稱為 [審核通過]
sheet = gc.open_by_url(CSV_URL)
worksheet = sheet.worksheet("審核通過")  # ← 這一行最關鍵！

# ✅ 轉成 DataFrame
df = pd.DataFrame(worksheet.get_all_records())

# 🔍 debug：印出欄位名稱
print("欄位名稱：", df.columns.tolist())

# ✅ 過濾「Status」為「通過」的行
df = df[df["Status"] == "通過"]

# ✅ 分組儲存 Markdown（依 Theme 分類）
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

    # ✅ 檔名格式：馬文君-2025-08-09.md（主題-最新日期）
    latest_date = max(group["Date"])
    latest_date = datetime.strptime(latest_date, "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
    filename = f"{topic}-{latest_date}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_lines))

# ✅ Git commit & push
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add *.md")
os.system('git commit -m "Auto upload material" || echo "Nothing to commit"')
os.system("git push")
