"""Milestone 1 task 2 (print every hyperlink) using SoupStrainer.

Usage: python task2.py <file.html|file.xml>

SoupStrainer("a") makes BeautifulSoup create objects only for <a> tags and
what is inside them; every other tag and all text outside a link is skipped
while parsing.
"""
from _common import get_input
from bs4 import BeautifulSoup, SoupStrainer

filename, parser = get_input()

only_links = SoupStrainer("a")

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, parse_only=only_links)

for a in soup.find_all("a"):
    print(a.get("href"), a.get_text(strip=True))
