"""Milestone 1 task 4 (print every tag that has an id) using SoupStrainer.

Usage: python task4.py <file.html|file.xml>

SoupStrainer(id=True) lets a tag be created only if it has an id attribute.
A tag with an id is kept with everything inside it, so tags with an id
nested in it are still found by find_all(id=True).
"""
from _common import get_input
from bs4 import BeautifulSoup, SoupStrainer

filename, parser = get_input()

has_id = SoupStrainer(id=True)

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, parse_only=has_id)

tags_with_id = soup.find_all(id=True)
for tag in tags_with_id:
    print(f"Tag: {tag.name}, ID: {tag['id']}")
