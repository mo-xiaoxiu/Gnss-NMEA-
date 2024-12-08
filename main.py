import os
import re
from datetime import datetime
import glob
import pandas as pd  # 导入pandas库

def dms_to_decimal(degrees, direction):
    """将度分秒格式转换为十进制度格式"""
    degrees = float(degrees)
    decimal_degree = degrees // 100 + (degrees % 100) / 60.0  # 提取度和分
    if direction == 'S' or direction == 'W':
        decimal_degree = -decimal_degree
    return decimal_degree

def parse_nmea_log(start_timestamp, end_timestamp):
    # 获取当前目录下所有以nmea.log开头的文件
    files = glob.glob('nmea.log*')  # 匹配以nmea.log开头的所有文件

    # 打开输出文件以写入定位信息
    location_file = 'location_data_2024-10-31_10-33.txt'
    satellites_file = 'satellites_data_2024-10-31_10-33.xlsx'
    bd_satellites_file = 'bd_satellites_data_2024-10-31_10-33.xlsx'

    # 初始化计数器用于生成name
    count = 1

    location_data = []
    satellites_data = []
    bd_satellites_data = []

    # 遍历所有相关的文件
    for file in files:
        with open(file, 'r') as f:
            # 初始化变量存储当前文件的所有有效定位数据
            current_timestamp = None
            lines = f.readlines()

            for line in lines:
                # 匹配time=后面的时间戳
                time_match = re.match(r'time=(\d+)', line)
                lat_decimal = 0
                lon_decimal = 0
                elevation = 0
                satellites_info = []
                if time_match:
                    current_timestamp = int(time_match.group(1))

                # 如果时间戳在指定范围内，继续处理
                if current_timestamp is not None and start_timestamp <= current_timestamp <= end_timestamp:
                    # 解析GNRMC或GNGNS语句
                    if line.startswith('$GNRMC') or line.startswith('$GNGNS'):
                        # 解析GNRMC或GNGNS，获取经纬度和高程信息
                        gnrmc_match = re.match(
                            r'^\$GNRMC,\d+\.\d+,[AV],([\d\.]+),([NS]),([\d\.]+),([EW]),.*?,.*?,.*?,.*?,.*?$', line)
                        if gnrmc_match:
                            lat = float(gnrmc_match.group(1))
                            lat_dir = gnrmc_match.group(2)
                            lon = float(gnrmc_match.group(3))
                            lon_dir = gnrmc_match.group(4)

                            lat_decimal = dms_to_decimal(lat, lat_dir)
                            lon_decimal = dms_to_decimal(lon, lon_dir)

                        # 解析GNGNS语句，获取高程信息
                        gngns_match = re.match(
                            r'^\$GNGNS,\d+\.\d+,.+?,([\d\.]+),([NS]),([\d\.]+),([EW]),.*?,.*?,.*?,([\d\.]+),.*',
                            line)
                        if gngns_match:
                            elevation = float(gngns_match.group(5))

                        # 将位置信息保存到location_data
                        location_data.append([current_timestamp, lon_decimal, lat_decimal, elevation])

                    # 解析GPGSV语句，提取卫星信息
                    if line.startswith('$GPGSV'):
                        # 修改正则表达式，以支持解析多个卫星数据
                        gsv_match = re.match(r'^\$GPGSV,\d+,\d+,\d+(.*)\*', line)
                        if gsv_match:
                            # 提取卫星数据（每4个字段为一颗卫星的PRN、仰角、方位角、信号强度）
                            satellite_info = gsv_match.group(1).split(',')
                            for i in range(0, len(satellite_info), 4):  # 每4个数据为一组（PRN, Elevation, Azimuth, SNR）
                                if i + 4 < len(satellite_info):  # 确保列表有足够的元素
                                    prn = satellite_info[i + 1]
                                    elevation = satellite_info[i + 2]
                                    azimuth = satellite_info[i + 3]
                                    snr = satellite_info[i + 4]

                                    # 保存每个卫星的信息
                                    satellites_data.append({
                                        'Timestamp': current_timestamp,
                                        'PRN': prn,
                                        'Elevation': elevation,
                                        'Azimuth': azimuth,
                                        'SNR': snr
                                    })
                    # 保存卫星数据到satellites_data
                    # if satellites_info:
                    #     for sat in satellites_info:
                    #         satellites_data.append(sat)

                    # 解析BDGSV语句，提取北斗卫星信息
                    if line.startswith('$BDGSV'):
                        # 修改正则表达式，以支持解析多个卫星数据
                        bdgsv_match = re.match(r'^\$BDGSV,\d+,\d+,\d+(.*)\*', line)
                        if bdgsv_match:
                            # 提取卫星数据（每4个字段为一颗卫星的PRN、仰角、方位角、信号强度）
                            satellite_info = bdgsv_match.group(1).split(',')
                            for i in range(0, len(satellite_info), 4):  # 每4个数据为一组（PRN, Elevation, Azimuth, SNR）
                                if i + 4 < len(satellite_info):  # 确保列表有足够的元素
                                    prn = satellite_info[i + 1]
                                    elevation = satellite_info[i + 2]
                                    azimuth = satellite_info[i + 3]
                                    snr = satellite_info[i + 4]

                                    # 保存每个卫星的信息
                                    bd_satellites_data.append({
                                        'Timestamp': current_timestamp,
                                        'PRN': prn,
                                        'Elevation': elevation,
                                        'Azimuth': azimuth,
                                        'SNR': snr
                                    })

                    # 保存卫星数据到satellites_data
                    # if satellites_info:
                    #     for sat in satellites_info:
                    #         satellites_data.append(sat)

    # 保存定位数据到location_data2.txt文件
    with open(location_file, 'w') as out:
        out.write("Longitude,Latitude,Elevation,name\n")
        for count, (timestamp, lon, lat, elev) in enumerate(location_data, start=1):
            out.write(f"{lon},{lat},{elev},m{count}\n")

    # 保存卫星数据到Excel文件
    df_location = pd.DataFrame(location_data, columns=['Timestamp', 'Longitude', 'Latitude', 'Elevation'])
    df_location.to_excel('locationd_2024-10-31_10-33.xlsx', index=False)

    # df_satellites = pd.DataFrame(satellites_data)
    df_satellites = pd.DataFrame(satellites_data, columns=['Timestamp', 'PRN', 'Elevation', 'Azimuth', 'SNR'])
    df_satellites.to_excel(satellites_file, index=False)

    # 保存BD卫星数据到Excel文件
    df_bd_satellites = pd.DataFrame(bd_satellites_data, columns=['Timestamp', 'PRN', 'Elevation', 'Azimuth', 'SNR'])
    df_bd_satellites.to_excel(bd_satellites_file, index=False)

    print(f"定位数据已保存至 {location_file}")
    print(f"卫星数据已保存至 {satellites_file}")

# 调用函数
if __name__ == "__main__":
    start_time = 1730341980  # 开始时间戳  2024-11-11 11:10  2024-11-05 19:40 2024-11-05 19:47  2024-11-05 19:41:48 2024-11-11 11:40 2024-10-31 10:33
    end_time = 1730342100  # 结束时间戳 2024-11-11 11:20  2024-11-05 20:00 2024-11-05 19:49  2024-11-05 19:48:43 2024-11-11 11:42 2024-10-31 10:35
    parse_nmea_log(start_time, end_time)
