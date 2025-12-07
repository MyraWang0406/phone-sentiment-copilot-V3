import pandas as pd

# 换成你自己的 reddit 帖子 CSV 文件名
df = pd.read_csv("data_reddit_20251206_103022.csv")

print("按品牌统计：")
print(df["brand_id"].value_counts())

print("\n按机型统计（Top 20）：")
print(df["phone_model_id"].value_counts().head(20))
