"""Milestone 1 task 6 (change every <b> to <blockquote>) using SoupReplacer.

Usage: python task6.py <file.html|file.xml>
Writes output_task6.html in the current directory.

Milestone 1 parsed the document and then walked the tree with
find_all("b") to rename each tag. Here the SoupReplacer renames the tags
while the tree is being built, so there is no second pass.
"""
from _common import get_input
from bs4 import BeautifulSoup, SoupReplacer

filename, parser = get_input()

b_to_blockquote = SoupReplacer("b", "blockquote")

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, replacer=b_to_blockquote)

with open("output_task6.html", "w", encoding="utf-8") as f:
    f.write(str(soup))
