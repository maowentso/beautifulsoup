from _common import get_input
from bs4 import BeautifulSoup, SoupReplacer

filename, parser = get_input()


# Called for every tag while it is parsed; returns the tag's new attributes.
def p_class_test(tag):
    if tag.name == "p":
        return {**tag.attrs, "class": "test"}
    return tag.attrs


add_test_class = SoupReplacer(attrs_xformer=p_class_test)
with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, parser, replacer=add_test_class)

with open("output_task7.html", "w", encoding="utf-8") as f:
    f.write(str(soup))
