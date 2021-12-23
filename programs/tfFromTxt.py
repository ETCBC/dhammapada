import os
import collections
import re
from textwrap import wrap

from tf.fabric import Fabric
from tf.convert.walker import CV


VERSION = "0.1"
SLOT_TYPE = "word"
GENERIC = dict(
    language="pli,lat",
    institute="Text and Traditions, VU Amsterdam",
    project="Dhammapada-latine",
    researcher="Bee Scherer",
    digitizers="Bee Scherer, Yvonne Mataar",
    converters="Dirk Roorda (Text-Fabric)",
    sourceFormat="plain text",
    title="The Dhammapada",
    subtitle="being a collection of moral verses in Pali",
    edition="2nd",
    editor="V. Fausboll",
    publisher="Luzac & Co.",
    place="London",
    yearPublished="1900",
    copynote1="Digitisation supported by Shri Brihad Bhartiya Samaj 20 February 2020",
    stamp="50480",
)
OTEXT = {
    "fmt:text-orig-full": "{palipre/latinpre}{pali/latin}{palipost/latinpost} ",
    "fmt:text-pali-full": "{palipre}{pali}{palipost} ",
    "fmt:text-latin-full": "{latinpre}{latin}{latinpost} ",
    "sectionTypes": "vagga,stanza",
    "sectionFeatures": "n,n",
}
INT_FEATURES = {"n", "trans", "extrastanza", "quote", "uncertain", "clarity"}

FEATURE_META = dict(
    n=dict(
        description=(
            "number of vagga, stanza (relative to work), "
            "sentence, clause (both relative to vagga)"
        ),
        format="positive number, 0 for pre-stanza material in a vagga",
    ),
    pali=dict(
        description="bare word (without non-word-letters)",
        format="string (for Pali original) or empty (for Latin translation)",
    ),
    palipre=dict(
        description="non-word letters before word, no leading spaces",
        format="string (for Pali original) or empty (for Latin translation)",
    ),
    palipost=dict(
        description="non-word letters after word, with trailing spaces",
        format="string (for Pali original) or empty (for Latin translation)",
    ),
    latin=dict(
        description="bare word (without non-word-letters)",
        format="string (for Latin translation) or empty (for Pali original)",
    ),
    latinpre=dict(
        description="non-word letters before word, no leading spaces",
        format="string (for Latin translation) or empty (for Pali original)",
    ),
    latinpost=dict(
        description="non-word letters after word, with trailing spaces",
        format="string (for Latin translation) or empty (for Pali original)",
    ),
    extrastanza=dict(
        description=(
            "word is outside a stanza," " between stanzas or in pre/post vagga material"
        ),
        format="1 (=true) or absent (=false)",
    ),
    quote=dict(
        description="word is inside a quote",
        format="1 (=true) or absent (=false)"
    ),
    uncertain=dict(
        description=(
            "word is marked as uncertain by inclusion in [ and ]; "
            "only in Pali original"
        ),
        format="1 (=true) or absent (=false)",
    ),
    clarity=dict(
        description=(
            "word is inserted for clarity, marked by inclusion in ( and ); "
            "only in Latin translation"
        ),
        format="1 (=true) or absent (=false)",
    ),
    trans=dict(
        description="whether the node belongs to the original text or a translation",
        format="1 (=Latin translation) or absent (=Pali original)",
    ),
)


BASE = os.path.expanduser("~/github")
ORG = "etcbc"
REPO = "dhammapada"
REPO_DIR = f"{BASE}/{ORG}/{REPO}"
SOURCE_DIR = f"{REPO_DIR}/sources"
TF_DIR = f"{REPO_DIR}/tf/{VERSION}"

PALI = "pali"
LATIN = "latin"

SOURCES = (PALI, LATIN)

ROMAN_SPEC = """
I
II
III
IV
V
VI
VII
VIII
IX
X
XI
XII
XIII
XIV
XV
XVI
XVII
XVIII
XIX
XX
XXI
XXII
XXIII
XXIV
XXV
XXVI
XXVII
XXVIII
XXIX
XXX
""".strip().split()

ROMAN = {r: i + 1 for (i, r) in enumerate(ROMAN_SPEC)}

CHANGE_STANZA = {"143a": "143"}
APPEND_STANZA = {"143b"}

PRE = "pre"
POST = "post"
AFFIX_KIND = (PRE, POST)


class Converter:
    def __init__(self):
        self.letters = {src: collections.Counter() for src in SOURCES}
        self.text = {src: [] for src in SOURCES}
        self.offset = {src: 0 for src in SOURCES}
        self.affixes = {
            src: {kind: collections.Counter() for kind in AFFIX_KIND} for src in SOURCES
        }
        self.tokens = {src: [] for src in SOURCES}
        self.chunks = {src: {} for src in SOURCES}
        self.read()

    def msg(self, msg):
        cur = self.cur
        print(f"{cur['line']:>4}: {msg}")

    def read(self, src=None):
        if src is None:
            for s in SOURCES:
                self.read(s)
            return

        print(f"READING {src}")
        letters = self.letters[src]
        letters.clear()
        text = self.text[src]
        text.clear()
        offsets = self.offset
        offsets[src] = 0
        inPali = src == PALI

        spaceRe = re.compile(r"([.,:;!?”])([^.,:;!?” ])")

        def spaceRepl(match):
            return f"{match.group(1)} {match.group(2)}"

        with open(f"{SOURCE_DIR}/{src}.txt") as f:
            inFront = True
            for line in f:
                if inFront:
                    offsets[src] += 1
                    if line.startswith("----------"):
                        inFront = False
                else:
                    material = line.rstrip("\n").replace("—", "-")
                    material = spaceRe.sub(spaceRepl, material)
                    for c in material:
                        letters[c] += 1
                    if inPali:
                        stanza = material[0:4]
                        chStanza = CHANGE_STANZA.get(stanza, None)
                        if chStanza is not None:
                            print(f"Change stanza {stanza} to {chStanza}")
                            material = chStanza + material[4:]
                        else:
                            if stanza in APPEND_STANZA:
                                print(f"Append stanza {stanza} to previous stanza")
                                if text[-1] == "":
                                    text.pop()
                                else:
                                    print("No previous empty line!")
                                material = material[5:]
                    text.append(material)
        print(f"{src:<5}: {len(text):>4} lines")

    def tokenize(self, src=None):
        if src is None:
            for s in SOURCES:
                self.tokenize(s)
            return

        print(f"TOKENIZING {src}")
        isPali = src == PALI

        text = self.text[src]
        offset = self.offset[src]

        tokens = self.tokens[src]
        tokens.clear()

        affixes = self.affixes[src]
        for kind in AFFIX_KIND:
            affixes[kind].clear()

        cur = dict(
            line=offset,
            vagga=0,
            stanza=0,
            sentence=1,
            clause=1,
            quote=False,
            uncertain=False,
            clarity=False,
        )
        self.cur = cur

        vaggaRe = re.compile(r"^([0-9]+)\s*\.\s*(.*)$" if isPali else r"^([IVX]+)$")

        stanzaNumPat = "[0-9]+"
        stanzaRe = re.compile(fr"^({stanzaNumPat})\s+(.*)$")

        wordPat = r"\w'*-" if isPali else r"\w-"
        wordRe = re.compile(fr"^([^{wordPat}]*)([{wordPat}]+)([^{wordPat}]*)$")

        bracketRe = re.compile(r"^([^()]*)(\([^()]*\))(.*)$")
        hasLetterRe = re.compile(r"\w")

        vaggaHead = False
        inStanza = False
        vaggaTail = False
        firstStanza = False

        for (i, line) in enumerate(text):
            cur["line"] += 1
            material = ""
            good = True
            vaggaNum = False
            stanzaNum = False

            for _ in [1]:
                match = vaggaRe.match(line)
                if match:
                    num = match.group(1)
                    n = int(num) if isPali else ROMAN[num]
                    material = match.group(2) if isPali else ""
                    exp = cur["vagga"] + 1
                    if n != exp:
                        self.msg(f"ERROR: vagga number {n} unexpected at {exp}")
                        good = False
                        break
                    cur["vagga"] = n
                    cur["sentence"] = 0
                    cur["clause"] = 0
                    vaggaNum = True
                    firstStanza = True
                    continue

                match = stanzaRe.match(line)
                if match:
                    n = int(match.group(1))
                    material = match.group(2)
                    expNum = cur["stanza"] + 1
                    if n != expNum:
                        self.msg(
                            f"ERROR: unexpected stanza number {n} instead of {expNum}"
                        )
                        good = False
                        break

                    cur["stanza"] = n
                    if firstStanza:
                        cur["sentence"] = 1
                        cur["clause"] = 1
                    stanzaNum = True
                    firstStanza = False
                    continue

                material = line

            if not good:
                break

            material = material.strip()
            if vaggaNum:
                if vaggaHead:
                    self.msg(f"Vagga {cur['vagga']} starts inside a vagga head")
                    good = False
                elif vaggaTail:
                    pass
                elif inStanza:
                    self.msg(
                        f"Vagga {cur['vagga']} starts inside stanza {cur['stanza']}"
                    )
                    good = False
                else:
                    pass
                vaggaHead = True
                inStanza = False
                vaggaTail = False
            elif stanzaNum:
                if vaggaHead:
                    pass
                elif vaggaTail:
                    self.msg(f"Stanza {cur['stanza']} starts inside a vagga tail")
                    good = False
                    pass
                elif inStanza:
                    if isPali:
                        self.msg(f"Stanza {cur['stanza']} starts inside another stanza")
                        good = False
                else:
                    pass
                vaggaHead = False
                inStanza = True
                vaggaTail = False
            else:
                if vaggaHead:
                    if material:
                        pass
                    else:
                        pass
                elif vaggaTail:
                    if material:
                        self.msg(f"vagga tail continued: {' ' * 20}{material}")
                    else:
                        pass
                elif inStanza:
                    if material:
                        pass
                    else:
                        inStanza = False
                else:
                    if material:
                        # we do a look ahead: if a stanza is following
                        # this is not a vagga tail but inter stanza material
                        # and we heap it on the current stanza

                        nx = i + 2
                        if nx < len(text):
                            match = stanzaRe.match(text[nx])
                            if match:
                                n = int(match.group(1))
                                self.msg(
                                    f"Inter-stanza in vagga {cur['vagga']:>2}"
                                    " between stanzas "
                                    f"{cur['stanza']:>3} and {n:>3}: {material}"
                                )
                                inStanza = True

                        if not inStanza:
                            self.msg(
                                f"Vagga tail after vagga {cur['vagga']:>2} and stanza "
                                f"{cur['stanza']:>3}: {material}"
                            )
                            vaggaTail = True
                    else:
                        pass

            if material:
                rawWords = material.split()
                words = []
                for rawWord in rawWords:
                    remaining = rawWord
                    while True:
                        match = bracketRe.match(remaining)
                        if match:
                            preBracket = match.group(1)
                            bracketed = match.group(2)
                            postBracket = match.group(3)
                            realPre = hasLetterRe.search(preBracket)
                            realPost = hasLetterRe.search(postBracket)
                            if not realPost:
                                if realPre:
                                    words.append([preBracket, False])
                                    words.append([bracketed + postBracket, False])
                                else:
                                    words.append([preBracket + bracketed + postBracket, False])
                                break
                            else:
                                if realPre:
                                    words.append([preBracket, False])
                                    words.append([bracketed, False])
                                else:
                                    words.append([preBracket + bracketed, False])
                                remaining = postBracket
                        else:
                            if remaining:
                                words.append([remaining, False])
                            break
                    words[-1][-1] = True

                for (word, addSpace) in words:
                    match = wordRe.match(word)
                    if not match:
                        self.msg(f"Strange word: │{word}│")
                        good = False
                        break

                    preWord = match.group(1)
                    word = match.group(2)
                    postWord = match.group(3)
                    if addSpace:
                        postWord += " "

                    if word == "-":
                        tokens[-1][-1] += " - "
                        affixes[POST][tokens[-1][-1]] += 1
                        continue

                    if word == "":
                        self.msg(f"Empty word: {preWord}||{postWord}")
                        good = False
                        break

                    affixes[PRE][preWord] += 1
                    affixes[POST][postWord] += 1

                    if '"' in preWord:
                        cur["quote"] = not cur["quote"]
                    if "“" in preWord:
                        cur["quote"] = True
                        preWord = preWord.replace("“", '"')
                    elif "”" in preWord:
                        cur["quote"] = False
                        preWord = preWord.replace("”", '"')
                    if "[" in preWord:
                        cur["uncertain"] = True
                    elif "]" in preWord:
                        cur["uncertain"] = False
                    if "(" in preWord:
                        cur["clarity"] = True
                    elif ")" in preWord:
                        cur["clarity"] = False

                    status = "±" if inStanza else "^" if vaggaHead else "$"
                    tokens.append(
                        [
                            cur["line"],
                            cur["vagga"],
                            cur["stanza"],
                            status,
                            cur["sentence"],
                            cur["clause"],
                            cur["quote"],
                            cur["uncertain"],
                            cur["clarity"],
                            preWord,
                            word,
                            postWord,
                        ]
                    )

                    if "[" in postWord:
                        cur["uncertain"] = True
                    elif "]" in postWord:
                        cur["uncertain"] = False
                    if "(" in postWord:
                        cur["clarity"] = True
                    elif ")" in postWord:
                        cur["clarity"] = False
                    if '"' in postWord:
                        cur["quote"] = not cur["quote"]
                    if "“" in postWord:
                        cur["quote"] = True
                        postWord = postWord.replace("“", '"')
                    elif "”" in postWord:
                        cur["quote"] = False
                        postWord = postWord.replace("”", '"')
                    if (
                        "," in postWord
                        or ";" in postWord
                        or ":" in postWord
                        or "-" in postWord
                    ):
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

    def chunkify(self, src=None):
        if src is None:
            for s in SOURCES:
                self.chunkify(s)
            return
        print(f"CHUNKIFYING {src}")

        tokens = self.tokens[src]

        chunks = self.chunks[src]
        chunks.clear()

        for (
            line,
            vagga,
            stanza,
            status,
            sentence,
            clause,
            quote,
            uncertain,
            clarity,
            preWord,
            word,
            postWord,
        ) in tokens:
            stanzaRep = stanza
            if status == "^":
                stanzaRep = stanza + 1001
                sentence = 0
                clause = 0
            elif status == "$":
                stanzaRep = stanza + 1000
            chunks.setdefault(vagga, {}).setdefault(stanzaRep, {}).setdefault(
                sentence, {}
            ).setdefault(clause, []).append(
                (line, quote, uncertain, clarity, preWord, word, postWord)
            )

    def showLetters(self, src=None):
        if src is None:
            for s in SOURCES:
                self.showLetters(s)
            return

        print(f"LETTERS OF {src}")
        theseLetters = self.letters[src]
        for (c, f) in sorted(theseLetters.items(), key=lambda x: (-x[1], x[0])):
            print(f"│{c}│ : {f:>7} x")
        print("".join(sorted(theseLetters)))

    def showAffixes(self, src=None):
        if src is None:
            for s in SOURCES:
                self.showAffixes(s)
            return

        print(f"AFFIXES OF {src}")
        affixes = self.affixes[src]

        for (kind, theseAffixes) in sorted(affixes.items()):
            kindRepE = "〉" if kind == PRE else "│"
            kindRepB = "〈" if kind == POST else "│"
            for (c, f) in sorted(theseAffixes.items(), key=lambda x: (-x[1], x[0])):
                rep = f"{kindRepB}{c}{kindRepE}"
                print(f"{rep:<4} : {f:>7} x")

    def showText(self, src=None, start=None, end=None, logical=True):
        if src is None:
            for s in SOURCES:
                self.showText(s, start=start, end=end, logical=logical)
            return

        print(f"TEXT OF {src}")
        text = self.text[src]
        offset = self.offset[src]
        numOffset = offset if logical else 0

        b = 0 if start is None else max((start - 1, 0))
        e = len(text) if end is None else min(end, len(text))
        if not logical:
            b = max((0, b - offset))
            e = min((len(text), e - offset))

        for ln in range(b, e):
            line = "\n".join(wrap(text[ln], width=80, subsequent_indent=" " * 6))
            print(f"{ln + 1 + numOffset:>4}: {line}")

    def showTokens(self, src=None, vagga=None, stanza=None):
        if src is None:
            for s in SOURCES:
                self.showTokens(s, vagga=vagga, stanza=stanza)
            return

        print(f"TOKENS OF {src}")
        tokens = self.tokens[src]
        for (
            line,
            vg,
            st,
            status,
            sentence,
            clause,
            quote,
            uncertain,
            clarity,
            pre,
            word,
            post,
        ) in tokens:
            if vagga is not None and vagga != vg:
                continue
            if stanza is not None and stanza != st:
                continue
            q = '"' if quote else ""
            u = "~" if uncertain else ""
            c = "!" if clarity else ""
            preRep = f"{pre:>3}│"
            postRep = f"│{post:<3}"
            print(
                f"{status}ln{line:>4}:v{vg:>2}:s{st:>3}:"
                f"{sentence:>2},{clause:>2} │{q:<1}{u:<1}{c:<1}│"
                f" {preRep}{word:<20}{postRep}"
            )

    def showChunks(self, src=None, vagga=None, stanza=None):
        if src is None:
            for s in SOURCES:
                self.showChunks(s, vagga=vagga, stanza=stanza)
            return

        print(f"LETTERS OF {src}")
        chunks = self.chunks[src]
        for (vg, stanzaData) in chunks.items():
            if vagga is not None and vagga != vg:
                continue
            if stanza is not None and stanza not in stanzaData:
                continue
            print(f"Vagga {vg}")
            for (st, sentenceData) in stanzaData.items():
                if stanza is not None and stanza != st:
                    continue
                print(f"\t{st}")
                for (sentence, clauseData) in sentenceData.items():
                    print(f"\t\tsentence {sentence}")
                    for (clause, wordData) in clauseData.items():
                        print(f"\t\t\tclause {clause}")
                        for (
                            line,
                            quote,
                            uncertain,
                            clarity,
                            pre,
                            word,
                            post,
                        ) in wordData:
                            q = '"' if quote else ""
                            u = "~" if uncertain else ""
                            c = "!" if clarity else ""
                            preRep = f"{pre:>3}│"
                            postRep = f"│{post:<3}"
                            print(
                                f"\t\t\t\t│{q:<1}{u:<1}{c:<1}│"
                                f" {preRep}{word:<20}{postRep}"
                            )

    def makeTf(self):
        chunks = self.chunks
        cv = CV(Fabric(locations=TF_DIR))

        def director(cv):
            SENTENCE = "sentence"
            CLAUSE = "clause"
            NTYPES = (SENTENCE, CLAUSE)

            for (vagga, stanzaData) in chunks[PALI].items():
                vaggaNode = cv.node("vagga")
                cv.feature(vaggaNode, n=vagga)
                pending = {src: {nType: None for nType in NTYPES} for src in SOURCES}
                last = {src: {nType: None for nType in NTYPES} for src in SOURCES}

                sentenceData = {}

                for (stanza, sentenceDataPali) in stanzaData.items():
                    extrastanza = 1 if stanza >= 1000 else None
                    sentenceDataLatin = (
                        {} if extrastanza else chunks[LATIN][vagga][stanza]
                    )

                    stanzaNode = cv.node("stanza")
                    cv.feature(stanzaNode, n=stanza)

                    sentenceDataAll = {PALI: sentenceDataPali, LATIN: sentenceDataLatin}

                    for (src, sentenceData) in sentenceDataAll.items():
                        trans = None if src == PALI else 1

                        myPending = pending[src]
                        myLast = last[src]

                        for (nType, node) in myPending.items():
                            if node:
                                cv.resume(node)

                        for (sentence, clauseData) in sentenceData.items():
                            sentenceNode = myPending[SENTENCE]
                            if myLast[SENTENCE] != sentence:
                                clauseNode = myPending[CLAUSE]
                                if clauseNode:
                                    cv.terminate(clauseNode)
                                    myPending[CLAUSE] = None
                                if sentenceNode:
                                    cv.terminate(sentenceNode)
                                sentenceNode = cv.node("sentence")
                                myPending[SENTENCE] = sentenceNode
                                cv.feature(sentenceNode, n=sentence, trans=trans)
                                myLast[CLAUSE] = None

                            for (clause, wordData) in clauseData.items():
                                clauseNode = myPending[CLAUSE]
                                if myLast[CLAUSE] != clause:
                                    if clauseNode:
                                        cv.terminate(clauseNode)
                                    clauseNode = cv.node("clause")
                                    myPending[CLAUSE] = clauseNode
                                    cv.feature(clauseNode, n=clause, trans=trans)

                                for (
                                    line,
                                    quote,
                                    uncertain,
                                    clarity,
                                    pre,
                                    word,
                                    post,
                                ) in wordData:
                                    wordNode = cv.slot()
                                    cv.feature(
                                        wordNode,
                                        trans=trans,
                                        extrastanza=extrastanza,
                                        quote=1 if quote else None,
                                        uncertain=1 if uncertain else None,
                                        clarity=1 if clarity else None,
                                    )
                                    wordFeatures = (
                                        dict(
                                            latinpre=pre,
                                            latin=word,
                                            latinpost=post,
                                        )
                                        if trans
                                        else dict(
                                            palipre=pre,
                                            pali=word,
                                            palipost=post,
                                        )
                                    )
                                    cv.feature(wordNode, **wordFeatures)

                                myLast[CLAUSE] = clause

                            myLast[SENTENCE] = sentence

                        for nType in NTYPES:
                            myPending[nType] = None
                        for n in cv.activeNodes(nTypes=NTYPES):
                            myPending[n[0]] = n
                            cv.terminate(n)

                    cv.terminate(stanzaNode)

                for (src, nTypeData) in pending.items():
                    for (nType, n) in nTypeData.items():
                        if n:
                            cv.terminate(n)
                cv.terminate(vaggaNode)

        return cv.walk(
            director,
            SLOT_TYPE,
            otext=OTEXT,
            generic=GENERIC,
            intFeatures=INT_FEATURES,
            featureMeta=FEATURE_META,
            generateTf=True,
        )

    def loadTf(self):
        TF = Fabric(locations=TF_DIR)
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        api = TF.load(loadableFeatures, silent=False)
        if api:
            print(f"max node = {api.F.otype.maxNode}")
            print("Frequencies of words")
            for (word, n) in api.F.pali.freqList()[0:20]:
                print(f"{n:>6} x {word}")

    def interLinking(self):
        pass
