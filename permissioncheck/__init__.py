from .permissionschecker import PermissionsChecker


def setup(bot):
    bot.add_cog(PermissionsChecker(bot))
