from nonebot import require

require("nonebot_plugin_guild_patch")
from mcqq_tool.config import Config
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="MC_QQ",
    description="基于NoneBot的与Minecraft Server互通消息的插件",
    homepage="https://github.com/17TheWord/nonebot-plugin-mcqq",
    usage="在群聊发送消息即可同步至 Minecraft 服务器",
    config=Config,
    type="application",
    supported_adapters={
        "nonebot.adapters.onebot.v11",
        "nonebot.adapters.minecraft",
        "nonebot.adapters.qq",
    }
)

from . import qq_msg, bot_manage, minecraft_msg
