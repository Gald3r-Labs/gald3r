"""
gald3r AstrBot Plugin
Brings gald3r project management skills into AstrBot agent runtime.
"""
from astrbot.api.plugin import AstrBotPlugin
from astrbot.api.skill import SkillManager

class GaldPlugin(AstrBotPlugin):
    async def initialize(self):
        await SkillManager.load_from_directory("skills/")
