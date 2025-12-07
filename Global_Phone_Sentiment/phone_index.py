from __future__ import annotations

"""
phone_index.py

把各个平台的 CSV 评论合并起来，做一个简单的 TF-IDF 检索器，
同时提供：
- 品牌情感汇总 / 代表机型 / 覆盖平台（给前端品牌表用）
- 品牌评论明细（给详情表用，可按平台筛选）
- 全局统计汇总（给头部 dashboard 用）

注意：
- 目前只接入 Reddit / B 站 / GSMArena 三个平台；
- 什么值得买的数据暂时不计入汇总；
- B 站只使用 data_bilibili_v2.csv，早期测试 CSV 当作「废弃」不加载。
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 当前文件所在目录（Global_Phone_Sentiment）
DATA_DIR = Path(__file__).parent

# === 这里是你当前目录里存在的 CSV 文件 ===
#   注意：
#   - 只保留最后一次完整爬取的 B 站 CSV：data_bilibili_v2.csv
#   - data_bilibili.csv 等早期测试文件当作废弃，不要放进来
#   - 什么值得买（smzdm）相关 CSV 也先排除
CSV_FILES: List[str] = [
    # Reddit 相关
    "data_reddit_2111.csv",
    "data_reddit_20251206_103022.csv",
    "data_reddit_comments_20251206_105256.csv",

    # gsmarena + notebookcheck（统一算作 GSMArena）
    "data_gsmarena_notebookcheck.csv",

    # B 站（只保留最终版）
    "data_bilibili_v2.csv",
]

# 文本列的候选名字（按优先级从上到下）
CANDIDATE_TEXT_COLS = [
    "cleaned_text",
    "raw_text",
    "content",
    "text",
    "comment",
    "body",
    "review",
    "title",
    "selftext",
    "评论内容",
    "评论",
]

# 机型/设备列的候选名字
CANDIDATE_MODEL_COLS = [
    "phone_model_id",
    "device_name",
    "model",
    "phone",
    "model_name",
    "sku",
]

# 发表时间列候选
CANDIDATE_TIME_COLS = [
    "published_at",
    "created_at",
    "pubtime_str",
    "time_str",
    "timestamp",
]

# 非常简陋的情感词典（demo 用）
POS_WORDS = ["好", "喜欢", "真香", "满意", "香", "推荐", "棒", "优秀", "惊喜", "爽"]
NEG_WORDS = ["差", "垃圾", "失望", "烂", "后悔", "坑", "生气", "气死", "不好", "一般"]

# 平台 ID -> 展示名称
PLATFORM_LABELS: Dict[str, str] = {
    "bilibili": "B站",
    "reddit": "Reddit",
    "gsmarena": "GSMArena",
    "smzdm": "什么值得买",
    "unknown": "其他",
}


def _guess_text_col(df: pd.DataFrame) -> str:
    """尝试在 DataFrame 里猜测哪一列是评论文本。"""
    for col in CANDIDATE_TEXT_COLS:
        if col in df.columns:
            return col
    raise ValueError(f"找不到评论文本列，当前列名有: {list(df.columns)}")


def _guess_model_col(df: pd.DataFrame) -> Optional[str]:
    """尝试猜测哪一列是机型/设备名，没有就返回 None。"""
    for col in CANDIDATE_MODEL_COLS:
        if col in df.columns:
            return col
    return None


def simple_sentiment(text: str) -> str:
    """非常简单的基于词典的情感打标：pos / neg / neu。"""
    t = str(text)
    if not t.strip():
        return "neu"
    pos = sum(1 for w in POS_WORDS if w in t)
    neg = sum(1 for w in NEG_WORDS if w in t)
    if pos > neg:
        return "pos"
    if neg > pos:
        return "neg"
    return "neu"


def extract_brand(model: str) -> str:
    """
    从机型字符串里大致抽一个“品牌名”，不准也没关系，主要是用来分组展示。
    未命中任何规则时，归为 "Other"。
    """
    if not isinstance(model, str):
        model = str(model or "")
    m = model.lower()

    # 很粗糙的规则，你以后可以根据需要再加
    if "iphone" in m or "apple" in m:
        return "Apple"
    if "samsung" in m or "galaxy" in m or "s23" in m or "a35" in m or "a55" in m:
        return "Samsung"
    if "redmi" in m or "xiaomi" in m or "mi " in m:
        return "Xiaomi"
    if "huawei" in m or "mate" in m or "pura" in m:
        return "Huawei"
    if "honor" in m or "荣耀" in m:
        return "Honor"
    if "oppo" in m:
        return "OPPO"
    if "vivo" in m:
        return "vivo"
    if "iqoo" in m:
        return "iQOO"
    if "oneplus" in m or "一加" in m:
        return "OnePlus"
    if "pixel" in m:
        return "Google Pixel"

    return "Other"


def guess_content_type(row: pd.Series) -> str:
    """
    粗略判断一条记录是「原文/视频」还是「评论」：
    - data_type 里包含 comment / reply 之类 → comment
    - 否则一律认为是 original
    """
    dt = str(row.get("data_type", "")).lower()
    if any(k in dt for k in ["comment", "reply", "评论"]):
        return "comment"
    return "original"


def detect_source_from_filename(name: str) -> str:
    """根据文件名粗略判断数据来源平台（内部 ID）。"""
    lower_name = name.lower()
    if "reddit" in lower_name:
        return "reddit"
    if "bilibili" in lower_name:
        return "bilibili"
    if "gsmarena" in lower_name or "notebookcheck" in lower_name:
        return "gsmarena"
    if "smzdm" in lower_name:
        return "smzdm"
    return "unknown"


class PhoneFeedbackIndex:
    def __init__(self) -> None:
        dfs: List[pd.DataFrame] = []

        for name in CSV_FILES:
            path = DATA_DIR / name
            if not path.exists():
                print(f"[WARN] {path} 不存在，先跳过")
                continue

            source_id = detect_source_from_filename(name)

            # 目前不纳入什么值得买
            if source_id == "smzdm":
                print(f"[INFO] {name} 来自什么值得买，当前版本不计入汇总，跳过")
                continue

            print(f"[LOAD] 正在读取 {path} ...")
            # 用更宽容的解析器，跳过坏行
            df = pd.read_csv(
                path,
                engine="python",
                on_bad_lines="skip",
            )

            if df.empty:
                print(f"[WARN] {name} 是空的，跳过")
                continue

            # 1）找出文本列，统一命名为 content
            text_col = _guess_text_col(df)
            df["content"] = df[text_col].astype(str).fillna("")

            # 2）机型字段 -> model_std
            model_col = _guess_model_col(df)
            if model_col:
                df["model_std"] = df[model_col].astype(str)
            else:
                df["model_std"] = "unknown"

            # 3）平台 / 来源（内部 ID + 展示名）
            df["source"] = source_id
            df["platform_std"] = PLATFORM_LABELS.get(source_id, PLATFORM_LABELS["unknown"])

            # 4）标记内容类型：原文 / 评论
            df["content_type"] = df.apply(guess_content_type, axis=1)

            # 保留原始文件名，方便排查
            df["source_file"] = name

            dfs.append(df)

        if not dfs:
            raise RuntimeError("没有找到任何 CSV 数据，请检查 CSV_FILES 配置是否正确。")

        # 合并所有数据
        self.df: pd.DataFrame = pd.concat(dfs, ignore_index=True)
        self.df["content"] = self.df["content"].fillna("")

        # 简单情感打标
        print("[INDEX] 开始打情感标签 …")
        self.df["sentiment"] = self.df["content"].apply(simple_sentiment)

        # 粗糙品牌归一
        self.df["brand_id"] = self.df["model_std"].apply(extract_brand)

        print(f"[INDEX] 已加载评论 {len(self.df)} 条，开始构建 TF-IDF 向量……")

        # 构建 TF-IDF 向量
        self.vectorizer = TfidfVectorizer(
            max_features=50000,
            max_df=0.9,
            min_df=3,
        )
        self.matrix = self.vectorizer.fit_transform(self.df["content"])

        print("[INDEX] 向量化完成 ✅")

    # ---------- 给 Copilot 用的检索 ----------

    def search(self, query: str, k: int = 30) -> pd.DataFrame:
        """
        用自然语言 query 搜索最相关的 k 条评论，
        返回一个带 score 的 DataFrame。
        """
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        idx = sims.argsort()[::-1][:k]
        results = self.df.iloc[idx].copy()
        results["score"] = sims[idx]
        return results

    # ---------- 品牌概览接口，给品牌表用 ----------

    def get_brand_insights(self) -> List[Dict[str, Any]]:
        """
        返回形如：
        [
          {
            brand_id, brand_name,
            total, pos, neg, neu, positive_rate,
            top_models: ["iphone_16_pro", ...],
            platforms: ["B站", "GSMArena", "Reddit"],
          },
          ...
        ]
        """
        df = self.df.copy()

        # 品牌 x 情感 分布
        grouped = df.groupby("brand_id")["sentiment"].value_counts().unstack(fill_value=0)

        results: List[Dict[str, Any]] = []

        for brand in grouped.index:
            brand_mask = df["brand_id"] == brand
            brand_df = df[brand_mask]

            pos = int(grouped.loc[brand].get("pos", 0))
            neg = int(grouped.loc[brand].get("neg", 0))
            neu = int(grouped.loc[brand].get("neu", 0))
            total = pos + neg + neu
            if total == 0:
                continue

            positive_rate = float(pos / total) if total > 0 else 0.0

            # 代表机型：按出现次数排序取前 3 个
            top_models_series = brand_df["model_std"].value_counts().head(3)
            top_models: List[str] = top_models_series.index.tolist()

            # 覆盖平台：用展示名去重
            platform_ids = brand_df["source"].dropna().unique().tolist()
            platform_labels = [
                PLATFORM_LABELS.get(pid, PLATFORM_LABELS["unknown"])
                for pid in platform_ids
            ]
            # 去重并稳定排序
            platform_labels = sorted(set(platform_labels))

            item: Dict[str, Any] = {
                "brand_id": brand,
                "brand_name": brand,
                "total": int(total),
                "pos": pos,
                "neg": neg,
                "neu": neu,
                "positive_rate": positive_rate,
                "top_models": top_models,
                "platforms": platform_labels,
            }
            results.append(item)

        # 按总评论数从高到低排
        results.sort(key=lambda x: x["total"], reverse=True)
        return results

    # ---------- 品牌评论明细接口，给详情表用 ----------

    def get_brand_opinions(
        self,
        brand_id: str,
        platform: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        返回某个品牌的若干条原始评论：
        [
          { published_at, platform, brand_id, model, sentiment, raw_text },
          ...
        ]
        可以按 platform 过滤（bilibili / reddit / gsmarena），None 表示全部。
        """
        df = self.df[self.df["brand_id"] == brand_id].copy()
        if df.empty:
            return []

        # 平台过滤（按内部 ID）
        if platform and platform != "all":
            df = df[df["source"] == platform]
            if df.empty:
                return []

        # 找一个时间字段
        time_col: Optional[str] = None
        for col in CANDIDATE_TIME_COLS:
            if col in df.columns:
                time_col = col
                break

        rows: List[Dict[str, Any]] = []

        for _, row in df.head(limit).iterrows():
            if time_col:
                published_at = row.get(time_col)
            else:
                published_at = None

            raw_text = (
                row.get("raw_text")
                or row.get("cleaned_text")
                or row.get("content")
                or ""
            )

            item: Dict[str, Any] = {
                "published_at": str(published_at) if published_at is not None else None,
                "platform": row.get("platform_std") or PLATFORM_LABELS.get(row.get("source", "unknown"), "其他"),
                "brand_id": brand_id,
                "model": row.get("model_std"),
                "sentiment": row.get("sentiment", "neu"),
                "raw_text": str(raw_text),
            }
            rows.append(item)

        return rows

    # ---------- 全局统计，用于头部 dashboard ----------

    def get_global_stats(self) -> Dict[str, Any]:
        """
        返回一个字典，包括：
        - 舆情平台数 / 列表
        - 品牌数 / 品牌列表
        - 型号数 / 型号列表
        - 原文数量 / 评论数量 + 各平台分布
        - 一小批 B 站原文链接样本
        """
        df = self.df

        # 平台
        platform_ids = [pid for pid in df["source"].dropna().unique().tolist() if pid != "unknown"]
        platform_ids = sorted(set(platform_ids))
        platforms = [
            {
                "id": pid,
                "name": PLATFORM_LABELS.get(pid, PLATFORM_LABELS["unknown"]),
            }
            for pid in platform_ids
        ]

        # 品牌 & 型号
        brands = sorted(df["brand_id"].dropna().unique().tolist())
        models = sorted(df["model_std"].dropna().unique().tolist())

        # 原文 / 评论统计
        original_mask = df["content_type"] == "original"
        comment_mask = df["content_type"] == "comment"

        original_count = int(original_mask.sum())
        comment_count = int(comment_mask.sum())

        def _count_by_platform(mask):
            if mask.sum() == 0:
                return {}
            sub = df[mask]
            s = sub.groupby("source")["content"].count()
            return {pid: int(s.get(pid, 0)) for pid in platform_ids}

        original_by_platform = _count_by_platform(original_mask)
        comment_by_platform = _count_by_platform(comment_mask)

        # 一些 B 站原文链接样本（方便在卡片里展示）
        bilibili_mask = (df["source"] == "bilibili") & original_mask
        url_col = "url" if "url" in df.columns else None
        bilibili_urls: List[str] = []
        if url_col:
            bilibili_urls = (
                df.loc[bilibili_mask, url_col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()[:10]
            )

        return {
            "platform_count": len(platforms),
            "platforms": platforms,
            "brand_count": len(brands),
            "brands": brands,
            "model_count": len(models),
            "models": models,
            "original_count": original_count,
            "original_by_platform": original_by_platform,
            "comment_count": comment_count,
            "comment_by_platform": comment_by_platform,
            "bilibili_sample_urls": bilibili_urls,
        }


# 方便你在当前项目里快速测试
if __name__ == "__main__":
    idx = PhoneFeedbackIndex()

    print("\n==== 数据概要 ====")
    print("总记录数：", len(idx.df))
    print("品牌数量：", idx.df["brand_id"].nunique())
    print(idx.df["brand_id"].value_counts().head(10))

    print("\n==== 品牌汇总示例 ====")
    for item in idx.get_brand_insights()[:5]:
        print(item)

    q = "iPhone 16 Pro 续航 发热"
    hits = idx.search(q, k=5)
    print(f"\n查询：{q}")
    cols = ["source", "brand_id", "model_std", "content", "score"]
    exist_cols = [c for c in cols if c in hits.columns]
    print(hits[exist_cols])
