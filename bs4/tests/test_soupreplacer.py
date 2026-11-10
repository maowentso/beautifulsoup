"""Tests for SoupReplacer (Milestone 2, Part 3)."""

import pytest

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from bs4.element import Tag

from . import LXML_PRESENT, SoupTest


class TestSoupReplacer(SoupTest):
    @pytest.mark.parametrize(
        "parser",
        [
            "html.parser",
            pytest.param(
                "lxml-xml",
                marks=pytest.mark.skipif(not LXML_PRESENT, reason="lxml not installed"),
            ),
        ],
    )
    def test_replaces_tags_during_parsing(self, parser):
        markup = (
            '<div><b class="a b" id="x">bold <i>it</i></b> and '
            "<b>outer <b>inner</b></b></div>"
        )

        # Record the name of every Tag the parser creates.
        created = []

        class RecordingTag(Tag):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                created.append(self.name)

        soup = BeautifulSoup(
            markup,
            parser,
            replacer=SoupReplacer("b", "blockquote"),
            element_classes={Tag: RecordingTag},
        )

        # No <b> was ever created, so the renaming happened during
        # parsing, not after it.
        assert "b" not in created
        assert soup.find("b") is None
        assert [t.name for t in soup.find_all(True)] == [
            "div", "blockquote", "i", "blockquote", "blockquote"
        ]

        # Nesting and attributes are kept.
        first = soup.blockquote
        assert first["id"] == "x"
        assert first.i.string == "it"
        assert soup.find_all("blockquote")[2].parent.name == "blockquote"

        # The result is the same as renaming after parsing (Milestone 1).
        expected = BeautifulSoup(markup, parser)
        for b in expected.find_all("b"):
            b.name = "blockquote"
        assert soup.decode() == expected.decode()

    def test_only_matching_tags_are_replaced(self):
        replacer = SoupReplacer("b", "blockquote")
        markup = "<p><b>1</b><bb>2</bb><abbr>3</abbr><strong>4</strong></p>"

        # Tags whose names merely contain "b" are left alone.
        soup = BeautifulSoup(markup, "html.parser", replacer=replacer)
        assert [t.name for t in soup.find_all(True)] == [
            "p", "blockquote", "bb", "abbr", "strong"
        ]

        # A replacer that matches nothing changes nothing.
        unchanged = BeautifulSoup(
            markup, "html.parser", replacer=SoupReplacer("u", "em")
        )
        assert unchanged.decode() == BeautifulSoup(markup, "html.parser").decode()

        # parse_only sees the original name, then the tag is renamed.
        strained = BeautifulSoup(
            markup, "html.parser", parse_only=SoupStrainer("b"), replacer=replacer
        )
        assert [t.name for t in strained.find_all(True)] == ["blockquote"]

        # Badly nested markup gives the same tree as renaming afterwards,
        # because end tags are renamed the same way as start tags.
        messy = "<div><b>one<b>two</b>three</div>four<b>five<p>six</p>"
        expected = BeautifulSoup(messy, "html.parser")
        for b in expected.find_all("b"):
            b.name = "blockquote"
        actual = BeautifulSoup(messy, "html.parser", replacer=replacer)
        assert actual.decode() == expected.decode()

        # Bad arguments are rejected.
        with pytest.raises(ValueError):
            SoupReplacer("", "blockquote")
        with pytest.raises(TypeError):
            SoupReplacer("b", None)
        with pytest.raises(TypeError):
            BeautifulSoup("<b>x</b>", "html.parser", replacer="b")


def two_pass(markup, parser, change):
    """The Milestone 1 way: parse the whole document, then walk the
    finished tree and change every tag."""
    soup = BeautifulSoup(markup, parser)
    for tag in soup.find_all(True):
        change(tag)
    return soup


def linkage_is_consistent(soup):
    """next_element / previous_element agree with the tree structure."""
    descendants = list(soup.descendants)
    forward = []
    element = descendants[0]
    while element is not None:
        forward.append(element)
        element = element.next_element
    backward = []
    element = descendants[-1]
    while element is not None and element is not soup:
        backward.append(element)
        element = element.previous_element
    return forward == descendants and backward[::-1] == descendants


class TestSoupReplacerXformers(SoupTest):
    """Milestone 3: name_xformer, attrs_xformer and xformer."""

    MARKUP = (
        '<div class="page"><p class="intro">one <b class="k">bold '
        "<b>nested</b></b></p><p>two</p><br><script>var x;</script>"
        '<p id="last">three</p></div>'
    )

    @pytest.mark.parametrize(
        "parser",
        [
            "html.parser",
            pytest.param(
                "lxml-xml",
                marks=pytest.mark.skipif(not LXML_PRESENT, reason="lxml not installed"),
            ),
        ],
    )
    def test_name_xformer(self, parser):
        def b_to_blockquote(tag):
            return "blockquote" if tag.name == "b" else tag.name

        soup = BeautifulSoup(
            self.MARKUP, parser, replacer=SoupReplacer(name_xformer=b_to_blockquote)
        )
        assert soup.find("b") is None
        assert len(soup.find_all("blockquote")) == 2
        # The nested <b> is still inside the outer one: end tags were
        # matched correctly even though the names changed.
        assert soup.blockquote.blockquote.string == "nested"

        def rename(tag):
            tag.name = b_to_blockquote(tag)

        assert soup.decode() == two_pass(self.MARKUP, parser, rename).decode()

    def test_attrs_xformer(self):
        def add_test_class(tag):
            if tag.name == "p":
                return {**tag.attrs, "class": "test"}
            return tag.attrs

        soup = BeautifulSoup(
            self.MARKUP, "html.parser", replacer=SoupReplacer(attrs_xformer=add_test_class)
        )
        assert [p["class"] for p in soup.find_all("p")] == ["test"] * 3
        # Other attributes of <p> are kept, other tags are untouched.
        assert soup.find("p", id="last") is not None
        assert soup.div["class"] == ["page"]
        assert soup.b["class"] == ["k"]

        def set_class(tag):
            if tag.name == "p":
                tag["class"] = "test"

        expected = two_pass(self.MARKUP, "html.parser", set_class)
        assert soup.decode() == expected.decode()

    def test_xformer(self):
        # The example from the assignment.
        def remove_class_attr(tag):
            if "class" in tag.attrs:
                del tag.attrs["class"]

        soup = BeautifulSoup(
            self.MARKUP, "html.parser", replacer=SoupReplacer(xformer=remove_class_attr)
        )
        assert soup.find_all(class_=True) == []
        assert soup.find("p", id="last") is not None
        expected = two_pass(self.MARKUP, "html.parser", remove_class_attr)
        assert soup.decode() == expected.decode()

    def test_xformers_run_during_parsing(self):
        # Record, for each call, the tag's name, the text it contains,
        # and how much of the document had been parsed at that moment.
        calls = []

        def record(tag):
            calls.append(
                (tag.name, tag.get_text(), len(list(tag.parent.children)))
            )

        BeautifulSoup(
            "<div><p>a<i>b</i></p><p>c</p></div>",
            "html.parser",
            replacer=SoupReplacer(xformer=record),
        )
        # Each tag is transformed once, as soon as it is closed:
        # innermost first, with all of its contents already parsed.
        # When the first <p> is transformed, its parent <div> has only
        # one child: the second <p> has not been parsed yet. So this
        # happens during parsing, not in a pass over the finished tree.
        assert calls == [
            ("i", "b", 2),
            ("p", "ab", 1),
            ("p", "c", 2),
            ("div", "abc", 1),
        ]

    def test_xformer_can_remove_and_add_elements(self):
        def edit(tag):
            if tag.name == "script":
                tag.decompose()
            elif tag.name == "p":
                tag.insert_after(BeautifulSoup("", "html.parser").new_tag("hr"))

        soup = BeautifulSoup(
            self.MARKUP + "after", "html.parser", replacer=SoupReplacer(xformer=edit)
        )
        assert soup.find("script") is None
        assert len(soup.find_all("hr")) == 3
        assert soup.find("p", id="last").next_sibling.name == "hr"
        # Text parsed after the changes is still linked correctly.
        assert linkage_is_consistent(soup)
        assert list(soup.strings)[-1] == "after"

    def test_combinations_and_invalid_arguments(self):
        order = []

        def name_x(tag):
            order.append(("name", tag.name))
            return tag.name.upper()

        def attrs_x(tag):
            order.append(("attrs", tag.name))
            return {"seen": "yes"}

        def x(tag):
            order.append(("x", tag.name))

        # og_tag/alt_tag first (when the tag is created), then the
        # transformers in the order name, attrs, xformer.
        replacer = SoupReplacer(
            "b", "strong", name_xformer=name_x, attrs_xformer=attrs_x, xformer=x
        )
        soup = BeautifulSoup('<b class="c">x</b>', "html.parser", replacer=replacer)
        assert order == [("name", "strong"), ("attrs", "STRONG"), ("x", "STRONG")]
        assert soup.decode() == '<STRONG seen="yes">x</STRONG>'

        # Tags rejected by parse_only are never created, so never transformed.
        seen = []
        BeautifulSoup(
            "<p>1</p><b>2</b>",
            "html.parser",
            parse_only=SoupStrainer("b"),
            replacer=SoupReplacer(xformer=lambda tag: seen.append(tag.name)),
        )
        assert seen == ["b"]

        # Bad arguments and bad transformer results are rejected.
        with pytest.raises(TypeError):
            SoupReplacer()
        with pytest.raises(TypeError):
            SoupReplacer("b")
        with pytest.raises(TypeError):
            SoupReplacer(xformer="not a function")
        with pytest.raises(ValueError):
            BeautifulSoup(
                "<b>x</b>", "html.parser",
                replacer=SoupReplacer(name_xformer=lambda tag: None),
            )
        with pytest.raises(TypeError):
            BeautifulSoup(
                "<b>x</b>", "html.parser",
                replacer=SoupReplacer(attrs_xformer=lambda tag: ["class"]),
            )
