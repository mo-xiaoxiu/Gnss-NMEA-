import pandas as pd
import glob
import plotly
import plotly.express as px

def stateliltes_data_vis(stateliltes_data_vis_excel, show_flag='scatter'):
    # 读取卫星数据
    satellites_data = pd.read_excel(stateliltes_data_vis_excel)

    if show_flag == 'bar':
        # 使用柱状图，x 轴为时间戳，y 轴为 SNR，按 PRN 显示不同的柱子
        # 创建一个新的列，用于联合显示 Timestamp 和 PRN 以确保它们分别显示为不同的柱子
        df = satellites_data
        df['Timestamp'] = df['Timestamp'].astype(str) + ' - PRN ' + df['PRN'].astype(str)
        fig = px.bar(df,
                     x='Timestamp',
                     y='SNR',
                     color='SNR',  # 按 PRN 的不同值着色
                     title="Satellite Signal Strength (SNR) by Timestamp and PRN",
                     labels={'Timestamp': 'Timestamp and PRN', 'SNR': 'Signal Strength (SNR)', 'PRN': 'PRN'},
                     hover_data={'Timestamp': True, 'PRN': True, 'SNR': True},  # 鼠标悬停显示详细信息
                     barmode='group'  # 同一时间戳的不同 PRN 以组的形式显示
                     )

        # 设置 x 轴为时间戳格式，并旋转标签使其更易读
        fig.update_xaxes(title='Timestamp', tickangle=-45)

        # 更新图形显示效果
        fig.update_layout(
            autosize=True,  # 自动调整图表大小
            hovermode="closest",  # 鼠标悬停时显示信息
            showlegend=True  # 显示图例
        )

        # 调整横轴显示密度，避免时间戳标签过于密集
        # 通过设置 tickvals 和 ticktext 来限制显示的时间戳
        fig.update_xaxes(
            tickvals=satellites_data['Timestamp'].iloc[::50],  # 每隔两个时间戳显示一个（可以根据需要调整）
            ticktext=[str(t) for t in satellites_data['Timestamp'].iloc[::50]]  # 显示时间戳的字符串形式
        )

        # 设置柱子上显示时间戳的样式
        fig.update_traces(textposition='inside', texttemplate='%{text}', textfont=dict(size=12, color='black'))

        # 显示交互式图表
        fig.show()
    elif show_flag == 'line':
        #使用 Plotly 绘制折线图
        fig = px.line(satellites_data,
                      x='Timestamp',
                      y='SNR',
                      color='PRN',  # 不同 PRN 用不同颜色
                      title="Satellite Signal Strength (SNR) by Timestamp and PRN",
                      labels={'Timestamp': 'Timestamp', 'SNR': 'Signal Strength (SNR)', 'PRN': 'PRN'},
                      markers=True)  # 在每个数据点上显示标记

        # 设置 x 轴为时间戳格式
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M:%S', title='Timestamp')

        # 更新图形显示效果
        fig.update_layout(
            xaxis_tickangle=-45,  # 旋转 X 轴标签
            autosize=True,  # 自动调整图表大小
            hovermode="closest",  # 鼠标悬停时显示信息
            showlegend=True  # 显示图例
        )

        # 显示交互式图表
        fig.show()
    else:
        # 使用 plotly 绘制散点图（时间戳和 PRN 为横坐标，SNR 为纵坐标）
        fig = px.scatter(satellites_data,
                         x='Timestamp',
                         y='SNR',
                         color='SNR',  # 不同的 PRN 用不同的颜色
                         title="Satellite Signal Strength (SNR) by Timestamp and PRN",
                         labels={'Timestamp': 'Timestamp', 'SNR': 'Signal Strength (SNR)', 'PRN': 'PRN'},
                         hover_data={'Timestamp': True, 'PRN': True, 'SNR': True},
                         color_discrete_sequence=px.colors.qualitative.Plotly)  # 鼠标悬停显示更多信息

        # 设置 x 轴为时间戳格式
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M:%S', title='Timestamp')

        # 更新图形显示效果
        fig.update_layout(
            xaxis_tickangle=-45,  # 旋转 X 轴标签
            autosize=True,  # 自动调整图表大小
            hovermode="closest",  # 鼠标悬停时显示信息
            showlegend=True  # 显示图例
        )

        # 显示交互式图表
        fig.show()


# 本地测试
if __name__ == "main":
    stateliltes_data_vis("D:/project/satellites_data_2024-11-07_04-17_2024-11-07_04-18.xlsx", 'bar')