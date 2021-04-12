import discord
import json
from threading import Thread
from datetime import datetime
from discord.ext import commands

bot = commands.Bot(command_prefix="$")
user = None
admin_id = 0


class NickNotFoundError(Exception):
    pass


def get_pms_from_logfile(nick) -> list:
    with open("pm_logs.json", "r") as pm_logs:
        try:
            data: dict = json.load(pm_logs)
        except json.decoder.JSONDecodeError:
            data: dict = {}
        if nick in data:
            return data[nick]
        else:
            raise NickNotFoundError


@bot.event
async def on_ready():
    global user
    global admin_id
    user = await bot.fetch_user(admin_id)
    print("Bot został uruchomiony.")


@bot.command(name="pms")
async def send_pms(ctx, nick):
    if ctx.channel.type == discord.ChannelType.private and ctx.author.id == admin_id:
        try:
            pms_from_nick: list = get_pms_from_logfile(nick)
            embed = discord.Embed(title=f"Wiadomości od użytkownika {nick}:",
                                  color=discord.Color.purple())
            for message in pms_from_nick:
                if len(embed) >= 6000 or len(embed.fields) >= 25:
                    await user.send(embed=embed)
                    embed.clear_fields()
                if len(message[0]) >= 235:
                    embed.add_field(name=f":small_blue_diamond: {message[0][:235]}",
                                    value=message[1],
                                    inline=False)
                else:
                    embed.add_field(name=f":small_blue_diamond: {message[0]}",
                                    value=message[1],
                                    inline=False)
            await user.send(embed=embed)
        except NickNotFoundError or FileNotFoundError as exception:
            if type(exception).__name__ == "FileNotFoundError":
                open("pm_logs.json", "x").close()
            embed = discord.Embed(title=":no_entry: Błąd :no_entry:",
                                  color=discord.Color.dark_red())
            embed.add_field(name=f"Brak wiadomości prywatnych od {nick}",
                            value="Nie znalazłem żadnej wiadomości prywatnej od tego użytkownika.\n"
                                  "Upewnij się, że nick został wprowadzony poprawnie i spróbuj ponownie.")
            await ctx.channel.send(embed=embed)


async def send_message(message):
    now: str = datetime.now().strftime("%H:%M:%S")
    embed = discord.Embed(title=":eyes: Dostałeś wiadomość!",
                          color=discord.Color.green())
    embed.add_field(name="ID nadawcy:",
                    value=message[0],
                    inline=False)
    embed.add_field(name="Nick:",
                    value=message[1],
                    inline=False)
    embed.add_field(name="Wiadomość:",
                    value=message[2],
                    inline=False)
    embed.set_footer(text=f"Godzina {now}")
    await user.send(embed=embed)


def start(admin_user_id, token):
    global admin_id
    admin_id = admin_user_id
    Thread(target=lambda: bot.run(token), daemon=True).start()
