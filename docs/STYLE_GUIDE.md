# 《卡德洞窟》简体中文译文风格指南 (STYLE GUIDE v1)

All translators (human or AI) MUST follow this guide. When the guide and the glossary disagree, the glossary (`docs/glossary.tsv`) wins.

## 0. The game in one paragraph
Caves of Qud is a far-future, post-apocalyptic "science fantasy" set in Qud, a salt-baked land of ruined arcologies, mutated beasts, sentient plants, and the half-remembered relics of the ancient Eaters and the Sultans of the Resheph sultanate. Its English is deliberately **ornate, archaic, and literary**: biblical cadence (Joppa, Golgotha, Bethesda, Nephilim), Semitic/Arabic/Persian/Yiddish names, Middle-English pastiche in poems, mock-scripture of the Mechanimist church, terse sci-fi technobabble on robots and computer terminals, and a dry, darkly comic narrator voice. Rare words (e.g. "hispid", "spheric", "tessellated", "puissant", "vittle", "meyvn", "gravens") are chosen on purpose. **Our Chinese must preserve that strangeness and dignity** — never flatten it into casual internet Chinese.

## 1. Register (语体) — by text type
| Text type | Register | Notes |
|---|---|---|
| UI, options, menus, keybinds, tutorial, status messages | 简洁现代书面语 | Short, clear, consistent. No classical flourishes. e.g. "Frame rate" → "帧率". |
| Item / creature / terrain descriptions (`Short`) | **典雅书面语，半文半白** | 四字格、对仗 welcome; 之/其/乃/亦/矣/焉 used sparingly and correctly. Keep the dry wit. Never 网络用语. |
| Dialogue (Conversations) | Match the speaker | Villagers: 朴素口语 with a rustic flavor. Barathrum, Mechanimist priests, sages: 文雅、带古意. Robots/terminals: 机械冷硬. Merchants: 市井. Children: 稚拙. |
| Lore, books, gospels, hagiographs, sultan history, quest accomplishments | **史传体 / 经文体** | Sultan gospels & accomplishments: like《史记》/《左传》narration (e.g. "某年，苏丹某某……"). Mechanimist scripture: 仿和合本圣经 cadence ("凡……的，必……"). |
| Poems / Middle-English pastiche (e.g. *Song of the Sky-Bear*) | 仿古诗、乐府、骈文 | Render archaic English as archaic Chinese (古体诗/歌行). Rhyme is welcome but meaning first. |
| Combat / log messages | 简洁、动作明确 | e.g. "=subject.T= =verb:stare= at =object.t= blankly." → "=subject.T=茫然地盯着=object.t=。" |

Golden rule: **雅而不涩，古而不僻** — classical-flavored but readable by a modern player. Prefer common characters; avoid obscure 生僻字 unless the English itself is obscure.

## 2. Rare / archaic English words
Translate the *meaning* with an equivalently elevated Chinese word, not a plain one.
- "hispid skin" → 刚毛覆体 / 糙毛之皮 (not 毛皮)
- "puissant" → 雄强 / 威烈
- "vittle" → 口粮 / 吃食
- "gravens" (face grows grave) → 神色凝重
- "lond / dide / swich" (Middle English) → 古体诗用字
If you are unsure of a word, infer from context — **never leave English words untranslated** except for markup, variables, and the cases in §5.

## 3. Markup and variables — MUST be preserved byte-for-byte
- **Game variables** `=...=` : keep exactly, e.g. `=subject.T=`, `=object.t=`, `=pronouns.possessive=`, `=player.formalAddressTerm=`, `=name=`, `=turns.things:turn=`, `=boost=`. Never translate or alter what is inside `= =`. You may reorder them in the sentence.
  - VERB TOKENS — `=verb:xxx=`, `=subject.verb:xxx=`, `=subject.Does:xxx=`, `=subject.does:xxx=`, `=subject.it.does:xxx=`, `=target.Does:xxx=` etc. In English they output a conjugated verb (Does = "The snapjaw slips"; it.does = "it slips"). In Chinese, **write the Chinese verb as the token's parameter**, keeping everything before the colon: `=subject.Does:slip= on the gel!` → `=subject.Does:滑倒=在凝胶上！` (renders 豺颚人滑倒在凝胶上！); `=subject.it.does:reflect= 100% damage` → `=subject.it.does:反射=100%伤害`; `whenever =subject.thisCreature= =subject.verb:gain= a follower` → `每当=subject.thisCreature==subject.verb:获得=新随从时`. Alternatively, for plain `=verb:x=` after a subject token you may delete the token and write the verb directly: `=subject.T= =verb:growl= softly.` → `=subject.T=低声咆哮。` An English verb left as the parameter in a Chinese line is an ERROR.
  - COUNTED NOUNS — `=amount.things:dram=`, `=turns.things:turn=`, `=x.pluralize:...=`: translate the noun parameter: `=amount.things:打兰=` (renders "3 打兰"). Keep the part before the colon.
  - Spacing: remove the spaces English puts around variables when they sit between Chinese characters. `=subject.T= =verb:are= stunned!` → `=subject.T=晕眩了！`
- **Color/markup** `{{X|text}}` : keep the `{{X|` and `}}` exactly, translate only the text inside. Nested markup the same. `&&`, `&y`, `^k` style color codes: keep exactly.
- `{{emote|*...*}}` : keep asterisks: `{{emote|*soft growling*}}` → `{{emote|*低沉的咆哮*}}`.
- `[[A.]]` style book hyperlinks: keep exactly.
- `&#xA;` / real newlines: keep the same line structure (same number of line breaks in the same logical places). Poems: keep line count when feasible.
- Leading/trailing spaces in a source string usually matter (e.g. `" [=turns.things:turn=]"`) — keep a leading space if the source has one.
- Placeholders like `%s`, `{0}`, `<...>` tags, `\n`: keep exactly.

## 4. Punctuation & typography
- Use full-width Chinese punctuation in prose: ，。！？：；“”‘’（）——……、
- English "..." → "……"; "—" or "--" → "——".
- Quotes inside text → “ ” (outer) and ‘ ’ (inner).
- No space between Chinese and Chinese. A space between Chinese and Latin letters/digits is NOT required; omit it.
- Numbers stay as Arabic digits.
- Keep `*emphasis*` asterisks if they are markup (emotes); otherwise convert emphasis to plain text.
- Structural separators MUST stay ASCII and in the same count: `~` (random alternatives), `,` in comma lists (xtagTextFragments like PoeticFeatures, Activity, SacredThing — each comma-separated item is used alone in generated sentences), `|`, `::`.
  - So `shiny teeth,coarse hair,sunken eyes` → `皓齿,粗发,凹目` (ASCII commas, same item count).

## 5. Proper nouns
- Use `docs/glossary.tsv` for every name it covers. Consistency beats elegance.
- New names: transliterate following 新华社译名 conventions **but**:
  - Biblical/Semitic names use the **和合本 (Chinese Union Version)** form when one exists: Joppa→约帕, Golgotha→各各他, Bethesda→毕士大, Nephilim→拿非利人, Ezra→以斯拉, Hinnom→欣嫩, Bethsaida→伯赛大, Issachar→以萨迦, Naphtali→拿弗他利, Resheph→利悉.
  - Keep transliterations short (≤4 characters when possible), avoid characters with comic or vulgar connotations.
  - Descriptive names are translated by meaning: "Grit Gate"→砂砾门, "Red Rock"→红岩, "Six Day Stilt"→六日高塔.
- Creature names: translate meaningfully when English is descriptive ("snapjaw"→豺颚人, "glowfish"→荧光鱼); transliterate invented words.
- Items: noun-final Chinese order. Material/adjective + noun: "bronze dagger"→青铜匕首.
- Do NOT add articles (a/an/the) — Chinese has none. "the" in proper names is dropped: "The Tomb of the Eaters"→食者之墓.

## 6. Grammar variables & articles in Chinese
- `=subject.T=` / `=subject.t=` / `=object.the=` etc. render a creature/item name (the engine handles it). Write the Chinese sentence around them; do not add 这个/那个 unless needed.
- Pronouns: the engine may insert `=pronouns.subjective=` etc. Keep them. Don't add extra 他/她.
- Plural markers (`=x.s=`, `=s=`) are meaningless in Chinese: if the token exists only to pluralize an English word, delete it.
- Players are addressed as 你 (not 您) in game messages; NPC speech may use 您 for formal/reverent address when the English is formal ("=player.formalAddressTerm=").

## 7. Tone examples
- "Moon and Sun. Wisdom and will." → "月与日。智与志。"
- "Live and drink." → "且生且饮。"
- "May the earth yield for us this season." → "愿此季大地为我等丰饶。"
- "Peace, =player.formalAddressTerm=." → "愿你平安，=player.formalAddressTerm=。"
- "The battle axe has better penetration and deals more damage than your dagger." → "战斧的穿透力比你的匕首更强，造成的伤害也更高。" (UI/tutorial: plain modern)
- "{{emote|*Barathrum's countenance suddenly gravens.*}}" → "{{emote|*巴拉斯鲁姆的神色骤然凝重。*}}"
- "I am a puppet of my shame." → "我不过是自身羞愧的傀儡。"

## 8. Output discipline
- One translation per unit id. Never merge or split units.
- Never translate content of `ID` keys; only the `src` given.
- If `src` is pure markup/number/symbol (e.g. "10", "VSync", "{{K|-}}"), return it unchanged or minimally localized ("Unlimited"→"无限制").
- No translator notes inside the translation text.
