"""Validation of a single translation against its source unit."""
import re, collections
VAR = re.compile(r"=[A-Za-z_.@]+\.join:[^=]{0,12}=|=[A-Za-z_^@][^=\n]{0,200}?=")
DROPPABLE = re.compile(r"^=([A-Za-z_.]*verb:[^=]*|[A-Za-z_.]*\.[Dd]oes:[^=]*|[A-Za-z_.]*\.[Dd]oesly:[^=]*|[a-z]+\.s|s|[a-z]+\.es|[a-z]+\.isPlural[^=]*)=$", re.I)
VERBTOK = re.compile(r"^=(?:[A-Za-z_.]*\.)?(?:verb|[Dd]oes|[Dd]id|[Dd]oesly)(?::[^:=]*)?:([^:=]+)(?::[^=]*)?=$")
def head(v):
    """Compare variables by name only; parameters after ':' may be localized (verbs, counted nouns)."""
    return v.split(":", 1)[0].rstrip("=") + "=" if ":" in v else v
STAR = re.compile(r"\*(?:[a-z]+[A-Z][A-Za-z]*|material|creature(?:\.a)?)\*")
COLOR_OPEN = re.compile(r"\{\{[^|{}]*\|")
LINK = re.compile(r"\[\[[^\]]*\]\]")
AMP = re.compile(r"&[A-Za-z]|\^[A-Za-z]")
CJK = re.compile(r"[㐀-鿿]")
LATIN_WORD = re.compile(r"[A-Za-z]{4,}")
ALLOW_WORDS = {"harmony","vsync","steam","ascii","unity","debug","mod","mods","gog","xbox","playstation","nintendo","windows","mac","linux","discord","patreon","twitter","freehold","games","caves","qud","utf","xml","json","png","api","rgb","fps","exe","dll","csharp","url","http","https","www","com","dpi","ok","lol","pda","shift","alt","ctrl","tab","esc","enter","space","backspace","switch","xml","txt","cs","local","session","support","freeholdgames"}
LIST_ATTRS = {"PoeticFeatures","Activity","VillageActivity","GuestActivity","NeedsItemFor","SacredThing","ArableLand","ValuedOre","Skin","YounglingNoise"}
ALLOW_WORDS.update({"sav", "bak", "using"})  # save filename extensions; C# keyword kept in a C#-facing option help text

XMLTAG = re.compile(r"<[^>]+>")
def strip_tokens(s):
    if s == "*delete": return " "  # XML overlay deletion directive, not prose
    s = XMLTAG.sub(" ", s)
    s = STAR.sub(" ", s)
    s = re.sub(r"[\w.<>/-]+\.(xml|json|txt|cs|dll|png|log)\b", " ", s)
    s = VAR.sub(" ", s); s = COLOR_OPEN.sub(" ", s); s = LINK.sub(" ", s)
    return s

def check(u, zh):
    src = u["src"]; E = []; W = []
    if zh is None: return ["missing"], W
    if not isinstance(zh, str): return ["not a string"], W
    if "▶" in XMLTAG.sub("", zh): E.append("contains ▶")
    if src.strip() and not zh.strip(): E.append("empty translation")
    sv = collections.Counter(head(v) for v in VAR.findall(src) if not DROPPABLE.match(v))
    zv = collections.Counter(head(v) for v in VAR.findall(zh))
    if CJK.search(zh):
        for v in VAR.findall(zh):
            m = VERBTOK.match(v)
            if m and re.fullmatch(r"[A-Za-z' -]+", m.group(1)):
                E.append(f"verb token {v} keeps an English verb: write the Chinese verb as its parameter (e.g. =subject.Does:滑倒=) or remove the token")
    for v, c in sv.items():
        if zv[v] < c: E.append(f"variable {v} missing ({zv[v]}/{c})")
    for v in zv:
        if v not in sv and not any(head(x) == v for x in VAR.findall(src)): E.append(f"unknown variable {v} added")
    def _norm_tag(t): return re.sub(r'Unit="[^"]*"', 'Unit="*"', t.replace("\u25b6", ""))
    for name, rx in (("color-open", COLOR_OPEN), ("amp-color", AMP), ("*placeholder*", STAR), ("xml-tag", XMLTAG)):
        a = collections.Counter(rx.findall(src)); b = collections.Counter(rx.findall(zh))
        if name == "xml-tag" and u.get("attr") != "#inner": continue
        if name == "xml-tag":
            a = collections.Counter(_norm_tag(t) for t in a.elements()); b = collections.Counter(_norm_tag(t) for t in b.elements())
        if a != b: E.append(f"{name} mismatch: {dict(a)} vs {dict(b)}")
    if src.count("}}") != zh.count("}}"): E.append("'}}' count mismatch")
    if src.count("[[") != zh.count("[[") or src.count("]]") != zh.count("]]"): E.append("'[[ ]]' header count mismatch")
    s_out, z_out = VAR.sub(" ", src), VAR.sub(" ", zh)
    for sep in ("~", "|", "::"):
        if s_out.count(sep) != z_out.count(sep): E.append(f"separator {sep!r} count {s_out.count(sep)}->{z_out.count(sep)}")
    if u.get("attr") in LIST_ATTRS and src.count(",") != zh.count(","):
        E.append(f"comma-list item count {src.count(',')+1}->{zh.count(',')+1} (use ASCII ',')")
    if src.startswith(" ") and not zh.startswith(" "): W.append("leading space dropped")
    sn, zn = src.count("\n"), zh.count("\n")
    if sn != zn and (sn < 3 or abs(sn - zn) > max(2, sn * 0.3)): W.append(f"newline count {sn}->{zn}")
    rest = strip_tokens(src)
    if LATIN_WORD.search(rest) and not CJK.search(zh) and src.strip() != zh.strip():
        W.append("no Chinese in output")
    if src.strip() == zh.strip() and LATIN_WORD.search(rest) and not u.get("copy"):
        W.append("identical to source (untranslated?)")
    zl = [w for w in LATIN_WORD.findall(strip_tokens(zh)) if w not in rest]
    if zl: W.append(f"latin words introduced: {zl[:5]}")
    # English words copied from the source into a Chinese output = untranslated fragment
    if not u.get("copy"):
        zrest = re.sub(r"~(?:Take A Step|Use Ability|Page Left|Page Right|[A-Za-z][\w:/]*)", " ", strip_tokens(zh))  # keybind tokens like ~CmdAbilities are not prose
        left = [w for w in re.findall(r"[A-Za-z][a-z]{2,}", zrest) if w.lower() not in ALLOW_WORDS and re.search(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])", rest)]
        if left and (CJK.search(zh) or len(left) >= 1 and LATIN_WORD.search(rest) and src.strip() == zh.strip()):
            E.append(f"untranslated English left in output: {left[:6]} (translate it; only markup/variables/acronyms may stay)")
    return E, W
