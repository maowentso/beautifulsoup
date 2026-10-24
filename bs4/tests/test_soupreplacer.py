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
