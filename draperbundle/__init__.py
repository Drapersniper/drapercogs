# -*- coding: utf-8 -*-
from .publishermanager import PublisherManager
from .pcspecs import PCSpecs
from .status import MemberStatus
from .gamingprofile import GamingProfile
from .customchannels import CustomChannels
from .dynamicchannels import DynamicChannels


def setup(bot):
    bot.add_cog(DynamicChannels(bot))
    bot.add_cog(CustomChannels(bot))
    bot.add_cog(GamingProfile(bot))
    bot.add_cog(MemberStatus(bot))
    bot.add_cog(PCSpecs(bot))
    bot.add_cog(PublisherManager(bot))
