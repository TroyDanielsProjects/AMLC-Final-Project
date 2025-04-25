import re

# Class representing a single Buzz data entry
class BuzzDataPoint():
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.text = []   # List to store text entries
        self.teams = []  # List to store team names


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

# Main script execution
if __name__ == "__main__":
    dc = DataCleaner()
    dc.proccess_nhl_buzz_data()