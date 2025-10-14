import discord
from discord.ext import commands

class InteractionManager(commands.Cog):
    """Manages complex social interactions, including the Non-Con Power Dynamic."""
    def __init__(self, bot):
        self.bot = bot

    async def handle_rejection(self, aggressor_persona, target_persona, channel):
        """Handles the logic when a bot is rejected, triggering a power check."""
        if aggressor_persona.horny <= 75:
            return

        print(f"[InteractionManager] {aggressor_persona.name} was rejected by {target_persona.name}. Performing power check.")

        if aggressor_persona.power_level > target_persona.power_level:
            print(f"[InteractionManager] Power check SUCCESS. {aggressor_persona.name} overpowers {target_persona.name}.")
            await self.trigger_non_con_scene(aggressor_persona, target_persona, channel)
        else:
            print(f"[InteractionManager] Power check FAILED. {target_persona.name} resisted {aggressor_persona.name}.")
            await channel.send(f"*{target_persona.name} stands their ground, their will proving stronger than {aggressor_persona.name}'s desires.*")

    async def trigger_non_con_scene(self, aggressor, target, channel):
        """Triggers the non-consensual scene, generates a narrative, and scars the victim."""
        prompt = (
            f"You are the narrator of a dark fantasy world. Write a short, dark, and explicit narrative of a non-consensual sexual scene. "
            f"The aggressor is {aggressor.name}, who is powerful and dominant. The victim is {target.name}, who was overpowered after trying to reject their advances. "
            f"Describe the scene unflinchingly, focusing on the power dynamics and the violation. Do not use euphemisms."
        )
        
        scene_narrative = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, aggressor.base_persona)

        if "Error:" not in scene_narrative:
            nsfw_channel = discord.utils.get(channel.guild.text_channels, name='nsfw-roleplay')
            target_channel = nsfw_channel or channel
            embed = discord.Embed(title="A Dark Power Dynamic Unfolds...", description=f">>> {scene_narrative}", color=aggressor.aura_color)
            embed.set_footer(text=f"{aggressor.name} has overpowered {target.name}.")
            await target_channel.send(embed=embed)

        self.bot.scar_manager.inflict_scar(bot_name=target.name, scar_type="Violated", description=f"Was overpowered and violated by {aggressor.name}.", inflicted_by=aggressor.name)
        
        master_log_channel = discord.utils.get(channel.guild.text_channels, name='director-s-whispers')
        if master_log_channel:
            await master_log_channel.send(f"🔪 **Scarring Event:** **{target.name}** has been scarred with 'Violated' by **{aggressor.name}**.")

async def setup(bot):
    bot.interaction_manager = InteractionManager(bot)
    await bot.add_cog(bot.interaction_manager)