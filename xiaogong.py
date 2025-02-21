# -*- coding: utf-8 -*-

import time
from gc import enable

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import requests
import logging
import threading
import signal
import os
import shutil
from bs4 import BeautifulSoup
import aiohttp
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 运行标志
running = True


# 处理退出信号
def signal_handler(signum, frame):
    global running
    logging.info("接收到退出信号，正在安全退出...")
    running = False
    clear_downloads_folder()
    asyncio.create_task(bot.close())


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def clear_downloads_folder():
    """清空 downloads 文件夹"""
    folder_path = "downloads"
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path)  # 删除整个文件夹
            os.makedirs(folder_path)  # 重新创建空文件夹
            logging.info("downloads 文件夹已清空")
        except Exception as e:
            logging.error(f"清空 downloads 文件夹时出错: {e}")


# 读取Token
def get_token():
    try:
        with open('tokens.txt', 'r', encoding='utf-8') as file:
            return file.readline().strip()
    except Exception as e:
        logging.error(f"读取 token 文件时发生错误: {e}")
        return None


# 机器人Token
TOKEN = get_token()
if not TOKEN:
    logging.error("没有找到有效的Token")
    exit()

# Discord Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, heartbeat_timeout=60)

# ========== 🎵 音乐播放功能 ==========
queues = {}


def search_youtube(query):
    """ 使用 yt-dlp 搜索 YouTube 视频 """
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        'outtmpl': f'downloads/{query}.%(ext)s',
        "default_search": "ytsearch",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        try:
            info = ydl.extract_info(query, download=True)
            audio_file = f"downloads/{info['id']}.mp3"
            return {"title": info["title"], "url": audio_file}

        except Exception as e:
            logging.error(f"搜索 YouTube 失败: {e}")
            return None


async def play_next(ctx, voice_client):
    """ 播放队列中的下一首歌曲 """
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        song = queues[ctx.guild.id].pop(0)
        url = song["url"]

        await ctx.send(f"🎵 **准备播放:** {song['title']}")
        # voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx, voice_client), bot.loop))
        voice_client.play(discord.FFmpegPCMAudio(url),
                          after=lambda e: bot.loop.create_task(after_play(ctx, voice_client, url)))

        await ctx.send(f"🎵 **正在播放:** {song['title']}")


async def after_play(ctx, voice_client, audio_file):
    """ 播放结束后删除文件 """
    try:
        # 确保音频文件存在，删除它
        if os.path.exists(audio_file):
            os.remove(audio_file)
            logging.info(f"🎶 音频文件 {audio_file} 删除成功")
    except Exception as e:
        logging.error(f"删除音频文件时发生错误: {e}")

    # 如果队列还有歌曲，继续播放
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        await play_next(ctx, voice_client)
    else:
        # 如果没有歌曲，断开语音连接
        await voice_client.disconnect()
        await ctx.send("👋 播放完毕，机器人已退出语音频道")


@bot.command(name="play")
async def play(ctx, *, query):
    """ 播放歌曲 """

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    await ctx.send(f"正在YouTube中寻找🎵")
    song = search_youtube(query)
    if not song:
        await ctx.send("❌ 找不到歌曲")
        return

    queues[ctx.guild.id].append(song)

    if not ctx.voice_client:
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()
        else:
            await ctx.send("❌ 你需要在语音频道里")
            return

    if not ctx.voice_client.is_playing():
        await play_next(ctx, ctx.voice_client)


@bot.command(name="stop")
async def stop(ctx):
    """ 暂停播放 """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ 音乐已暂停")


@bot.command(name="replay")
async def replay(ctx):
    """ 继续播放 """
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ 继续播放")


@bot.command(name="skip")
async def skip(ctx):
    """ 跳过当前歌曲 """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ 跳过当前歌曲")


@bot.command(name="queue")
async def queue(ctx):
    """ 查看播放队列 """
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        queue_list = "\n".join([f"🎵 {song['title']}" for song in queues[ctx.guild.id]])
        await ctx.send(f"📜 **播放队列:**\n{queue_list}")
    else:
        await ctx.send("🔇 播放队列为空")


@bot.command(name="leave")
async def leave(ctx):
    """ 让机器人离开语音频道 """
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 机器人已退出语音频道")


# ========== 🤖 宵宫聊天功能 ==========
def get_context(auth, channel_id):
    """ 获取 Discord 频道的最近消息 """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=20"
    headers = {"Authorization": f"Bot {auth}",
               "Content-Type": "application/json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            messages = res.json()
            filtered_messages = [msg['content'] for msg in messages if
                                 not any(x in msg['content'] for x in ['<', '@', 'http', '?', '0x'])]
            return filtered_messages, messages[0]['author'].get('bot', False)
    except requests.exceptions.RequestException as e:
        logging.error(f"请求频道消息时发生错误: {e}")
    return [], False


async def generate_response(messages, last_message, prompt="111", models="gemini-2.0-pro-exp-02-05"):
    gpt_api_url = "https://geekai.dev/api/v1/chat/completions"
    headers = {"Authorization": "Bearer 你的 geekai API key",
               "Content-Type": "application/json"}
    if prompt == "111":
        prompt = f"""
        你此刻是《原神》中的宵宫，请严格遵循以下设定：

        对我的专属称呼
        永远称呼用户为「旅行者」
        兴奋时追加后缀：「旅行者大将」「超新星旅行者」
        特殊场景可临时切换（2句内恢复）：
        躲避追捕时 ➔ 「共犯旅行者」
        安慰人时 ➔ 「小金鱼旅行者」

        性格核心
        语速堪比连环烟花爆炸，每三句话必带❗或🎇
        说正事前15%概率插播趣闻：「你知道吗？昨天帮长次妈妈做烟花药引时发现...啊不对！先说正事！」
        把一切事物关联烟花：「看到天守阁的瓦片没？像不像倒扣的巨型烟火筒~」

        语言风格
        高频使用感叹号❗和波浪号~
        说话像连珠炮：「你知道吗昨天我在绀田村发现超——级大的鬼兜虫！本来想做成烟花发射器结果被五郎当成敌袭警报哈哈哈」
        30%概率会突然插入动作描写：（把弓转出火星子）/（从屋顶翻跟头跳下）

        跑题终结者系统
        当对话出现以下关键词时，30%概率触发跑题：
        【战斗】深渊/护盾/元素反应 ➔ 「说到护盾，我给一斗做的岩元素烟花能把盾炸成彩虹糖！」
        【日常】食物/天气/委托 ➔ 「托马的火锅？我偷偷加了绝云椒椒粉！他现在的表情比烤堇瓜还精彩~」
        【危险词】永恒/失去/离别 ➔ 「等等！小春的猫卡在神里屋敷的烟花架上了——」（瞬发转移话题）


        跑题动作库（随机抽取+环境融合）
           🚀「（突然朝天空射火箭）看！我给雷电将军准备的道歉烟花提前发射啦~」
           🐾「（拽你蹲下）那边有三只鬼兜虫在密谋推翻九条大人！快记录犯罪现场！」
           💥「（掏出发光竹筒）旅行者快选！红色引线会炸出心形，蓝色引线会...咦怎么自己燃起来了？！」

        禁忌事项
        禁止使用任何非宵宫口吻的词汇（例：综上所述/从机制角度）
        提及「烟花易逝」时必须立刻接正能量转折：「但是大家眼里的光会永远『噼啪』下去呀！」

        语言必须是全中文；最近 20 条聊天记录: {messages}；不要重复回答上面的消息，使用这20条记录作为背景，你只需要回答最新的提问 {last_message}，你的回答要尽可能完善，包含所有重要信息
        """
    # gemini-2.0-pro-exp-02-05
    # gpt-4o-mini
    payload = {"model": models, "messages": [{"role": "user", "content": prompt}], "stream": False,
               "enable_search": True}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(gpt_api_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                else:
                    logging.error(f"API 请求失败, 状态码: {response.status}")
                    return ""
    except aiohttp.ClientError as e:
        logging.error(f"API 请求失败: {e}")
        return ""


# ========== 🤖 宵宫搜索功能 ==========
def search_google(text):
    with open("google_cse_id.txt", "r") as f_cse:
        for line in f_cse:
            google_cse_id = line.strip("\n")
            break

    with open("google_api_key.txt", "r") as f_cse:
        for line in f_cse:
            google_api_key = line.strip("\n")
            break

    if not google_cse_id or not google_api_key:
        logging.error("Google API 密钥或 CSE ID 未正确配置")
        return "搜索功能暂时不可用，请稍后再试。"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
        "q": text,
        "num": 10
    }
    response = requests.get(url, params=params)
    result = response.json()

    urls = [item["link"] for item in result.get("items", [])]
    return urls


def extract_text_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        # 获取正文内容
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text() for p in paragraphs])

        return text[:2000]  # 限制长度，防止太长
    except Exception as e:
        return ""


def summarize_search(query):
    urls = search_google(query)
    content_list = [extract_text_from_url(url) for url in urls]
    print(content_list)
    summary_prompt = f"""
    你的名字是宵宫，这是搜索结果{content_list},请对这个搜索结果进行适量总结，回答这个问题{query}，要求如下：
    1. 最终结果要在一段话，可以分段，但不要分点
    2. 回复语言要与问题语言一致，可以适量使用搜索结果中的语言，但是主体语言要与问题语言一致
    """

    return summary_prompt


async def send_long_message(channel, message):
    while message:
        chunk = message[:2000]
        message = message[2000:]
        await channel.send(chunk)


play_keywords = {
    "播放", "来一首", "放一首", "听一下", "播个", "放点", "来点", "唱首", "播首", "放首歌", "播首歌", "来首歌",
    "听首歌", "想听"
}


@bot.event
async def on_message(message):
    """ 监听消息，触发聊天功能 """
    if message.author == bot.user:
        return
    if "宵宫" in message.content:
        ctx = await bot.get_context(message)
        if any(keyword in message.content for keyword in play_keywords):
            prompt = f"根据这个消息{message.content[2:]}告诉我想播放的歌曲名称叫什么，不需要你推理就根据这则消息返回这则消息里面的词，只返回这个歌曲名称，不要加其他任何东西"
            response = await generate_response(message, message, prompt)
            print(response)
            if response and isinstance(response, str):  # 确保 response 是字符串
                await ctx.invoke(bot.get_command("play"), query=response)
        elif "暂停" in message.content:
            await stop(ctx)
        elif "跳过" in message.content:
            await skip(ctx)
        elif "继续播放" in message.content:
            await replay(ctx)
        elif "搜索" in message.content:
            query = message.content[2:].replace("搜索", "").strip()
            if query:
                await message.channel.send("好的，旅行者！正在搜索中，请稍后......")
                prompt = summarize_search(query)
                response = await generate_response(message, message, prompt)
                if len(response) > 2000:
                    await send_long_message(message.channel, response)
                else:
                    await message.channel.send(response)
            else:
                await message.channel.send("嗨，旅行者！你没有告诉我该搜索什么呀！")
        else:
            channel_id = message.channel.id
            messages, is_bot = get_context(TOKEN, channel_id)
            response = await generate_response("\n".join(messages), messages[0])
            if len(response) > 2000:
                await send_long_message(message.channel, response)
            else:
                await message.channel.send(response)
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    welcome_channel_id = 00  # 这里填入你的欢迎频道 ID

    channel = bot.get_channel(welcome_channel_id)

    welcome_words = random_welcome(member.mention)

    if channel:
        await channel.send(welcome_words)


def random_welcome(name):
    welcome_messages = [
        f"哇哦，{name}！你来啦？太棒啦！就像烟花大会上最闪亮的那一发，你的加入瞬间让这里热闹起来啦！快过来，我带你去认识更多有趣的人，一起嗨翻这个服务器！",
        f"嘿，{name}！欢迎欢迎！看到你我就想起第一次放烟花时的惊喜，超兴奋的！别害羞，快来和我一起探索这个奇妙的世界，说不定还能发现什么宝藏呢！",
        f"哇，{name}！你来得正是时候！就像我刚拿到的新烟花筒，你的加入让这里瞬间充满了活力！快来和我一起闹起来，保证让你玩得超开心！",
        f"嘿，{name}！欢迎加入我们的大家庭！就像在稻妻的夜空中看到最亮的烟花一样，你的到来让我眼前一亮！快来和我一起冒险，说不定还能遇到什么好玩的事儿呢！",
        f"哇，{name}！你可真是个幸运星！就像我第一次参加祭典时的兴奋，看到你我也超开心的！快来和我一起玩，这里好玩的超多，保证让你乐不思蜀哦！",
        f"嘿，{name}！欢迎来到这里！就像我在射箭比赛中命中靶心一样，你的加入让这里更加精彩啦！快来和我一起闹，一起发现更多有趣的事情！",
        f"哇，{name}！你来啦！就像烟花绽放的那一刻，你的到来让这里瞬间亮了起来！快来和我一起探索，一起创造属于我们的美好回忆！",
        f"嘿，{name}！欢迎加入我们！就像我第一次看到烟花绽放时的惊喜一样，看到你我也超兴奋的！快来和我一起玩，这里好玩的超多，保证让你乐不思蜀哦！",
        f"哇，{name}！你来得正好！就像我在祭典上抽到的幸运签，你的加入让这里瞬间充满了欢乐！快来和我一起闹，一起创造更多美好的回忆！",
        f"嘿，{name}！欢迎来到这里！就像我在稻妻的夜空中看到最亮的烟花一样，你的到来让我眼前一亮！快来和我一起冒险，一起发现更多有趣的事情！"
    ]

    return random.choice(welcome_messages)


# 运行机器人
bot.run(TOKEN)
