import json


def load_scraping_data(filename) -> dict:
    # Load the scraping data
    with open(filename, "r") as file:
        return json.load(file)