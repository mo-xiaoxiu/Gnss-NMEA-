import time
import datetime
import pandas as pd

# 将nmea时间转换为时间戳和北京时间
def conver_time_to_timestamp_and_bj(time_str):
    # nmea时间格式：HHMMSS.sss
    utc_time = time_str[:6] # HHMMSS
    fractional_seconds = float(time_str[6:]) # sss

    # 转换度时分秒
    hours = int(utc_time[:2])
    minutes = int(utc_time[2:4])
    seconds = int(utc_time[4:6]) # 只取整数部分作为标准秒数

    # 获取utc时间戳
    utc_time = datetime.datetime(2000, 1, 1, hours, minutes, seconds)

    # 用timedelta调整浮动的小数秒部分
    utc_time  += datetime.timedelta(seconds=fractional_seconds)

    # 转换UNIX时间戳
    timestamp = time.mktime(utc_time.timetuple())

    # 北京时间为utc+8
    bj_time = utc_time + datetime.timedelta(hours=8)

    return timestamp, bj_time.strftime('%Y-%m-%d %H:%M:%S')


# 转换将nmea经纬度
def convert_to_decimal(degress_minutes_str):
    # 经纬度格式：DDMM.MMMM
    degrees = float(degress_minutes_str)
    decimal_degrees = degrees // 100 + (degrees % 100) / 60.0
    return decimal_degrees


# 解析nmea报文
def prase_nmea(sentence):
    parsed_results = []
    table_data = []

    for line in sentence:
        if not line.startswith('$'):
            raise ValueError("Invalid NMEA sentence, it must start with $")

        # 计算校验和
        checksum = line.split('*')[-1]
        data = line[1:].split('*')[0]  # 去除‘$’和校验和后面的部分

        # 提取数据句子的类型
        sentence_type = data.split(',')[0]

        parsed_data = {'sentence_type': sentence_type, 'GGA': {}, 'RMC':{}, 'GNS':{}, 'GSV':{}}

        # 初始化一个字典，用于存储行数据
        row = {
            'sentence_type': parsed_data.get('sentence_type'),
            'time': None, "timestamp": None, 'beijing_time': None,
            'latitude': None, 'longitude': None, 'fix_quality': None,
            'statellites': None, 'altitude': None, 'status': None, 'speed': None, 'date': None
        }

        # 不同句子的解析方法
        if sentence_type in ['GPGGA', 'BDGGA', 'GLGGA']:
            parts = data.split(',')
            timestamp, bj_time = conver_time_to_timestamp_and_bj(parts[1])
            latitude = convert_to_decimal(parts[2]) if parts[3] == 'N' else -convert_to_decimal(parts[2])
            longitude = convert_to_decimal(parts[4]) if parts[5] == 'E' else -convert_to_decimal(parts[4])

            if longitude > 360:
                longitude = longitude - 360

            parsed_data['GGA'] = {
                'time': parts[1],
                'timestamp': timestamp,
                'beijing_time': bj_time,
                'latitude': latitude,
                'longitude': longitude,
                'fix_quality': parts[6],
                'statellites': parts[7],
                'altitude': parts[9]
            }
            row.update({
                'time': parsed_data['GGA'].get('time'),
                'timestamp': parsed_data['GGA'].get('timestamp'),
                'beijing_time': parsed_data['GGA'].get('beijing_time'),
                'latitude': parsed_data['GGA'].get('latitude'),
                'longitude': parsed_data['GGA'].get('longitude'),
                'fix_quality': parsed_data['GGA'].get('fix_quality'),
                'statellites': parsed_data['GGA'].get('statellites'),
                'altitude': parsed_data['GGA'].get('altitude')
            })
        elif sentence_type in ['GPRMC', 'BDRMC', 'GLRMC', 'GNRMC']:
            parts = data.split(',')
            timestamp, bj_time = conver_time_to_timestamp_and_bj(parts[1])
            latitude = convert_to_decimal(parts[3]) if parts[4] == 'N' else -convert_to_decimal(parts[3])
            longitude = convert_to_decimal(parts[5]) if parts[6] == 'E' else -convert_to_decimal(parts[5])

            if longitude > 360:
                longitude = longitude - 360

            parsed_data['RMC'] = {
                'time': parts[1],
                'timestamp': timestamp,
                'beijing_time': bj_time,
                'status': parts[2],
                'latitude': latitude,
                'longitude': longitude,
                'speed': parts[7],
                'date': parts[9]
            }
            row.update({
                'time': parsed_data['RMC'].get('time'),
                'timestamp': parsed_data['RMC'].get('timestamp'),
                'beijing_time': parsed_data['RMC'].get('beijing_time'),
                'status': parsed_data['RMC'].get('status'),
                'latitude': parsed_data['RMC'].get('latitude'),
                'longitude': parsed_data['RMC'].get('longitude'),
                'speed': parsed_data['RMC'].get('speed'),
                'date': parsed_data['RMC'].get('date')
            })
        elif sentence_type in ['GPGSV', 'BDGSV', 'GLGSV']:
            parts = data.split(',')
            statellite_info = []
            num_of_statellites = int(parts[3])
            for i in range(num_of_statellites):
                if 4 * i + 4 < len(parts):
                    statellite_info.append({
                        'statellite_prn': parts[4 + 4 * i],
                        'elevation': parts[5 + 4 * i],
                        'azimuth': parts[6 + 4 * i],
                        'snr': parts[7 + 4 * i]
                    })
                    parsed_data['GSV'] = {'statellites_in_view': statellite_info}
                    row[f'statellites_prn_{i + 1}'] = parts[4 + 4 * i]
                    row[f'elevation_{i + 1}'] = parts[5 + 4 * i]
                    row[f'azimuth_{i + 1}'] = parts[6 + 4 * i]
                    row[f'snr_{i + 1}'] = parts[7 + 4 * i]
        elif sentence_type in ['GPGNS', 'BDGNS', 'GLGNS']:
            parts = data.split(',')
            timestamp, bj_time = conver_time_to_timestamp_and_bj(parts[1])
            latitude = convert_to_decimal(parts[2]) if parts[3] == 'N' else -convert_to_decimal(parts[2])
            longitude = convert_to_decimal(parts[4]) if parts[5] == 'E' else -convert_to_decimal(parts[4])

            if longitude > 360:
                longitude = longitude - 360

            parsed_data['GNS'] = {
                'time': parts[1],
                'timestamp': timestamp,
                'beijing_time': bj_time,
                'latitude': latitude,
                'longitude': longitude,
                'fix_quality': parts[6],
                'statellites': parts[7],
                'altitude': parts[9]
            }
            row.update({
                'time': parsed_data['GNS'].get('time'),
                'timestamp': parsed_data['GNS'].get('timestamp'),
                'beijing_time': parsed_data['GNS'].get('beijing_time'),
                'latitude': parsed_data['GNS'].get('latitude'),
                'longitude': parsed_data['GNS'].get('longitude'),
                'fix_quality': parsed_data['GNS'].get('fix_quality'),
                'statellites': parsed_data['GNS'].get('statellites'),
                'altitude': parsed_data['GNS'].get('altitude')
            })

        parsed_results.append(parsed_data)
        table_data.append(row)

    df = pd.DataFrame(table_data)
    df.to_excel('nmeaParse_single.xlsx', index=False)

    count = 1
    with open('nmeaParse_single.txt', 'w') as outfile:
        outfile.write('Longitude,Latitude,Elevation,name\n')
        for pr in parsed_results:
            if pr.get('RMC'):
                outfile.write(f"{pr['RMC']['longitude']},{pr['RMC']['latitude']},{0.0},m{count}\n")
                count += 1

    return parsed_results
