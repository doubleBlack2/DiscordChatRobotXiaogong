# Discord Bot - 音乐播放与宵宫聊天机器人

这是一个基于 Discord 的多功能机器人，支持音乐播放和以《原神》角色宵宫风格进行聊天的功能。机器人使用 Python 编写，依赖于 `discord.py`、`yt_dlp` 和其他库。

## 功能介绍

### 音乐播放功能
- **播放歌曲**：通过 YouTube 搜索并播放歌曲。
- **暂停/继续播放**：控制音乐播放状态。
- **跳过歌曲**：跳过当前播放的歌曲。
- **查看队列**：显示当前播放队列。
- **退出语音频道**：让机器人离开当前语音频道。

### 宵宫聊天功能
- **角色扮演**：机器人以《原神》中的宵宫角色进行对话，具有独特的语言风格和行为。
- **搜索功能**：通过 Google 搜索并总结相关内容，以宵宫的口吻回复。
- **音乐播放指令**：支持通过聊天指令播放音乐。

### 其他功能
- **欢迎新成员**：当新成员加入服务器时，发送随机欢迎消息。
- **信号处理**：支持安全退出，清理下载文件夹。

## 运行环境

- **Python**：3.8 或更高版本。
- **依赖库**：
  - `discord.py`
  - `yt_dlp`
  - `aiohttp`
  - `requests`
  - `beautifulsoup4`
- **其他工具**：
  - `ffmpeg`（用于音频处理）

## 配置文件

- **`tokens.txt`**：存储 Discord Bot 的 Token。
- **`google_cse_id.txt` 和 `google_api_key.txt`**：存储 Google Custom Search 的 API 密钥和 CSE ID。
- **`downloads` 文件夹**：用于存储下载的音频文件。

## 使用方法

### 安装依赖
在终端中运行以下命令以安装所需的 Python 库：
```bash
pip install -r requirements.txt
```

### 配置文件
1. 创建 `tokens.txt` 文件，写入 Discord Bot 的 Token。
2. 创建 `google_cse_id.txt` 和 `google_api_key.txt` 文件，分别写入 Google Custom Search 的 CSE ID 和 API 密钥。

### 运行机器人
运行以下命令启动机器人：
```bash 
python bot.py
```

### 使用命令
- 在 Discord 中使用 `!play <歌曲名>` 播放音乐。
- 使用 `!pause`、`!resume`、`!skip`、`!queue` 和 `!leave` 控制音乐播放。
- 通过提及机器人并输入指令（如“宵宫，播放音乐”）触发宵宫音乐功能。
- 通过提及机器人并输入暂停，继续，跳过和继续播放指令触发音乐播放功能。
- 通过提及机器人并输入句子（如“宵宫，你好”）触发宵宫聊天功能。
- 通过提及机器人并输入搜索关键词（如“宵宫，搜索关键词”）触发宵宫搜索功能。
- 机器人会在新成员加入服务器时发送随机欢迎消息。

## 注意事项

- 确保 `ffmpeg` 已安装并添加到系统路径中。
- 如果遇到网络问题，请检查 API 链接的合法性并适当重试。
- 机器人需要足够的权限才能连接到语音频道。

## 问题反馈

如果在使用过程中遇到问题，请随时联系开发者或提交 Issue。
邮箱：muyuan_yan@126.com