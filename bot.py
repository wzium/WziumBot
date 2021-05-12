import discord
import json
from typing import Optional, List, Dict
from threading import Thread
from datetime import datetime
from discord.ext import commands

bot = commands.Bot(command_prefix="$")
user: Optional[discord.User] = None
admin_id: int = 0


class NickNotFoundError(Exception):
    pass


class NoMessagesFoundError(Exception):
    pass


def obtain_data() -> Dict[str, str]:
    with open("pm_logs.json") as pm_logs:
        try:
            data: dict = json.load(pm_logs)
        except json.decoder.JSONDecodeError:
            data = {}
        return data


def get_nicks_from_logfile() -> Optional[List[str]]:
    data = obtain_data()
    dict_keys = list(data.keys())
    if len(dict_keys) > 0:
        return dict_keys
    else:
        raise NoMessagesFoundError


def get_pms_from_logfile(nick) -> Optional[str]:
    data = obtain_data()
    if nick in data:
        return data[nick]
    else:
        raise NickNotFoundError


def create_instruction_embed() -> discord.Embed:
    instruction_embed: discord.Embed = discord.Embed(title=":page_with_curl: Lista graczy",
                                                     color=discord.Color.gold())
    instruction_embed.add_field(name="Instrukcja:",
                                value="Wybierz nick z poniższej listy i użyj komendy "
                                      "`$pms <nick>`\n "
                                      "Przykładowe użycie:\n"
                                      "`$pms jjay31`")
    return instruction_embed


@bot.event
async def on_ready():
    global user
    global admin_id
    user = await bot.fetch_user(admin_id)
    print("Bot został uruchomiony.")


@bot.command(name="pms")
async def send_pms(ctx, nick=None):
    if ctx.channel.type == discord.ChannelType.private and ctx.author.id == admin_id:
        try:
            if nick:
                pms_from_nick: str = get_pms_from_logfile(nick)
                embed: discord.Embed = discord.Embed(title=f"Wiadomości od użytkownika {nick}:",
                                                     color=discord.Color.purple())
                for message in pms_from_nick:
                    if len(embed) >= 6000 or len(embed.fields) >= 25:
                        await ctx.channel.send(embed=embed)
                        embed.clear_fields()
                    if len(message[0]) >= 235:
                        embed.add_field(name=f":small_blue_diamond: {message[0][:235]}",
                                        value=message[1],
                                        inline=False)
                    else:
                        embed.add_field(name=f":small_blue_diamond: {message[0]}",
                                        value=message[1],
                                        inline=False)
                await ctx.channel.send(embed=embed)
            else:
                try:
                    nicks_from_logs: list = get_nicks_from_logfile()
                    if len(nicks_from_logs) > 25:
                        embed = create_instruction_embed()
                        await ctx.channel.send(embed=embed)
                        number_of_nicks = len(nicks_from_logs)
                        if isinstance((number_of_nicks/25), float):
                            pages: int = (number_of_nicks // 25) + 1
                        else:
                            pages: int = number_of_nicks // 25
                        i: int = 0
                        page_number: int = 1
                        list_of_nicks: list = []
                        for nickname in nicks_from_logs:
                            if i <= 25:
                                list_of_nicks.append(nickname)
                                i += 1
                            else:
                                nicknames: str = '\n'.join(list_of_nicks)
                                embed.set_field_at(index=0,
                                                   name=f"Znalezione nicki ({page_number}/{pages}):",
                                                   value=f"```{nicknames}```")
                                await ctx.channel.send(embed=embed)
                                page_number += 1
                                i = 0
                                list_of_nicks = []
                        nicknames: str = '\n'.join(list_of_nicks)
                        embed.set_field_at(index=0,
                                           name=f"Znalezione nicki ({page_number}/{pages}):",
                                           value=f"```{nicknames}```")
                        await ctx.channel.send(embed=embed)
                    else:
                        nicks: str = '\n'.join(nicks_from_logs)
                        embed = create_instruction_embed()
                        await ctx.channel.send(embed=embed)
                        embed.set_field_at(index=0,
                                           name="Znalezione nicki:",
                                           value=f"```{nicks}```")
                        await ctx.channel.send(embed=embed)
                except NoMessagesFoundError:
                    embed = discord.Embed(title=":no_entry: Błąd :no_entry:",
                                          color=discord.Color.dark_red())
                    embed.add_field(name=f"Nie znaleziono wiadomości!",
                                    value="Nie udało się znaleźć wiadomości prywatnych,\n"
                                          "upewnij się, że plik `pm_logs.json` nie został usunięty bądź uszkodzony.\n"
                                          "Jeśli nie, oznacza to, że bot nie zarejestrował jeszcze żadnej wiadomości.")
                    await ctx.channel.send(embed=embed)
        except NickNotFoundError or FileNotFoundError as exception:
            if type(exception).__name__ == "FileNotFoundError":
                open("pm_logs.json", "x").close()
            embed = discord.Embed(title=":no_entry: Błąd :no_entry:",
                                  color=discord.Color.dark_red())
            embed.add_field(name=f"Brak wiadomości prywatnych od \"{nick}\"",
                            value="Nie znalazłem żadnej wiadomości prywatnej od tego użytkownika.\n"
                                  "Upewnij się, że nick został wprowadzony poprawnie i spróbuj ponownie.")
            await ctx.channel.send(embed=embed)


async def send_message(message):
    now: str = datetime.now().strftime("%H:%M:%S")
    embed: discord.Embed = discord.Embed(title=":eyes: Dostałeś wiadomość!",
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
