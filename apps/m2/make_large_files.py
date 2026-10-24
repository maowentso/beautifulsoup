"""Generate large HTML and XML files for testing the Milestone 2 apps.

Usage: python make_large_files.py [size_in_MB]     (default 25)
Writes data/large.html and data/large.xml next to this script.

The files are generated, not downloaded, so anyone can recreate them. They
contain the things the tasks look for (links, tags with ids, <b> tags,
nested markup, scripts, tables, namespaced XML tags) mixed into a lot of
ordinary text, roughly like a long real-world page.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

WORDS = (
    "soup parser tree node tag string strainer replacer milestone html xml "
    "document element attribute value parse memory time large file python "
    "the a of and to in is it that for on with as by this be are from"
).split()


def text(rng, n):
    return " ".join(rng.choice(WORDS) for _ in range(n))


def html_section(rng, i):
    parts = [f'<section id="sec-{i}" class="chapter">', f"<h2>Section {i}</h2>"]
    for j in range(rng.randint(3, 6)):
        pid = f' id="p-{i}-{j}"' if rng.random() < 0.1 else ""
        parts.append(
            f"<p{pid}>{text(rng, 40)} <b>{text(rng, 3)}</b> {text(rng, 20)} "
            f'<a href="https://example.com/{i}/{j}">{text(rng, 2)}</a> '
            f"<i>{text(rng, 4)}</i> <span class=\"note\">{text(rng, 10)}</span> "
            f"<b>{text(rng, 2)} <em>{text(rng, 2)}</em></b>.</p>"
        )
    parts.append("<ul>")
    for j in range(rng.randint(2, 5)):
        parts.append(f'<li><a href="#sec-{rng.randint(0, i)}">see {j}</a> {text(rng, 8)}</li>')
    parts.append("</ul>")
    if i % 5 == 0:
        parts.append('<table class="data"><tr><th>key</th><th>value</th></tr>')
        for j in range(5):
            parts.append(f"<tr><td>{text(rng, 2)}</td><td>{rng.random():.6f}</td></tr>")
        parts.append("</table>")
    if i % 50 == 0:
        parts.append(f"<script>var s{i} = '<b>not a tag</b>';</script>")
    parts.append("</section>\n")
    return "".join(parts)


def xml_record(rng, i):
    return (
        f'<record id="r{i}" type="{rng.choice(["book", "paper", "web"])}">'
        f"<title>{text(rng, 6)}</title>"
        f"<dc:creator>{text(rng, 2)}</dc:creator>"
        f"<abstract>{text(rng, 50)} <b>{text(rng, 3)}</b> {text(rng, 30)}</abstract>"
        f'<a href="https://example.com/r/{i}">{text(rng, 2)}</a>'
        f'<keywords><kw>{text(rng, 1)}</kw><kw>{text(rng, 1)}</kw></keywords>'
        f"</record>\n"
    )


def write(path, head, tail, make, target_bytes, rng):
    size = 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        i = 0
        while size < target_bytes:
            chunk = make(rng, i)
            f.write(chunk)
            size += len(chunk)
            i += 1
        f.write(tail)
    print(f"wrote {path}: {os.path.getsize(path) / 1e6:.1f} MB, {i} blocks")


def main():
    mb = float(sys.argv[1]) if len(sys.argv) > 1 else 25
    os.makedirs(DATA, exist_ok=True)
    rng = random.Random(261)  # fixed seed: the same files every time
    write(
        os.path.join(DATA, "large.html"),
        "<!DOCTYPE html>\n<html><head><title>Large test page</title>"
        "<style>b { color: red }</style></head>\n<body>\n"
        '<nav id="top"><a href="#sec-0">start</a></nav>\n',
        "</body></html>\n",
        html_section,
        mb * 1e6,
        rng,
    )
    write(
        os.path.join(DATA, "large.xml"),
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<catalog xmlns:dc="http://purl.org/dc/elements/1.1/">\n',
        "</catalog>\n",
        xml_record,
        mb * 1e6,
        rng,
    )


if __name__ == "__main__":
    main()
