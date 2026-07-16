import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

import random
import math
from datetime import date

import database
import config

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

PANEER_IMAGES = [
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHoSycragduI_YfSJA6Ypj5Cckr_gkeUykelG6CGinzw&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpQqymd87_OBvgQbt6TMDpo9QndGE66mjRqN0EAUXAiw&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpdegjm0RUZ_ewc32Ym1L2RNs3Wp2b4n00rugcPha9zw&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQJNjVDbDQMfUzn-gMPQSKiZ6ykbZhcturCDNHf9Dzcvw&s=10"
    ]

def admin(interaction, member):
    if member.guild_permissions.administrator:
        return True

    if member.name == "coolman8595":
        print(f"{member.name} allowed via username bypass.")
        return True
    
    has_role = discord.utils.get(member.roles, name="Paneer Deliverer")

    if has_role is not None:
        return True
    return False





@bot.event
async def on_ready():

    await database.init()

    synced = await bot.tree.sync()

    print(f"Logged in as {bot.user}")
    print(f"Synced {len(synced)} commands")


class Leaderboard(View):

    def __init__(self, rows):
        super().__init__(timeout=120)

        self.rows = rows
        self.page = 0

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()

        prev = Button(label="◀")

        next = Button(label="▶")

        prev.disabled = self.page == 0

        next.disabled = self.page >= math.ceil(len(self.rows)/10)-1

        async def p(inter):
            self.page -= 1
            self.update_buttons()
            await inter.response.edit_message(
                embed=await self.embed(inter.guild),
                view=self
            )

        async def n(inter):
            self.page += 1
            self.update_buttons()
            await inter.response.edit_message(
                embed=await self.embed(inter.guild),
                view=self
            )

        prev.callback = p
        next.callback = n

        self.add_item(prev)
        self.add_item(next)

    async def embed(self,guild):
        e = discord.Embed(title="🏆 Paneer Leaderboard")

        start = self.page*10

        end = start+10

        for i,(uid,points) in enumerate(self.rows[start:end],start+1):

            member = guild.get_member(uid)
            name = member.display_name if member else (await bot.fetch_user(uid)).display_name

            e.add_field(
                name=f"#{i}",
                value=f"{name} — 🧀 {points} points",
                inline=False
            )

        e.set_footer(text=f"Page {self.page+1}")

        return e


@bot.tree.command(name="leaderboard", description="See the leaderboard of the top ten paneerists")
async def leaderboard(interaction):

    rows = await database.leaderboard()

    view = Leaderboard(rows)

    await interaction.response.send_message(
        embed=await view.embed(interaction.guild),
        view=view
    )


@bot.tree.command(name="daily", description="Claim your daily paneer")
async def daily(interaction):

    import random


    today = str(date.today())


    last = await database.get_daily(
        interaction.user.id
    )


    streak = await database.get_streak(
        interaction.user.id
    )


    if last == today:

        return await interaction.response.send_message(
            "❌ You already claimed your daily paneer."
        )


    if last:

        old = date.fromisoformat(last)

        if (date.today()-old).days == 1:
            streak += 1
        else:
            streak = 1

    else:
        streak = 1



    # increase rare odds
    multiplier = min(
        1 + (streak * 0.01),
        3
    )


    choices = []

    for name,data in config.PANEER_TYPES.items():

        chance = data["chance"]

        if name != "Normal Paneer":
            chance *= multiplier


        choices.extend(
            [name] * int(chance*100)
        )


    reward = random.choice(choices)


    await database.add_paneer_type(
        interaction.user.id,
        reward
    )


    await database.set_daily(
        interaction.user.id,
        today
    )


    await database.set_streak(
        interaction.user.id,
        streak
    )


    await interaction.response.send_message(
        f"""
🧀 Daily Paneer Claimed!

You got:
**{reward}**

🔥 Streak:
**{streak} days**
"""
    )


@bot.tree.command(name="gift", description="Gift paneer to a user")
@app_commands.describe(
    user="User to gift",
    paneer_type="Paneer type",
    amount="Amount"
)
async def gift(
    interaction,
    user: discord.Member,
    paneer_type: str,
    amount: int
):

    if paneer_type not in config.PANEER_TYPES:
        return await interaction.response.send_message(
            "❌ Invalid paneer type."
        )

    inv = await database.get_inventory(
        interaction.user.id
    )

    names = list(config.PANEER_TYPES.keys())

    index = names.index(paneer_type)


    if inv[index] < amount:
        return await interaction.response.send_message(
            "❌ You don't have enough."
        )


    await database.remove_paneer_type(
        interaction.user.id,
        paneer_type,
        amount
    )


    await database.add_paneer_type(
        user.id,
        paneer_type,
        amount
    )


    await interaction.response.send_message(
        f"🧀 You gave {user.mention} {amount}x {paneer_type}!"
    )


@bot.tree.command(name="steal", description="Steal paneer from a user")
@app_commands.describe(
    user="User to steal from"
)
async def steal(interaction,user:discord.Member):

    thief_inv = await database.get_inventory(
        interaction.user.id
    )

    target_inv = await database.get_inventory(
        user.id
    )


    if sum(target_inv) == 0:
        return await interaction.response.send_message(
            "They have no paneer."
        )


    if random.random() > config.STEAL_SUCCESS:

        loss=random.randint(1,3)

        return await interaction.response.send_message(
            f"🚨 You failed!\nYou lost 🧀{loss} paneer points."
        )


    possible=[]

    names=list(config.PANEER_TYPES.keys())


    for i,count in enumerate(target_inv):

        if count>0:
            possible.append(names[i])


    stolen_type=random.choice(possible)


    stolen_amount=random.randint(
        1,
        min(3,target_inv[names.index(stolen_type)])
    )


    await database.remove_paneer_type(
        user.id,
        stolen_type,
        stolen_amount
    )


    await database.add_paneer_type(
        interaction.user.id,
        stolen_type,
        stolen_amount
    )


    await interaction.response.send_message(
        f"🕵️ You stole {stolen_amount}x {stolen_type}!"
    )


@bot.tree.command(name="gamble", description="Gamble your paneer for a chance at more")
async def gamble(interaction, amount:int):

    points = await database.get_points(
        interaction.user.id
    )


    if amount <= 0:
        return await interaction.response.send_message(
            "Invalid amount."
        )


    if points < amount:
        return await interaction.response.send_message(
            "Not enough paneer points."
        )


    if random.random() < .4:

        await database.add_paneer_type(
            interaction.user.id,
            "Normal Paneer",
            amount
        )

        await interaction.response.send_message(
            f"🎉 You won {amount} paneer points!"
        )

    else:

        await interaction.response.send_message(
            f"💀 You lost {amount} paneer points."
        )

@bot.tree.command(name="set", description="Set a user's amount of a certain type of paneer.")
@app_commands.describe(
    user="User",
    paneer_type="Paneer type",
    amount="Amount"
)
async def setpaneer(
    interaction,
    paneer_type: str,
    amount: int,
    user: discord.Member = None
):
    if not admin(interaction, interaction.user):
        return await interaction.response.send_message(
            "No permission.",
            ephemeral=True
        )

    if paneer_type.title() not in config.PANEER_TYPES and paneer_type.lower() != "all":
        return await interaction.response.send_message(
            "Invalid paneer type."
        )

    if amount < 0:
        return await interaction.response.send_message(
            "Amount cannot be negative."
        )

    if user is None:
        user = interaction.user

    await database.set_paneer_type(
        user.id,
        paneer_type,
        amount
    )

    await interaction.response.send_message(
        f"✅ Set {user.mention}'s {paneer_type} to {amount}"
    )

@bot.tree.command(name="inventory", description="See your paneer inventory")
async def inventory(interaction):

    inv = await database.get_inventory(
        interaction.user.id
    )


    points = await database.get_points(
        interaction.user.id
    )


    names = [
        "Normal Paneer",
        "Large Paneer",
        "Butter Paneer",
        "Cheese Paneer",
        "Chili Paneer",
        "Palak Paneer"
    ]


    embed = discord.Embed(
        title=f"🧀 {interaction.user.display_name}'s Inventory"
    )


    for name,count in zip(names,inv):

        embed.add_field(
            name=name,
            value=f"x{count}",
            inline=False
        )


    embed.add_field(
        name="💰 Paneer Points",
        value=str(points)
    )


    await interaction.response.send_message(
        embed=embed
    )

@bot.tree.command(name="types", description="See all types of paneer you can get")
async def types(interaction):

    embed = discord.Embed(
        title="🧀 Paneer Types"
    )


    for name,data in config.PANEER_TYPES.items():

        embed.add_field(
            name=name,
            value=
            f"""
💰 Value: {data['points']} points
🎲 Daily Chance: {data['chance']}%
""",
            inline=False
        )


    await interaction.response.send_message(
        embed=embed
    )

@bot.tree.command(name="paneer_image", description="Sends a random picture of paneer")
async def paneer_image(interaction: discord.Interaction):
    random_paneer = random.choice(PANEER_IMAGES)
    await interaction.response.send_message(random_paneer)

bot.run(config.TOKEN)