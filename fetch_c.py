import csv
import os
import sys
import time
from datetime import datetime

import requests

from parse_helpers import fetch_html, parse_by_type


CSV_JOURNALS = "auto_list.csv"
OUT_DIR = "data"
OUT_CSV = os.path.join(OUT_DIR, "daily_c.cssci.csv")

OUT_COLUMNS = [
    "分组",
    "刊名",
    "期次/日期",
    "文章标题",
    "作者",
    "来源/栏目",
    "链接",
    "抓取时间",
]


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def read_journals(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "分组": row["分组"].strip(),
                "刊名": row["刊名"].strip(),
                "url": row["url"].strip(),
                "parser": row["parser"].strip(),
            })
    return rows


def append_rows(path, group, name, items):
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(OUT_COLUMNS)
        for item in items:
            w.writerow([group, name] + item)


def main():
    ensure_out_dir()
    journals = read_journals(CSV_JOURNALS)

    for i, j in enumerate(journals, 1):
        group = j["分组"]
        name = j["刊名"]
        url = j["url"]
        parser_type = j["parser"]

        print(f"[{i}/{len(journals)}] {group} | {name} | {parser_type} | {url}", flush=True)

        try:
            html = fetch_html(url)
            items = parse_by_type(parser_type, html, url)
            append_rows(OUT_CSV, group, name, items)
            print(f"  -> {len(items)} rows", flush=True)
        except Exception as e:
            print(f"  !! error: {e}", flush=True)
            append_rows(OUT_CSV, group, name, [
                [
                    "",
                    f"抓取失败: {e}",
                    "",
                    "",
                    url,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            ])

        if i < len(journals):
            time.sleep(1)

    print("done:", OUT_CSV, flush=True)


if __name__ == "__main__":
    main()
