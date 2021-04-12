import os
import bot
import json
from time import sleep
from datetime import datetime
import asyncio


if not os.path.isfile("config.json"):
    with open("config.json", 'w', encoding="utf-8") as config_file:
        config_data = {"path": "C:\\Program Files (x86)\\MTA San Andreas 1.5\\MTA\\logs\\console.log",
                       "admin_id": "Tu wprowadź swoje id użytkownika z discorda.",
                       "token": "Tu wprowadź token bota z panelu deweloperskiego."}
        json.dump(config_data,
                  config_file,
                  indent=4,
                  sort_keys=True)
else:
    with open("config.json", "r") as config_file:
        config_data: dict = json.load(config_file)


class PrivateMessage:
    def __init__(self, parsed_message: tuple):
        self.user_id: str = parsed_message[0]
        self.user_nick: str = parsed_message[1]
        self.user_message: str = parsed_message[2]


class ChatProcessor:
    def __init__(self):
        self.log_file_path: str = config_data["path"]
        if not os.path.isfile("pm_logs.json"):
            open("pm_logs.json", 'x').close()
        if os.path.isfile(self.log_file_path):
            try:
                os.remove(self.log_file_path)
            except PermissionError:
                print("Gra jest już uruchomiona.")
        while not os.path.isfile(self.log_file_path):
            sleep(5)
        self.execute()

    def get_private_message(self) -> str:
        with open(self.log_file_path, encoding="utf-8") as log_file:
            log_file.seek(0, 2)
            while True:
                try:
                    log_line = log_file.readline().rstrip()
                except UnicodeDecodeError:
                    print("Wystąpił błąd.")
                if not log_line:
                    sleep(0.1)
                    continue
                if log_line[33:][:2] == "<<":
                    yield log_line[36:]

    def parse_message(self) -> tuple:
        for pm in self.get_private_message():
            unparsed_message: list = pm.lstrip('[').split(']')
            user_id: str = unparsed_message[0]
            try:
                user_nick, user_message = unparsed_message[1].split(": ")
            except ValueError:
                user_nick: str = unparsed_message[1].rstrip(':')
                user_message: str = "(pusta wiadomość)"
            current_datetime: str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            yield user_id, user_nick, user_message, current_datetime

    @staticmethod
    def save_to_pmlogs(message: tuple):
        with open("pm_logs.json", 'r') as pm_logs:
            try:
                data: dict = json.load(pm_logs)
            except json.decoder.JSONDecodeError:
                data: dict = {}
            if message[1] in data:
                data[message[1]].append([message[2], message[3]])
            else:
                data[message[1]] = [[message[2], message[3]]]
        with open("pm_logs.json", 'w') as update_content:
            json.dump(data, update_content)

    def execute(self):
        for parsed_message in self.parse_message():
            print(parsed_message)
            try:
                self.save_to_pmlogs(parsed_message)
            except FileNotFoundError:
                open("pm_logs.json", 'x').close()
                self.save_to_pmlogs(parsed_message)
            asyncio.get_event_loop().create_task(bot.send_message(parsed_message))


if __name__ == "__main__":
    if config_data["admin_id"] and config_data["token"]:
        if config_data["admin_id"].isdigit():
            bot.start(int(config_data["admin_id"]), config_data["token"])
            ChatProcessor()
