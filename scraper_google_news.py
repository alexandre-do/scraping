import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import feedparser
from requests_html import HTMLSession
from dateparser import parse as parse_date
from collections.abc import MutableMapping
import warnings
import typer
from typer.params import Argument
import hashlib
from tqdm import tqdm
import jsonlines
from datetime import timedelta

warnings.filterwarnings("ignore")
SAVE_ATTRIBUTES = [
    "title",
    "link",
    "id",
    "published",
    "published_parsed",
    "summary",
    "source",
    "link_query",
]
TIME_DELTA = 7


class Rte_google_search:
    def __init__(self):
        self.lang = "fr"
        self.country = "FR"
        self.BASE_URL = "https://news.google.fr/rss"

    def parser_date(self, date):
        try:
            date_parsered = parse_date(date).strftime("%Y-%m-%d")
            return str(date_parsered)
        except:
            raise Exception("date values could not be parserd")

    def __ceid(self):
        """Compile correct country-lang parameters for Google News RSS URL"""
        return "?ceid={}:{}&hl={}&gl={}".format(
            self.country, self.lang, self.lang, self.country
        )

    def __top_news_parser(self, text):
        """Return subarticles from the main and topic feeds"""
        try:
            bs4_html = BeautifulSoup(text, "html.parser")
            # find all li tags
            lis = bs4_html.find_all("li")
            sub_articles = []
            for li in lis:
                try:
                    sub_articles.append(
                        {
                            "url": li.a["href"],
                            "title": li.a.text,
                            "publisher": li.font.text,
                        }
                    )
                except:
                    pass
            return sub_articles
        except:
            return text

    def add_sub_articles(self, entries):
        for i, val in enumerate(entries):
            if "summary" in entries[i].keys():
                entries[i]["sub_articles"] = self.__top_news_parser(
                    entries[i]["summary"]
                )
            else:
                entries[i]["sub_articles"] = None
        return entries

    def __search_helper(self, query):
        return urllib.parse.quote_plus(query)

    def create_query(
        self,
        keywords,
        time_when=None,
        time_from=None,
        time_to=None,
        time_delta=TIME_DELTA,
        helper=True,
    ):
        search_ceid = self.__ceid()
        search_ceid = search_ceid.replace("?", "&")

        if time_delta and time_from and time_to:
            list_query = []
            time_from, time_to = parse_date(time_from), parse_date(time_to)
            num_delta = int((time_to - time_from).days / time_delta)
            for i in range(num_delta):
                time_to = time_from + timedelta(days=time_delta)
                # create a query with specific time_to and time_from
                query_ = keywords
                query_ += " after:" + self.parser_date(date=str(time_from))
                query_ += " before:" + self.parser_date(date=str(time_to))
                time_from = time_to
                if helper == True:
                    query_ = self.__search_helper(query_)
                query_ = self.BASE_URL + "/search?q={}".format(query_) + search_ceid
                list_query.append(query_)
            return list_query
        else:
            query = keywords
            if time_when:
                query += " when:" + time_when
            if time_from and not time_when:
                time_from = self.parser_date(date=time_from)
                query += " after:" + time_from
            if time_to and not time_when:
                time_to = self.parser_date(date=time_to)
                query += " before:" + time_to
            if helper == True:
                query = self.__search_helper(query)
            query = self.BASE_URL + "/search?q={}".format(query) + search_ceid
        return query

    def launch_query(
        self, query, proxies=None, scraping_bee=None,
    ):
        outs = []
        if isinstance(query, list):
            for query_ in tqdm(query):
                scraping_ = self.parse_feed(
                    query_, proxies=proxies, scraping_bee=scraping_bee
                )
                if len(scraping_['entries']) ==0:
                    return outs
                link_query, entries = scraping_["feed"]["link"], scraping_["entries"]
                for entry in entries:
                    entry["link_query"] = link_query
                    outs.append(
                        {
                            save_attribut: entry[save_attribut]
                            if save_attribut in entry
                            else None
                            for save_attribut in SAVE_ATTRIBUTES
                        }
                    )

        else:
            scraping_ = self.parse_feed(
                query, proxies=proxies, scraping_bee=scraping_bee
            )
            link_query, entries = scraping_["feed"]["link"], scraping_["entries"]
            for entry in entries:
                entry["link_query"] = link_query
                outs.append(
                    {
                        save_attribut: entry[save_attribut]
                        if save_attribut in entry
                        else None
                        for save_attribut in SAVE_ATTRIBUTES
                    }
                )
        return outs

    def __scaping_bee_request(self, api_key, url):
        response = requests.get(
            url="https://app.scrapingbee.com/api/v1/",
            params={"api_key": api_key, "url": url, "render_js": "false"},
        )
        if response.status_code == 200:
            return response
        if response.status_code != 200:
            raise Exception(
                "ScrapingBee status_code: "
                + str(response.status_code)
                + " "
                + response.text
            )

    def parse_feed(self, feed_url, proxies=None, scraping_bee=None):

        if scraping_bee and proxies:
            raise Exception("Pick either ScrapingBee or proxies. Not both!")
        if proxies:
            r = requests.get(feed_url, proxies=proxies)

        elif scraping_bee:
            r = self.__scaping_bee_request(url=feed_url, api_key=scraping_bee)
        else:
            r = requests.get(feed_url)

        if "https://news.google.fr/rss/unsupported" in r.url:
            raise Exception("This feed is not available")
        d = feedparser.parse(r.text)
        if not scraping_bee and not proxies and len(d["entries"]) == 0:
            d = feedparser.parse(feed_url)

        return dict((k, d[k]) for k in ("feed", "entries"))

    @staticmethod
    def save_entry_to_jsonl(entry, path_jsonl, mode="a"):
        path = "/".join(path_jsonl.split("/")[:-1])
        if path and not os.path.isdir(path):
            os.makedirs(path)
        if isinstance(entry, list):
            with jsonlines.open(path_jsonl, mode=mode) as f:
                for entry_ in entry:
                    f.write(entry_)
        else:
            with jsonlines.open(path_jsonl, mode=mode) as f:
                f.write(entry)


app = typer.Typer()


@app.command()
def search(
    keywords: str = typer.Argument(
        None, help="keywords for google news search engine."
    ),
    date_from: str = typer.Argument(None, help="Start date for searching."),
    date_to: str = typer.Argument(None, help="End date for searching."),
    save_file: str = typer.Argument(None, help="Path for saved file."),
    time_delta: int = typer.Option(
        TIME_DELTA, help="delta time to decompose the time duration."
    ),
):
    query = scraper.create_query(
        keywords=keywords, time_from=date_from, time_to=date_to, time_delta=time_delta
    )
    print(
        f"Searching for the keywords: {keywords} for dates between: {date_from} and {date_to}"
    )
    entries = scraper.launch_query(query)
    # write the result:
    print(f"Save the result to: {save_file}")
    scraper.save_entry_to_jsonl(entries, save_file)


@app.command()
def auto_search(
    inputfile_path: str = typer.Argument(
        None, help="Path to input file containing keywords, dates, saved file's name."
    ),
    time_delta: int = typer.Option(
        TIME_DELTA, help="delta time to decompose the time duration."
    ),
):
    # read input file and remove the duplicates:
    with open(inputfile_path, "r") as f:
        requests = f.readlines()
        requests = list(set(requests))

    for request in requests:
        keywords, date_from, date_to, save_file = request.split(";")
        save_file = save_file.rstrip("\n")
        query = scraper.create_query(
            keywords=keywords,
            time_from=date_from,
            time_to=date_to,
            time_delta=time_delta,
        )
        print(
            f"Searching for the keywords: {keywords} for dates between: {date_from} and {date_to}"
        )
        entries = scraper.launch_query(query)

        # write the result:
        print(f"Save the result to: {save_file}")
        scraper.save_entry_to_jsonl(entries, save_file)


if __name__ == "__main__":
    scraper = Rte_google_search()
    app()

