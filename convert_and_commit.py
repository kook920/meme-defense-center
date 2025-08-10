import pandas as pd
import os
import urllib.parse

sheet_name = os.environ.get("SHEET_NAME", "審核通過")
encoded_sheet_name = urllib.parse.quote(sheet_name)
spreadsheet_id = os.environ["SPREADSHEET_ID"]
CSV_URL = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

from datetime import datetime

# 🔹 讀取 Google Sheet CSV
CSV_URL = os.environ["SHEET_CSV_URL"]
df = pd.read_csv(CSV_URL)

# 🔍 debug：顯示欄位
print("欄位名稱：", df.columns.tolist())

# 🔹 過濾 Status 為通過
df = df[df["Status"] == "通過"]

# 🔹 建立主題資料夾，寫入單篇檔案與 index.md
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

        # 單篇 Markdown 檔案
        post_filename = f"{date_str}.md"
        with open(f"{folder}/{post_filename}", "w", encoding="utf-8") as f:
            f.write(f"""tags: {tags}
date: {raw_date}
---
{content}
""")

        # 整合頁 index.md 中的段落
        md_lines.append(f"## {raw_date}\n\n{content}")

    # 寫入 index.md
    with open(f"{folder}/index.md", "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n" + "\n\n---\n\n".join(md_lines))

# 🔹 自動產出 SUMMARY.md
with open("SUMMARY.md", "w", encoding="utf-8") as f:
    f.write("# Summary\n\n")
    f.write("- [首頁](README.md)\n")
    for folder in sorted(os.listdir()):
        if os.path.isdir(folder) and not folder.startswith("."):
            f.write(f"- [{folder}]({folder}/index.md)\n")

# 🔹 Git 操作
os.system("git config --global user.name 'github-actions'")
os.system("git config --global user.email 'github-actions@users.noreply.github.com'")
os.system("git add .")
os.system('git commit -m "Auto upload material" || echo "Nothing to commit"')
os.system("git push")
