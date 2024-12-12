import os
import re
from datetime import datetime
import glob
import pandas as pd  # 导入pandas库
# import statelilteData_vis as sv
import nmeaParse_single as nmeasingle
from tkinter import *
from tkinter import filedialog, messagebox
import time
from tkcalendar import Calendar  # 用于日期选择控件
import pyautogui
import numpy as np

#打开输出文件以写入定位信息
def format_time(timestamp):
    """将时间戳格式化为 YYYY-MM-DD_HH-MM 格式"""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M')

def dms_to_decimal(degrees, direction):
    """将度分秒格式转换为十进制度格式"""
    degrees = float(degrees)
    decimal_degree = degrees // 100 + (degrees % 100) / 60.0  # 提取度和分
    if direction == 'S' or direction == 'W':
        decimal_degree = -decimal_degree
    return decimal_degree

def parse_nmea_log(start_timestamp, end_timestamp, input_dir, output_dir, show_flag):
    # 格式化开始时间和结束时间
    start_time_str = format_time(start_timestamp)
    end_time_str = format_time(end_timestamp)

    # 确保output文件夹存在
    # output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 如果output文件夹不存在，则创建它

    # 获取当前目录下所有以nmea.log开头的文件
    files = glob.glob(os.path.join(input_dir, 'nmea.log*'))  # 匹配以nmea.log开头的所有文件

    # 构造输出文件路径
    location_file = os.path.join(output_dir, f'location_data_{start_time_str}_{end_time_str}.txt')
    location_excel = os.path.join(output_dir, f'location_data_{start_time_str}_{end_time_str}.xlsx')
    satellites_file = os.path.join(output_dir, f'satellites_data_{start_time_str}_{end_time_str}.xlsx')
    bd_satellites_file = os.path.join(output_dir, f'bd_satellites_data_{start_time_str}_{end_time_str}.xlsx')
    error_location_excel = os.path.join(output_dir, f'error_location_data_{start_time_str}_{end_time_str}.xlsx')

    # 初始化计数器用于生成name
    count = 1

    location_data = []
    satellites_data = []
    bd_satellites_data = []
    error_location_data = []  # 用于存储经纬度为0的记录

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
                    if line.startswith('$GNRMC'):
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
                        # gngns_match = re.match(
                        #     r'^\$GNGNS,\d+\.\d+,.+?,([\d\.]+),([NS]),([\d\.]+),([EW]),.*?,.*?,.*?,([\d\.]+),.*',
                        #     line)
                        # if gngns_match:
                        #     elevation = float(gngns_match.group(5))

                        if lat_decimal == 0 or lon_decimal == 0:
                            error_location_data.append([current_timestamp, lat_decimal, lon_decimal, elevation])

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

    # 保存错误数据到Excel（经纬度为0的记录）
    if error_location_data:
        df_error_location = pd.DataFrame(error_location_data,
                                         columns=['Timestamp', 'Longitude', 'Latitude', 'Elevation'])
        df_error_location.to_excel(error_location_excel, index=False)

    # 保存卫星数据到Excel文件
    df_location = pd.DataFrame(location_data, columns=['Timestamp', 'Longitude', 'Latitude', 'Elevation'])
    df_location.to_excel('locationd_2024-10-31_10-33.xlsx', index=False)

    # df_satellites = pd.DataFrame(satellites_data)
    df_satellites = pd.DataFrame(satellites_data, columns=['Timestamp', 'PRN', 'Elevation', 'Azimuth', 'SNR'])
    df_satellites.to_excel(satellites_file, index=False)

    # 保存BD卫星数据到Excel文件
    df_bd_satellites = pd.DataFrame(bd_satellites_data, columns=['Timestamp', 'PRN', 'Elevation', 'Azimuth', 'SNR'])
    df_bd_satellites.to_excel(bd_satellites_file, index=False)

    # sv.stateliltes_data_vis(satellites_file, show_flag)


# Tkinter GUI
class NMEAParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NMEA Parser')
        self.root.geometry('1000x1000')

        self.input_dir = None
        self.output_dir = None

        # Tkinter GUI 日期时间选择
        self.start_data_label = Label(root, text='选择nmea日志分析的开始时间(YYYY-MM-DD HH:MM:SS)')
        self.start_data_label.pack(pady=5)
        self.start_data_entry = Entry(root) # 允许手动输入
        self.start_data_entry.pack(pady=5)

        self.end_data_label = Label(root, text="选择nmea日志分析的结束时间(YYYY-MM-DD HH:MM:SS)")
        self.end_data_label.pack(pady=5)
        self.end_data_entry = Entry(root) # 允许手动输入
        self.end_data_entry.pack(pady=5)

        # 文件路径选择按钮
        self.input_button = Button(root, text="选择nmea日志文件路径", command=self.select_input_path)
        self.input_button.pack(pady=10)

        self.output_button = Button(root, text="选择分析结果输出路径", command=self.select_output_path)
        self.output_button.pack(pady=10)

        self.output_button = Label(root, text="选择生成图表类型")
        self.output_button.pack(pady=10)

        self.chart_type_var = StringVar(value='scatter')
        self.scatter_radio = Radiobutton(root, text="散点图", variable=self.chart_type_var, value='scatter')
        self.scatter_radio.pack(pady=5)
        self.line_radio = Radiobutton(root, text="折线图", variable=self.chart_type_var, value='line')
        self.line_radio.pack(pady=5)
        self.bar_radio = Radiobutton(root, text="柱状图", variable=self.chart_type_var, value='bar')
        self.bar_radio.pack(pady=5)

        self.generate_button = Button(root, text="分析数据", command=self.generate_chart)
        self.generate_button.pack(pady=20)

        # 输入NMEA报文的文本框和按钮
        self.nmea_label = Label(root, text="输入nmea报文（每条以回车分隔）")
        self.nmea_label.pack(pady=10)

        self.nmea_input = Text(root, height=10, width=20)
        self.nmea_input.pack(pady=10)

        self.nmea_button = Button(root, text="解析nmea报文", command=self.parse_nmea_input)
        self.nmea_button.pack(pady=10)

    def show_succ(self, message):
        succ_window = Toplevel(self.root)
        succ_window.title("完成")
        Label(succ_window, text=message, fg="blue").pack(pady=20)
        Button(succ_window, text="确定", command=succ_window.destroy).pack(pady=5)

    def show_error(self, message):
        error_window = Toplevel(self.root)
        error_window.title("错误")
        Label(error_window, text=message, fg="red").pack(pady=20)
        Button(error_window, text="关闭", command=error_window.destroy).pack(pady=5)

    def select_input_path(self):
        self.input_dir = filedialog.askdirectory(title="选择待nmea日志输入的文件路径")

    def select_output_path(self):
        self.output_dir = filedialog.askdirectory(title="选择分析结果输出的文件路径")

    # 解析用户输入的nmea报文
    def parse_nmea_input(self):
        nmea_data = self.nmea_input.get("1.0", END).strip()
        if not nmea_data:
            messagebox.showerror("错误", "请输入nmea报文")
            return

        # 将每行nmea报文解析并显示在文本框内
        nmea_lines = nmea_data.split('\n')

        nmeasingle.prase_nmea(nmea_lines)

        self.show_succ("解析完成！")

    def generate_chart(self):
        if self.input_dir and self.output_dir:
            try:
                start_time = int(datetime.strftime(self.start_data_entry.get(), "%Y-%m-%d %H:%M:%S").timestamp())
                end_time = int(datetime.strftime(self.end_data_entry.get(), "%Y-%m-%d %H:%M:%S").timestamp())
                if start_time < end_time:
                    parse_nmea_log(start_time, end_time, self.input_dir, self.output_dir, self.chart_type_var.get())
                else:
                    self.show_error("请确保开始时间和结束时间正确！")
            except ValueError:
                self.show_error("无效的时间格式！请确保格式为 'YYYY-MM-DD HH:MM:SS'. ")
                return
        else:
            self.show_error("请确保输入有效的输入/输出文件路径")


# 调用函数
if __name__ == "__main__":
    # start_time = 1730341980  # 开始时间戳  2024-11-11 11:10  2024-11-05 19:40 2024-11-05 19:47  2024-11-05 19:41:48 2024-11-11 11:40 2024-10-31 10:33
    # end_time = 1730342100  # 结束时间戳 2024-11-11 11:20  2024-11-05 20:00 2024-11-05 19:49  2024-11-05 19:48:43 2024-11-11 11:42 2024-10-31 10:35
    # parse_nmea_log(start_time, end_time)
    root = Tk()
    app = NMEAParserApp(root)
    root.mainloop()
