from _common import get_input
from bs4 import BeautifulSoup, SoupReplacer

filename, parser = get_input()

b_to_blockquote = SoupReplacer("b", "blockquote")
with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, replacer=b_to_blockquote)

with open("output_task6.html", "w", encoding="utf-8") as f:
    f.write(str(soup))
