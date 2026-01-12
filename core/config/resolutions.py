# Empirically Verified Resolution Table (Truth Table)
# This table defines the valid resolution pairs for specific aspect ratios at different quality tiers (1K, 2K, 4K).
# Format: "Aspect Ratio": {"Quality Tier": (Width, Height)}

RESOLUTION_TABLE = {
    "1:1":  {"1K": (1024, 1024), "2K": (2048, 2048), "4K": (4096, 4096)},
    "16:9": {"1K": (1376, 768),  "2K": (2752, 1536), "4K": (5504, 3072)},
    "9:16": {"1K": (768, 1376),  "2K": (1536, 2752), "4K": (3072, 5504)},
    "4:3":  {"1K": (1200, 896),  "2K": (2400, 1792), "4K": (4800, 3584)},
    "3:4":  {"1K": (896, 1200),  "2K": (1792, 2400), "4K": (3584, 4800)},
    "3:2":  {"1K": (1264, 848),  "2K": (2528, 1696), "4K": (5056, 3392)},
    "2:3":  {"1K": (848, 1264),  "2K": (1696, 2528), "4K": (3392, 5056)},
    "5:4":  {"1K": (1152, 928),  "2K": (2304, 1856), "4K": (4608, 3712)},
    "4:5":  {"1K": (928, 1152),  "2K": (1856, 2304), "4K": (3712, 4608)},
    "21:9": {"1K": (1584, 672),  "2K": (3168, 1344), "4K": (6336, 2688)}
}

# List of all supported aspect ratios
SUPPORTED_ASPECT_RATIOS = list(RESOLUTION_TABLE.keys())
