#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地时间获取脚本

当 MCP 工具不可用时，使用此脚本获取本地时间
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

def get_local_time():
    """
    获取本地时间（上海时区 UTC+8）

    Returns:
        dict: 包含各种格式的时间信息
    """
    # 获取上海时区时间
    shanghai_tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(shanghai_tz)

    return {
        "current": now.strftime("%Y-%m-%d %H:%M:%S"),
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timestamp": int(now.timestamp()),
        "timezone": "Asia/Shanghai",
        "utc_offset": "+08:00"
    }

def main():
    """主函数"""
    # 解析参数
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    # 获取时间信息
    time_info = get_local_time()

    # 根据参数输出
    if arg == "--iso":
        print(time_info["iso"])
    elif arg == "--date":
        print(time_info["date"])
    elif arg == "--time":
        print(time_info["time"])
    elif arg == "--timestamp":
        print(time_info["timestamp"])
    elif arg == "--help":
        print("用法: python get_local_time.py [选项]")
        print("")
        print("选项:")
        print("  --iso       输出 ISO 8601 格式")
        print("  --date      仅输出日期")
        print("  --time      仅输出时间")
        print("  --timestamp 输出 Unix 时间戳")
        print("  --help      显示帮助信息")
        print("")
        print("示例:")
        print("  python get_local_time.py")
        print("  python get_local_time.py --iso")
        print("  python get_local_time.py --date")
    else:
        # 输出完整信息
        print(f"当前时间: {time_info['current']}")
        print(f"ISO格式: {time_info['iso']}")
        print(f"日期: {time_info['date']}")
        print(f"时间: {time_info['time']}")
        print(f"时间戳: {time_info['timestamp']}")
        print(f"时区: {time_info['timezone']} (UTC{time_info['utc_offset']})")

if __name__ == "__main__":
    main()
