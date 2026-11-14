"""Build-time normalisation of English-only grammar tokens inside Chinese translations."""
import re
CJK = re.compile(r"[㐀-鿿]")
def _it_is(m):
    tgt, cap, p = m.group(1), m.group(2), m.group(3) or ""
    return f"={tgt}.{'Subjective' if cap == 'I' else 'subjective'}=" + p
def zh_post(s):
    if not s or not CJK.search(s): return s
    # =X.it.is= / =X.It.is:P=  -> pronoun + P
    s = re.sub(r"=([A-Za-z_]+)\.(I|i)t\.is(?::([^=]*))?=", _it_is, s)
    # =X.is= / =X.is:P= -> P
    s = re.sub(r"=[A-Za-z_]+\.(?:is|are)(?::([^=]*))?=", lambda m: m.group(1) or "", s)
    # parameterless =X.Does= / =X.does= -> name
    s = re.sub(r"=([A-Za-z_]+)\.Does=", r"=\1.T=", s)
    s = re.sub(r"=([A-Za-z_]+)\.does=", r"=\1.t=", s)
    return s
if __name__ == "__main__":
    for t in ["=subject.T==subject.is:未通电=。", "=object.it.is=被冻住了", "=subject.It.is:很=饿", "=campfire.is=熄灭了", "=subject.Does=什么也没做"]:
        print(t, "->", zh_post(t))
