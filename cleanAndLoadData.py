import re

# Class representing a single Buzz data entry
class BuzzDataPoint():
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.text = None   
        self.team = None 

    def __str__(self):
        return f"Date: {self.month}-{self.day}-{self.year}\n{self.team}\n{self.text}\n"
    

nhl_teams = {
    "Anaheim Ducks": 1,
    "Arizona Coyotes": 1,
    "Boston Bruins": 1,
    "Buffalo Sabres": 1,
    "Calgary Flames": 1,
    "Carolina Hurricanes": 1,
    "Chicago Blackhawks": 1,
    "Colorado Avalanche": 1,
    "Columbus Blue Jackets": 1,
    "Dallas Stars": 1,
    "Detroit Red Wings": 1,
    "Edmonton Oilers": 1,
    "Florida Panthers": 1,
    "Los Angeles Kings": 1,
    "Minnesota Wild": 1,
    "Montreal Canadiens": 1,
    "Nashville Predators": 1,
    "New Jersey Devils": 1,
    "New York Islanders": 1,
    "New York Rangers": 1,
    "Ottawa Senators": 1,
    "Philadelphia Flyers": 1,
    "Pittsburgh Penguins": 1,
    "San Jose Sharks": 1,
    "Seattle Kraken": 1,
    "St. Louis Blues": 1,
    "Tampa Bay Lightning": 1,
    "Toronto Maple Leafs": 1,
    "Vancouver Canucks": 1,
    "Vegas Golden Knights": 1,
    "Washington Capitals": 1,
    "Winnipeg Jets": 1
}


# Class for cleaning and processing NHL Buzz data
class DataCleaner():

    # Function to clean unwanted characters from a file and write cleaned text to another file
    def clean_data_charaters(self, path, path_to_write):
        with open(path, 'r') as ofile:
            with open(path_to_write, 'w') as wfile:
                for line in ofile:
                    text = self.clean_line(line)  # Clean each line
                    wfile.write(text + "\n")  # Write cleaned line to output file

    # Helper function to remove unwanted characters from a line
    def clean_line(self, text):
        text = re.sub(r"[^A-Za-z0-9'/\.,;\-\+=: \"\']", "", text)
        return text.strip()

    # Orchestrates the cleaning and token counting for NHL Buzz data
    def proccess_nhl_buzz_data(self):
        path = "./data/nhl_buzz_data.txt"
        path_to_write = "./clean_data/clean_nhl_buzz_data.txt"
        self.clean_data_charaters(path, path_to_write)  # Clean the raw data file
        self.count_tokens(path_to_write)  # Count tokens in the cleaned file

    # Counts and prints the total number of tokens (words) in a given file
    def count_tokens(self, path):
        total = 0
        with open(path, 'r') as ofile:
            for line in ofile:
                tokens = line.split(" ")
                total += len(tokens)
        print(f"Total tokens found in {path}: {total}")

    # many of the entries have a date with no text. Remove them
    def remove_empty_dates(self, path="./clean_nhl_buzz_data.txt", path_to_write="./usable_buzz_data.txt"):
        with open(path, 'r') as ofile:
            with open(path_to_write, 'w') as wfile:
                string_to_write = ""
                for line in ofile:
                    if re.match(r"^[A-Za-z]+-\d+-\d{4}:$", line):
                        if not string_to_write:
                            string_to_write += line
                    else:
                        string_to_write += line
                        wfile.write(string_to_write)
                        string_to_write = ""
    
    def load_data(self, path="./usable_buzz_data.txt"):
        inputs = []
        data_point = None
        text = ""
        month = None
        day = None
        year = None
        with open(path, 'r') as ofile:
            for line in ofile:
                line = line.strip()
                date = re.match(r"^([A-Za-z]+)-(\d+)-(\d{4}):$", line)
                if not line:
                    continue
                elif date:
                    month = date.group(1)
                    day = date.group(2)
                    year = date.group(3)
                    if data_point:
                        data_point.text = text
                        inputs.append(data_point)
                        text = ""
                elif line in nhl_teams:
                    if text:
                        data_point.text = text
                        inputs.append(data_point)
                        text = ""
                    data_point = BuzzDataPoint(year=year, month=month, day=day)
                    data_point.team = line
                else:
                    if text:
                        text+= " " + line
                    else:
                        text += line
            data_point.text = text
            inputs.append(data_point)
        return inputs

    
                    
                    
                        


# Main script execution
if __name__ == "__main__":
    dc = DataCleaner()
    inputs = dc.load_data()
    for input in inputs:
        print(input)