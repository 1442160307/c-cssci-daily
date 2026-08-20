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


def load_existing_keys(path):
    """读取已有CSV，返回(分组, 刊名, 标题, 链接)的去重集合"""
    keys = set()
    if not os.path.exists(path):
        return keys
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 7:
                keys.add((row[0], row[1], row[3], row[6]))
    return keys


def is_noise(title):
    """过滤导航栏、表头、失败信息等噪音"""
    if not title:
        return True
    noise_keywords = [
        "关于光明网", "联系我们", "法律声明", "网站地图",
        "English", "光明图片", "我要投稿", "光明报系",
        "更多>>", "理论导读", "光明独家", "百场讲坛",
        "理论视频", "理论图解", "文章精选", "理论专题", "报网动态",
        "文章标题", "作者单位", "摘要", "关键词", "ISSN", "EISSN",
        "抓取失败", "HTTPSConnectionPool",
    ]
    for kw in noise_keywords:
        if kw in title:
            return True
    return False


def append_rows(path, group, name, items, existing_keys):
    new_file = not os.path.exists(path)
    count = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(OUT_COLUMNS)
        for item in items:
            title = item[2] if len(item) > 2 else ""
            url = item[5] if len(item) > 5 else ""
            if is_noise(title):
                continue
            key = (group, name, title, url)
            if key in existing_keys:
                continue
            existing_keys.add(key)
            w.writerow([group, name] + item)
            count += 1
    return count


def main():
    ensure_out_dir()
    journals = read_journals(CSV_JOURNALS)
    existing_keys = load_existing_keys(OUT_CSV)

    for i, j in enumerate(journals, 1):
        group = j["分组"]
        name = j["刊名"]
        url = j["url"]
        parser_type = j["parser"]

        print(f"[{i}/{len(journals)}] {group} | {name} | {parser_type} | {url}", flush=True)

        try:
            html = fetch_html(url)
            items = parse_by_type(parser_type, html, url)
            added = append_rows(OUT_CSV, group, name, items, existing_keys)
            print(f"  -> {added} new rows", flush=True)
        except Exception as e:
            # 只打印错误，不写入CSV
            print(f"  !! skip: {e}", flush=True)

        if i < len(journals):
            time.sleep(1)

    print("done:", OUT_CSV, flush=True)


if __name__ == "__main__":
    main()
