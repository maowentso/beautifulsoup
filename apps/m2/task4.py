from _common import get_input
from bs4 import BeautifulSoup, SoupStrainer

filename, parser = get_input()

has_id = SoupStrainer(id=True)

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, parse_only=has_id)

tags_with_id = soup.find_all(id=True)
for tag in tags_with_id:
    print(f"Tag: {tag.name}, ID: {tag['id']}")
