from DrissionPage import ChromiumPage, ChromiumOptions
import pandas as pd
import time
import random
from datetime import datetime
import urllib.parse
import re
import os

import config

# 每个机型最多翻多少页
MAX_PAGES_PER_MODEL = 5

# 每个机型最多抓多少篇帖子，防止太多数据和无限翻页
MAX_POSTS_PER_MODEL = 80

# 每篇帖子最多抓多少条评论
MAX_COMMENTS_PER_POST = 30

# 固定 CSV 文件名，方便多次运行往同一个文件里续写和断点续爬
CSV_FILENAME = "data_smzdm.csv"


def append_row_to_csv(row: dict):
    """把一条记录追加写入到 CSV，文件不存在时写表头"""
    df = pd.DataFrame([row])
    file_exists = os.path.exists(CSV_FILENAME)
    df.to_csv(
        CSV_FILENAME,
        mode="a",                # 追加写入
        index=False,
        encoding="utf-8-sig",
        header=not file_exists,  # 只有第一次写入才写表头
    )


def _extract_first_int(text: str, keyword: str):
    """从类似 '18点赞 5收藏 3评论' 文本里提取数字，找不到返回 None"""
    if not text:
        return None
    try:
        m = re.search(rf'{keyword}\D*(\d+)', text)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def crawl_post_detail(page: ChromiumPage, post_url: str, base_row: dict):
    """
    进入帖子详情页，抓取：
    - 点赞数 / 收藏数 / 评论总数（如果能解析到）
    - 前 MAX_COMMENTS_PER_POST 条评论
    """
    like_count = None
    fav_count = None
    comment_count = None
    comment_rows = []

    try:
        # 新开 tab 抓详情页，避免把列表页搞丢
        tab = page.new_tab(url=post_url)
    except Exception as e:
        print(f"         ⚠️ 打开详情页失败: {e}")
        return like_count, fav_count, comment_count, comment_rows

    try:
        # 等页面加载完一点
        time.sleep(random.uniform(1.0, 1.8))

        # --- 1. 点赞 / 收藏 / 评论数 ---
        try:
            # 这块选择器可能需要你根据实际页面微调一下
            meta_block = (
                tab.ele('css:.article-meta')  # 常见信息栏
                or tab.ele('css:.article-info')
                or tab.ele('xpath://*[contains(text(),"点赞") and contains(text(),"收藏")]')
            )
            if meta_block:
                meta_text = meta_block.text
                like_count = _extract_first_int(meta_text, '点赞')
                fav_count = _extract_first_int(meta_text, '收藏')
                comment_count = _extract_first_int(meta_text, '评论')
        except Exception:
            pass

        # --- 2. 评论内容 ---
        try:
            # 评论区容器（class 名不一样就改这里）
            comment_container = (
                tab.ele('css:.comment-list')
                or tab.ele('css:.comment_list')
                or tab.ele('css:#commentTabBlock')
            )
            if comment_container:
                items = comment_container.eles('tag:li') or comment_container.eles('css:.comment-item')
            else:
                items = []

            for idx, c in enumerate(items):
                if idx >= MAX_COMMENTS_PER_POST:
                    break

                content_ele = (
                    c.ele('css:.comment_con')
                    or c.ele('css:.comment_content')
                    or c.ele('tag:p')
                )
                if not content_ele:
                    continue

                content = (content_ele.text or '').strip()
                if not content:
                    continue

                author_ele = (
                    c.ele('css:.user-name')
                    or c.ele('css:.user_name')
                    or c.ele('xpath:.//a[contains(@href,"zhiyou.smzdm.com")]')
                )
                author = (author_ele.text or '').strip() if author_ele else ''

                time_ele = c.ele('css:.time') or c.ele('css:.comment_time')
                comment_time = (time_ele.text or '').strip() if time_ele else ''

                like_ele = (
                    c.ele('css:.comment_love')
                    or c.ele('css:.J_ding')
                    or c.ele('css:.like-count')
                )
                like_text = (like_ele.text or '').strip() if like_ele else ''
                try:
                    comment_like = int(''.join(ch for ch in like_text if ch.isdigit())) if like_text else 0
                except ValueError:
                    comment_like = 0

                row = {
                    **base_row,
                    "source_id": f"{base_row['source_id']}_c{idx}",
                    "data_type": "comment",
                    "url": post_url,  # 评论还是挂在帖子 URL 下面
                    "raw_text": f"[评论] {content}",
                    "cleaned_text": content,
                    "comment_author": author,
                    "comment_time": comment_time,
                    "comment_like": comment_like,
                }
                comment_rows.append(row)
        except Exception:
            pass

    finally:
        try:
            tab.close()
        except Exception:
            pass

    return like_count, fav_count, comment_count, comment_rows


def crawl_smzdm_by_model():
    """
    支持：
      1. 实时存：每抓完一条就 append_row_to_csv()
      2. 断点续爬：如果已存在 data_smzdm.csv，则：
         - 跳过其中已经出现过的 url
         - 按每个机型已经抓过的帖子数继续往后抓
    """
    # --- 1. 读取历史进度（如果有旧的 CSV） ---
    seen_urls = set()              # 已经抓过的帖子 URL（用于去重 + 断点续爬）
    posts_done_per_model = {}      # 每个机型已经抓过多少 “帖子”（data_type == 'post'）

    total_posts = 0                # 所有机型的帖子数
    total_comments = 0             # 所有机型的评论数
    total_rows = 0                 # CSV 中总记录数（帖子 + 评论）

    if os.path.exists(CSV_FILENAME):
        try:
            old_df = pd.read_csv(CSV_FILENAME)

            # 所有已经抓过的 URL（帖子和评论都挂在帖子 URL 下）
            if "url" in old_df.columns:
                seen_urls = set(old_df["url"].dropna().unique())

            # 每个机型已经抓过多少篇“帖子”
            if {"data_type", "phone_model_id", "url"}.issubset(old_df.columns):
                posts_done_per_model = (
                    old_df[old_df["data_type"] == "post"]
                    .groupby("phone_model_id")["url"]
                    .nunique()
                    .to_dict()
                )

            # 统计总帖子数和总评论数（仅用于打印日志）
            if "data_type" in old_df.columns:
                total_posts = (
                    old_df[old_df["data_type"] == "post"]["url"]
                    .dropna()
                    .nunique()
                )
                total_comments = (old_df["data_type"] == "comment").sum()

            total_rows = len(old_df)

            print(f"📂 检测到已有历史文件 {CSV_FILENAME}，")
            print(f"   已抓帖子 {total_posts} 篇，评论 {total_comments} 条，总记录 {total_rows} 行。")
            print(f"   后续将跳过这些 URL，继续往后抓。")
        except Exception as e:
            print(f"⚠️ 读取历史 CSV 失败，不启用断点续爬逻辑: {e}")
    else:
        print(f"📁 未发现历史文件，将从头开始抓取并写入 {CSV_FILENAME}")

    # --- 2. 浏览器配置 ---
    co = ChromiumOptions()
    co.set_local_port(9333)
    co.set_user_data_path(r'./tmp_browser_data')
    page = ChromiumPage(addr_or_opts=co)

    print("🚀 开始抓取什么值得买 (综合搜索-含好价，帖子+评论)...")
    print(f"📁 数据会实时追加写入: {CSV_FILENAME}")

    # --- 3. 按机型循环 ---
    for model_idx, (model_key, keywords) in enumerate(config.TARGET_MODELS.items(), start=1):
        if not keywords:
            continue

        # 这个机型已经在历史数据中抓过多少帖子
        posts_this_model = posts_done_per_model.get(model_key, 0)

        # 如果之前已经达到上限，整机型直接跳过
        if posts_this_model >= MAX_POSTS_PER_MODEL:
            print(
                f"\n================ 机型 {model_idx}: {model_key} 已在历史记录中达到上限 "
                f"{MAX_POSTS_PER_MODEL} 篇，跳过该机型 ================"
            )
            continue

        search_kw = keywords[0]
        encoded_kw = urllib.parse.quote_plus(search_kw)
        base_url = f"https://search.smzdm.com/?c=home&s={encoded_kw}&v=b&mx_v=b"

        print(
            f"\n================ 机型 {model_idx}: {model_key} ({search_kw}) ================"
        )
        print(
            f"   （历史已抓 {posts_this_model} 篇，本轮继续往后抓，最多到 {MAX_POSTS_PER_MODEL} 篇）"
        )

        # --- 4. 翻页 ---
        for page_num in range(1, MAX_PAGES_PER_MODEL + 1):
            if posts_this_model >= MAX_POSTS_PER_MODEL:
                print(f"   ⛔ 本机型帖子数达到上限 {MAX_POSTS_PER_MODEL}，停止翻页。")
                break

            url = f"{base_url}&p={page_num}"
            print(f"\n   👉 第 {page_num} 页 -> {url}")

            try:
                page.get(url)

                # 等列表出来
                try:
                    page.ele('#feed-main-list', timeout=8)
                except Exception:
                    print("      ⚠️ 找不到列表容器，可能已经没有更多页面了。")
                    break

                # 触发懒加载
                page.scroll.to_bottom()
                time.sleep(random.uniform(1.0, 1.5))

                ul = page.ele('#feed-main-list')
                items = ul.eles('tag:li') if ul else []

                # 兜底 selector
                if not items:
                    items = page.eles('css:div.feed-main-con ul#feed-main-list li')
                if not items:
                    items = page.eles('css:.feed-list-hits li')
                if not items:
                    items = page.eles('css:.feed-list-new li')

                print(f"      ✅ 本页发现 {len(items)} 条内容（原始 DOM）")

                if not items:
                    print("      ⛔ 本页无内容，结束该机型翻页。")
                    break

                # --- 5. 遍历列表里的每一条内容 ---
                for item in items:
                    if posts_this_model >= MAX_POSTS_PER_MODEL:
                        print(f"      ⛔ 本机型帖子数达到上限 {MAX_POSTS_PER_MODEL}，停止本页剩余项目。")
                        break

                    try:
                        # 标题 & 链接
                        title_ele = (
                            item.ele('css:h5.feed-block-title a')
                            or item.ele('css:h5 a')
                            or item.ele('tag:a')
                        )
                        if not title_ele:
                            continue

                        title = (title_ele.text or '').strip()
                        if not title:
                            continue

                        link = title_ele.attr('href')
                        if not link:
                            continue

                        # === 断点续爬关键：这个 URL 已经在历史 CSV 里出现过，就直接跳过 ===
                        if link in seen_urls:
                            # print(f"         ⏭ 已抓过，跳过: {title[:30]}...")
                            continue

                        # 没抓过的新 URL：加入已抓集合
                        seen_urls.add(link)

                        # 列表页尝试拿价格
                        price_ele = (
                            item.ele('css:.z-highlight')
                            or item.ele('css:span[class*="price"]')
                            or item.ele('css:div[class*="price"]')
                        )
                        price = (price_ele.text or '').strip() if price_ele else None

                        # 列表页的附加信息（时间、来源、热度等）
                        extra_ele = (
                            item.ele('css:.feed-block-extras')
                            or item.ele('css:.z-feed-foot')
                        )
                        extra_info = (extra_ele.text or '').strip() if extra_ele else ''

                        source_id = f"smzdm_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

                        base_row = {
                            "platform": "smzdm",
                            "source_id": source_id,
                            "url": link,
                            "phone_model_id": model_key,
                            "data_type": "post",
                            "raw_text": f"【价格: {price or '无'}】 {title} ({extra_info})",
                            "cleaned_text": title,
                            "search_kw": search_kw,
                            "created_at": datetime.now().isoformat(timespec="seconds"),
                        }

                        print(f"         📰 帖子: {title[:40]}...  |  价格: {price or '无'}")

                        # 详情页：互动 + 评论
                        like_count, fav_count, comment_count, comment_rows = crawl_post_detail(
                            page, link, base_row
                        )

                        base_row["like_count"] = like_count if like_count is not None else 0
                        base_row["fav_count"] = fav_count if fav_count is not None else 0
                        base_row["comment_count"] = (
                            comment_count if comment_count is not None else len(comment_rows)
                        )

                        # 记录帖子 —— 实时写入 CSV
                        append_row_to_csv(base_row)
                        total_posts += 1
                        total_rows += 1

                        # 记录评论 —— 实时写入 CSV
                        for cr in comment_rows:
                            append_row_to_csv(cr)
                            total_comments += 1
                            total_rows += 1

                        posts_this_model += 1

                        print(
                            f"         ✅ 已抓帖子 {posts_this_model} 篇(本机型), "
                            f"本帖评论 {len(comment_rows)} 条, "
                            f"👍 {base_row['like_count']} | ⭐ {base_row['fav_count']} | 💬 {base_row['comment_count']}"
                        )

                        # 每个帖子之间也稍微等一下，降低压力
                        time.sleep(random.uniform(0.6, 1.2))

                    except Exception as e:
                        print(f"         ⚠️ 解析单条出错: {e}")
                        continue

                # 每翻一页歇一下，防止被封
                time.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                print(f"      ❌ 第 {page_num} 页出错: {e}")
                break

        print(
            f"   📊 机型 {model_key} 完成累计：帖子 {posts_this_model} 篇，"
            f"评论累计 {total_comments} 条（所有机型总和）。"
        )

    # --- 6. 结束统计 ---
    if total_rows > 0:
        print(
            f"\n✅ 抓取结束 / 当前状态：共帖子 {total_posts} 篇，评论 {total_comments} 条，"
            f"总记录数 {total_rows}，已保存为 {CSV_FILENAME}"
        )
    else:
        print("\n⚠️ 没有抓到任何数据，请检查网页结构或选择器。")


if __name__ == "__main__":
    crawl_smzdm_by_model()
