from __future__ import annotations

import csv
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ========================
# 路径 & 日志
# ========================

# 当前 main.py 所在目录：Global_Phone_Sentiment
# 项目根目录是 Global_Phone_Sentiment 的父目录
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent  # 项目根目录（ZDM+Reddit）

# 数据目录：Global_Phone_Sentiment 目录
GLOBAL_SENTIMENT_DIR = CURRENT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("phone_feedback")


# ========================
# 数据结构
# ========================


@dataclass
class OpinionRow:
    platform: str
    brand_id: str
    brand_name: str
    model: str
    sentiment: str  # 'pos' | 'neg' | 'neu'
    published_at: str  # YYYY-MM-DD
    raw_text: str
    is_original: bool = False


@dataclass
class BrandInsight:
    """品牌维度聚合，用于 /insights"""

    brand_id: str
    brand_name: str
    platforms: List[str] = field(default_factory=list)
    top_models: List[str] = field(default_factory=list)
    total: int = 0
    pos: int = 0
    neg: int = 0
    neu: int = 0

    @property
    def positive_rate(self) -> float:
        return (self.pos / self.total) if self.total else 0.0

    def to_dict(self) -> Dict:
        return {
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "platforms": self.platforms,
            "top_models": self.top_models,
            "total": self.total,
            "pos": self.pos,
            "neg": self.neg,
            "neu": self.neu,
            "positive_rate": self.positive_rate,
        }


@dataclass
class PhoneFeedbackIndex:
    """全局索引，启动时加载一次"""

    platforms: Dict[str, str] = field(default_factory=dict)  # id -> name
    brands: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    bilibili_sample_urls: List[str] = field(default_factory=list)
    original_count: int = 0
    original_by_platform: Dict[str, int] = field(default_factory=dict)
    comment_count: int = 0
    comment_by_platform: Dict[str, int] = field(default_factory=dict)
    crawl_time: str = ""

    brand_insights: Dict[str, BrandInsight] = field(default_factory=dict)
    opinions_by_brand: Dict[str, List[OpinionRow]] = field(
        default_factory=lambda: defaultdict(list)
    )

    @property
    def stats_payload(self) -> Dict:
        return {
            "platform_count": len(self.platforms),
            "platforms": [
                {"id": pid, "name": name} for pid, name in sorted(self.platforms.items())
            ],
            "brands": sorted(self.brands),
            "models": sorted(self.models),
            "bilibili_sample_urls": self.bilibili_sample_urls[:5],
            "original_count": self.original_count,
            "original_by_platform": self.original_by_platform,
            "comment_count": self.comment_count,
            "comment_by_platform": self.comment_by_platform,
            "crawl_time": self.crawl_time,
        }

    @property
    def insights_payload(self) -> List[Dict]:
        # 过滤掉 Other 品牌
        filtered = [
            ins.to_dict()
            for ins in self.brand_insights.values()
            if ins.brand_id not in ["other", "unknown", ""]
            and ins.brand_name not in ["Other", "other", "未知", "unknown"]
        ]
        return filtered


# ========================
# 工具函数
# ========================


def _first_non_empty(row: Dict, keys: List[str]) -> str:
    """获取第一个非空字段值"""
    for k in keys:
        if k in row and row[k]:
            val = str(row[k]).strip()
            if val:
                return val
    return ""


def _is_url(s: str) -> bool:
    """判断字符串是否为 URL"""
    if not s:
        return False
    s_lower = s.lower().strip()
    return (
        s_lower.startswith("http://")
        or s_lower.startswith("https://")
        or "://" in s_lower
        or s_lower.startswith("www.")
    )


def _extract_brand_from_model_id(model_id: str) -> Optional[str]:
    """
    从 phone_model_id 中提取品牌，例如: iphone_16_pro -> Apple
    """
    if not model_id or _is_url(model_id):
        return None

    model_lower = model_id.lower().strip()

    if model_lower.startswith("iphone") or "apple" in model_lower:
        return "Apple"
    if model_lower.startswith("xiaomi") or model_lower.startswith("redmi") or model_lower.startswith("mi"):
        return "Xiaomi"
    if model_lower.startswith("huawei") or model_lower.startswith("mate") or model_lower.startswith("pura"):
        return "Huawei"
    if model_lower.startswith("samsung") or "galaxy" in model_lower:
        return "Samsung"
    if model_lower.startswith("vivo") or model_lower.startswith("iqoo"):
        return "Vivo"
    if model_lower.startswith("oppo"):
        return "OPPO"
    if model_lower.startswith("honor"):
        return "Honor"

    # 下划线分割再试一次
    parts = model_lower.split("_")
    if parts:
        first_part = parts[0]
        if first_part in ["iphone", "apple"]:
            return "Apple"
        if first_part in ["xiaomi", "redmi", "mi"]:
            return "Xiaomi"
        if first_part in ["huawei", "mate", "pura"]:
            return "Huawei"
        if first_part in ["samsung", "galaxy"]:
            return "Samsung"
        if first_part in ["vivo", "iqoo"]:
            return "Vivo"
        if first_part == "oppo":
            return "OPPO"
        if first_part == "honor":
            return "Honor"

    return None


def _normalize_brand_id(brand_raw: str) -> str:
    """
    统一品牌 ID：小写 + 去空格 + 别名映射
    """
    if not brand_raw:
        return "other"

    b = str(brand_raw).strip()
    low = b.lower().replace(" ", "").replace("_", "")

    mapping = {
        "apple": "apple",
        "iphone": "apple",
        "xiaomi": "xiaomi",
        "mi": "xiaomi",
        "redmi": "xiaomi",
        "华为": "huawei",
        "huawei": "huawei",
        "honor": "honor",
        "荣耀": "honor",
        "samsung": "samsung",
        "vivo": "vivo",
        "iqoo": "vivo",
        "oppo": "oppo",
        "oneplus": "oneplus",
        "一加": "oneplus",
        "realme": "realme",
    }

    for k, v in mapping.items():
        if low == k or low.startswith(k):
            return v

    return low if low else "other"


def _normalize_brand_name(brand_raw: str) -> str:
    """
    统一品牌显示名称：返回首字母大写的品牌名
    """
    if not brand_raw:
        return "Other"

    b = str(brand_raw).strip()
    low = b.lower()

    mapping = {
        "apple": "Apple",
        "iphone": "Apple",
        "xiaomi": "Xiaomi",
        "mi": "Xiaomi",
        "redmi": "Xiaomi",
        "华为": "Huawei",
        "huawei": "Huawei",
        "honor": "Honor",
        "荣耀": "Honor",
        "samsung": "Samsung",
        "vivo": "Vivo",
        "iqoo": "Vivo",
        "oppo": "OPPO",
        "oneplus": "OnePlus",
        "一加": "OnePlus",
        "realme": "Realme",
    }

    for k, v in mapping.items():
        if low == k or low.startswith(k + " ") or low.startswith(k):
            return v

    return b.capitalize() if b else "Other"


def _parse_date(row: Dict) -> str:
    """
    解析日期字段，统一返回 YYYY-MM-DD 格式
    """
    value = _first_non_empty(
        row,
        [
            "published_at",
            "pubtime_str",
            "time_str",
            "date",
            "created_at",
            "time",
            "timestamp",
        ],
    )
    if not value:
        return ""

    txt = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(txt[:19], fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue

    if len(txt) >= 10:
        try:
            test_str = txt[:10]
            datetime.strptime(test_str, "%Y-%m-%d")
            return test_str
        except Exception:
            pass

    return txt[:10] if len(txt) >= 10 else ""


def _parse_text(row: Dict) -> str:
    """解析文本内容字段"""
    return _first_non_empty(
        row,
        [
            "raw_text",
            "cleaned_text",
            "comment",
            "content",
            "text",
            "body",
            "review",
            "title",
            "评论内容",
            "评论",
        ],
    )


def _parse_sentiment(row: Dict) -> str:
    """
    解析情感标签，返回 "pos" | "neg" | "neu"
    优先级：显式标签 > 评分推断 > 文本关键词 > 默认中性
    """
    label = _first_non_empty(row, ["sentiment", "label", "sentiment_label", "情感", "情感标签"])
    if label:
        l = str(label).strip().lower()
        if l in {"pos", "positive", "好评", "正向", "正面", "积极"}:
            return "pos"
        if l in {"neg", "negative", "差评", "负向", "负面", "消极"}:
            return "neg"
        if l in {"neu", "neutral", "中性", "中"}:
            return "neu"

    score_text = _first_non_empty(row, ["rating", "score", "stars", "评分", "星级"])
    if score_text:
        try:
            score = float(str(score_text).strip())
            if score <= 5:
                if score >= 4:
                    return "pos"
                if score <= 2:
                    return "neg"
                return "neu"
            if score <= 10:
                if score >= 8:
                    return "pos"
                if score <= 4:
                    return "neg"
                return "neu"
            if score <= 100:
                if score >= 80:
                    return "pos"
                if score <= 40:
                    return "neg"
                return "neu"
        except Exception:
            pass

    text = _parse_text(row)
    if text:
        text_lower = str(text).lower()

        positive_keywords = [
            "good",
            "great",
            "excellent",
            "amazing",
            "fantastic",
            "wonderful",
            "love",
            "best",
            "perfect",
            "awesome",
            "brilliant",
            "outstanding",
            "推荐",
            "好评",
            "很好",
            "不错",
            "满意",
            "喜欢",
            "赞",
            "棒",
            "优秀",
            "recommend",
            "highly recommend",
            "worth it",
            "worth buying",
        ]

        negative_keywords = [
            "bad",
            "terrible",
            "awful",
            "horrible",
            "worst",
            "disappointed",
            "hate",
            "poor",
            "garbage",
            "trash",
            "junk",
            "useless",
            "broken",
            "差评",
            "不好",
            "垃圾",
            "失望",
            "问题",
            "故障",
            "坏",
            "差",
            "烂",
            "not worth",
            "don't buy",
            "avoid",
            "problem",
            "issue",
            "bug",
        ]

        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)

        if pos_count > neg_count and pos_count > 0:
            return "pos"
        if neg_count > pos_count and neg_count > 0:
            return "neg"
        return "neu"

    return "neu"


def _parse_is_comment(row: Dict, platform: str) -> bool:
    """
    判断一条记录是评论还是原文
    platform: 平台 ID (bilibili/gsmarena/reddit)
    """
    if platform == "bilibili":
        data_type = _first_non_empty(row, ["data_type", "type"])
        data_type_lower = data_type.lower() if data_type else ""
        if "comment" in data_type_lower or "评论" in data_type_lower:
            return True
        if "video" in data_type_lower:
            return False

    if platform == "reddit":
        source_type = _first_non_empty(row, ["source_type", "type"])
        source_type_lower = source_type.lower() if source_type else ""
        if "comment" in source_type_lower or "reply" in source_type_lower:
            return True
        if "post" in source_type_lower:
            return False

    if platform == "gsmarena":
        data_type = _first_non_empty(row, ["data_type", "type"])
        data_type_lower = data_type.lower() if data_type else ""
        if (
            "opinion" in data_type_lower
            or "comment" in data_type_lower
            or "评论" in data_type_lower
        ):
            return True
        if "review" in data_type_lower or "article" in data_type_lower:
            return False
        return True

    return True  # 默认视为评论


def _safe_read_csv(path: Path) -> List[Dict]:
    if not path.exists():
        logger.warning("数据文件不存在: %s", path)
        return []
    rows: List[Dict] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        logger.info("读取 CSV 成功: %s，%d 行", path.name, len(rows))
    except UnicodeDecodeError:
        with path.open("r", encoding="gbk", errors="ignore") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        logger.info("读取 CSV(GBK) 成功: %s，%d 行", path.name, len(rows))
    except Exception as e:
        logger.error("读取 CSV 失败: %s: %s", path, e)
    return rows


def _load_single_csv(
    path: Path,
    platform: str,
    force_is_comment: Optional[bool] = None,
) -> List[Dict]:
    """
    加载单个 CSV 文件并统一清洗字段
    """
    rows = _safe_read_csv(path)
    if not rows:
        return []

    result: List[Dict] = []

    for row in rows:
        # ===== 品牌提取（严格过滤 URL） =====
        brand_raw = None

        phone_model_id = _first_non_empty(row, ["phone_model_id"])
        if phone_model_id and not _is_url(phone_model_id):
            brand_raw = _extract_brand_from_model_id(phone_model_id)

        if not brand_raw:
            device_name = _first_non_empty(row, ["device_name"])
            if device_name and not _is_url(device_name):
                device_lower = device_name.lower()
                if "iphone" in device_lower or "apple" in device_lower:
                    brand_raw = "Apple"
                elif "samsung" in device_lower or "galaxy" in device_lower:
                    brand_raw = "Samsung"
                elif "xiaomi" in device_lower or "redmi" in device_lower:
                    brand_raw = "Xiaomi"
                elif "huawei" in device_lower or "mate" in device_lower or "pura" in device_lower:
                    brand_raw = "Huawei"
                elif "vivo" in device_lower or "iqoo" in device_lower:
                    brand_raw = "Vivo"
                elif "oppo" in device_lower:
                    brand_raw = "OPPO"

        if not brand_raw:
            brand_field = _first_non_empty(row, ["brand", "brand_name", "phone_brand"])
            if brand_field and not _is_url(brand_field):
                brand_raw = brand_field

        if not brand_raw:
            brand_raw = "Other"

        brand_id = _normalize_brand_id(brand_raw)
        brand_name = _normalize_brand_name(brand_raw)

        # ===== 机型提取（严格过滤 URL） =====
        model = None

        if phone_model_id and not _is_url(phone_model_id):
            model_id_lower = phone_model_id.lower().strip()
            try:
                import importlib.util

                config_path = GLOBAL_SENTIMENT_DIR / "config.py"
                if config_path.exists():
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)
                    TARGET_MODELS = config_module.TARGET_MODELS
                    if model_id_lower in TARGET_MODELS:
                        model = phone_model_id
            except Exception:
                pass

        if not model:
            device_name = _first_non_empty(row, ["device_name"])
            if device_name and not _is_url(device_name):
                model = device_name

        if not model:
            model_field = _first_non_empty(row, ["model", "phone_model", "model_name"])
            if model_field and not _is_url(model_field):
                model = model_field

        if model and _is_url(model):
            model = None

        # ===== 是否为评论 =====
        if force_is_comment is not None:
            is_comment_val = 1 if force_is_comment else 0
        else:
            is_comment_val = 1 if _parse_is_comment(row, platform) else 0

        # ===== 时间 / 文本 / 情感 / URL =====
        published_at = _parse_date(row)
        text = _parse_text(row)
        sentiment = _parse_sentiment(row)
        url = _first_non_empty(row, ["url", "link", "page_url", "video_url", "链接"])

        result.append(
            {
                "platform": platform,
                "brand": brand_name,
                "brand_id": brand_id,
                "model": model,
                "is_comment": is_comment_val,
                "published_at": published_at,
                "text": text,
                "sentiment": sentiment,
                "url": url,
            }
        )

    return result


# ========================
# 构建索引
# ========================


def build_index() -> PhoneFeedbackIndex:
    """
    构建全局索引，统一加载和清洗所有平台的 CSV 数据
    只使用 bilibili/gsmarena/reddit 三个平台，排除 smzdm
    """
    index = PhoneFeedbackIndex()

    PLATFORM_NAME = {
        "bilibili": "Bilibili",
        "gsmarena": "Gsmarena",
        "reddit": "Reddit",
    }

    source_files = []

    # Bilibili
    bili_v2_path = GLOBAL_SENTIMENT_DIR / "data_bilibili_v2.csv"
    bili_comment_path = GLOBAL_SENTIMENT_DIR / "data_bilibili.csv"

    if bili_v2_path.exists():
        source_files.append((bili_v2_path, "bilibili", None))
    if bili_comment_path.exists():
        source_files.append((bili_comment_path, "bilibili", True))

    # GSMArena
    gsm_path = GLOBAL_SENTIMENT_DIR / "data_gsmarena_notebookcheck.csv"
    if gsm_path.exists():
        source_files.append((gsm_path, "gsmarena", None))

    # Reddit（在 ZDM+Reddit 根目录）
    reddit_files = [
        (ROOT_DIR / "data_reddit_2111.csv", "reddit", None),
        (ROOT_DIR / "data_reddit_20251206_103022.csv", "reddit", None),
        (ROOT_DIR / "data_reddit_comments_20251206_105256.csv", "reddit", True),
    ]
    for path, platform, force_comment in reddit_files:
        if path.exists():
            source_files.append((path, platform, force_comment))

    logger.info("准备加载 %d 个 CSV 文件", len(source_files))

    all_rows: List[Dict] = []

    for path, platform, force_is_comment in source_files:
        logger.info("正在加载: %s (平台: %s)", path.name, platform)
        rows = _load_single_csv(path, platform, force_is_comment)

        if platform not in index.platforms:
            index.platforms[platform] = PLATFORM_NAME.get(platform, platform)

        all_rows.extend(rows)
        logger.info("  加载了 %d 条记录", len(rows))

    if not all_rows:
        logger.error("没有加载到任何数据，请检查 CSV 文件是否存在")
        return index

    df_original = [r for r in all_rows if r["is_comment"] == 0]
    df_comments = [r for r in all_rows if r["is_comment"] == 1]

    logger.info("数据分离完成：原文 %d 条，评论 %d 条", len(df_original), len(df_comments))

    all_brands_set = set()
    all_models_set = set()
    bilibili_urls: List[str] = []
    original_by_platform = Counter()
    comment_by_platform = Counter()

    # 原文
    for row in df_original:
        platform = row["platform"]
        brand_name = row["brand"]
        model = row["model"]

        if brand_name and not _is_url(brand_name) and brand_name not in ["Other", "other", ""]:
            all_brands_set.add(brand_name)
        if model and not _is_url(model):
            all_models_set.add(model)

        original_by_platform[platform] += 1

        if platform == "bilibili" and row.get("url") and len(bilibili_urls) < 3:
            url_val = str(row["url"]).strip()
            if url_val.startswith("http"):
                bilibili_urls.append(url_val)

    # 评论
    for row in df_comments:
        platform = row["platform"]
        brand_id = row["brand_id"]
        brand_name = row["brand"]
        model = row["model"]

        if brand_name and not _is_url(brand_name) and brand_name not in ["Other", "other", ""]:
            all_brands_set.add(brand_name)
        if model and not _is_url(model):
            all_models_set.add(model)

        comment_by_platform[platform] += 1

        op = OpinionRow(
            platform=platform,
            brand_id=brand_id,
            brand_name=brand_name,
            model=model,
            sentiment=row["sentiment"],
            published_at=row["published_at"],
            raw_text=row["text"],
            is_original=False,
        )
        index.opinions_by_brand[brand_id].append(op)

    # 品牌聚合
    brand_comment_counter: Dict[str, Counter] = defaultdict(Counter)
    brand_platforms: Dict[str, set] = defaultdict(set)

    for row in df_comments:
        brand_id = row["brand_id"]
        brand_name = row["brand"]
        platform = row["platform"]
        model = row["model"]
        sentiment = row["sentiment"]

        if brand_id not in index.brand_insights:
            index.brand_insights[brand_id] = BrandInsight(
                brand_id=brand_id,
                brand_name=brand_name,
            )

        ins = index.brand_insights[brand_id]
        brand_platforms[brand_id].add(platform)

        ins.total += 1
        if sentiment == "pos":
            ins.pos += 1
        elif sentiment == "neg":
            ins.neg += 1
        else:
            ins.neu += 1

        if model and not _is_url(str(model)) and str(model).strip():
            model_str = str(model).strip()
            if not model_str.startswith("http") and "://" not in model_str:
                brand_comment_counter[brand_id][model_str] += 1

    # 设置平台列表 & 热门机型
    for brand_id, ins in index.brand_insights.items():
        ins.platforms = sorted(list(brand_platforms.get(brand_id, set())))

        counter = brand_comment_counter.get(brand_id)
        if counter:
            top_models_list: List[str] = []
            try:
                import importlib.util

                config_path = GLOBAL_SENTIMENT_DIR / "config.py"
                if config_path.exists():
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config_module)
                    TARGET_MODELS = config_module.TARGET_MODELS
                    for m, _ in counter.most_common(10):
                        if not m or _is_url(str(m)):
                            continue
                        model_str = str(m).strip()
                        model_lower = model_str.lower()
                        is_target_model = any(
                            target_key in model_lower or model_lower in target_key
                            for target_key in TARGET_MODELS.keys()
                        )
                        if is_target_model or len(top_models_list) < 3:
                            top_models_list.append(model_str)
                            if len(top_models_list) >= 3:
                                break
                else:
                    raise ImportError
            except Exception:
                for m, _ in counter.most_common(3):
                    if not m or _is_url(str(m)):
                        continue
                    model_str = str(m).strip()
                    top_models_list.append(model_str)

            ins.top_models = top_models_list[:3]
        else:
            ins.top_models = []

    # 品牌列表（彻底过滤 URL 等垃圾）
    filtered_brands: List[str] = []
    for brand in all_brands_set:
        brand_str = str(brand).strip()
        if not brand_str:
            continue
        if _is_url(brand_str):
            continue
        if brand_str.lower() in ["other", "未知", "unknown"]:
            continue
        if any(x in brand_str.lower() for x in ["http://", "https://", "www.", ".com", ".net"]):
            continue
        if len(brand_str) > 50:
            continue
        filtered_brands.append(brand_str)
    index.brands = sorted(list(set(filtered_brands)))

    # 型号列表：只保留 config.TARGET_MODELS
    try:
        import importlib.util

        config_path = GLOBAL_SENTIMENT_DIR / "config.py"
        if config_path.exists():
            spec = importlib.util.spec_from_file_location("config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            TARGET_MODELS = config_module.TARGET_MODELS
            target_model_keys = set(TARGET_MODELS.keys())
            logger.info("加载目标型号配置成功，共 %d 个目标型号", len(target_model_keys))
        else:
            raise ImportError(f"config.py not found at {config_path}")

        filtered_models: List[str] = []
        for m in all_models_set:
            model_str = str(m).strip()
            if not model_str or _is_url(model_str):
                continue
            if any(
                x in model_str.lower()
                for x in ["http://", "https://", "www.", ".com", ".net"]
            ):
                continue
            model_lower = model_str.lower()
            for target_key in target_model_keys:
                if (
                    target_key == model_lower
                    or target_key in model_lower
                    or model_lower in target_key
                ):
                    if model_str not in filtered_models:
                        filtered_models.append(model_str)
                    break

        if not filtered_models:
            filtered_models = sorted(list(target_model_keys))
        else:
            filtered_models = sorted(list(set(filtered_models)))

        index.models = filtered_models
        logger.info("型号统计：总型号 %d 个，过滤后目标型号 %d 个", len(all_models_set), len(filtered_models))
    except Exception as e:
        logger.warning("无法加载目标型号配置，使用全部型号（过滤 URL）: %s", e)
        filtered_models = [m for m in all_models_set if not _is_url(str(m))]
        index.models = sorted(filtered_models)

    index.bilibili_sample_urls = bilibili_urls[:3]
    index.original_by_platform = dict(original_by_platform)
    index.comment_by_platform = dict(comment_by_platform)
    index.original_count = len(df_original)
    index.comment_count = len(df_comments)

    # 最近日期
    max_date = ""
    for row in all_rows:
        date_str = str(row.get("published_at", "")).strip()
        if date_str and len(date_str) >= 10:
            date_part = date_str[:10]
            if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
                try:
                    datetime.strptime(date_part, "%Y-%m-%d")
                    if date_part > max_date:
                        max_date = date_part
                except Exception:
                    pass

    if max_date:
        index.crawl_time = max_date
    else:
        try:
            file_times = []
            for path, _, _ in source_files:
                if path.exists():
                    file_times.append(path.stat().st_mtime)
            if file_times:
                max_mtime = max(file_times)
                index.crawl_time = datetime.fromtimestamp(max_mtime).strftime("%Y-%m-%d")
            else:
                index.crawl_time = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            index.crawl_time = datetime.now().strftime("%Y-%m-%d")

    total_records = len(all_rows)
    logger.info(
        "[STARTUP] PhoneFeedbackIndex 就绪 ✅ | 总记录 %d, 原始内容 %d, 评论 %d",
        total_records,
        index.original_count,
        index.comment_count,
    )

    return index


# ========================
# FastAPI
# ========================

app = FastAPI(title="Phone & Robot Sentiment API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（前端文件）
# 注意：你的前端在 ZDM+Reddit/netlify-deploy 目录下
FRONTEND_DIR = ROOT_DIR / "netlify-deploy"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

INDEX = build_index()


# 首页：返回静态 index.html（如果存在）
@app.get("/")
async def read_root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Frontend file not found. Please check netlify-deploy/index.html exists."}


# 兼容旧路径
@app.get("/frontend/")
async def read_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Frontend file not found. Please check netlify-deploy/index.html exists."}


class CopilotQuery(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str


# ========================
# Metrics API 响应模型（使用 Pydantic BaseModel，不用 dataclass）
# ========================


class OverviewMetrics(BaseModel):
    """概览统计指标"""
    platform_count: int
    brand_count: int
    model_count: int
    original_count: int
    comment_count: int
    original_by_platform: Dict[str, int]
    comment_by_platform: Dict[str, int]
    crawl_time: str


class BrandOverviewRow(BaseModel):
    """品牌概览行"""
    brand_id: str
    brand_name: str
    total: int
    pos: int
    neg: int
    neu: int
    positive_rate: float
    platforms: List[str]
    top_models: List[str]


class BrandOverviewResponse(BaseModel):
    """品牌概览完整响应"""
    overview: OverviewMetrics
    brands: List[BrandOverviewRow]


class BrandsOnlyResponse(BaseModel):
    """仅品牌列表响应"""
    brands: List[BrandOverviewRow]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def get_stats():
    return INDEX.stats_payload


@app.get("/insights")
def get_insights():
    return INDEX.insights_payload


@app.get("/opinions")
def get_opinions(
    brand_id: str = Query(..., description="品牌 ID，与 /insights 中的 brand_id 一致"),
    platform: Optional[str] = Query(
        None, description="可选平台过滤：bilibili / gsmarena / reddit / all（all 或 None 表示不过滤）"
    ),
    model: Optional[str] = Query(
        None, description="可选型号过滤：如 iphone_16_pro、xiaomi_15 等"
    ),
    year: Optional[int] = Query(None, description="年份过滤（如 2025），需要同时提供月份才生效"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份过滤（1-12），需要同时提供年份才生效"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    获取品牌评论明细，支持平台、型号和年月筛选
    """
    rows = INDEX.opinions_by_brand.get(brand_id, [])

    if platform and platform.lower() != "all":
        rows = [r for r in rows if r.platform == platform.lower()]

    if model and model.strip():
        model_lower = model.lower().strip()
        filtered = []
        for r in rows:
            row_model = r.model
            if row_model:
                row_model_lower = str(row_model).lower().strip()
                if (
                    row_model_lower == model_lower
                    or model_lower in row_model_lower
                    or row_model_lower in model_lower
                ):
                    filtered.append(r)
        rows = filtered

    if year is not None and month is not None:
        filtered = []
        for r in rows:
            date_str = r.published_at
            if date_str and len(date_str) >= 7:
                try:
                    date_parts = date_str.split("-")
                    if len(date_parts) >= 2:
                        row_year = int(date_parts[0])
                        row_month = int(date_parts[1])
                        if row_year == year and row_month == month:
                            filtered.append(r)
                except (ValueError, IndexError):
                    continue
        rows = filtered
    elif year is not None:
        filtered = []
        for r in rows:
            date_str = r.published_at
            if date_str and len(date_str) >= 4:
                try:
                    row_year = int(date_str[:4])
                    if row_year == year:
                        filtered.append(r)
                except (ValueError, IndexError):
                    continue
        rows = filtered

    def get_sort_key(r: OpinionRow) -> str:
        date_str = r.published_at or ""
        if len(date_str) >= 10:
            return date_str[:10]
        return "0000-01-01"

    rows.sort(key=get_sort_key, reverse=True)

    sliced = rows[:limit]

    return [
        {
            "published_at": (
                r.published_at[:10]
                if r.published_at and len(r.published_at) >= 10
                else r.published_at
            ),
            "platform": r.platform,
            "brand_id": r.brand_id,
            "model": r.model or "",
            "sentiment": r.sentiment,
            "raw_text": r.raw_text,
        }
        for r in sliced
    ]


@app.post("/copilot", response_model=CopilotResponse)
def copilot(query: CopilotQuery):
    """
    智能分析助手（占位实现）
    暂时不调用外部大模型，基于规则返回统计信息
    """
    q = query.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="问题不能为空")

    q_lower = q.lower()

    detected_brands = []
    brand_keywords = {
        "apple": ["apple", "iphone", "苹果"],
        "xiaomi": ["xiaomi", "小米", "redmi", "红米"],
        "huawei": ["huawei", "华为", "honor", "荣耀"],
        "samsung": ["samsung", "三星", "galaxy"],
        "vivo": ["vivo"],
        "oppo": ["oppo"],
    }

    for brand_id, keywords in brand_keywords.items():
        for keyword in keywords:
            if keyword in q_lower:
                detected_brands.append(brand_id)
                break

    answer_parts: List[str] = []
    answer_parts.append("【规则分析结果】当前为占位实现，不调用外部大模型。\n")

    if detected_brands:
        answer_parts.append(f"\n检测到品牌：{', '.join(set(detected_brands))}\n")

        for brand_id in set(detected_brands):
            insight = INDEX.brand_insights.get(brand_id)
            if insight:
                answer_parts.append(
                    f"\n**{insight.brand_name}**：\n"
                    f"- 评论总数：{insight.total}\n"
                    f"- 正向：{insight.pos}，负向：{insight.neg}，中性：{insight.neu}\n"
                    f"- 好评率：{insight.positive_rate * 100:.1f}%\n"
                    f"- 覆盖平台：{', '.join(insight.platforms)}\n"
                )
    else:
        answer_parts.append("\n当前已抓取数据概览：\n")
        answer_parts.append(f"- 品牌数量：{len(INDEX.brands)}\n")
        answer_parts.append(f"- 评论总数：{INDEX.comment_count}\n")
        answer_parts.append(f"- 原始内容：{INDEX.original_count}\n")
        answer_parts.append(
            "- 覆盖平台："
            + ", ".join([p["name"] for p in INDEX.stats_payload["platforms"]])
            + "\n"
        )

    answer_parts.append(
        "\n---\n"
        "提示：基础链路已就绪，等数据验证通过后，可在此接口中接入真实的大模型调用逻辑。"
    )

    return CopilotResponse(answer="\n".join(answer_parts))


# ========================
# Metrics API 路由
# ========================


def _build_brand_overview_rows(index: PhoneFeedbackIndex) -> List[BrandOverviewRow]:
    """
    从索引中构建品牌概览行列表
    复用逻辑，避免代码重复
    """
    brand_rows: List[BrandOverviewRow] = []
    
    for brand_id, insight in index.brand_insights.items():
        # 过滤掉无效品牌
        if brand_id in ["other", "unknown", ""]:
            continue
        if insight.brand_name in ["Other", "other", "未知", "unknown"]:
            continue
        
        # 确保 top_models 不超过 3 个，且过滤掉 URL
        top_models_filtered = []
        for model in insight.top_models[:3]:
            if model and not _is_url(str(model)):
                model_str = str(model).strip()
                if model_str and not model_str.startswith("http"):
                    top_models_filtered.append(model_str)
        
        brand_row = BrandOverviewRow(
            brand_id=insight.brand_id,
            brand_name=insight.brand_name,
            total=insight.total,
            pos=insight.pos,
            neg=insight.neg,
            neu=insight.neu,
            positive_rate=insight.positive_rate,
            platforms=insight.platforms,
            top_models=top_models_filtered,
        )
        brand_rows.append(brand_row)
    
    return brand_rows


@app.get("/api/v1/metrics/overview", response_model=BrandOverviewResponse)
def get_metrics_overview():
    """
    获取完整的概览统计和品牌列表
    """
    # 构建概览指标
    # 过滤掉 "other" 和 "unknown" 品牌
    valid_brand_count = len([
        bid for bid in INDEX.brand_insights.keys()
        if bid not in ["other", "unknown", ""]
        and INDEX.brand_insights[bid].brand_name not in ["Other", "other", "未知", "unknown"]
    ])
    
    overview = OverviewMetrics(
        platform_count=len(INDEX.platforms),
        brand_count=valid_brand_count,
        model_count=len(INDEX.models),
        original_count=INDEX.original_count,
        comment_count=INDEX.comment_count,
        original_by_platform=INDEX.original_by_platform,
        comment_by_platform=INDEX.comment_by_platform,
        crawl_time=INDEX.crawl_time,
    )
    
    # 构建品牌列表
    brands = _build_brand_overview_rows(INDEX)
    
    return BrandOverviewResponse(
        overview=overview,
        brands=brands,
    )


@app.get("/api/v1/metrics/brands", response_model=BrandsOnlyResponse)
def get_metrics_brands():
    """
    仅获取品牌列表（不包含概览统计）
    """
    brands = _build_brand_overview_rows(INDEX)
    return BrandsOnlyResponse(brands=brands)


# 本地调试用：在 Global_Phone_Sentiment 目录下运行：
#   python main.py
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
