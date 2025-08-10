import os
import pandas as pd
from datetime import datetime
import gspread

SHEET_URL = os.environ.get("SHEET_URL")
WORKSHEET = os.environ.get("SHEET_WORKSHEET", "審核通過")
if not SHEET_URL:
    raise RuntimeError("SHEET_URL is not set")

# 使用 service account 驗證
gc = gspread.service_account(filename='credentials.json')

# 指定分頁
ws = gc.open_by_url(SHEET_URL).worksheet(WORKSHEET)
df = pd.DataFrame(ws.get_all_records())

print("欄位名稱：", df.columns.tolist())

if "Status" not in df.columns:
    raise RuntimeError("找不到 'Status' 欄位，請確認 [審核通過] 分頁的欄名。")

# 過濾通過
df = df[df["Status"] == "通過"]

# 依主題輸出 md
for topic, group in df.groupby("Theme"):
    md_lines = []
    for _, row in group.iterrows():
        # 原始為 2025/8/9 21:00 -> 2025-08-09
        date_str = datetime.strptime(row["Date"], "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
        tags = row["Tag"]
        content = row["Markdown"]

        md = f"""tags: {tags}
date: {row['Date']}
---
{content}
"""
        md_lines.append(md)

    latest_date = max(group["Date"])
    latest_date = datetime.strptime(latest_date, "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
    filename = f"{topic}-{latest_date}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_lines))
