import os
import base64
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

# 你的 Google Sheets CSV 匯出網址
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1yXofSNohNOnZFUGT6n0jz8FggSiAtGwITt4YMLoVLSs/export?format=csv&gid=0"
GITHUB_REPO = "kook920/meme-defense-center"
BRANCH = "main"
GH_TOKEN = os.getenv("GH_TOKEN")

def slugify(text):
    return text.replace(" ", "_").replace("#", "").replace("/", "_")

def get_markdown_content(row):
    return row["內文markdown"].strip()

def main():
    df = pd.read_csv(SHEET_CSV_URL)

    for _, row in df.iterrows():
        topic = row["主題"].strip()
        tags = row["tag"].strip()
        timestamp = row["時間戳記"].strip()

        folder = slugify(topic)
        filename = f"{folder}-{timestamp}.md"
        content = get_markdown_content(row)

        # 組合 Markdown 文件內容
        frontmatter = f"---\ntags: [{tags}]\n---\n\n"
        markdown = frontmatter + content

        # 編碼為 Base64
        encoded = base64.b64encode(markdown.encode("utf-8")).decode("utf-8")

        # 建立 GitHub API URL
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{folder}/{filename}"

        # 建立 body
        data = {
            "message": f"Add {filename}",
            "content": encoded,
            "branch": BRANCH
        }

        headers = {
            "Authorization": f"Bearer {GH_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"Uploading {filename} to GitHub...")
        res = requests.put(url, headers=headers, json=data)
        if res.status_code in [200, 201]:
            print(f"✅ Success: {filename}")
        else:
            print(f"❌ Error {res.status_code}: {res.text}")

if __name__ == "__main__":
    main()
