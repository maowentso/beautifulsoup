import sys
import os
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("you need a file")
    sys.exit(1)

filename = sys.argv[1]
ext = os.path.splitext(filename)[1].lower()
parser = "xml" if ext == ".xml" else "html.parser"

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser)

for b_tag in soup.find_all("b"):
    b_tag.name = "blockquote"

with open("output_task6.html", "w", encoding="utf-8") as f:
    f.write(str(soup))