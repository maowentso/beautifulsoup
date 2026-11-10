# Milestone-3

| file | what it is |
|---|---|
| `bs4/filter.py` | `SoupReplacer` now also takes `name_xformer`, `attrs_xformer`, `xformer` |
| `bs4/__init__.py` | the transformers are called from `popTag`, i.e. while parsing |
| `bs4/tests/test_soupreplacer.py` | 6 new test cases (class `TestSoupReplacerXformers`) |
| `apps/m3/task7.py` | Milestone 1 task 7 (`class="test"` on every `<p>`) using `attrs_xformer` |
| `apps/m3/benchmark.py` | runs Milestone 1 `task7.py` and Milestone 3 `task7.py`, compares output, time, memory |
| `apps/m3/milestone1/task7.py` | copy of my Milestone 1 task 7 (unchanged), used by the benchmark |

```bash
python apps/m3/task7.py apps/m2/data/large.html
python apps/m3/benchmark.py apps/m2/data/large.html apps/m2/data/large.xml
pytest bs4/tests/test_soupreplacer.py
```

The large files are made by `python apps/m2/make_large_files.py` (Milestone 2).

---

## The new API

```python
SoupReplacer(og_tag=None, alt_tag=None, *, name_xformer=None, attrs_xformer=None, xformer=None)
```

The Milestone 2 form `SoupReplacer("b", "blockquote")` works exactly as before. The new keyword arguments are
functions that take a `Tag` that is already in the tree:

| argument | returns | effect |
|---|---|---|
| `name_xformer(tag)` | a non-empty string | becomes the tag's new name |
| `attrs_xformer(tag)` | a dict | becomes the tag's new attributes |
| `xformer(tag)` | nothing | may change the tag in any way (side effects) |

```python
b_to_blockquote = SoupReplacer(name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name)
print(BeautifulSoup(html_doc, "html.parser", replacer=b_to_blockquote).prettify())

def remove_class_attr(tag):
    if "class" in tag.attrs:
        del tag.attrs["class"]

class_deleter = SoupReplacer(xformer=remove_class_attr)
print(BeautifulSoup(html_doc, "html.parser", replacer=class_deleter).prettify())
```

**When the functions are called.** Each tag is transformed once, at the moment the parser *closes* it. At that point
the tag is complete: it has its attributes, its parent, and all of its contents. Tags are therefore transformed
innermost first, and a function sees the tag's children already transformed. If more than one function is given,
the order is `name_xformer`, then `attrs_xformer`, then `xformer`. A Milestone 2 `og_tag`/`alt_tag` rename happens
earlier, when the tag is created.

Why on close and not on open:

* The parser finds the open tag that an end tag such as `</b>` belongs to **by name** (`_popToTag`), and counts open
  tags by name (`open_tag_counter`). If a function renamed a tag while it was still open, its end tag would no longer
  match, and the nesting would break. A closed tag has already left the tag stack, so renaming it is safe.
* A function called on open could not see the tag's contents, so `xformer` would be much weaker.

### Changes (line numbers in the modified files)

| where | change |
|---|---|
| `bs4/filter.py:685` | `SoupReplacer` class rewritten; docstring explains both forms and the timing |
| `bs4/filter.py:743` | `__init__(og_tag=None, alt_tag=None, *, name_xformer=None, attrs_xformer=None, xformer=None)`: checks that `og_tag`/`alt_tag` come as a pair, that the transformers are callable, and that at least something is given |
| `bs4/filter.py:783` | `has_xformers` property, so the parser can skip the hook when there are no transformers (the Milestone 2 form costs nothing extra) |
| `bs4/filter.py:787` | `replace(name)`: the Milestone 2 rename, unchanged except that `og_tag` may now be `None` |
| `bs4/filter.py:798` | `transform(tag)`: calls the three functions in order and checks their results (`name_xformer` must return a non-empty string, `attrs_xformer` a dict) |
| `bs4/__init__.py:832-837` | in `popTag`: after the tag has left the tag stack, call `_transform_closed_tag(tag)` |
| `bs4/__init__.py:840` | new `_transform_closed_tag`: runs `replacer.transform(tag)`, then resets `_most_recent_element` to the last element of the still-open parent. Without this, an `xformer` that removes or replaces the tag (`decompose()`, `replace_with()`) or adds elements after it (`insert_after()`) would leave the next parsed element linked to the wrong place in the `next_element` chain. |
| `bs4/__init__.py:266` | constructor docstring for `replacer` updated |

`popTag` is the one place where all tags are closed, with `html.parser`, `lxml` and `lxml-xml`. That covers explicit
end tags, empty-element tags such as `<br>`, tags closed implicitly by badly nested markup, and the tags still open at
the end of the document. As before, `html5lib` builds its own tree, so it does not support a replacer and gives a
warning.

### Tests – `bs4/tests/test_soupreplacer.py`, class `TestSoupReplacerXformers`

1. `test_name_xformer` (run for `html.parser` and `lxml-xml`): `<b>` → `<blockquote>`, including a `<b>` nested inside
   a `<b>`, which stays nested. This shows end tags still match after renaming. The result is identical to the
   Milestone 1 way (parse, then rename in a second pass).
2. `test_attrs_xformer`: Milestone 1 task 7 (`class="test"` on every `<p>`). Other attributes are kept, other tags are
   untouched, and the result is identical to the Milestone 1 way.
3. `test_xformer`: the `remove_class_attr` example from the assignment. The result is identical to the Milestone 1 way.
4. `test_xformers_run_during_parsing`: records each call. The results show each tag is transformed once, innermost
   first, with its contents complete. When the first `<p>` is transformed, its parent has only one child, because the
   second `<p>` has not been parsed yet. So the work really happens during parsing, not in a second pass.
5. `test_xformer_can_remove_and_add_elements`: an `xformer` that removes `<script>` and inserts an `<hr>` after each
   `<p>`. Text parsed afterwards is still linked correctly (`next_element` / `previous_element` agree with the tree).
   I checked that this test fails if the linkage fix in `_transform_closed_tag` is removed.
6. `test_combinations_and_invalid_arguments`: `og_tag`/`alt_tag` with all three transformers runs in the documented
   order. Tags rejected by `parse_only` are never transformed. Bad arguments (no arguments, only `og_tag`, a
   non-callable) and bad results (`name_xformer` returning `None`, `attrs_xformer` returning a list) raise errors.


### Task 7 application

`apps/m3/task7.py` uses `attrs_xformer` to give every `<p>` `class="test"` while parsing, and writes
`output_task7.html`, like Milestone 1.

`python apps/m3/benchmark.py apps/m2/data/large.html apps/m2/data/large.xml` (25 MB each, separate processes):

| file | M1 time | M3 time | M1 peak | M3 peak | output |
|---|---|---|---|---|---|
| large.html | 9.88 s | 10.03 s | 694 MB | 676 MB | same |
| large.xml | 5.75 s | 6.60 s | 585 MB | 552 MB | same |

---

## Technical brief: SoupReplacer, Milestone 2 vs. Milestone 3

*To: the team. Subject: should we extend Beautiful Soup with transform-while-parsing, and in which form?*

### The two designs

**Milestone 2 – `SoupReplacer("b", "blockquote")`.** A declarative rename: one tag name maps to another.

* The parser applies it before the `Tag` object is created, so the tag is born with its new name. The tree builder's
  per-tag rules (empty-element tags, multi-valued `class`, whitespace handling) follow the new name, and end tags are
  renamed the same way.
* It is a single string comparison per tag. It cannot fail at run time, and it is easy to document and reason about.
* It is very narrow. It cannot depend on attributes or position, cannot touch attributes, and cannot remove or add
  anything. It cannot even do two renames, because `BeautifulSoup` accepts only one replacer.

**Milestone 3 – `SoupReplacer(name_xformer=, attrs_xformer=, xformer=)`.** A function hook: arbitrary Python runs on
each tag.

* It covers the Milestone 2 case and much more: renames that depend on attributes, attribute rewriting (task 7),
  removing elements (`<script>`), wrapping and inserting.
* The cost is complexity, and most of it is about *when* the function runs. A function cannot run on a tag before the
  tag exists, and it cannot safely rename a tag while the parser still has to match its end tag. I chose to call the
  functions when a tag is closed. That gives the function the complete tag and makes renaming safe, but it means
  bottom-up order: a function never sees later siblings, and children are transformed before their parent.
* Side effects can break the parser's internal state. An `xformer` that removed the tag it was given corrupted the
  `next_element` chain until I added a fix (`_transform_closed_tag`). Each new kind of side effect is a new way to
  break invariants that the rest of Beautiful Soup relies on.
* Errors appear in the middle of a parse, and the user gets no tree at all.
* `xformer` alone can do everything `name_xformer` and `attrs_xformer` can (`tag.name = …`, `tag.attrs = …`). Three
  overlapping hooks make users ask which one to use and in what order the hooks run.

### What the measurements say

On a 25 MB page (398,282 tags), parsing alone takes about 7.1 s. The second pass that a replacer avoids
(`find_all("p")` plus setting the class) costs only 0.2–0.5 s, which is within run-to-run noise. A Milestone 3
transformer that does *nothing* costs about the same, because it is a Python call for every tag. Peak memory is the
same too, because the whole tree is still built. **Neither design makes parsing measurably faster.** The value is
in the API (one step instead of two, and the change is applied at the same time the tag is created), not in
performance. We should not advertise this as a speed feature.

### Recommendation

1. **Adopt the Milestone 3 hook, but make `xformer` the primary interface.** Keep `name_xformer` / `attrs_xformer` as
   convenience wrappers, since they validate their results and read well for the common case. Keep the Milestone 2
   `SoupReplacer(og, alt)` as shorthand for the most common job. It is the only form that can rename before creation,
   so builder rules follow the new name.
2. **Document the timing as part of the contract:** called once per tag, when it is closed, innermost first, with the
   tag's contents complete and its later siblings not yet parsed. Users who need the finished document should
   transform it after parsing.
3. **Let users say which tags to call the function for**, ideally by accepting a `SoupStrainer` as a selector
   (`SoupReplacer(xformer=f, only=SoupStrainer("p"))`). This avoids a Python call for every tag. It also reuses
   matching logic users already know: SoupStrainer *selects*, SoupReplacer *changes*.
4. **Limit side effects to the given tag and its subtree.** Removing, replacing or adding siblings is supported now,
   but we should keep tests like `test_xformer_can_remove_and_add_elements` for every operation we allow. Changing
   ancestors should be documented as unsupported.
5. **Be honest about the limits:** no support for `html5lib`, and no performance gain. The one case where it can
   help memory is an `xformer` that removes large subtrees as they close (for example `<script>` or `<svg>`), because
   those subtrees are freed during the parse instead of being kept until the end.
