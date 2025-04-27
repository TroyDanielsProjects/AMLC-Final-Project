from bs4 import BeautifulSoup
import requests
from collections import defaultdict
import os
import datetime

class PodScraper():
    
    ref_dict = {}  # Dictionary to track visited URLs

    def run(self, url):
        podcast_name=url.split('/')[4]
        if not os.path.isdir(podcast_name):
            os.makedirs(podcast_name)
        page_to_scrape= requests.get(url)
        page_html=page_to_scrape.text
        soup= BeautifulSoup(page_html, "html.parser")
        max_page= self.max_page(soup)
        for page in range (1, max_page):
            print(page)
            curr_url=url[:-1]+f"?page={page}"
            page_to_scrape= requests.get(curr_url)
            page_html=page_to_scrape.text
            soup= BeautifulSoup(page_html, "html.parser")
            self.get_episodes(soup, podcast_name)
        self.get_transcriptions()
    
    #need to find how many pages of urls to parse
    def max_page(self, soup):
        pagination=soup.find("div", attrs={"class":"pagination"})
        links= pagination.find_all('a', attrs={"class":None})
        max_page=int(links[0].string)
        return max_page
        
    def get_episodes(self, soup, podcast_name):
        #get all episodes per page
        for podcast in soup.find_all('div', attrs={"class": "geodir-category-content fl-wrap"}):
            links=podcast.find_all('a')
            for link in links:
                link_href=link.get('href')
            date_raw=podcast.find('span', attrs={"class":"episode_date"}).contents[0]
            date=date_raw.split(":")[1].strip(',').strip()
            format = '%B %d, %Y'
            date=datetime.datetime.strptime(date, format)
            episode= link_href.split('/')[3]
            print(episode)
            http="https://podscripts.co"
            if podcast_name in link_href:
                print(http+link_href)
                self.ref_dict[episode]=(date, http+link_href)

    def get_transcriptions(self):
        for episode in self.ref_dict.keys():
            print(episode)
    

#TODO: make scraper setting where only scrape episodes after "date"; if date less than date, stop scraping
    
if __name__ == "__main__":
    url= "https://podscripts.co/podcasts/spittin-chiclets/"
    podscaper = PodScraper()
    print(url)
    podscaper.run(url)