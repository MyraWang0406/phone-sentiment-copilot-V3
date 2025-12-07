# config.py 

# 1. 品牌定义 (用于归类)
BRANDS = {
    "apple": "Apple",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",  # 归类为小米集团
    "huawei": "Huawei",
    "honor": "Honor",
    "oppo": "OPPO",
    "vivo": "vivo",
    "iqoo": "vivo",     # 归类为vivo集团
    "samsung": "Samsung"
}

# 2. 目标抓取型号清单 (精准搜索词)
# 键(Key)是我们在CSV里显示的标准化型号ID，值(Value)是用于搜索的关键词列表
# 注意：这里把 K系列、Y系列、A系列拆解到了具体型号
TARGET_MODELS = {
    # --- Apple ---
    "iphone_16_pro": ["iPhone 16 Pro", "iPhone16 Pro"],
    "iphone_16": ["iPhone 16", "iPhone16"],
    "iphone_15_pro": ["iPhone 15 Pro", "iPhone15 Pro"],
    "iphone_15": ["iPhone 15", "iPhone15"],
    
    # --- Xiaomi / Redmi (重点区分 K系列) ---
    # 这里把英文放在第一个，方便给 GSMArena / Notebookcheck 用英文搜索
    "xiaomi_15": ["Xiaomi 15", "小米15"],
    "xiaomi_14": ["Xiaomi 14", "小米14"],
    "redmi_k70_pro": ["Redmi K70 Pro", "红米K70 Pro", "K70 Pro"],
    "redmi_k70": ["Redmi K70", "红米K70", "K70"],
    "redmi_k70e": ["Redmi K70E", "红米K70E"],
    "redmi_note_13_pro": ["Redmi Note 13 Pro", "红米Note 13 Pro"],
    
    # --- Huawei ---
    "mate_60_pro": ["Mate 60 Pro", "Mate60 Pro"],
    "mate_60": ["Mate 60", "Mate60"],
    "pura_70": ["Pura 70", "Pura70"],
    
    # --- OPPO (包含 A系列, K系列) ---
    "oppo_find_x7": ["Find X7", "OPPO Find X7"],
    "oppo_reno_12": ["Reno 12", "Reno12"],
    "oppo_k12": ["OPPO K12", "K12"], 
    "oppo_a3_pro": ["OPPO A3 Pro", "A3 Pro"],  # 走量耐用机
    
    # --- vivo / iQOO (包含 Y系列) ---
    "vivo_x100": ["vivo X100", "X100"],
    "vivo_s19": ["vivo S19", "S19"],
    "vivo_y200": ["vivo Y200", "Y200"],  # 线下走量王
    "vivo_y78": ["vivo Y78", "Y78"],
    "iqoo_12": ["iQOO 12"],
    "iqoo_neo9": ["iQOO Neo 9", "Neo9"],
    
    # --- Samsung (包含 A系列) ---
    "samsung_s24_ultra": ["S24 Ultra", "Galaxy S24 Ultra"],
    "samsung_a55": ["Galaxy A55", "Samsung A55"],  # 全球畅销
    "samsung_a35": ["Galaxy A35", "Samsung A35"]
}

# 3. 爬虫配置
REDDIT_SUBREDDITS = [
    "Android",
    "PickAnAndroidForMe",
    "Xiaomi",
    "Huawei",
    "Samsung",
    "Apple",
    "vivo",
    "Oppo",
]
