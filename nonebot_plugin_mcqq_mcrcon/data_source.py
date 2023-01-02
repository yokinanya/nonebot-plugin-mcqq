import json
import mcrcon
import websockets

from nonebot import logger, get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot_plugin_guild_patch import GuildMessageEvent

from typing import Union
from .utils import (
    send_msg_to_qq,
    get_mc_qq_ip,
    get_mc_qq_ws_port,
    get_mc_qq_mcrcon_password,
    msg_process,
    get_mc_qq_servers_list,
    get_mc_qq_mcrcon_rcon_list,
)

CLIENTS = []


async def ws_client(websocket):
    msg = {}
    try:
        async for message in websocket:
            msg = json.loads(message)
            if msg['event_name'] == "ConnectEvent":
                mcrcon_connect = mcrcon.MCRcon(
                    websocket.remote_address[0],
                    get_mc_qq_mcrcon_password(),
                    get_mc_qq_mcrcon_rcon_list()[msg['server_name']]
                )
                mcrcon_connect.connect()
                logger.success(f"[MC_QQ_Rcon]丨[Server:{msg['server_name']}] 的 Rcon 已连接")
                CLIENTS.append(
                    {"server_name": msg['server_name'], "ws_client": websocket, "mcrcon_connect": mcrcon_connect}
                )
                logger.success(f"[MC_QQ_Rcon]丨[Server:{msg['server_name']}] 已连接至 WebSocket 服务器")
            # 发送消息到QQ
            else:
                await send_msg_to_qq(bot=get_bot(), recv_msg=message)
    except websockets.WebSocketException:
        CLIENTS.remove([msg['server_name'], websocket])
    if websocket.closed:
        mcrcon_connect.disconnect()
        logger.error(f"[MC_QQ_Rcon]丨[Server:{msg['server_name']}] 的 WebSocket、Rcon 连接已断开")


# 启动 WebSocket 服务器
async def start_ws_server():
    global ws
    ws = await websockets.serve(ws_client, get_mc_qq_ip(), get_mc_qq_ws_port())
    logger.success("[MC_QQ_Rcon]丨WebSocket 服务器已开启")


# 关闭 WebSocket 服务器
async def stop_ws_server():
    global ws
    ws.close()


# 关闭 MCRcon 连接
async def mcrcon_disconnect(mcrcon_connect: mcrcon.MCRcon):
    mcrcon_connect.disconnect()


# 发送消息到 Minecraft
async def send_msg_to_mc(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    text_msg, command_msg = await msg_process(bot=bot, event=event)
    client = await get_client(event=event)
    if client and client['mcrcon_connect']:
        client['mcrcon_connect'].command(command_msg)
        logger.success(f"[MC_QQ_Rcon]丨发送至 [server:{client['server_name']}] 的消息 \"{text_msg}\"")


# 发送命令到 Minecraft
async def send_command_to_mc(event: Union[GroupMessageEvent, GuildMessageEvent]):
    client = await get_client(event=event)
    if client and client['mcrcon_connect']:
        client['mcrcon_connect'].command(event.raw_message.strip("/mcc"))
        logger.success(
            f"[MC_QQ_Rcon]丨发送至 [server:{client['server_name']}] 的命令 \"{event.raw_message.strip('/mcc')}\"")


# 获取 服务器名、ws客户端、Rcon连接
async def get_client(event: Union[GroupMessageEvent, GuildMessageEvent]):
    for per_client in CLIENTS:
        try:
            for per_server in get_mc_qq_servers_list():
                # 如果 服务器名 == ws客户端中记录的服务器名，且ws客户端存在
                if per_server[0] == per_client['server_name'] and per_client['ws_client']:
                    if event.message_type == "group":
                        if event.group_id in per_server[1]:
                            return per_client
                    if event.message_type == "guild":
                        if [event.guild_id, event.channel_id] in per_server[2]:
                            return per_client
        except mcrcon.MCRconException:
            logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{per_client['server_name']}] 的过程中出现了错误")
            # 连接关闭则移除客户端
            CLIENTS.remove(per_client)
            continue
    return None
