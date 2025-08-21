import argparse
import os
import re
import sys
import threading
import xml.etree.ElementTree as ET
from queue import Queue

import requests
from bs4 import BeautifulSoup
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

BASE_BBS_URL = "https://www.lexaloffle.com/"
console = Console()
q = Queue()


parser = argparse.ArgumentParser()
parser.add_argument(
    "-t", type=int, default=20, help="Set the number of parallel download threads."
)
parser.add_argument("-p", type=int, default=10, help="Set the number of pages.")
args = parser.parse_args()

print(
    """
░▒█▀▀█░▀█▀░▒█▀▀▄░▒█▀▀▀█░▄▀▀▄
░▒█▄▄█░▒█░░▒█░░░░▒█░░▒█░▄▀▀▄
░▒█░░░░▄█▄░▒█▄▄▀░▒█▄▄▄█░▀▄▄▀
░█▀▄░█▀▀▄░█▀▀▄░▀█▀░█░░▄▀▀▄░█▀▀▄░█▀▄░█▀▀░█▀▀▄
░█░░░█▄▄█░█▄▄▀░░█░░█░░█░░█░█▄▄█░█░█░█▀▀░█▄▄▀
░▀▀▀░▀░░▀░▀░▀▀░░▀░░▀▀░░▀▀░░▀░░▀░▀▀░░▀▀▀░▀░▀▀
                                                                                  
Developed by @icaroferre

"""
)


class PICOGAME:
    def __init__(self, title, url):
        print(f"Game found: {title}")
        self.title = title
        self.url = url
        self.card_url = ""
        self.card_name = ""
        self.description = ""
        self.developer = ""
        self.thumb_url = ""

        self.thumb_file = ""

    def getDetails(self):
        cardUrl = BASE_BBS_URL + "/bbs/" + self.url
        cardPage = getPageContent(cardUrl)
        self.card_url = cardPage.find("a", {"title": "Open Cartridge File"}).get("href")
        self.card_name = self.card_url.split("/")[-1]

        try:
            devDiv = cardPage.find("a", href=re.compile(r"^/bbs/\?uid=\d+"))
            self.developer = devDiv.get_text(strip=True)
        except:
            console.print(f"Failed to retrieve developer name for {self.title}")

        try:
            # Description parser
            descriptionDiv = cardPage.find("div", {"style": "min-height:44px;"})
            self.description = descriptionDiv.text.strip()
            self.description = self.description.split(
                "Copy and paste the snippet below into your HTML."
            )[1]
            self.description = self.description.replace(
                "Note: This cartridge's settings do not allow embedded playback. A [Play at lexaloffle] link will be included instead.",
                "",
            )
            self.description = (
                self.description.replace("\t", "").replace("\r", "").strip()
            )
            while "\n\n" in self.description:
                self.description = self.description.replace("\n\n", "\n")
        except:
            console.print(f"Failed to retrieve description for {self.title}")

        # Image parser
        images = cardPage.find_all("img")
        for i in images:
            if "thumbs" in i.get("src"):
                self.thumb_url = i.get("src").strip()
                self.thumb_file = self.thumb_url.split("/")[-1]
                break
        self.download()

    def download(self):
        console.print("Downloading game: {}".format(self.title))
        downloadFile(BASE_BBS_URL + self.card_url, self.card_name, "/output/")
        downloadFile(
            BASE_BBS_URL + self.thumb_url, self.thumb_file, "/output/media/screenshots/"
        )


def threader():
    while True:
        game = q.get()
        try:
            game.getDetails()
        except:
            console.print("Failed to download: {}".format(game.title))
            console.print_exception()
        q.task_done()


def downloadFile(url, filename, path):
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Error downloading {url} - Status Code: {r.status_code}")
    with open(sys.path[0] + path + filename, "wb") as outfile:
        outfile.write(r.content)


def createFolder(foldername):
    try:
        path = sys.path[0] + "/" + foldername
        os.mkdir(path, 0o777)
    except FileExistsError:
        pass


def getPageContent(url):
    params = {}
    if "#" in url:
        maybe_params = url.split("#")[1].split("&")
        for i in maybe_params:
            keys = i.split("=")
            params[keys[0]] = keys[1]
    res = requests.get(url, params=params)
    content = BeautifulSoup(res.content, "html.parser")
    return content


def getGamesFromPage(url):
    with console.status("[bold green]Scraping page for games...") as status:
        content = getPageContent(url)
        links = content.find_all("a")
        games_found = []
        for i in links:
            link_url = str(i.get("href"))
            link_title = i.text.strip()
            if "?tid" in link_url:
                new_game = PICOGAME(link_title, link_url)
                games_found.append(new_game)
                # print(link_title)
    console.print("Games found: {}".format(len(games_found)))
    return games_found


def printGames(games):
    table = Table(title="Games found")
    table.add_column("Title", justify="left", no_wrap=True)
    table.add_column("Developer", style="magenta")
    table.add_column("Card URL", style="green")
    table.add_column("Thumbnail", justify="right", style="green")
    for i in games:
        table.add_row(i.title, i.developer, i.card_url, i.thumbnail)
    console.print(table)


def createInitialFolder():
    createFolder("output")
    createFolder("output/media")
    createFolder("output/media/screenshots")


def generateXMLFile(games):
    with console.status("[bold green]Generating XML file...") as status:
        data = ET.Element("gameList")
        for i in games:
            newgame = ET.SubElement(data, "game")
            name = ET.SubElement(newgame, "name")
            path = ET.SubElement(newgame, "path")
            image = ET.SubElement(newgame, "image")
            developer = ET.SubElement(newgame, "developer")
            description = ET.SubElement(newgame, "desc")
            name.text = i.title
            path.text = "./" + i.card_name
            developer.text = i.developer
            description.text = i.description
            image.text = "./media/screenshots/" + i.thumb_file

        mydata = ET.tostring(data).decode("utf-8")
        myfile = open(sys.path[0] + "/output/gamelist.xml", "w")
        myfile.write(str(mydata))
        print("XML file written successfully.")


def searchAndDownload():
    games = []
    for i in range(args.p):
        url = "https://www.lexaloffle.com/bbs/?cat=7#sub=2&mode=carts&orderby=featured&page={}".format(
            i + 1
        )
        newgames = getGamesFromPage(url)
        for n in newgames:
            games.append(n)

    with console.status(
        "[bold green]Downloading {} games ({} threads)...".format(len(games), args.t)
    ) as status:
        for i in games:
            q.put(i)
        q.join()
    return games


for x in range(args.t):
    t = threading.Thread(target=threader)
    t.daemon = True
    t.start()

if __name__ == "__main__":

    createInitialFolder()
    games = searchAndDownload()
    generateXMLFile(games)
