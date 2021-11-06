import jsonlines
from pandas.io import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import Comment, BeautifulSoup
import re
import typer
import pandas as pd
import os
import warnings
from tqdm import tqdm
import hashlib

warnings.filterwarnings("ignore")

PATH = "/Users/alexandredo/Desktop/GIT/scraping/chromedriver"
USER_AGENT = "/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
OPTIONS = webdriver.ChromeOptions()
OPTIONS.add_experimental_option("excludeSwitches", ["enable-automation"])
OPTIONS.add_argument("--headless")
ACCEPT_COOKIES = [
    "Ok",
    "ok",
    "consent",
    "Consent",
    "Accept",
    "accept",
    "J'aceppt",
    "j'accept",
]


class Html_scraper:
    def __init__(self, webdriver_path, webdriver_options, user_agent):
        self.webdriver_path = webdriver_path
        self.webdriver_options = webdriver_options
        self.driver = webdriver.Chrome(
            self.webdriver_path, options=self.webdriver_options
        )
        self.user_agent = {"User-Agent": user_agent}

    def log_in(self, username, password):
        username = self.driver.find_element_by_xpath("//div[contains(., 'username']")
        password = self.driver.find_element_by_xpath("//div[contains(., 'password']")
        username.send_keys(username)
        password.send_keys(password)
        self.driver.find_element_by_name("submit").click()

    def accept_cookies(self):
        # find the cookies button
        buttons = self.driver.find_element_by_xpath("//button")
        for button in buttons:
            if any([name_cookies in button.text for name_cookies in ACCEPT_COOKIES]):
                button.click()
                print(f"Clicked : {button.text}")
                break

    def driver_wait(self, prensence_object=None, time_implicity=None):
        if prensence_object:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, prensence_object))
            )
        else:
            self.driver.implicitly_wait(time_implicity)

    def set_cookies(self):
        pass

    def update_cookies(self, new_cookies):
        pass

    def get_html(self, url, timeout=30):
        self.driver.set_page_load_timeout(timeout)
        self.driver.get(url)
        return self.driver.page_source

    def parser_html(self, page_source):
        if page_source is None:
            return dict(meta=None, title=None)
        soup = BeautifulSoup(page_source, "html.parser")
        parser = {}
        # parser["dataloader"] = self._parser_dataloader(soup)
        parser["meta"] = self._parser_meta(soup)
        parser["title"] = self._parser_title(soup)
        headers = soup.find_all(re.compile("h[0-9]{1}"))
        if headers:
            parser_headers = self._parser_headers(soup)
            parser_paragraphs = self._parser_paragraph_by_headers(soup, headers)

            # sortting the header by their levels
            parser["paragraphs"] = [
                p_ for _, p_ in sorted(zip(parser_headers, parser_paragraphs))
            ]
            parser["headers"] = sorted(parser_headers)
        return parser

    def _parser_meta(self, soup):
        meta = {
            meta.get("property"): meta.get("content")
            for meta in soup.find_all("meta")
            if meta.get("property") is not None
        }
        datetime = soup.find("time")
        if "datetime" not in meta and datetime:
            try:
                meta["datetime"] = datetime.get("datetime")
            except:
                meta["datetime"] = datetime
        return meta

    @staticmethod
    def _header_to_text(headers):
        return [header.string for header in headers]

    @staticmethod
    def _paragraphs_to_text(paragraphs):
        return "\n".join([paragraph.text for paragraph in paragraphs])

    def _parser_title(self, soup):
        return self._header_to_text(soup.find("title")) if soup.find("title") else None

    def _parser_headers(self, soup):
        headers_ = soup.find_all(re.compile("h[0-9]{1}"))
        headers = []
        for header in headers_:
            headers.append(header.name + "_" + header.text)
        return headers

    def _parser_dataloader(self, soup):
        pattern = re.compile(r"dataLayer")
        script = soup.find("script", text=pattern)
        if script:
            blocked = '"statut":"Blocked"' in script.text
            restrictedaccess = '"restrictedaccess":"Oui"' in script.text
            s = ""
            if blocked:
                s += "blocked "
            if restrictedaccess:
                s += "restrictedaccess "
            return s
        else:
            return ""

    def save_pagesource_to_html(self, html_path):
        path_ = "/".join(html_path.split("/")[:-1])

        if not os.path.isdir(path_):
            os.makedirs(path_)
        with open(html_path, "w") as f:
            f.write(self.driver.page_source)

    def _parser_paragraph_by_headers(self, soup, headers):
        # remove all comments
        div = soup.find("div")
        for element in div(text=lambda text: isinstance(text, Comment)):
            element.extract()  # remove it from the tree
        paragraphs = []
        # find all paragraphs
        for header in headers:
            level, text = header.name, header.text
            siblings = header.find_next_siblings(["p", level])
            paragraph_for_header = []
            for sibling in siblings:
                if sibling.name == level:
                    break
                else:
                    paragraph_for_header.append(sibling)

            # Cas for the first level h1 in <div><h1></div>
            if len(paragraph_for_header) == 0 and level == "h1":
                paragraph_for_header = []
                parent = header.find_parent()
                for sibling in parent.find_next_siblings(
                    ["p", re.compile("h[0-9]{1}")]
                ):
                    # case sibling doesnot containt any header
                    if sibling.find(
                        re.compile("h[0-9]{1}")
                    ):  # cas siblinng contains the header
                        # extract the paragrahs before the header
                        paragraphs_before_header = sibling.find(
                            re.compile("h[0-9]{1}")
                        ).find_previous_siblings("p")
                        paragraphs_before_header.reverse()
                        paragraph_for_header += paragraphs_before_header
                        break

                    else:
                        # Extract all paragrahs in sibling
                        paragraph_for_header += sibling.find_all("p")

            paragraphs.append(self._paragraphs_to_text(paragraph_for_header))
        return paragraphs

    @staticmethod
    def url_to_uuid(url):
        m = hashlib.md5()
        m.update(url.encode())
        return str(int(m.hexdigest(), 16))[0:12]


app = typer.Typer()


@app.command()
def scrape(
    url: str = typer.Argument(None, help="URL link for scrapping."),
    save_path: str = typer.Option(
        None, help="Path for writting results. File is in jsonl format."
    ),
    save_html: bool = typer.Option(False, help="Save html page source."),
):
    page_source = scraper.get_html(url)
    parser = scraper.parser_html(page_source)
    uuid = scraper.url_to_uuid(url)
    parser["uuid"] = uuid
    parser["url"] = url
    print(parser)

    if save_path:
        path_ = "/".join(save_path.split("/")[:-1])
        if not os.path.isdir(path_):
            os.makedirs(path_)
        with jsonlines.open(save_path, "w") as f:
            f.write(parser)

    if save_html:
        name_file = save_path.split("/")[-1].split(".")[0]
        if save_path:
            path_ = "/".join(save_path.split("/")[:-1])
            if not os.path.isdir(path_):
                os.makedirs(path_)
        scraper.save_pagesource_to_html(f"{path_}/{name_file}_pagesource.html")


@app.command()
def auto_scrape(
    inputfile_path: str = typer.Argument(
        None, help="path of jsonlines input file containing the urls."
    ),
    save_path: str = typer.Argument(None, help="Path for writting results."),
    save_html: bool = typer.Option(False, help="Save html page source."),
):
    # read jsonline input file
    df = pd.read_json(inputfile_path, lines=True, orient="records")
    df.drop_duplicates("link", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["site"] = df["source"].apply(lambda x: x["href"] if "href" in x else None)
    df.sort_values("site", inplace=True)
    urls = df.link.to_list()

    outputfile_name = inputfile_path.split("/")[-1].split(".")[0] + "_parser.jsonl"
    outputfile_exception_name = (
        inputfile_path.split("/")[-1].split(".")[0] + "_parser_exception.jsonl"
    )

    # check if exist path
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    outputfile_path = save_path + "/" + outputfile_name
    outputfile_exception_path = save_path + "/" + outputfile_exception_name
    parsers_exception = []
    with jsonlines.open(outputfile_path, "w") as f:

        for url in tqdm(urls):
            try:
                page_source = scraper.get_html(url)
                parser = scraper.parser_html(page_source)
                uuid = scraper.url_to_uuid(url)
                parser["uuid"] = uuid
                parser["url"] = url
                f.write(parser)
                if save_html:
                    scraper.save_pagesource_to_html(
                        f"{save_path}/page_source/uuid_{uuid}.html"
                    )
            except Exception as e:
                parsers_exception.append({"url": url, "message": e.args[0]})

    if len(parsers_exception) > 0:
        with jsonlines.open(outputfile_exception_path, "w") as f:
            for exception in parsers_exception:
                f.write(exception)


if __name__ == "__main__":
    scraper = Html_scraper(PATH, OPTIONS, USER_AGENT)
    app()
