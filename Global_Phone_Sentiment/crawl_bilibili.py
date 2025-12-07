import os
import time
import random
import re
from datetime import datetime

import requests
import pandas as pd

import config

# =========================
# 基本配置
# =========================

# ✅ 新文件名，避免跟之前跑的混在一起
CSV_FILENAME = "data_bilibili_v2.csv"

MAX_VIDEOS_PER_MODEL = 30      # 每个机型最多抓多少视频
MAX_COMMENTS_PER_VIDEO = 30    # 每个视频最多抓多少条评论（前 30 条热门）

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

# ===== 登录 Cookie（从 DevTools 里复制过来的那一整段 value）=====
# ⚠️ 注意：这里包含你的登陆身份信息，请不要把这个文件对外分享
BILIBILI_COOKIE = (
    "buvid3=BB9B4F7D-4802-694D-0B40-E1566BBFCFBC76161infoc; "
    "b_nut=1764996576; "
    "b_lsid=26B6565C_19AF1FE7B85; "
    "_uuid=C2994A510-5B54-EBB10-110E7-817FF55CF9EE78194infoc; "
    "buvid_fp=53a1d05875fd5fffd24ee2833f7add7d; "
    "buvid4=24CDD821-3713-9F04-4E63-07A76666E51C78607-025120612-BAMKQ6YEN+Yk2N6xTwm3yw%3D%3D; "
    "CURRENT_QUALITY=0; "
    "bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjUyNTU3ODIsImlhdCI6MTc2NDk5NjUyMiwicGx0IjotMX0.9dnIDJIEPN6kLiGCP-AjNppZ-98APwvd4Sku4g2_q4Q; "
    "bili_ticket_expires=1765255722; "
    "rpdid=|(J~R~JJ)m)R0J'u~YRmmYl)J; "
    "CURRENT_FNVAL=2000; "
    "SESSDATA=33b95b9b%2C1780550431%2C26c95%2Ac2CjD5WfQg3mcRJQFLjwlJ8xEwmMk5lu44DtxH6HkKtjIr1w9icmxn_Vh6cfVtIY1RBgkSVkRDNzkxaC1IajFCM2FWcl9KZGc1bDlMTEhXSTVrLUgzbnQxMUozbmpHYnl6cFc3Rjh4ci10cGZMNXdUUFVQaDJYQlpGSEVub0k2VEowS1pMaE5VaC1nIIEC; "
    "bili_jct=7d690342832787b86a8a378b8c8620ac; "
    "DedeUserID=38638790; "
    "DedeUserID__ckMd5=ecf9c0bc13c38c69; "
    "sid=gxpnozgm; "
    "bp_t_offset_38638790=1143148684481921024; "
    "theme-tip-show=SHOWED"
)

if BILIBILI_COOKIE:
    HEADERS["Cookie"] = BILIBILI_COOKIE

# 搜索 / 详情 / 评论 API
SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
VIEW_API = "https://api.bilibili.com/x/web-interface/view"
REPLY_API = "https://api.bilibili.com/x/v2/reply/main"

# BV 号正则
BVID_RE = re.compile(r"BV[0-9A-Za-z]{10}")


# =========================
# 工具函数：CSV 追加 & 请求
# =========================

def append_row_to_csv(row: dict):
    """把一条记录实时追加写入 CSV，文件不存在时自动写表头"""
    df = pd.DataFrame([row])
    file_exists = os.path.exists(CSV_FILENAME)
    df.to_csv(
        CSV_FILENAME,
        mode="a",
        index=False,
        encoding="utf-8-sig",
        header=not file_exists,
    )


def get_json(url: str, params: dict = None, sleep_range=(0.3, 0.8)):
    """简易 GET JSON（用于 B 站 API）"""
    for i in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code == 200:
                time.sleep(random.uniform(*sleep_range))
                return resp.json()
            else:
                print(f"   ⚠️ API {url} 返回 {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ API {url} 出错: {e}")
        time.sleep(1.0 + i)
    return None


# =========================
# 断点续跑：从 CSV 里恢复进度
# =========================

SEEN_VIDEO_URLS = set()       # 已经抓过的视频 URL
VIDEOS_DONE_PER_MODEL = {}    # 每个机型已经抓过多少条视频


def load_existing_progress():
    """从历史 CSV 恢复去重 & 每机型已抓视频数"""
    global SEEN_VIDEO_URLS, VIDEOS_DONE_PER_MODEL

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

    if "url" in df.columns and "data_type" in df.columns:
        video_df = df[df["data_type"] == "video"].copy()
        SEEN_VIDEO_URLS = set(video_df["url"].dropna().unique())

        if {"phone_model_id", "url"}.issubset(video_df.columns):
            VIDEOS_DONE_PER_MODEL = (
                video_df.groupby("phone_model_id")["url"]
                .nunique()
                .to_dict()
            )

        print(f"   🔁 已有视频 {len(SEEN_VIDEO_URLS)} 条，"
              f"{len(VIDEOS_DONE_PER_MODEL)} 个机型有历史记录。")


# =========================
# 1. 搜索列表页（搜索 API）
# =========================

def parse_play_count(text: str) -> int:
    """把 B 站的播放量字符串 (例：'29.5万') 转成整数"""
    if text is None:
        return 0
    if isinstance(text, (int, float)):
        return int(text)
    text = str(text).strip()
    try:
        if text.endswith("万"):
            return int(float(text[:-1]) * 10000)
        if text.endswith("亿"):
            return int(float(text[:-1]) * 100000000)
        return int("".join(ch for ch in text if ch.isdigit()))
    except Exception:
        return 0


TAG_RE = re.compile(r"<.*?>")


def strip_html_tags(s: str) -> str:
    if not s:
        return ""
    return TAG_RE.sub("", s)


def search_bilibili_videos(search_kw: str, page_no: int):
    """
    用 B 站搜索 API 按关键词查视频，返回本页的视频信息列表：
    [ {title, url, bvid, up_name, play_str, pubtime_str}, ... ]
    """
    params = {
        "search_type": "video",
        "keyword": search_kw,
        "page": page_no,
    }
    print(f"\n   👉 第 {page_no} 页搜索(API)：{SEARCH_API}  keyword={search_kw}")
    data = get_json(SEARCH_API, params=params)
    if not data:
        print("   ⚠️ 搜索 API 无响应。")
        return []
    if data.get("code") != 0:
        print(f"   ⚠️ 搜索 API 返回错误 code={data.get('code')} msg={data.get('message')}")
        return []

    d = data.get("data") or {}
    results_raw = d.get("result") or []
    print(f"   🔎 搜索 API 返回结果数：{len(results_raw)}")

    results = []
    for item in results_raw:
        title_html = item.get("title") or ""
        title = strip_html_tags(title_html).strip()

        url = item.get("arcurl") or ""
        bvid = item.get("bvid") or ""

        if not url and bvid:
            url = f"https://www.bilibili.com/video/{bvid}"

        if not url or not title:
            continue

        up_name = (item.get("author") or "").strip()

        play_raw = item.get("play")
        play_str = str(play_raw) if play_raw is not None else ""

        pub_ts = item.get("pubtime") or item.get("pubdate")
        if isinstance(pub_ts, (int, float)) and pub_ts > 0:
            try:
                pubtime_str = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pubtime_str = ""
        else:
            pubtime_str = ""

        results.append(
            {
                "title": title,
                "url": url,
                "bvid": bvid,
                "up_name": up_name,
                "play_str": play_str,
                "pubtime_str": pubtime_str,
            }
        )

    return results


# =========================
# 2. B 站评论接口：view + reply/main
# =========================

def extract_bvid(url: str):
    """从视频 URL 中抽出 BV 号（兜底）"""
    if not url:
        return None
    m = BVID_RE.search(url)
    if m:
        return m.group(0)
    return None


def fetch_aid_from_bvid(bvid: str):
    """通过 bvid 调用 view 接口拿 aid"""
    params = {"bvid": bvid}
    data = get_json(VIEW_API, params=params)
    if not data or data.get("code") != 0:
        return None
    try:
        return int(data["data"]["aid"])
    except Exception:
        return None


def fetch_comments_by_api(bvid: str, max_comments: int = 30):
    """
    调用 B 站评论 API，按“热度”拿前 max_comments 条评论。
    """
    aid = fetch_aid_from_bvid(bvid)
    if not aid:
        print(f"      ⚠️ 无法获取 aid，bvid={bvid}")
        return []

    comments = []
    page_no = 1
    page_size = 30  # API 单页最多 30

    while True:
        if max_comments is not None and len(comments) >= max_comments:
            break

        params = {
            "type": 1,       # 1 = 视频
            "oid": aid,
            "mode": 3,       # 3 = 按热度排序
            "ps": page_size,
            "pn": page_no,
        }
        print(f"      💬 拉取评论第 {page_no} 页，当前已有 {len(comments)} 条...")
        data = get_json(REPLY_API, params=params, sleep_range=(0.3, 0.7))
        if not data or data.get("code") != 0:
            print(f"      ⚠️ 评论 API 返回异常，code={data.get('code') if data else 'N/A'}")
            break

        d = data.get("data") or {}
        replies = d.get("replies") or []
        if not replies:
            break

        for rep in replies:
            if max_comments is not None and len(comments) >= max_comments:
                break

            content = ((rep.get("content") or {}).get("message") or "").strip()
            if not content:
                continue

            member = rep.get("member") or {}
            uname = (member.get("uname") or "").strip()

            like = int(rep.get("like") or 0)
            ctime = int(rep.get("ctime") or 0)
            try:
                comment_time = datetime.fromtimestamp(ctime).isoformat(timespec="seconds")
            except Exception:
                comment_time = ""

            comments.append(
                {
                    "author": uname,
                    "comment_time": comment_time,
                    "comment_like": like,
                    "content": content,
                }
            )

        # 本页数量不足 page_size，说明已经到底了
        if len(replies) < page_size:
            break

        page_no += 1

    return comments


# =========================
# 3. 主流程：按机型抓 B 站
# =========================

def crawl_bilibili_by_model():
    print("🚀 开始抓取 B 站（每机型最多 30 个视频 + 每视频前 30 条评论）")
    print(f"📁 数据会实时写入: {CSV_FILENAME}")

    load_existing_progress()

    total_videos = 0
    total_comments = 0
    total_rows = 0

    # 统计已有（方便打印总量）
    if os.path.exists(CSV_FILENAME):
        try:
            df_old = pd.read_csv(CSV_FILENAME)
            total_rows = len(df_old)
            if "data_type" in df_old.columns:
                total_videos = (
                    df_old[df_old["data_type"] == "video"]["url"]
                    .dropna()
                    .nunique()
                )
                total_comments = (df_old["data_type"] == "comment").sum()
        except Exception:
            pass

    # 逐个机型
    for idx, (model_key, keywords) in enumerate(config.TARGET_MODELS.items(), start=1):
        if not keywords:
            continue

        search_kw = keywords[0]
        videos_this_model = int(VIDEOS_DONE_PER_MODEL.get(model_key, 0))

        print(
            f"\n================ 机型 {idx}: {model_key} ({search_kw}) ================"
        )
        print(f"   （历史已抓 {videos_this_model} 个视频，本轮上限 {MAX_VIDEOS_PER_MODEL} 个）")

        if videos_this_model >= MAX_VIDEOS_PER_MODEL:
            print(f"   ⛔ 该机型历史视频数已达上限 {MAX_VIDEOS_PER_MODEL}，跳过。")
            continue

        # 只要没够 30 个视频，就一页一页往后翻，直到搜索结果空
        page_no = 1
        while videos_this_model < MAX_VIDEOS_PER_MODEL:
            videos = search_bilibili_videos(search_kw, page_no)
            if not videos:
                print("   ⛔ 本页无搜索结果，结束该机型。")
                break

            print(f"   ✅ 第 {page_no} 页共 {len(videos)} 条搜索结果。")

            for vid in videos:
                if videos_this_model >= MAX_VIDEOS_PER_MODEL:
                    break

                url = vid["url"]
                title = vid["title"]

                # 断点续爬：已经抓过的视频直接跳过
                if url in SEEN_VIDEO_URLS:
                    continue
                SEEN_VIDEO_URLS.add(url)

                play_count = parse_play_count(vid["play_str"])

                source_id = f"bilibili_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

                base_row = {
                    "platform": "bilibili",
                    "source_id": source_id,
                    "url": url,
                    "phone_model_id": model_key,
                    "data_type": "video",
                    "raw_text": f"[UP: {vid['up_name'] or '未知'}][播放: {vid['play_str'] or '无'}]"
                                f"[时间: {vid['pubtime_str'] or '无'}] {title}",
                    "cleaned_text": title,
                    "search_kw": search_kw,
                    "up_name": vid["up_name"],
                    "play_str": vid["play_str"],
                    "play_count": play_count,
                    "pubtime_str": vid["pubtime_str"],
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }

                print(
                    f"   🎬 视频: {title[:50]}... | UP: {vid['up_name'] or '未知'} | 播放: {vid['play_str'] or '无'}"
                )

                # ---- 评论：用 API 抓前 30 条 ----
                bvid = vid.get("bvid") or extract_bvid(url)
                comment_rows = []
                if bvid:
                    comments = fetch_comments_by_api(bvid, MAX_COMMENTS_PER_VIDEO)
                    for c_idx, c in enumerate(comments):
                        row = {
                            **base_row,
                            "source_id": f"{source_id}_c{c_idx}",
                            "data_type": "comment",
                            "raw_text": f"[评论] {c['content']}",
                            "cleaned_text": c["content"],
                            "comment_author": c["author"],
                            "comment_time": c["comment_time"],
                            "comment_like": c["comment_like"],
                        }
                        comment_rows.append(row)
                else:
                    print(f"      ⚠️ 无法从 URL 中解析出 bvid: {url}")

                # 先写视频行
                append_row_to_csv(base_row)
                total_videos += 1
                total_rows += 1
                videos_this_model += 1

                # 再写评论行
                for cr in comment_rows:
                    append_row_to_csv(cr)
                    total_comments += 1
                    total_rows += 1

                print(
                    f"      ✅ 已写入视频 1 条，本视频评论 {len(comment_rows)} 条，"
                    f"本机型累计视频 {videos_this_model} 条，所有机型总评论 {total_comments} 条。"
                )

                # 视频之间休息一下，别把接口打爆
                time.sleep(random.uniform(0.5, 1.0))

            page_no += 1
            # 翻页之间也歇一下
            time.sleep(random.uniform(0.8, 1.5))

        print(
            f"   📊 机型 {model_key} 完成累计：视频 {videos_this_model} 条，"
            f"所有机型总评论 {total_comments} 条。"
        )

    if total_rows > 0:
        print(
            f"\n✅ 抓取结束 / 当前状态：共视频 {total_videos} 条，评论 {total_comments} 条，"
            f"总记录数 {total_rows}，已保存为 {CSV_FILENAME}"
        )
    else:
        print("\n⚠️ 没有抓到任何数据，请检查网络或选择器。")


if __name__ == "__main__":
    crawl_bilibili_by_model()
