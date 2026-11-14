"""Deterministic English-syllable -> Chinese transliteration (新华译音表-inspired), for name-generator syllables."""
import re
V = ["a","e","i","o","u","ai","ao","ei","ou"]
T = {  # onset: chars for vowels a e i o u ai ao ei ou
 "":   "阿埃伊奥乌艾奥埃欧", "b": "巴贝比博布拜鲍贝博", "p": "帕佩皮波普派保佩波",
 "d":  "达德迪多杜代道德道", "t": "塔特蒂托图泰陶特托", "g": "加盖吉戈古盖高盖戈",
 "k":  "卡凯基科库凯考凯科", "f": "法费菲福富法福费福", "v": "瓦维维沃武瓦沃维沃",
 "s":  "萨塞西索苏赛绍塞索", "z": "扎泽齐佐祖扎藻泽佐", "sh": "沙谢希肖舒夏绍谢肖",
 "ch": "查切奇乔丘柴乔切乔", "j": "贾杰吉乔朱贾焦杰乔", "h": "哈赫希霍胡海豪赫霍",
 "m":  "马梅米莫穆迈毛梅莫", "n": "纳内尼诺努奈瑙内诺", "l": "拉莱利洛卢莱劳莱洛",
 "r":  "拉雷里罗鲁赖劳雷罗", "w": "瓦韦威沃乌怀沃韦沃", "y": "亚耶伊约尤亚尧耶约",
 "th": "萨瑟西索苏赛绍瑟索", "ts": "察策齐措楚柴曹策措", "zh": "扎热日若茹扎绕热若",
}
NAS = {  # onset: an en in on un
 "": "安恩因翁温", "b": "班本宾邦本", "p": "潘彭平庞彭", "d": "丹登丁东敦", "t": "坦滕廷通吞",
 "g": "甘根金贡贡", "k": "坎肯金孔昆", "f": "凡芬芬丰丰", "v": "万文文冯文", "s": "桑森辛松孙",
 "z": "赞曾津宗尊", "sh": "尚申欣雄顺", "ch": "钱琴钦琼春", "j": "詹珍金琼君", "h": "汉亨欣洪洪",
 "m": "曼门明蒙蒙", "n": "南嫩宁农农", "l": "兰伦林隆伦", "r": "兰伦林隆伦", "w": "万文温翁温",
 "y": "扬延因永云", "th": "桑森辛松孙", "ts": "灿岑钦聪村", "zh": "然仁任戎润",
}
CODA = {"b":"布","p":"普","d":"德","t":"特","g":"格","k":"克","f":"夫","v":"夫","s":"斯","z":"兹",
 "sh":"什","ch":"奇","j":"吉","h":"","m":"姆","n":"恩","l":"勒","r":"尔","w":"","y":"","th":"斯","ts":"茨","zh":"日","x":"克斯"}
DIGR = ["sh","ch","th","ph","ts","zh","kh","gh","ck","qu","wh"]
def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z]", "", s)
    return s
def tokens(s):
    """split into consonant/vowel tokens with normalization"""
    out = []; i = 0
    while i < len(s):
        two = s[i:i+2]
        if two in DIGR:
            m = {"ph":"f","kh":"k","gh":"g","ck":"k","qu":"kw","wh":"w"}.get(two, two)
            if m == "kw": out += [("C","k"),("C","w")]
            else: out.append(("C", m))
            i += 2; continue
        c = s[i]
        if c in "aeiouy" and not (c == "y" and i+1 < len(s) and s[i+1] in "aeiou"):
            j = i
            while j < len(s) and s[j] in "aeiouy" and not (s[j]=="y" and j+1<len(s) and s[j+1] in "aeiou" and j>i): j += 1
            out.append(("V", s[i:j])); i = j; continue
        m = {"c": "k" if not (i+1 < len(s) and s[i+1] in "eiy") else "s", "q": "k", "x": "x"}.get(c, c)
        out.append(("C", m)); i += 1
    # drop glide w after consonant before vowel (shwu -> shu)
    o2 = []
    for idx, t in enumerate(out):
        if t == ("C","w") and o2 and o2[-1][0]=="C" and idx+1 < len(out) and out[idx+1][0]=="V": continue
        o2.append(t)
    out = o2
    # merge doubled consonants
    res = []
    for t in out:
        if res and t[0]=="C" and res[-1]==t: continue
        res.append(t)
    return res
def vclass(v):
    v = v.replace("y", "i")
    for k, c in (("ai","ai"),("ay","ai"),("au","ao"),("aw","ao"),("ao","ao"),("ei","ei"),("ey","ei"),("ou","ou"),("oo","u"),("ee","i"),("ea","i"),("ie","i"),("oi","o"),("ia","a"),("io","o"),("ua","a"),("ue","u"),("eu","ou")):
        if v.startswith(k): return c, v[len(k):]
    return v[0], v[1:]
def translit(s):
    s = norm(s)
    if not s: return ""
    toks = tokens(s); out = []; i = 0
    while i < len(toks):
        k, x = toks[i]
        if k == "C":
            if i+1 < len(toks) and toks[i+1][0] == "V":
                on = x if x in T else ("k" if x=="x" else x)
                if on not in T: out.append(CODA.get(x, "")); i += 1; continue
                vc, rest = vclass(toks[i+1][1])
                # nasal coda merge
                if vc in ("a","e","i","o","u") and i+2 < len(toks) and toks[i+2] == ("C","n") and not (i+3 < len(toks) and toks[i+3][0]=="V"):
                    out.append(NAS[on]["aeiou".index(vc)]); i += 3
                else:
                    out.append(T[on][V.index(vc)]); i += 2
                # leftover vowels in the cluster
                while rest:
                    vc2, rest = vclass(rest); out.append(T[""][V.index(vc2)])
            else:
                out.append(CODA.get(x, "")); i += 1
        else:
            vc, rest = vclass(x)
            if vc in "aeiou" and len(vc)==1 and i+1 < len(toks) and toks[i+1] == ("C","n") and not (i+2 < len(toks) and toks[i+2][0]=="V"):
                out.append(NAS[""]["aeiou".index(vc)]); i += 2
            else:
                out.append(T[""][V.index(vc)]); i += 1
            while rest:
                vc2, rest = vclass(rest); out.append(T[""][V.index(vc2)])
    r = "".join(out)
    return r or "阿"
if __name__ == "__main__":
    import sys
    for w in sys.argv[1:]: print(w, translit(w))
