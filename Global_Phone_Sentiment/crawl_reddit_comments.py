import requests
import pandas as pd
import time
import random
from datetime import datetime
import os
import json

# ========= 配置区 =========

# 代理（如果不用代理，就改成 PROXIES = None）
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8"
}

# ✅ 这里已经帮你改成当前帖子 CSV 的名字
# 注意：我们会让你在 “ZDM+Reddit” 根目录下运行脚本，这样路径就是对的
POSTS_CSV = "data_reddit_20251206_103022.csv"

# 评论输出的新文件（在根目录下生成）
COMMENTS_CSV = f"data_reddit_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# 评论抓取进度文件（也在根目录）
COMMENTS_PROGRESS = "reddit_comments_progress.json"


# ========= 工具函数 =========

def append_comment_row(row: dict):
    """把一条评论写入到评论 CSV（实时追加）"""
    df = pd.DataFrame([row])
    file_exists = os.path.exists(COMMENTS_CSV)
    df.to_csv(
        COMMENTS_CSV,
        mode="a",
        index=False,
        encoding="utf-8-sig",
        header=not file_exists,
    )


def load_progress(num_posts: int) -> dict:
    """读取进度（处理到第几个帖子了）"""
    if not os.path.exists(COMMENTS_PROGRESS):
        return {"posts_csv": POSTS_CSV, "last_index": -1}

    try:
        with open(COMMENTS_PROGRESS, "r", encoding="utf-8") as f:
            p = json.load(f)
    except Exception:
        return {"posts_csv": POSTS_CSV, "last_index": -1}

    # 如果帖子 CSV 换了，就从头开始
    if p.get("posts_csv") != POSTS_CSV:
        return {"posts_csv": POSTS_CSV, "last_index": -1}

    last = p.get("last_index", -1)
    if not isinstance(last, int) or last >= num_posts:
        last = -1

    return {"posts_csv": POSTS_CSV, "last_index": last}


def save_progress(progress: dict):
    """保存进度"""
    with open(COMMENTS_PROGRESS, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_seen_comment_ids() -> set:
    """从历史评论 CSV 中读出已经保存过的评论 ID，避免重复"""
    seen = set()
    if os.path.exists(COMMENTS_CSV):
        try:
            df = pd.read_csv(COMMENTS_CSV, usecols=["source_id"])
            seen = set(df["source_id"].dropna().astype(str).tolist())
        except Exception as e:
            print(f"⚠️ 读取已有评论 CSV 失败（忽略，可能是第一次跑）: {e}")
    return seen


def fetch_comments_for_post(
    post_id: str,
    post_permalink: str,
    brand_id: str,
    phone_model_id: str,
    post_source_id: str,
    seen_comment_ids: set,
    max_comments: int = 50,
) -> int:
    """抓取某一个帖子下面的评论，返回本次新抓到的评论数量"""

    url = f"https://www.reddit.com/comments/{post_id}.json"

    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            proxies=PROXIES,
            params={"limit": max_comments, "sort": "top"},
        )
    except Exception as e:
        print(f"      ⚠️ 请求评论失败: {e}")
        return 0

    if resp.status_code != 200:
        print(f"      ⚠️ 请求评论失败 status={resp.status_code}")
        return 0

    try:
        data = resp.json()
    except Exception as e:
        print(f"      ⚠️ 解析评论 JSON 失败: {e}")
        return 0

    # comments 接口是一个 list，第 2 个元素才是评论树
    if not isinstance(data, list) or len(data) < 2:
        return 0

    comments_listing = data[1].get("data", {}).get("children", [])
    count_new = 0

    for item in comments_listing:
        # kind == t1 才是评论本体；t3 是帖子；more 是“更多评论”
        if item.get("kind") != "t1":
            continue

        c = item.get("data", {})
        body = (c.get("body") or "").strip()
        if not body:
            continue

        cid = c.get("id")
        if not cid:
            continue

        comment_source_id = f"reddit_comment_{cid}"
        if comment_source_id in seen_comment_ids:
            continue
        seen_comment_ids.add(comment_source_id)

        created_ts = c.get("created_utc")
        if created_ts:
            published_str = datetime.fromtimestamp(created_ts).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            published_str = ""

        comment_permalink = c.get("permalink")
        if comment_permalink:
            comment_url = "https://www.reddit.com" + comment_permalink
        else:
            comment_url = "https://www.reddit.com" + (post_permalink or "")

        # 多了 parent_source_id，方便跟帖子对应起来
        row = {
            "platform": "reddit",
            "source_id": comment_source_id,
            "source_type": "comment",
            "parent_source_id": post_source_id,
            "url": comment_url,
            "brand_id": brand_id,
            "phone_model_id": phone_model_id,
            "lang": "en",
            "published_at": published_str,
            "raw_text": body[:500],
            "cleaned_text": body[:500],
        }

        append_comment_row(row)
        count_new += 1

        if count_new >= max_comments:
            break

    return count_new


# ========= 主逻辑 =========

def main():
    # 1. 读帖子 CSV
    df_posts = pd.read_csv(POSTS_CSV)
    print(f"📄 从帖子 CSV 读取到 {len(df_posts)} 行数据（每行一个帖子）")

    # 2. 已有评论 ID，防止重复
    seen_comment_ids = load_seen_comment_ids()
    print(f"🔁 已从历史评论 CSV 读取 {len(seen_comment_ids)} 条评论 ID，避免重复")

    # 3. 进度（处理到第几个帖子）
    progress = load_progress(len(df_posts))
    last_index = progress["last_index"]
    print(f"⏩ 将从第 {last_index + 1} 行帖子开始抓评论")

    total_new_comments = 0

    for idx, row in enumerate(df_posts.itertuples()):
        if idx <= last_index:
            continue

        post_source_id = getattr(row, "source_id")
        # 帖子里是 reddit_{id} 这种形式
        post_id = str(post_source_id).replace("reddit_", "", 1)

        brand_id = getattr(row, "brand_id", "Other")
        phone_model_id = getattr(row, "phone_model_id", "")
        post_url = getattr(row, "url", "")
        post_permalink = post_url.replace("https://www.reddit.com", "")

        print(f"\n--- [{idx + 1}/{len(df_posts)}] 帖子 {post_source_id} ---")

        n = fetch_comments_for_post(
            post_id=post_id,
            post_permalink=post_permalink,
            brand_id=brand_id,
            phone_model_id=phone_model_id,
            post_source_id=post_source_id,
            seen_comment_ids=seen_comment_ids,
            max_comments=50,   # 每个帖子最多抓 50 条评论，需要的话可以改
        )

        print(f"      ✅ 新抓到评论 {n} 条")

        total_new_comments += n

        # 更新进度
        progress["last_index"] = idx
        save_progress(progress)

        # 歇一会儿，防止 429
        time.sleep(random.uniform(1, 2.5))

    print(f"\n🎉 完成！本次共新增评论 {total_new_comments} 条，已写入 {COMMENTS_CSV}")


if __name__ == "__main__":
    main()
