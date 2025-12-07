import os
import time
import random
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd

import config

# -------- 基本设置 --------
CSV_FILENAME = "data_gsmarena_notebookcheck.csv"

MAX_DEVICES_PER_MODEL = 1        # 每个关键词最多取几个搜索结果（一般 1 个够用）
MAX_PAGES_PER_DEVICE = 10        # GSMArena opinions 最多翻几页
MAX_OPINIONS_PER_DEVICE = 100    # 每个机型最多抓多少条 opinion

MAX_COMMENTS_PER_REVIEW = 50     # Notebookcheck 每篇评测最多抓多少条评论

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}

GS_BASE = "https://www.gsmarena.com"
NB_BASE = "https://www.notebookcheck.net"

# Notebookcheck 使用 Google Custom Search，这里用你提供的模板
NB_SEARCH_URL_TEMPLATE = (
    "https://www.notebookcheck.net/Google-Search.36690.0.html"
    "?cx=partner-pub-9323363027260837%3Atxif1w-xjer"
    "&cof=FORID%3A10&ie=UTF-8&q={q}&search="
)

# -------- 断点续跑用的集合 / 统计 --------
SEEN_GS_OPINION_KEYS = set()    # (phone_model_id, device_name, raw_text[:80])
GS_OPINION_COUNT = {}           # (phone_model_id, device_name) -> 历史 opinion 数

SEEN_NB_ARTICLE_URLS = set()    # Notebookcheck 评测 URL
SEEN_NB_COMMENT_KEYS = set()    # (url, raw_text[:80])


def append_row_to_csv(row: dict):
    """实时将一条记录追加写入 CSV，文件不存在时自动写表头"""
    df = pd.DataFrame([row])
    file_exists = os.path.exists(CSV_FILENAME)
    df.to_csv(
        CSV_FILENAME,
        mode="a",
        index=False,
        encoding="utf-8-sig",
        header=not file_exists,
    )


def get_soup(url: str, sleep_range=(0.5, 1.2)):
    """带 headers + 简单重试的 GET，然后返回 BeautifulSoup"""
    for i in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                time.sleep(random.uniform(*sleep_range))
                return BeautifulSoup(resp.text, "lxml")
            else:
                print(f"   ⚠️ 请求 {url} 返回 {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ 请求 {url} 出错: {e}")
        time.sleep(1.0 + i)
    return None


def load_existing_progress():
    """启动时读取旧 CSV，构建去重用的集合，实现断点续跑"""
    global GS_OPINION_COUNT

    if not os.path.exists(CSV_FILENAME):
        print(f"📁 未发现历史文件，将从头开始抓取并写入 {CSV_FILENAME}")
        return

    try:
        df = pd.read_csv(CSV_FILENAME)
    except Exception as e:
        print(f"⚠️ 读取历史 CSV 失败，不启用断点续爬逻辑: {e}")
        return

    if df.empty:
        print(f"📂 发现历史文件 {CSV_FILENAME}，但为空，将从头开始抓。")
        return

    print(f"📂 检测到已有历史文件 {CSV_FILENAME}，总记录 {len(df)} 行。")

    # GSMArena opinions 去重 + 计数（虽然这次不跑 GSMArena，但保留信息没坏处）
    if {"platform", "data_type", "phone_model_id", "device_name", "raw_text"}.issubset(df.columns):
        gsm_df = df[(df["platform"] == "gsmarena") & (df["data_type"] == "opinion")].copy()
        for _, row in gsm_df.iterrows():
            key = (
                str(row.get("phone_model_id", "")),
                str(row.get("device_name", "")),
                str(row.get("raw_text", ""))[:80],
            )
            SEEN_GS_OPINION_KEYS.add(key)

        if not gsm_df.empty:
            counts = (
                gsm_df.groupby(["phone_model_id", "device_name"])["raw_text"]
                .count()
                .to_dict()
            )
            GS_OPINION_COUNT = {tuple(k): int(v) for k, v in counts.items()}

        print(f"   🔁 已有 GSMArena opinions 去重键 {len(SEEN_GS_OPINION_KEYS)} 个")
        print(f"   🔁 已有 GSMArena 机型-设备组合 {len(GS_OPINION_COUNT)} 个")

    # Notebookcheck 评测正文 + 评论去重
    if {"platform", "data_type", "url"}.issubset(df.columns):
        nb_df = df[df["platform"] == "notebookcheck"].copy()

        art_df = nb_df[nb_df["data_type"] == "review_article"]
        for u in art_df["url"].dropna().unique():
            SEEN_NB_ARTICLE_URLS.add(str(u))
        print(f"   🔁 已有 Notebookcheck 评测 {len(SEEN_NB_ARTICLE_URLS)} 篇")

        if "raw_text" in nb_df.columns:
            comm_df = nb_df[nb_df["data_type"] == "review_comment"]
            for _, row in comm_df.iterrows():
                key = (
                    str(row.get("url", "")),
                    str(row.get("raw_text", ""))[:80],
                )
                SEEN_NB_COMMENT_KEYS.add(key)
            print(f"   🔁 已有 Notebookcheck 评论去重键 {len(SEEN_NB_COMMENT_KEYS)} 个")


# =========================
# 1. （保留）GSMArena：搜索 + opinions
# =========================

def search_gsmarena_devices(search_kw: str):
    """在 GSMArena 搜索机型，返回设备页 URL 列表"""
    q = urllib.parse.quote_plus(search_kw)
    url = f"{GS_BASE}/results.php3?sQuickSearch=yes&sName={q}"
    print(f"   🔍 GSMArena 搜索: {url}")
    soup = get_soup(url)
    if not soup:
        return []

    results = []
    makers = soup.select("div.makers ul li a")
    for a in makers:
        href = a.get("href") or ""
        name = (a.get_text() or "").strip()
        if not href:
            continue
        if not href.startswith("http"):
            href = GS_BASE + "/" + href.lstrip("/")
        results.append((name, href))
    print(f"   ✅ GSMArena 搜索结果 {len(results)} 个")
    return results


def find_gsmarena_opinions_url(device_url: str):
    """从设备页里找到 opinions（用户评论）的链接"""
    soup = get_soup(device_url)
    if not soup:
        return None

    # 1）优先找文本带 "opinions" / "opinion" 的链接
    for a in soup.find_all("a"):
        text = (a.get_text() or "").lower()
        href = a.get("href") or ""
        # 加括号避免 and / or 优先级问题
        if ("opinion" in text and "review" in href) or ("-reviews-" in href):
            if not href.startswith("http"):
                href = GS_BASE + "/" + href.lstrip("/")
            return href

    # 2）兜底：找 href 里带 "-reviews-" 的链接
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        if "-reviews-" in href:
            if not href.startswith("http"):
                href = GS_BASE + "/" + href.lstrip("/")
            return href

    return None


def crawl_gsmarena_opinions(device_name: str, device_url: str,
                            phone_model_id: str, search_kw: str):
    """对单个设备，抓 opinions 多页（保留函数，不在本轮调用）"""
    base_key = (phone_model_id, device_name)
    already = GS_OPINION_COUNT.get(base_key, 0)
    if already >= MAX_OPINIONS_PER_DEVICE:
        print(f"      ⏭ {device_name} 已有意见 {already} 条，达到上限 {MAX_OPINIONS_PER_DEVICE}，跳过。")
        return 0

    opinions_total = 0

    opinions_url = find_gsmarena_opinions_url(device_url)
    if not opinions_url:
        print(f"      ⚠️ {device_name} 找不到 opinions 链接，跳过。")
        return opinions_total

    print(f"      💬 opinions 起始页: {opinions_url} (历史已有 {already} 条)")

    for page_no in range(1, MAX_PAGES_PER_DEVICE + 1):
        if already + opinions_total >= MAX_OPINIONS_PER_DEVICE:
            print(f"      ⛔ 本设备 opinions 已达到上限 {MAX_OPINIONS_PER_DEVICE}，停止翻页。")
            break

        if page_no == 1:
            url = opinions_url
        else:
            if "?" in opinions_url:
                base = opinions_url.split("?", 1)[0]
            else:
                base = opinions_url
            url = f"{base}?page={page_no}"

        print(f"      👉 GSMArena opinions 第 {page_no} 页: {url}")
        soup = get_soup(url)
        if not soup:
            print("         ⚠️ 本页请求失败，停止翻页。")
            break

        items = (
            soup.select(".user-thread .uopin")
            or soup.select(".opinions li")
        )
        print(f"         🔎 本页疑似 opinion 元素数: {len(items)}")

        if not items:
            if page_no == 1:
                print("         ⚠️ 没找到任何 opinion 元素，可能需手动调整选择器。")
            break

        for ele in items:
            if already + opinions_total >= MAX_OPINIONS_PER_DEVICE:
                break

            text = (ele.get_text() or "").strip()
            if not text:
                continue

            key = (phone_model_id, device_name, text[:80])
            if key in SEEN_GS_OPINION_KEYS:
                continue
            SEEN_GS_OPINION_KEYS.add(key)

            user = ""
            date_str = ""

            parent = ele.parent
            if parent:
                uname = parent.select_one(".uname, .user-nick")
                if uname:
                    user = (uname.get_text() or "").strip()

                dt = parent.select_one(".time, .opinion-date")
                if dt:
                    date_str = (dt.get_text() or "").strip()

            row = {
                "platform": "gsmarena",
                "data_type": "opinion",
                "phone_model_id": phone_model_id,
                "search_kw": search_kw,
                "device_name": device_name,
                "url": url,
                "author": user,
                "time_str": date_str,
                "raw_text": text,
                "cleaned_text": text,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            append_row_to_csv(row)
            opinions_total += 1

        print(f"         ✅ 本页新增 {opinions_total} 条，本设备历史+本次共 {already + opinions_total} 条。")

    GS_OPINION_COUNT[base_key] = already + opinions_total
    return opinions_total


# =========================
# 2. Notebookcheck：抓评测正文 + 评论
# =========================

def search_notebookcheck_reviews(search_kw: str, max_results: int = 2):
    """Notebookcheck 搜索，返回可能的评测链接列表"""
    q = urllib.parse.quote_plus(search_kw)
    url = NB_SEARCH_URL_TEMPLATE.format(q=q)   # ★ 用 Google-Search 模板
    print(f"   🔍 Notebookcheck 搜索: {url}")
    soup = get_soup(url)
    if not soup:
        return []

    links = []
    for a in soup.select("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        if not href or not text:
            continue
        if "review" in href.lower():
            if not href.startswith("http"):
                href = NB_BASE.rstrip("/") + "/" + href.lstrip("/")
            links.append((text, href))

    uniq = []
    seen = set()
    for title, href in links:
        if href in seen:
            continue
        uniq.append((title, href))
        seen.add(href)
        if len(uniq) >= max_results:
            break

    print(f"   ✅ Notebookcheck 评测候选 {len(uniq)} 条")
    return uniq


def crawl_notebookcheck_review(title: str, url: str,
                               phone_model_id: str, search_kw: str):
    """抓单篇 Notebookcheck 评测正文 + 评论（最多 50 条评论）"""
    print(f"      📰 Notebookcheck 评测: {title[:50]}... -> {url}")
    soup = get_soup(url)
    if not soup:
        print("         ⚠️ 请求失败，跳过。")
        return

    # ------- 正文 -------
    article = (
        soup.select_one("article")
        or soup.select_one("div#content")
        or soup.select_one("div.text")
    )
    text = ""
    if article:
        paras = [(p.get_text() or "").strip() for p in article.select("p")]
        text = "\n".join([p for p in paras if p])

    if text.strip() and url not in SEEN_NB_ARTICLE_URLS:
        row = {
            "platform": "notebookcheck",
            "data_type": "review_article",
            "phone_model_id": phone_model_id,
            "search_kw": search_kw,
            "device_name": title,
            "url": url,
            "author": "",
            "time_str": "",
            "raw_text": text,
            "cleaned_text": text,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        append_row_to_csv(row)
        SEEN_NB_ARTICLE_URLS.add(url)
        print(f"         ✅ Notebookcheck 评测正文已写入 CSV （约 {len(text)} 字）")
    elif not text.strip():
        print("         ⚠️ 正文为空，跳过正文。")
    else:
        print("         ⏭ 正文已抓过，跳过正文写入。")

    # ------- 评论 -------
    comments_container = (
        soup.select_one("div.comments")
        or soup.select_one("div#comments")
        or soup.select_one("section.comments")
    )
    if not comments_container:
        print("         ℹ️ 未找到明显的评论容器（div.comments / #comments / section.comments）。")
        return

    comment_items = (
        comments_container.select(".comment")
        or comments_container.find_all("li")
        or comments_container.find_all("div")
    )
    print(f"         💬 疑似评论条目 {len(comment_items)} 个")

    written = 0
    for c in comment_items:
        if written >= MAX_COMMENTS_PER_REVIEW:
            break

        content_ele = (
            c.select_one(".comment_text")
            or c.select_one(".text")
            or c.select_one("p")
        )
        content = (content_ele.get_text() or "").strip() if content_ele else ""
        if not content:
            continue

        key = (url, content[:80])
        if key in SEEN_NB_COMMENT_KEYS:
            continue
        SEEN_NB_COMMENT_KEYS.add(key)

        author_ele = (
            c.select_one(".user")
            or c.select_one(".author")
            or c.select_one(".name")
        )
        author = (author_ele.get_text() or "").strip() if author_ele else ""

        time_ele = (
            c.select_one(".date")
            or c.select_one(".time")
        )
        time_str = (time_ele.get_text() or "").strip() if time_ele else ""

        row = {
            "platform": "notebookcheck",
            "data_type": "review_comment",
            "phone_model_id": phone_model_id,
            "search_kw": search_kw,
            "device_name": title,
            "url": url,
            "author": author,
            "time_str": time_str,
            "raw_text": content,
            "cleaned_text": content,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        append_row_to_csv(row)
        written += 1

    print(f"         ✅ Notebookcheck 评论本轮写入 {written} 条（去重后）")


# =========================
# 3. 仅 Notebookcheck：按机型循环
# =========================

def crawl_notebookcheck_only():
    print("🚀 开始【仅】抓取 Notebookcheck 评测")
    print(f"📁 数据写入: {CSV_FILENAME}")

    load_existing_progress()

    for idx, (model_key, keywords) in enumerate(config.TARGET_MODELS.items(), start=1):
        if not keywords:
            continue

        search_kw = keywords[0]
        print(f"\n================ 机型 {idx}: {model_key} ({search_kw}) ================")

        reviews = search_notebookcheck_reviews(search_kw, max_results=1)
        if not reviews:
            print("   ⚠️ Notebookcheck 未找到评测。")
        else:
            for title, url in reviews:
                crawl_notebookcheck_review(
                    title=title,
                    url=url,
                    phone_model_id=model_key,
                    search_kw=search_kw,
                )

    print("\n✅ Notebookcheck 抓取结束。")


if __name__ == "__main__":
    # 现在只跑 Notebookcheck，不跑 GSM
    crawl_notebookcheck_only()
