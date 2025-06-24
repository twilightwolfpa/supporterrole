import discord
from redbot.core import commands, Config, app_commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.modhelper import parse_extension
import asyncio

# Define a constant for the cog's name (useful for config)
COG_NAME = "SupporterRole"

class SupporterRole(commands.Cog):
    """
    A cog to assign/remove a specific role based on the presence of other roles.
    Now supports up to 5 condition roles (A, B, C, E, F) and one target role (D).
    """

    def __init__(self, bot):
        self.bot = bot
        # Use Config for guild-specific settings (role IDs)
        self.config = Config.guild(self)

        default_guild_settings = {
            "role_a_id": None,
            "role_b_id": None,
            "role_c_id": None,
            # --- NEW CODE ---
            "role_e_id": None,
            "role_f_id": None,
            # --- END NEW CODE ---
            "role_d_id": None,
            "scan_on_join": False, # Option to scan on member join
        }
        self.config.register_guild(**default_guild_settings)

    async def cog_load(self):
        """Register the listener on cog load."""
        self.bot.add_listener(self.on_member_update, 'on_member_update')
        self.bot.add_listener(self.on_member_join, 'on_member_join')


    async def cog_unload(self):
        """Remove the listener on cog unload."""
        self.bot.remove_listener(self.on_member_update, 'on_member_update')
        self.bot.remove_listener(self.on_member_join, 'on_member_join')

    async def _get_roles_from_config(self, guild: discord.Guild):
        """Helper to get role objects from configured IDs."""
        config_data = await self.config.guild(guild).all()
        role_a = guild.get_role(config_data["role_a_id"])
        role_b = guild.get_role(config_data["role_b_id"])
        role_c = guild.get_role(config_data["role_c_id"])
        # --- NEW CODE ---
        role_e = guild.get_role(config_data["role_e_id"])
        role_f = guild.get_role(config_data["role_f_id"])
        # --- END NEW CODE ---
        role_d = guild.get_role(config_data["role_d_id"])
        # --- MODIFIED CODE ---
        return role_a, role_b, role_c, role_e, role_f, role_d
        # --- END MODIFIED CODE ---

    async def _check_and_assign_role_d(self, member: discord.Member):
        """
        Checks if a member has role A, B, C, E, or F and assigns/removes role D accordingly.
        """
        guild = member.guild
        if not guild:
            return

        # --- MODIFIED CODE ---
        role_a, role_b, role_c, role_e, role_f, role_d = await self._get_roles_from_config(guild)

        # Ensure Role D is configured, and at least one of the condition roles is configured
        if not role_d:
            # Role D is not set, cannot operate.
            return
        
        # Collect all condition roles that are actually configured
        condition_roles = [role for role in [role_a, role_b, role_c, role_e, role_f] if role is not None]

        if not condition_roles:
            # No condition roles configured, so no logic to apply.
            return

        has_any_condition_role = any(
            role in member.roles for role in condition_roles
        )
        # --- END MODIFIED CODE ---

        has_d = role_d in member.roles

        if has_any_condition_role and not has_d:
            # Member has A, B, C, E, or F but not D, so add D.
            try:
                await member.add_roles(role_d, reason="Supporter role logic: has A, B, C, E, or F")
                # print(f"Added role {role_d.name} to {member.display_name} in {guild.name}") # For debugging
            except discord.Forbidden:
                print(f"Bot lacks permissions to add role {role_d.name} in {guild.name} for {member.display_name}")
            except Exception as e:
                print(f"Error adding role {role_d.name} to {member.display_name}: {e}")
        elif not has_any_condition_role and has_d:
            # Member does not have A, B, C, E, or F but has D, so remove D.
            try:
                await member.remove_roles(role_d, reason="Supporter role logic: lost A, B, C, E, or F")
                # print(f"Removed role {role_d.name} from {member.display_name} in {guild.name}") # For debugging
            except discord.Forbidden:
                print(f"Bot lacks permissions to remove role {role_d.name} in {guild.name} for {member.display_name}")
            except Exception as e:
                print(f"Error removing role {role_d.name} from {member.display_name}: {e}")

    # region Listeners
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Listens for role changes on a member and triggers the check.
        """
        # Only check if roles have actually changed
        if before.roles != after.roles:
            await self._check_and_assign_role_d(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Listens for new members joining and triggers the check if configured.
        """
        config_data = await self.config.guild(member.guild).all()
        if config_data["scan_on_join"]:
            await self._check_and_assign_role_d(member)
    # endregion

    # region Commands
    @commands.group(name="supporterset", aliases=["srset"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    async def supporterset(self, ctx: commands.Context):
        """
        Commands for configuring the Supporter Role cog.
        """
        pass

    @supporterset.command(name="rolea")
    async def supporterset_rolea(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role A' for supporter logic.
        """
        await self.config.guild(ctx.guild).role_a_id.set(role.id)
        await ctx.send(f"Role A set to: `{role.name}`")

    @supporterset.command(name="roleb")
    async def supporterset_roleb(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role B' for supporter logic.
        """
        await self.config.guild(ctx.guild).role_b_id.set(role.id)
        await ctx.send(f"Role B set to: `{role.name}`")

    @supporterset.command(name="rolec")
    async def supporterset_rolec(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role C' for supporter logic.
        """
        await self.config.guild(ctx.guild).role_c_id.set(role.id)
        await ctx.send(f"Role C set to: `{role.name}`")

    # --- NEW CODE ---
    @supporterset.command(name="rolee")
    async def supporterset_rolee(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role E' for supporter logic.
        """
        await self.config.guild(ctx.guild).role_e_id.set(role.id)
        await ctx.send(f"Role E set to: `{role.name}`")

    @supporterset.command(name="rolef")
    async def supporterset_rolef(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role F' for supporter logic.
        """
        await self.config.guild(ctx.guild).role_f_id.set(role.id)
        await ctx.send(f"Role F set to: `{role.name}`")
    # --- END NEW CODE ---

    @supporterset.command(name="roled")
    async def supporterset_roled(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the 'Role D' (the role to be assigned/removed).
        """
        await self.config.guild(ctx.guild).role_d_id.set(role.id)
        await ctx.send(f"Role D set to: `{role.name}`")

    @supporterset.command(name="scanonjoin")
    async def supporterset_scanonjoin(self, ctx: commands.Context, true_or_false: bool):
        """
        Toggle whether to scan new members for supporter roles upon joining.
        `True` to enable, `False` to disable.
        """
        await self.config.guild(ctx.guild).scan_on_join.set(true_or_false)
        status = "enabled" if true_or_false else "disabled"
        await ctx.send(f"Scanning for supporter roles on member join has been {status}.")

    @supporterset.command(name="status")
    async def supporterset_status(self, ctx: commands.Context):
        """
        Show the current supporter role configuration for this guild.
        """
        config_data = await self.config.guild(ctx.guild).all()
        role_a_id = config_data["role_a_id"]
        role_b_id = config_data["role_b_id"]
        role_c_id = config_data["role_c_id"]
        # --- NEW CODE ---
        role_e_id = config_data["role_e_id"]
        role_f_id = config_data["role_f_id"]
        # --- END NEW CODE ---
        role_d_id = config_data["role_d_id"]
        scan_on_join = config_data["scan_on_join"]

        role_a = ctx.guild.get_role(role_a_id) if role_a_id else "Not Set"
        role_b = ctx.guild.get_role(role_b_id) if role_b_id else "Not Set"
        role_c = ctx.guild.get_role(role_c_id) if role_c_id else "Not Set"
        # --- NEW CODE ---
        role_e = ctx.guild.get_role(role_e_id) if role_e_id else "Not Set"
        role_f = ctx.guild.get_role(role_f_id) if role_f_id else "Not Set"
        # --- END NEW CODE ---
        role_d = ctx.guild.get_role(role_d_id) if role_d_id else "Not Set"

        msg = f"**Supporter Role Configuration for {ctx.guild.name}:**\n"
        msg += f"  Role A (trigger): `{role_a.name if role_a != 'Not Set' else role_a}` (ID: `{role_a_id}`)\n"
        msg += f"  Role B (trigger): `{role_b.name if role_b != 'Not Set' else role_b}` (ID: `{role_b_id}`)\n"
        msg += f"  Role C (trigger): `{role_c.name if role_c != 'Not Set' else role_c}` (ID: `{role_c_id}`)\n"
        # --- NEW CODE ---
        msg += f"  Role E (trigger): `{role_e.name if role_e != 'Not Set' else role_e}` (ID: `{role_e_id}`)\n"
        msg += f"  Role F (trigger): `{role_f.name if role_f != 'Not Set' else role_f}` (ID: `{role_f_id}`)\n"
        # --- END NEW CODE ---
        msg += f"  Role D (to assign/remove): `{role_d.name if role_d != 'Not Set' else role_d}` (ID: `{role_d_id}`)\n"
        msg += f"  Scan on Join: `{scan_on_join}`\n"
        await ctx.send(msg)

    @commands.command(name="checksupporterroles")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    async def check_supporter_roles(self, ctx: commands.Context):
        """
        Manually trigger a check for all members in the guild.
        This can be useful after initial setup or if roles were changed manually.
        """
        await ctx.send("Starting scan of all members for supporter role logic. This may take a moment...")
        count_added = 0
        count_removed = 0
        skipped = 0

        # Retrieve configured roles once to avoid repeated config calls inside loop
        # --- MODIFIED CODE ---
        role_a, role_b, role_c, role_e, role_f, role_d = await self._get_roles_from_config(ctx.guild)

        if not role_d:
            await ctx.send(
                "Role D (the target role) is not configured. Please set it using `[p]supporterset roled`."
            )
            return

        # Filter out None values from the condition roles
        condition_roles = [role for role in [role_a, role_b, role_c, role_e, role_f] if role is not None]

        if not condition_roles:
            await ctx.send(
                "No condition roles (A, B, C, E, or F) are configured. "
                "Please set at least one using `[p]supporterset`."
            )
            return
        # --- END MODIFIED CODE ---

        async with ctx.typing():
            for member in ctx.guild.members:
                # --- MODIFIED CODE ---
                has_any_condition_role = any(
                    role in member.roles for role in condition_roles
                )
                # --- END MODIFIED CODE ---
                has_d = role_d in member.roles

                if has_any_condition_role and not has_d:
                    try:
                        await member.add_roles(role_d, reason="Manual supporter role scan")
                        count_added += 1
                    except discord.Forbidden:
                        skipped += 1
                    except Exception:
                        skipped += 1
                elif not has_any_condition_role and has_d:
                    try:
                        await member.remove_roles(role_d, reason="Manual supporter role scan")
                        count_removed += 1
                    except discord.Forbidden:
                        skipped += 1
                    except Exception:
                        skipped += 1
                await asyncio.sleep(0.1) # Be a good citizen, don't spam Discord API

        await ctx.send(
            f"Scan complete!\n"
            f"Role D added to {count_added} members.\n"
            f"Role D removed from {count_removed} members.\n"
            f"Skipped {skipped} members due to permission issues or other errors."
        )

    # endregion

async def setup(bot):
    """
    Adds the cog to the bot.
    """
    await bot.add_cog(SupporterRole(bot))
