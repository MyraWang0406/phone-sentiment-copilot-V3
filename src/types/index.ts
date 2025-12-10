// 统一的数据类型定义

export type Category = 'phone' | 'car' | 'device';
export type Platform = 'Bilibili' | 'Reddit' | 'GSM Arena' | string;
export type Sentiment = 'pos' | 'neg' | 'neutral';

export interface DashboardSummary {
  category: Category;
  platforms: Platform[];
  brand_count: number;
  model_count: number;
  raw_comment_count: number;
  user_sentence_count: number;
  brands: BrandRow[];
}

export interface BrandRow {
  brand_cn: string;
  brand_en: string;
  hot_models: string[];
  sources: Platform[];
  stats: {
    total_reviews: number;
    pos: number;
    neg: number;
    neutral: number;
    positive_rate: number; // 0~1
  };
}

export interface UnifiedComment {
  id: string;
  platform: Platform;
  category: Category;
  brand_cn: string;
  brand_en: string;
  model_cn: string;
  model_en: string;
  datetime: string; // ISO string
  year: number;
  month: number;
  sentiment: Sentiment;
  sentiment_score?: number;
  title?: string;
  content: string;
  like_count?: number;
  reply_count?: number;
}

export interface CommentFilters {
  brands: string[];
  models: string[];
  platforms: Platform[];
  sentiment: Sentiment | 'all';
  year: number | 'all';
  month: number | 'all';
}
