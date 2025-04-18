from bs4 import BeautifulSoup
import requests
import re

class Parser():

    insider_ref_dict = {}
    
    def get_html_from_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return None   
        
    def iterate_over_year(self, year):
        months = [("January", 31), ("February", 28), ("March", 31), ("April", 30), ("May", 31), ("June", 30), ("July", 31), ("August", 31),
                   ("September", 30), ("October", 31), ("November", 30), ("December", 31)]
        with open("./data/nhlcombuzznewsnotes.txt", 'a') as ofile:
            for i in range(len(months)):
                month, days_in_month = months[i]
                for day in range(4, days_in_month+1):
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
                    else:
                        continue
    
    def clean_text(self, path):
        with open(path, 'r') as rfile:
            with open(path+"_cleaned", 'w') as wfile:
                previous_line = ""
                for line in rfile:
                    if previous_line == line:
                        continue
                    else:
                        wfile.write(line)
                    previous_line = line

    def get_home_page_links(self, base_url="https://www.nhl.com", path="/news", depth=0, max_depth=100):
        print(depth)
        url = base_url + path
        html = self.get_html_from_url(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all('a'):
                ref = link.get('href')
                if ref and ref.startswith("/news/topic/nhl-insider/"):
                    if ref not in self.insider_ref_dict:
                        self.insider_ref_dict[ref] = 1
                        if depth < max_depth:
                            self.get_home_page_links(path=ref, depth=depth+1)

    def write_out_insider_dict(self):
        with open("data/insiderrefs.txt", 'w') as ofile:
            for key in self.insider_ref_dict:
                ofile.write(key+"\n")
                    
    def get_insider_text(self):
        with open("./data/nhlcominsidertext.txt", 'w') as ofile:
                for ref in self.insider_ref_dict:
                    url = f"https://www.nhl.com{ref}"
                    html = self.get_html_from_url(url)
                    if html:
                        soup = BeautifulSoup(html, "html.parser")
                        text_div = soup.find_all('div', class_="oc-c-markdown-stories")
                        for match in text_div:
                            text = match.get_text()
                            ofile.write(text)
                    else:
                        continue


parser = Parser()
parser.get_home_page_links()
# parser.get_insider_text()


