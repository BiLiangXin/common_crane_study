# -*- coding: utf-8 -*-
"""
config.py
---------
把所有可调参数集中在这里，便于复现实验与敏感性分析。

建议你在论文方法部分把关键参数（eps、min_stay、max_interval、夜间判定阈值等）
写成表格，并在补充材料中给出不同参数组合下的结果对比。
"""

from pathlib import Path



# ========== 字段名（按你的CSV） ==========
COL_BIRD_ID = "bird_id"
COL_TIME = "time"
COL_LON = "lon"
COL_LAT = "lat"
COL_AVAILABLE = "Available"  # Available / UnAvailable

# 其余字段如果你有需要可在输出中保留
KEEP_EXTRA_COLS = [
    "heading", "height", "temperature", "HDOP", "VDOP", "ACCUURACY", COL_AVAILABLE
]

# ========== 数据清洗 ==========
# 1) 坐标合法范围
LON_RANGE = (-180.0, 180.0)
LAT_RANGE = (-90.0, 90.0)

# 2) Available 字段中表示“有效定位”的取值
AVAILABLE_OK_VALUES = {"Available"}

# 3) 速度异常值剔除（km/h）
# 文献与综述中提到灰鹤典型巡航 60–70 km/h，最高 90–100 km/h，强尾风可达约 120 km/h。
# 因此默认把 >120 km/h 作为异常（你可在敏感性分析中测试 100/120/150 等阈值）。
MAX_SPEED_KMH = 120.0

# 4) 两点时间差过小会导致速度非常不稳定（例如 GPS 秒级噪声），可设最小间隔（秒）
MIN_DT_SECONDS = 30

# 5) 分段阈值：相邻两点时间间隔超过该值，则认为轨迹断裂（缺失段），开始新的 segment
SEGMENT_GAP_HOURS = 6.0

# ========== 夜间点识别 ==========
# 提供两种方式：
# (A) solar：基于太阳高度角（推荐用于论文）
# (B) clock：基于固定时段（18:00–06:00），用于快速检查/对照
NIGHT_METHOD = "solar"   # "solar" 或 "clock"

# 你的 time 字段是否为 UTC？
# - 如果你的GPS时间是UTC：TIME_IS_UTC=True
# - 如果你的时间已经是北京时间/当地时间：TIME_IS_UTC=False，并设置 LOCAL_TIMEZONE
TIME_IS_UTC = False
LOCAL_TIMEZONE = "Asia/Shanghai"   # 当 TIME_IS_UTC=False 时生效

# 太阳高度角阈值（度）：太阳低于 -6° 常用作“夜间/暮光”分界（民用曙暮光）
# 你也可以用 0°（日出日落）或 -12°（航海曙暮光）做敏感性分析。
NIGHT_SUN_ELEV_THRESHOLD_DEG = -6.0

# 固定时段夜间：默认 18:00–06:00（包含晨昏时段，便于和城市照明开启时段对齐）
NIGHT_CLOCK_START_HOUR = 18
NIGHT_CLOCK_END_HOUR = 6

# ========== T-DBSCAN（基于“最小停留时长”的时空聚类） ==========
# 是否只用夜间点做聚类（识别夜栖地/栖息地核心）
CLUSTER_USE_NIGHT_ONLY = False
# CLUSTER_USE_NIGHT_ONLY = True
# 空间阈值 eps（米）：用于判断“停留在同一站点”的空间范围
# 经验：夜栖地可用 200–1000m；站点尺度（含觅食范围）可用 5–25km（需敏感性分析）。
TDBSCAN_EPS_METERS = 10000.0
# TDBSCAN_EPS_METERS = 50000.0
# TDBSCAN_EPS_METERS = 25000.0
# 最大时间间隔 max_interval（小时）：用于避免把时间断裂（缺失）强行连成同一簇
# 你的数据以 1小时采样为主，少量 2–5小时缺失；默认设 6小时可以覆盖绝大多数连续记录。
TDBSCAN_MAX_INTERVAL_HOURS = 6.0

# 最小停留时长 min_stay（小时）：用于把“短暂经过/飞行”过滤掉
# 综述中常用：停留超过 2 天视为一次停歇；连续停留超过 14 天定义为关键停歇地。
TDBSCAN_MIN_STAY_HOURS = 48.0

# 当 CLUSTER_USE_NIGHT_ONLY=True 时，把白天点“归入”夜间簇的半径（米）
DAY_ASSIGN_RADIUS_METERS = 15000.0

# ========== 栖息地类型划分（站点级） ==========
# 这里用“停留时长 + 站点时间窗口（月份）”的规则分类。
# 你也可以改为“纬度极值/NDVI/土地覆被”等更生态学的规则。
MIN_STOP_DAYS = 2.0
KEY_STOP_DAYS = 14.0
BREEDING_MIN_DAYS = 30.0
WINTERING_MIN_DAYS = 30.0

BREEDING_MONTHS = {4, 5, 6, 7, 8}
WINTERING_MONTHS = {11, 12, 1, 2, 3}

# ========== 路径 ==========
PROJECT_DIR = Path(__file__).resolve().parent
INPUT_CSV = PROJECT_DIR / "Common_Crane_Dataset2.csv"     # 原始数据（你可以替换为新的CSV）
OUTPUT_DIR = PROJECT_DIR / f"outputs_{TDBSCAN_EPS_METERS}"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ========== 输出文件名 ==========
OUT_POINTS_CSV = OUTPUT_DIR / f"gps_points_with_cluster_{TDBSCAN_EPS_METERS}.csv"
OUT_FLIGHT_POINTS_CSV = OUTPUT_DIR /f"flight_points_{TDBSCAN_EPS_METERS}.csv"
OUT_SITES_ALL_CSV = OUTPUT_DIR / f"sites_all_{TDBSCAN_EPS_METERS}.csv"
OUT_SITES_CSV = OUTPUT_DIR / f"sites_{TDBSCAN_EPS_METERS}.csv"  # 仅越冬地/繁殖地/关键停留地（满足你的要求）
