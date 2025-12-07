import requests
import pandas as pd
import time
import random
from datetime import datetime
import os
import json

import config

# 代理设置
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

# 进度文件
PROGRESS_FILENAME = "reddit_progress.json"

# 本次运行使用的全局 CSV 文件名（会在 init_run 里初始化）
CSV_FILENAME = None


def save_progress(progress: dict):
    """把进度写入到本地 JSON 文件"""
    try:
        with open(PROGRESS_FILENAME, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存进度失败: {e}")


def init_run():
    """
    初始化本次运行的 CSV 文件名和进度：
    - 如果发现有未完成的进度文件，且对应 CSV 还在，则继续上次的位置；
    - 否则新建一个 CSV 和进度文件。
    """
    global CSV_FILENAME

    progress = {}
    if os.path.exists(PROGRESS_FILENAME):
        try:
            with open(PROGRESS_FILENAME, "r", encoding="utf-8") as f:
                progress = json.load(f)
        except Exception as e:
            print(f"⚠️ 读取进度文件失败，将重新开始: {e}")
            progress = {}

    csv_from_progress = progress.get("csv_filename")
    models_state = progress.get("models", {}) or {}

    # 判断是否还有模型未完成（包括 progress 中没有记录的型号）
    has_incomplete = False
    if models_state:
        for model_key in config.TARGET_MODELS.keys():
            state = models_state.get(model_key)
            if not state or not state.get("completed"):
                has_incomplete = True
                break

    if csv_from_progress and os.path.exists(csv_from_progress) and has_incomplete:
        # 续跑
        CSV_FILENAME = csv_from_progress
        print(f"🔄 检测到未完成的任务，将继续写入: {CSV_FILENAME}")
        progress.setdefault("models", models_state)
        return progress

    # 否则开启一个新的任务
    CSV_FILENAME = f"data_reddit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    progress = {
        "csv_filename": CSV_FILENAME,
        "models": {}
    }
    save_progress(progress)
    print(f"🆕 开始新的抓取任务，本次数据将写入: {CSV_FILENAME}")
    return progress


def append_row_to_csv(row: dict):
    """把一条记录追加写入到 CSV，文件不存在时写表头（实时写盘）"""
    if CSV_FILENAME is None:
        raise RuntimeError("CSV_FILENAME 尚未初始化，请先调用 init_run()")

    df = pd.DataFrame([row])
    file_exists = os.path.exists(CSV_FILENAME)
    df.to_csv(
        CSV_FILENAME,
        mode="a",                # 追加写入
        index=False,
        encoding="utf-8-sig",
        header=not file_exists,  # 只有第一次写入才写表头
    )


def load_seen_ids_from_csv() -> set:
    """从已有 CSV 中把已经抓过的 source_id 读出来，避免多次运行产生重复"""
    seen_ids = set()
    if CSV_FILENAME and os.path.exists(CSV_FILENAME):
        try:
            df_exist = pd.read_csv(CSV_FILENAME, usecols=["source_id"])
            seen_ids = set(df_exist["source_id"].dropna().astype(str).tolist())
            print(f"🔁 已从历史 CSV 加载 {len(seen_ids)} 条 source_id，避免重复。")
        except Exception as e:
            print(f"⚠️ 读取历史 CSV 失败，可能会产生少量重复数据: {e}")
    return seen_ids


def crawl_reddit_by_model():
    # 初始化本次运行（决定是否续跑 & CSV 文件名）
    progress = init_run()
    models_state = progress.get("models", {})
    all_data = []

    # 读取历史 CSV 中的 source_id，跨多次运行去重
    seen_ids = load_seen_ids_from_csv()

    # 模拟更真实的浏览器头
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,*/*;q=0.8"
    }

    print(f"🚀 开始抓取 Reddit，共 {len(config.TARGET_MODELS)} 个具体机型...")
    print(f"📁 数据将实时写入: {CSV_FILENAME}")

    for model_key, keywords in config.TARGET_MODELS.items():
        if not keywords:
            continue

        # 读出该型号的历史进度（如果有）
        state = models_state.get(model_key, {})
        if state.get("completed"):
            print(f"\n--- 型号: {model_key} 已完成，跳过 ---")
            continue

        after_token = state.get("after_token")  # 上次停留的 after
        current_page = state.get("current_page", 0)
        search_term = keywords[0]

        if current_page > 0:
            print(f"\n--- 继续型号: {model_key} ({search_term}) "
                  f"从第 {current_page + 1} 页开始 ---")
        else:
            print(f"\n--- 正在搜索型号: {model_key} ({search_term}) ---")

        # --- 翻页配置 ---
        max_pages = 5  # 每个型号最多抓几页（防止死循环）

        while current_page < max_pages:
            try:
                # 构造参数：limit=100 (最大值), after=翻页标记
                params = {
                    "q": search_term,
                    "limit": 100,        # 每页最多 100 条
                    "sort": "new",
                    "type": "link",
                    "after": after_token  # 告诉 Reddit 我要看下一页
                }

                resp = requests.get(
                    "https://www.reddit.com/search.json",
                    headers=headers,
                    params=params,
                    timeout=15,
                    proxies=PROXIES,
                )

                if resp.status_code != 200:
                    print(
                        f"⚠️ 第 {current_page + 1} 页请求失败 "
                        f"({resp.status_code})，跳过该型号剩余页..."
                    )
                    break  # 这一页挂了就停下，防止死循环请求

                data = resp.json()
                children = data.get("data", {}).get("children", [])

                if not children:
                    print(f"   第 {current_page + 1} 页无数据，停止翻页。")
                    # 该型号视为完成
                    models_state[model_key] = {
                        "after_token": None,
                        "current_page": current_page,
                        "completed": True,
                    }
                    progress["models"] = models_state
                    save_progress(progress)
                    break

                print(f"   ✅ 第 {current_page + 1} 页抓取到 {len(children)} 条 raw 数据")

                # 处理数据
                for post in children:
                    p = post.get("data", {})
                    title = p.get("title", "") or ""
                    selftext = p.get("selftext", "") or ""
                    full_text = f"{title} {selftext}"

                    # 匹配关键词
                    if not any(kw.lower() in full_text.lower() for kw in keywords):
                        continue

                    # 组装唯一 ID
                    post_id = p.get("id")
                    if not post_id:
                        continue
                    source_id = f"reddit_{post_id}"

                    # 去重（跨多次运行）
                    if source_id in seen_ids:
                        continue
                    seen_ids.add(source_id)

                    # 匹配品牌
                    brand_name = "Other"
                    for b_code, b_name in config.BRANDS.items():
                        if b_code in model_key:
                            brand_name = b_name
                            break

                    # 时间戳转时间
                    created_ts = p.get("created_utc")
                    if created_ts:
                        published_str = datetime.fromtimestamp(
                            created_ts
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        published_str = ""

                    row = {
                        "platform": "reddit",
                        "source_id": source_id,
                        "source_type": "post",
                        "url": f"https://www.reddit.com{p.get('permalink', '')}",
                        "brand_id": brand_name,
                        "phone_model_id": model_key,
                        "lang": "en",
                        "published_at": published_str,
                        "raw_text": f"{title}\n{selftext[:500]}",
                        "cleaned_text": title,
                    }

                    # 内存里存一份，方便统计
                    all_data.append(row)
                    # 立刻写入 CSV（实时存）
                    append_row_to_csv(row)

                # 获取下一页的标记
                after_token = data.get("data", {}).get("after")
                current_page += 1

                # 更新该型号的进度（中止自动存）
                completed = not after_token or current_page >= max_pages
                models_state[model_key] = {
                    "after_token": after_token,
                    "current_page": current_page,
                    "completed": completed,
                }
                progress["models"] = models_state
                save_progress(progress)

                # 如果没有 after token，说明没有下一页了
                if not after_token:
                    print("   没有更多页面了。")
                    break

                # 翻页之间必须休息，Reddit 容易 429 Too Many Requests
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                print(f"❌ 抓取出错: {e}")
                # 出错时也保存当前的进度（已在上一次成功页保存过）
                break  # 出错跳出当前型号循环

    # 结束统计
    if all_data:
        print(
            f"\n✅ Reddit 抓取完成/本次运行结束！本次新增 {len(all_data)} 条有效数据，"
            f"已追加保存到 {CSV_FILENAME}"
        )
    else:
        print("⚠️ 本次运行未抓取到新数据（可能是全部都已经在历史 CSV 中）。")


if __name__ == "__main__":
    try:
        crawl_reddit_by_model()
    except KeyboardInterrupt:
        print("\n🛑 手动中止抓取，进度和已抓取数据已经保存（可下次继续运行续爬）。")
