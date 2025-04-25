from bs4 import BeautifulSoup
import requests
import time

# Class to scrape NHL and ESPN hockey articles
class Webscraper():

    ref_dict = {}  # Dictionary to track visited URLs

    # Run different scraping tasks based on provided flags
    def run(self, run_nhl_sections=True, run_full_nhl=False, run_full_espn=False):
        if run_nhl_sections:
            self.get_nhl_buzz_data()
            self.get_nhl_insider_data()
            self.get_nhl_edge_data()
            self.get_espn_story_data()
        if run_full_nhl:
            self.get_nhl_data()
        if run_full_espn:
            self.get_espn_data()

    # Fetch HTML from a URL, returning None if it fails
    def get_html_from_url(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    # Scrape NHL Buzz articles by day for given years
    def get_nhl_buzz_data(self, years=[2024, 2025]):
        for year in years:
            months = [("January", 31), ("February", 28), ("March", 31), ("April", 30), ("May", 31), ("June", 30),
                      ("July", 31), ("August", 31), ("September", 30), ("October", 31), ("November", 30), ("December", 31)]
            with open("./data/nhl_buzz_data.txt", 'w') as ofile:
                for month, days_in_month in months:
                    for day in range(1, days_in_month + 1):
                        url = f"https://www.nhl.com/news/nhl-buzz-news-and-notes-{month}-{day}-{year}"
                        ofile.write(f"{month}-{day}-{year}:\n")
                        html = self.get_html_from_url(url)
                        if html:
                            soup = BeautifulSoup(html, "html.parser")
                            text_div = soup.find_all('div', class_="oc-c-markdown-stories")
                            for match in text_div:
                                text = match.get_text()
                                str_to_remove = "Welcome to the NHL Buzz. Each day during the regular season, NHL.com has you covered with all the latest news.\n"
                                text = text.replace(str_to_remove, "")
                                ofile.write(text)

    # Recursively retrieve and visit all links that match the filter from a starting page
    def get_home_page_links(self, ofile, html_class, base_url="https://www.nhl.com", path="/news", depth=0, max_depth=100, filter="/news"):
        url = base_url + path
        html = self.get_html_from_url(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            text_div = soup.find_all('div', class_=html_class)
            for match in text_div:
                text = match.get_text() + "\n"
                ofile.write(text)
            for link in soup.find_all('a'):
                ref = link.get('href')
                if ref and ref.startswith(filter) and ref not in self.ref_dict:
                    self.ref_dict[ref] = 1
                    if depth < max_depth:
                        self.get_home_page_links(ofile, html_class, path=ref, depth=depth+1)

    # Generalized method to get article data given a URL, path, and HTML class
    def get_data(self, url, path, filter, path_to_write, html_class):
        with open(path_to_write, 'w') as ofile:
            self.get_home_page_links(ofile, html_class, base_url=url, path=path, filter=filter)

    # Count and print number of tokens (words) in a given file
    def count_tokens(self, path):
        total = 0
        with open(path, 'r') as ofile:
            for line in ofile:
                tokens = line.split(" ")
                total += len(tokens)
        print(f"Total tokens found in {path}: {total}")

    # Specific methods for scraping different types of NHL and ESPN articles

    def get_nhl_insider_data(self):
        url = "https://www.nhl.com"
        path = "/news"
        filter = "/news/topic/nhl-insider"
        path_to_write = "./data/nhl_insider_data.txt"
        html_class = "oc-c-markdown-stories"
        self.get_data(url, path, filter, path_to_write, html_class)
        self.count_tokens(path_to_write)

    def get_nhl_edge_data(self):
        url = "https://www.nhl.com"
        path = "/news"
        filter = "/news/topic/nhl-edge"
        path_to_write = "./data/nhl_edge_data.txt"
        html_class = "oc-c-markdown-stories"
        self.get_data(url, path, filter, path_to_write, html_class)
        self.count_tokens(path_to_write)

    def get_nhl_data(self):
        url = "https://www.nhl.com"
        path = "/news"
        filter = "/news"
        path_to_write = "./data/nhl_data.txt"
        html_class = "oc-c-markdown-stories"
        self.get_data(url, path, filter, path_to_write, html_class)
        self.count_tokens(path_to_write)

    def get_espn_data(self):
        url = "https://www.espn.com"
        path = "/nhl"
        filter = "/nhl"
        path_to_write = "./data/espn_data.txt"
        html_class = "article-body"
        self.get_data(url, path, filter, path_to_write, html_class)
        self.count_tokens(path_to_write)

    def get_espn_story_data(self):
        url = "https://www.espn.com"
        path = "/nhl"
        filter = "/nhl/story"
        path_to_write = "./data/espn_story_data.txt"
        html_class = "article-body"
        self.get_data(url, path, filter, path_to_write, html_class)
        self.count_tokens(path_to_write)

# Main script execution
if __name__ == "__main__":
    webscraper = Webscraper()
    webscraper.run()
