from bs4 import BeautifulSoup
import requests
from collections import defaultdict
import os
import datetime
import re
import argparse
import time

class PodScraper():
    
    def __init__(self) -> None:
        self.ref_dict = {}  # Dictionary to track visited URLs
        self.stop = False

    def run(self, url, after_date=None):
        podcast_name=url.split('/')[4]
        if not os.path.isdir(podcast_name):
            os.makedirs(podcast_name)
        soup=self.get_soup(url)
        max_page= self.max_page(soup)
        print(f"We will Scrape {max_page} pages")
        for page in range (1, max_page+1):
            if self.stop:
                print("Stopped scraping early.")
                break
            curr_url=url[:-1]+f"?page={page}"
            soup=self.get_soup(curr_url)
            self.get_episodes(soup, podcast_name, after_date)

        self.write_transcriptions(podcast_name)


    #need to find how many pages of urls to parse
    def max_page(self, soup):
        pagination=soup.find("div", attrs={"class":"pagination"})
        links= pagination.find_all('a', attrs={"class":None})
        max_page=int(links[0].string)
        return max_page
        
    def get_episodes(self, soup, podcast_name, after_date):
    
        after_datetime = datetime.datetime.strptime(after_date, '%Y-%m-%d') if after_date else None
        #get all episodes per page
        for podcast in soup.find_all('div', attrs={"class": "geodir-category-content fl-wrap"}):
            links=podcast.find_all('a')
            for link in links:
                link_href=link.get('href')
            
            #extract date
            date_raw=podcast.find('span', attrs={"class":"episode_date"}).contents[0]
            date_text=date_raw.split(":")[1].strip(',').strip()
            format = '%B %d, %Y'
            date=datetime.datetime.strptime(date_text, format)
            
            #check if we are going into older episodes
            if after_date and date < after_datetime:
                print(f"Reached Episode after {after_datetime.date()}, stopping scrape...")
                self.stop=True
                return

            #only get the episode number and title
            episode = link_href.rstrip('/').split('/')[-1].replace(podcast_name+"-episode-", "")
            full_link= "https://podscripts.co" + link_href

            if podcast_name in link_href:
                self.ref_dict[episode]=(date, full_link)

    def write_transcriptions(self, podcast_name):
        for episode in self.ref_dict.keys():
            date=self.ref_dict[episode][0]
            link=self.ref_dict[episode][1]
            soup=self.get_soup(link)
            
            #Find the main transcript container
            transcript_div = soup.find('div', class_='podcast-transcript')

            #Find all the spans that contain sentences
            sentences = transcript_div.find_all('span', class_='pod_text seek_pod_segment sentence-tooltip transcript-text')
            
            file_path = os.path.join(podcast_name, f"{episode}|{date.date()}.txt")
            with open(file_path, 'w') as wfile:
                for sentence in sentences:
                    sentence_strip=sentence.contents[0].strip()
                    text = self.clean_line(sentence_strip)  # Clean each line
                    wfile.write(text + "\n")  # Write cleaned line to output file
            print(f"Wrote to {file_path}")
    
    def clean_line(self, text):
        """
        Remove unwanted characters from a line of text.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        text = re.sub(r"[^A-Za-z0-9'/\.,;\-\+=: \"\'\?!]", "", text)
        return text.strip()                

    def get_soup(self, url):
        """
        Get Beautiful Soup object from url.
        Implement Exponential Back-Off to avoid Too Many Requests Error
        Args:
            url: string of url webpage

        Returns:
            soup: Beautiful Soup Object
        """
        retries=0
        while retries < 10:
            try:
                response = requests.get(url)
                if response.status_code == 429:
                    print(f"429 Too Many Requests at {url}, waiting...")
                    time.sleep(5 * (retries + 1))  #increase backoff each time
                    retries += 1
                    continue  # retry
                response.raise_for_status()  # raise other bad codes
                return BeautifulSoup(response.text, 'html.parser')

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                time.sleep(5 * (retries + 1))
                retries += 1
    
    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Podcast Transcript Scraper")
        parser.add_argument(
            "--url", type=str, required=False,
            help="url of podcast episode page to scrape 'https://podscripts.co/podcasts/{podcast}/'")
        
        parser.add_argument(
            "--date", type=str, required=False,
            help="only scrape podcasts after specific date format: yyyy-mm-dd")
        return parser

if __name__ == "__main__":
    podscaper = PodScraper()
    args= podscaper.build_parser().parse_args()
    if args.url:
        url=args.url
    else:
        url= "https://podscripts.co/podcasts/spittin-chiclets/"
    
    if args.date:
        podscaper.run(url, args.date)
    else:
        podscaper.run(url)