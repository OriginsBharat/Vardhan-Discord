from discord.ext import commands

class CommandFactory(commands.Cog):
    """A factory for creating and removing commands dynamically."""
    def __init__(self, bot):
        self.bot = bot
        self.created_commands = []

    def create_command(self, name, description, callback):
        """Creates a new command and adds it to the bot."""
        if self.bot.get_command(name):
            self.bot.remove_command(name)

        new_command = commands.Command(callback, name=name, help=description)
        self.bot.add_command(new_command)
        self.created_commands.append(name)
        print(f"[CommandFactory] Dynamically created command: !{name}")

    def remove_all_created_commands(self):
        """Removes all dynamically created commands."""
        for name in self.created_commands:
            self.bot.remove_command(name)
        self.created_commands = []
        print("[CommandFactory] Cleared all dynamic event commands.")

async def setup(bot):
    bot.command_factory = CommandFactory(bot)
    await bot.add_cog(bot.command_factory)