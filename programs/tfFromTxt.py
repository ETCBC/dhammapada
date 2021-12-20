import os
import collections
import re
from textwrap import wrap


BASE = os.path.expanduser("~/github")
ORG = "etcbc"
REPO = "dhammapada"
SOURCE_DIR = f"{BASE}/{ORG}/{REPO}/sources"

PALI = "pali"
LATIN = "latin"

SOURCES = (PALI, LATIN)


class Converter:
    def __init__(self):
        self.read()

    def read(self):
        texts = {}
        self.texts = texts
        offsets = {src: 0 for src in SOURCES}
        self.offsets = offsets
        letters = {src: collections.Counter() for src in SOURCES}
        self.letters = letters
        self.affixes = {
            src: {kind: collections.Counter() for kind in ("pre", "post")}
            for src in SOURCES
        }
        self.chunks = {src: [] for src in SOURCES}

        for src in SOURCES:
            theseLetters = letters[src]

            with open(f"{SOURCE_DIR}/{src}.txt") as f:
                text = []
                texts[src] = text
                inFront = True

                for line in f:
                    if inFront:
                        offsets[src] += 1
                        if line.startswith("----------"):
                            inFront = False
                    else:
                        material = line.rstrip("\n")
                        for c in material:
                            theseLetters[c] += 1
                        text.append(material)
            print(f"{src:<5}: {len(text):>4} lines")

    def showLetters(self, src):
        theseLetters = self.letters[src]
        for (c, f) in sorted(theseLetters.items(), key=lambda x: (-x[1], x[0])):
            print(f"│{c}│ : {f:>7} x")
        print("".join(sorted(theseLetters)))

    def showAffixes(self, src):
        affixes = self.affixes[src]

        for (kind, theseAffixes) in sorted(affixes.items()):
            kindRepE = "〉" if kind == "pre" else "│"
            kindRepB = "〈" if kind == "post" else "│"
            for (c, f) in sorted(theseAffixes.items(), key=lambda x: (-x[1], x[0])):
                rep = f"{kindRepB}{c}{kindRepE}"
                print(f"{rep:<4} : {f:>7} x")

    def showChunks(self, src):
        chunks = self.chunks[src]
        for (
            line,
            vagga,
            stanza,
            label,
            sentence,
            clause,
            quote,
            uncertain,
            code,
            pre,
            word,
            post,
        ) in chunks:
            q = '"' if quote else ""
            u = "~" if uncertain else ""
            preRep = f"{pre}│"
            postRep = f"│{post}"
            print(
                f"ln{line}:v{vagga}:s{stanza}{label}:"
                f"{sentence},{clause}{q}{u}"
                f"={preRep}{word}{postRep}"
            )

    def show(self, src, start=None, end=None):
        text = self.texts[src]
        offset = self.offsets[src]

        b = 0 if start is None else max((start - 1, 0))
        e = len(text) if end is None else min(end, len(text))

        for ln in range(b, e):
            line = "\n".join(wrap(text[ln], width=80, subsequent_indent=" " * 6))
            print(f"{ln + 1 + offset:>4}: {line}")

    def chunk(self, src):
        if src == PALI:
            self.chunkPali()
        elif src == LATIN:
            self.chunkLatin()

    def msg(self, msg):
        cur = self.cur
        print(f"{cur['line']}: {msg}")

    def chunkPali(self):
        offset = self.offsets[PALI]
        affixes = self.affixes[PALI]
        chunks = self.chunks[PALI]
        chunks.clear()
        cur = dict(
            line=offset,
            vagga=0,
            stanza=0,
            label="",
            sentence=1,
            clause=1,
            quote=False,
            uncertain=False,
        )
        self.cur = cur
        text = self.texts[PALI]

        vaggaRe = re.compile(r"^([0-9]+)\s*\.\s*(.*)$")
        stanzaRe = re.compile(r"^([0-9]+)([a-z]?)\s+(.*)$")

        wordPat = r"\w'‘*-"
        wordRe = re.compile(fr"^([^{wordPat}]*)([{wordPat}]+)([^{wordPat}]*)$")

        for line in text:
            cur["line"] += 1
            material = ""
            code = ""
            good = True

            for _ in [1]:
                match = vaggaRe.match(line)
                if match:
                    n = int(match.group(1))
                    material = match.group(2)
                    exp = cur["vagga"] + 1
                    if n != exp:
                        self.msg(f"ERROR: vagga number {n} unexpected at {exp}")
                        good = False
                        break
                    cur["vagga"] = n
                    code = "title"
                    continue

                match = stanzaRe.match(line)
                if match:
                    n = int(match.group(1))
                    label = match.group(2)
                    material = match.group(3)
                    expNum = (
                        cur["stanza"] if label and label != "a" else cur["stanza"] + 1
                    )
                    if n != expNum:
                        self.msg(
                            f"ERROR: unexpected stanza number {n} instead of {expNum}"
                        )
                        good = False
                        break

                    if label:
                        expLabel = chr(ord(cur["label"]) + 1) if cur["label"] else "a"
                        if label != expLabel:
                            self.msg(
                                f"ERROR: unexpected stanza label {label}"
                                f" instead of {expLabel}"
                            )
                            good = False
                            break

                    cur["stanza"] = n
                    cur["label"] = label
                    code = "stanza"
                    continue

                material = line

            if not good:
                break

            material = material.strip()
            if material:
                words = material.split()
                for word in words:
                    match = wordRe.match(word)
                    if not match:
                        self.msg(f"Strange word: │{word}│")
                        good = False
                        break

                    preWord = match.group(1)
                    word = match.group(2)
                    postWord = match.group(3)

                    affixes["pre"][preWord] += 1
                    affixes["post"][postWord] += 1

                    if '"' in preWord:
                        cur["quote"] = not cur["quote"]
                    if "[" in preWord:
                        cur["uncertain"] = True
                    elif "]" in preWord:
                        cur["uncertain"] = False

                    chunks.append(
                        (
                            cur["line"],
                            cur["vagga"],
                            cur["stanza"],
                            cur["label"],
                            cur["sentence"],
                            cur["clause"],
                            cur["quote"],
                            cur["uncertain"],
                            code,
                            preWord,
                            word,
                            postWord,
                        )
                    )

                    if "[" in postWord:
                        cur["uncertain"] = True
                    elif "]" in postWord:
                        cur["uncertain"] = False
                    if '"' in postWord:
                        cur["quote"] = not cur["quote"]
                    if "," in postWord or ";" in postWord or ":" in postWord:
                        cur["clause"] += 1
                    if "." in postWord or "?" in postWord:
                        cur["sentence"] += 1
                        cur["clause"] += 1

            if not good:
                break

        if not good:
            self.msg("Aborted")
        else:
            self.msg(f"{cur['vagga']} vaggas")
            self.msg(f"{cur['stanza']} stanzas")
