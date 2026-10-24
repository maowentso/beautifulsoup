from _common import get_input
from bs4 import BeautifulSoup, SoupStrainer

filename, parser = get_input()

all_tags = set()


def record_name(name):
    if parser == "xml" and ":" in name:
        return False
    all_tags.add(name)
    return False


names_only = SoupStrainer(record_name)

with open(filename, "r", encoding="utf-8") as f:
    BeautifulSoup(f, parser, parse_only=names_only)

print("Document tags:", all_tags)
