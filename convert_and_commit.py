import pandas as pd
import os
import urllib.parse
from datetime import datetime

# 讀取環境變數
sheet_name = os.environ.get("SHEET_NAME", "審核通過")
spreadsheet_id = os.environ.get("SPREADSHEET_ID")

encoded_sheet_name = urllib.parse.quote(sheet_name)
csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"
df = pd.read_csv(csv_url)

print("✅ 欄位名稱：", df.columns.tolist())

# 過濾 Status 欄位為 "通過"
df = df[df["Status"] == "通過"]

# 按主題分類寫入
for topic, group in df.groupby("Theme"):
    folder = topic.strip()
    os.makedirs(folder, exist_ok=True)

    md_lines = []
    for _, row in group.iterrows():
        raw_date = row["Date"]
        date_obj = datetime.strptime(raw_date, "%Y/%m/%d %H:%M")
        date_str = date_obj.strftime("%Y-%m-%d")

        tags = row["Tag"]
        content = row["Markdown"]

        # 單篇 Markdown
        post_filename = f"{date_str}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""tags: {tags}
date: {raw_date}
---
{content}
""")

        # 加入 index.md 段落
        md_lines.append(f"## {raw_date}\n\n{content}")

    # 寫入 index.md
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n" + "\n\n---\n\n".join(md_lines))

# 自動產出 SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for folder in sorted(os.listdir()):
        if os.path.isdir(folder) and not folder.startswith("."):
            f.write(f"- [{folder}]({folder}/index.md)\n")

# Git 操作
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "🟡 Nothing to commit"')
os.system("git push")
