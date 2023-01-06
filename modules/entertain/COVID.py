from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne.model import Group
from graia.saya import Channel
from graiax.shortcut.saya import listen, decorate

import aiohttp
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from io import BytesIO

channel = Channel.current()

channel.name("COVID-19")
channel.description("发送'COVID-19'获取新冠确诊病例排名前20的国家")
channel.author("I_love_study")

font_path = "static/font/SourceHanSans-Medium.otf"  # Your font path goes here
fm.fontManager.addfont(font_path)
prop = fm.FontProperties(fname=font_path) # type: ignore

plt.rcParams['font.family'] = prop.get_name()
plt.rcParams['mathtext.fontset'] = 'cm'  # 'cm' (Computer Modern)

@listen(GroupMessage)
@decorate(MatchContent("COVID-19"))
async def COVID(app: Ariadne, group: Group):
    top_10, img = await get_COVID_19()
    await app.send_group_message(group, MessageChain([
        "新型冠状病毒前10:\n"+"\n".join(top_10),
        Image(data_bytes=img)
    ]))

async def get_COVID_19(pic=True):
    headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/81.0.4044.69 Safari/537.36 Edg/81.0.416.34'}
    async with aiohttp.request("GET", "https://c.m.163.com/ug/api/wuhan/app/data/list-total", headers=headers) as r:
        reponse = await r.json()
    country_total = reponse['data']['areaTree']
    country_total.sort(key=lambda s: s['total']['confirm'], reverse=True)
    get = [(f"{a['name']}:{a['total']['confirm']}例 "
            f"新增{a['today']['confirm']}\n{a['lastUpdateTime']}")
           for a in country_total[:10]]

    x, y1, y2 = [(a['name'], a['total']['confirm'] - a['today']['confirm'],
                  (a['today']['confirm'] if a['today']['confirm'] is not None else 0))
                 for a in country_total[:20]]

    if not pic:
        return get, b''

    # 创建一个点数为 8 x 6 的窗口, 并设置分辨率为 80像素/每英寸
    plt.figure(figsize=(30, 20), dpi=100)
    plt.style.use("dark_background")
        # 包含每个柱子下标的序列
    index = np.arange(20)
    # 柱子的宽度
    width = 0.5
    # 绘制柱状图, 每根柱子的颜色
    plt.bar(index, y1, width, label="昨日累计人数", color="#FF0000")
    plt.bar(index, y2, width, label="今日新增人数", color="#FF8C00",bottom=y1)
    # 设置横轴标签
    plt.xlabel('各个国家')
    # 设置纵轴标签
    plt.ylabel('累计感染人数')
    # 添加标题
    plt.title('各国新冠病毒感染人数排行')
    # 添加纵横轴的刻度
    plt.xticks(index, x)
    # 添加图例
    plt.legend(loc="upper right")


    for a, b, c in zip(index, y1, y2):
        plt.text(a, b + c + 0.05 , str(b + c),
         ha='center', va='bottom', fontsize=10)

    read = BytesIO()
    plt.savefig(read, format = "png", bbox_inches='tight')
    plt.clf()
    return get, read.getvalue()