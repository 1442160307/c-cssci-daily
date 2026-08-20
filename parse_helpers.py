import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def clean_text(x):
    if x is None:
        return ""
    return re.sub(r"\s+", " ", x).strip().strip("：:").strip()


def parse_cnki_journal(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    title = clean_text(soup.find("title").get_text()) if soup.find("title") else ""

    name = ""
    for tag in soup.select(".journalName, .name, h1, h2"):
        t = clean_text(tag.get_text())
        if t:
            name = t
            break

    issue = ""
    date_text = ""
    articles = []

    for td in soup.find_all("td"):
        txt = clean_text(td.get_text())
        if not txt:
            continue
        if "期" in txt and ("年" in txt or "/" in txt or re.search(r"\d{4}", txt)):
            date_text = txt
        elif re.search(r"^\d{4}.*期$", txt) or re.search(r"Vol|No|期", txt, re.I):
            if not date_text:
                date_text = txt

    items = soup.select(
        ".docList .item, .listItem, .articleItem, ul.list li, ol.list li, "
        ".paper-item, .item"
    )

    seen = set()
    for it in items:
        a = it.find("a", href=True)
        if not a:
            continue
        art_title = clean_text(a.get_text())
        if not art_title or art_title in seen:
            continue
        seen.add(art_title)

        href = a["href"]
        url = href if href.startswith("http") else urljoin(base_url, href)

        authors = ""
        source = ""
        for small in it.find_all(["span", "p", "div", "em", "i"]):
            s = clean_text(small.get_text())
            if not s:
                continue
            if any(k in s for k in ["作者", "著", "编", "译"]):
                authors = s
                break
            if any(k in s for k in ["来源", "期刊", "学报", "研究", "杂志"]):
                source = s

        if not issue:
            issue = date_text

        articles.append([
            name or title,
            issue,
            art_title,
            authors,
            source,
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

    if not articles:
        articles.append([
            name or title,
            date_text or issue,
            "",
            "",
            "",
            base_url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

    return articles


def parse_gmw_theory(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    name = "光明日报·理论版"
    articles = []

    for a in soup.find_all("a", href=True):
        txt = clean_text(a.get_text())
        if not txt:
            continue
        if len(txt) < 4:
            continue
        if txt in {"首页", "光明网", "理论", "理论版", "更多", "评论"}:
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin(base_url, href)
        articles.append([
            name,
            "",
            txt,
            "",
            "光明日报·理论版",
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

    seen = set()
    uniq = []
    for row in articles:
        key = row[2], row[5]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)

    return uniq or [[name, "", "", "", "光明日报·理论版", base_url,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]


def parse_people_theory(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    name = "人民日报·理论版"
    articles = []

    for a in soup.find_all("a", href=True):
        txt = clean_text(a.get_text())
        if not txt:
            continue
        if len(txt) < 4:
            continue
        if txt in {"首页", "人民网", "理论", "理论版", "更多", "观点", "评论"}:
            continue
        href = a["href"]
        url = href if href.startswith("http") else urljoin(base_url, href)
        articles.append([
            name,
            "",
            txt,
            "",
            "人民日报·理论版",
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

    seen = set()
    uniq = []
    for row in articles:
        key = row[2], row[5]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)

    return uniq or [[name, "", "", "", "人民日报·理论版", base_url,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]


PARSERS = {
    "cnki_journal": parse_cnki_journal,
    "gmw_theory": parse_gmw_theory,
    "people_theory": parse_people_theory,
}


def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.encoding = r.apparent_encoding or "utf-8"
    r.raise_for_status()
    return r.text


def parse_by_type(parser_type, html, url):
    func = PARSERS.get(parser_type)
    if not func:
        raise ValueError(f"unknown parser: {parser_type}")
    return func(html, url)
