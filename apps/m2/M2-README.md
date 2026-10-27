# Milestone-2

| file |  | what it is |
|---|---|---|
| `apps/m2/task2.py`, `task3.py`, `task4.py` |  | Milestone 1 tasks 2, 3, 4 using `SoupStrainer` |
| `apps/m2/task6.py` |  | Milestone 1 task 6 using `SoupReplacer` |
| `apps/m2/make_large_files.py` |  | generates the large test files (`data/large.html`, `data/large.xml`) |
| `apps/m2/benchmark.py` | | runs each Milestone 1 program and its Milestone 2 version, compares output, time, memory |
| `bs4/filter.py`, `bs4/__init__.py` |  | the new `SoupReplacer` API |
| `bs4/tests/test_soupreplacer.py` |  | the 2 new test cases |

```bash
python apps/m2/make_large_files.py          # creates 25 MB data/large.html and data/large.xml
python apps/m2/task2.py apps/m2/data/large.html
python apps/m2/benchmark.py apps/m2/data/large.html apps/m2/data/large.xml
pytest bs4/tests/test_soupreplacer.py
```

---

## SoupStrainer

| program | Milestone 1 output | strainer |
|---|---|---|
| `task2.py` | `href` and text of every `<a>` | `SoupStrainer("a")`: only `<a>` tags and their contents are built |
| `task3.py` | the set of all tag names | `SoupStrainer(record_name)`: see below |
| `task4.py` | name and id of every tag with an `id` | `SoupStrainer(id=True)`: only tags with an `id` (and their contents) are built |

**Task 3.** The obvious strainer, `SoupStrainer(True)`, accepts every tag, so it builds the whole tree and saves
nothing. `task3.py` uses another approach. During parsing, `BeautifulSoup.handle_starttag` asks the strainer whether
each tag may be created (`SoupStrainer.allow_tag_creation`). That call passes the tag *name* to a name function. The
function in `task3.py` adds the name to a set and returns `False`, so no tag is ever created. Because no tag is
accepted, the parser never goes "inside" an accepted tag, so the strainer is asked about every tag in the document.
Text is dropped too, because a strainer with a name rule rejects all strings. The result is the full set of names,
with an almost empty tree.

### Large-file test

`make_large_files.py` generates the files with a fixed random seed, so anyone can recreate them. (They are
not committed because of their size.) `large.html` (25 MB): 8,772 `<section id=…>` blocks with paragraphs, links,
`<b>`, lists, tables and scripts. `large.xml` (25 MB): 36,699 `<record id=…>` blocks, including a namespaced
`<dc:creator>` tag.

`python apps/m2/benchmark.py apps/m2/data/large.html apps/m2/data/large.xml` runs each program in its own process.
"Peak" is the process's maximum resident memory.

| file | task | M1 time | M2 time | M1 peak | M2 peak | output |
|---|---|---|---|---|---|---|
| large.html | 2 | 6.98 s | **3.73 s** | 550 MB | **166 MB** | same |
| large.html | 3 | 7.57 s | **2.99 s** | 513 MB | **76 MB** | same |
| large.html | 4 | 7.85 s | 8.08 s | 521 MB | 545 MB | same |
| large.html | 6 | 10.16 s | 9.87 s | 693 MB | 657 MB | same |
| large.xml | 2 | 4.60 s | **1.93 s** | 396 MB | **217 MB** | same |
| large.xml | 3 | 4.26 s | **1.53 s** | 411 MB | **177 MB** | same |
| large.xml | 4 | 4.29 s | 4.29 s | 490 MB | 478 MB | same |
| large.xml | 6 | 5.81 s | 6.01 s | 642 MB | 531 MB | same |

Findings:

1. **Tasks 2 and 3** produce exactly the Milestone 1 output while using 2–7× less memory and about half the time.
   The parser still has to tokenize the whole file, so time drops less than memory.
2. **Task 4 gains nothing on these files**, and this is expected. A strainer keeps the *whole* subtree of a tag it
   accepts. Here every `<section>` / `<record>` has an `id` and contains almost all of the document, so almost
   everything is still built. `SoupStrainer(id=True)` only pays off when the tags with an `id` are small parts of
   the document.
3. A strainer only checks tags and strings that are outside every accepted tag (`len(self.tagStack) <= 1` in
   `handle_starttag` and `endData`). This explains both the trick in task 3 and the lack of savings in task 4.
4. Timings vary by roughly ±10 % between runs, so only the large differences above are meaningful.

## Where the API functions are defined

### Milestone 1

| API used | task(s) | defined at |
|---|---|---|
| `BeautifulSoup(markup, parser)` | 1–8 | class `BeautifulSoup` `bs4/__init__.py:133`, constructor `BeautifulSoup.__init__` `bs4/__init__.py:209`; parsing starts in `BeautifulSoup._feed` `bs4/__init__.py:650` |
| `soup.prettify()` | 1 | `Tag.prettify` `bs4/element.py:2601` (it calls `BeautifulSoup.decode` `bs4/__init__.py:1073` → `Tag.decode` `bs4/element.py:2334`) |
| `find_all("a")`, `find_all(True)`, `find_all(id=True)`, `find_all("b")`, `find_all("p")` | 2–7 | `Tag.find_all` `bs4/element.py:2715` → `PageElement._find_all` `bs4/element.py:1079`; returns a `ResultSet` `bs4/element.py:2861`. `find_all(id=True)` creates a `SoupStrainer` and calls `ElementFilter.find_all` `bs4/filter.py:137` → `SoupStrainer.match` `bs4/filter.py:650` → `SoupStrainer.matches_tag` `bs4/filter.py:475` |
| `tag.get("href")` | 2 | `Tag.get` `bs4/element.py:2160` |
| `tag.get_text(...)` / `soup.get_text()` | 2, 8 | `PageElement.get_text` `bs4/element.py:524` (alias `getText` `:549`); uses `Tag._all_strings` `bs4/element.py:1873` |
| `tag.name` (read in 3, 4, 5; assigned in 6) | 3–6 | plain attribute of `Tag`, set in `Tag.__init__` `bs4/element.py:1618` at `bs4/element.py:1648` (`self.name = name`); class `Tag` `bs4/element.py:1569` |
| `tag["id"]`, `a["href"]` | 4, 5 | `Tag.__getitem__` `bs4/element.py:2203` |
| `a.find_parent([...])` | 5 | `PageElement.find_parent` `bs4/element.py:992` (calls `find_parents` `bs4/element.py:1022`) |
| `p_tag["class"] = "test"` | 7 | `Tag.__setitem__` `bs4/element.py:2223` |
| `str(soup)` | 6, 7 | `Tag.__str__` `bs4/element.py:2302` (`__str__ = __unicode__ = __repr__`) → `Tag.__repr__` `bs4/element.py:2298` → `BeautifulSoup.decode` `bs4/__init__.py:1073` |
| `soup.select("script, style")` | 8 | `Tag.select` `bs4/element.py:2799` → `Tag.css` `bs4/element.py:2825` → `CSS.select` `bs4/css.py:161` (which calls the external `soupsieve` package) |
| `tag.decompose()` | 8 | `PageElement.decompose` `bs4/element.py:635` |

### Milestone 2, Part 1

| API used | defined at |
|---|---|
| `SoupStrainer(...)` | class `SoupStrainer` `bs4/filter.py:313`, constructor `SoupStrainer.__init__` `bs4/filter.py:345` (arguments turned into rules by `_make_match_rules` `bs4/filter.py:434`); base class `ElementFilter` `bs4/filter.py:43` |
| `BeautifulSoup(..., parse_only=...)` | parameter at `bs4/__init__.py:214`, stored at `bs4/__init__.py:437`; empty-strainer warning uses `SoupStrainer.excludes_everything` `bs4/filter.py:399` |
| tags filtered while parsing | `BeautifulSoup.handle_starttag` `bs4/__init__.py:987` calls `SoupStrainer.allow_tag_creation` `bs4/filter.py:580` at `bs4/__init__.py:1024`; the name function of task 3 is called from `MatchRule.matches_string` `bs4/filter.py:259` |
| strings filtered while parsing | `BeautifulSoup.endData` `bs4/__init__.py:826` calls `SoupStrainer.allow_string_creation` `bs4/filter.py:621` at `bs4/__init__.py:859` |
| who calls `handle_starttag` | `BeautifulSoupHTMLParser.handle_starttag` `bs4/builder/_htmlparser.py:142` (call at `:182`) for `html.parser`; `LXMLTreeBuilderForXML.start` `bs4/builder/_lxml.py:312` for `xml` / `lxml` |
| `find_all`, `get`, `get_text`, `name`, `tag["id"]` on the strained tree | same as in the Milestone 1 table |


---


## SoupReplacer

```python
from bs4 import BeautifulSoup, SoupReplacer

b_to_blockquote = SoupReplacer("b", "blockquote")
print(BeautifulSoup(html_doc, "html.parser", replacer=b_to_blockquote).prettify())
```

### Changes (line numbers in the **modified** files)

| where | change |
|---|---|
| `bs4/filter.py:685` | new class `SoupReplacer(og_tag, alt_tag)`; `replace(name)` (`:722`) returns `alt_tag` for `og_tag`, otherwise `name`. Both arguments must be non-empty strings. |
| `bs4/__init__.py:36`, `:94` | exported, so `from bs4 import SoupReplacer` works |
| `bs4/__init__.py:225` | new optional constructor argument `replacer=None`, documented at `:266` |
| `bs4/__init__.py:451-462` | type check, warning for `html5lib`, `self.replacer = replacer`. This runs before the document is fed to the parser. |
| `bs4/__init__.py:189` | class-level default `replacer = None`. `BeautifulSoup` is a `Tag`, and `Tag.__getattr__` would treat a missing attribute as a search for a child tag named `<replacer>`. |
| `bs4/__init__.py:1055-1056` | in `handle_starttag`: the name is replaced **before the `Tag` object is created**, so a tag with the old name never exists. This comes after the `parse_only` check, so a `SoupStrainer` sees the name used in the document. |
| `bs4/__init__.py:1095-1096` | in `handle_endtag`: the end tag is renamed too. Otherwise `</b>` would not find the open `<blockquote>` in `_popToTag` and the nesting would break. |

`handle_starttag` and `handle_endtag` are where the `html.parser`, `lxml` and `lxml-xml` builders all report tags, so
this one change covers all three. Because the `Tag` is created with the new name, the builder's per-tag rules follow
the new name too.

Limits: names must match exactly (HTML parsers lower-case tag names, so use `"b"`). Only the name changes, not
attributes or contents. `html5lib` builds its own tree without calling `handle_starttag`, so it ignores the replacer and
gives a warning.

### Tests – `bs4/tests/test_soupreplacer.py`

1. `test_replaces_tags_during_parsing` (runs for `html.parser` and `lxml-xml`) checks these points. A `Tag` subclass
   passed with `element_classes` records every tag the parser creates, and no tag named `b` is ever created, which
   proves the replacement happens during parsing. Nesting, attributes and text are kept. The result is identical to the
   Milestone 1 way (parse, then rename every `find_all("b")`).
2. `test_only_matching_tags_are_replaced` checks the remaining behaviour. Tags such as `bb`, `abbr` and `strong` are
   not touched, and a replacer that matches nothing changes nothing. It works together with `parse_only`. Badly nested
   markup gives the same tree as renaming afterwards. Bad arguments raise `ValueError` / `TypeError`.

Full test: 729 passed, 107 skipped before the change; 732 passed, 107 skipped after it. Nothing that passed before fails now.

### Task 6 application

`python apps/m2/task6.py apps/m2/data/large.html` writes `output_task6.html`. On the 25 MB file its output is
byte-for-byte the same as Milestone 1's `task6.py`. The 176 `<b>` left in the output are
text inside `<script>` elements, not tags, exactly as in Milestone 1. The time is about the same as Milestone 1: the
`find_all("b")` pass that `SoupReplacer` avoids is small compared to parsing and writing 25 MB.
