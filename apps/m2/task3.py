"""Milestone 1 task 3 (print the set of tag names) using SoupStrainer.

Usage: python task3.py <file.html|file.xml>

Task 3 needs the name of every tag, so a plain SoupStrainer(True) would keep
the whole document and save nothing. Instead, the strainer is given a
function. While parsing, BeautifulSoup calls it with the name of each tag it
is about to create (SoupStrainer.allow_tag_creation). The function records
the name and returns False, so the tag is never built. Because no tag is ever
accepted, every tag in the document is shown to the function, and text is
dropped too (a strainer with name rules rejects all strings). The tree stays
almost empty, but the set of names is complete.
"""
from _common import get_input
from bs4 import BeautifulSoup, SoupStrainer

filename, parser = get_input()

all_tags = set()


def record_name(name):
    # With the xml parser, a prefixed tag <x:b> is offered twice: first as
    # its local name "b", then as "x:b". Milestone 1 printed tag.name, which
    # is the local name, so skip the prefixed form.
    if parser == "xml" and ":" in name:
        return False
    all_tags.add(name)
    return False


names_only = SoupStrainer(record_name)

with open(filename, "r", encoding="utf-8") as f:
    BeautifulSoup(f, parser, parse_only=names_only)

print("Document tags:", all_tags)
