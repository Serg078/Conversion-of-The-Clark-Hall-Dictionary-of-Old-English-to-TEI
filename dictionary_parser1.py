"""
Dictionary Entry Parser using Lark
This parser handles dictionary entries with complex grammatical structures one by one, outputs 3 files: entries that failed to parse,
successfully parsed entries (parse trees) and the result of transforming the parse trees into TEI XML. 
"""

from lark import Lark, Transformer, v_args, Tree, Token
from lark.exceptions import ParseError
import sys
import re
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


GRAMMAR = r"""
?start: entry

entry: headword ((preceding_content? main_content) | (etym? (poet_symb | ge_pref)* form* xr_section+)) subsequent_content?

preceding_content: etym? gramgrp? (poet_symb | ge_pref | form )* gramgrp?
main_content: hom_entry+ | sense_section+ | simple_xr
subsequent_content: ((etym | biblref) metamark?)* sb? relatedentry* parenvidexr? editorcomm?

hom_entry: ROM_NUM ( ((preceding_content? (simple_xr | sense_section+))|etym? (poet_symb | ge_pref)* form* xr_section+)|grambiblhom ) subsequent_content?

sb: SUBST (preceding_content? (xr_section+ | sense_section+)) subsequent_content?

relatedentry.4:  ((oneword gramgrp? | collocation| inflect_var (bibl|parenbibl|DOT_SEP)*) parenbibl?  ((poet_symb |  form)* sb | (((poet_symb | form)* xr_section+ | (poet_symb | gramgrp | form)* (simple_xr | sense_section+))) (sb|((etym | biblref) metamark?)*)) | adv_word etym? ) editorcomm?

collocation: COLLOC | DOTSCOLLOC
oneword: ONEWORD 
!adv_word: ", "? "adv. " (" -"? WORD)  (DOT_SEP | sense_section |COMMA? (bibl|parenbibl))*


!headword: ge_pref? WORD VERB_INFL_TYPE? qm? (bibl | parenbibl)? (gramgrp ", ")?

form.4: (inflect_var |( orth_variant)|(inflect_var spell_var) | spell_var | orth_variant  )  (bibl | parenbibl | parenbibl COMMA)? qm? poet_symb?
spell_var: SPELLVAR
!orth_variant: (", "|"-") ge_pref? VARIANT+ spell_var? GEN? COMMA?| LP lbl? ge_pref? VARIANT+ GEN? bibl?  RP
inflect_var.5: LP? COMMA? (lbl? infgramgrp ge_pref? INFVARIANT ((COMMA|SEMICOL_SEP) infgramgrp ge_pref? INFVARIANT)*) RP?

grambiblhom: gramgrp bibl metamark | gramgrp // for cases like "II. adv. Æ."

poet_symb: POET_SYMB
sense_poet_symb: LP POET_SYMB RP | SNS_POET_SYMB
ge_pref: LP? (GE_PREF | GE_OPT) RP?

infgramgrp.12: ((lbl? tense person lbl? person? number lbl? number? lbl? pos?)|(lbl? case gen number)|(lbl? gen case number)|(lbl? case number gen )|(lbl? case gen)|(lbl? case number)|(lbl? tense number?)|(lbl? degree)|(lbl? singlecase))+
gramgrp.10: (lbl? declension tense person number)|(lbl? mood tense number)|(lbl? tense number)+|(lbl? pos tense)+|(lbl? (pos degree)|(degree pos))+|(lbl? nodotgen number)+|(lbl? mood number)+|(lbl? gen)+|(lbl? pos VERB_INFL_TYPE)+ | (lbl? pos)+ |(lbl? number)+|(lbl? tense)+|(lbl? person)+|(lbl? mood)+|(lbl? degree)+|caseofsb|(lbl? declension)+|(lbl? valency)+|(lbl? singlecase)+
gen: GEN
nodotgen: NODOTGEN
pos.3: POS
case: lbl? CASE
singlecase: SINGLECASE
number: NUM
tense: TNS
person: PERS
mood: MOOD
degree: DGR
caseofsb.5: CASE OF POS
declension: DECL
valency.10: VALEN+ parenbibl?
lbl: LBL

simple_xr: usglbl? parenbibl? reflbl (refword | refwords) parenxr? (parenbibl  | biblref | xrsense)? "."?
xr_section.2: ( usglbl? parenbibl?  ((reflbl? gramgrp | reflbl? infgramgrp) OF)  (refword | refwords) parenxr? (parenbibl  | biblref | xrsense)? "."? ) | parenvidexr | equals_variant_xr
reflbl: REFLBL
refword: ge_pref? REFWORD  ("." | homref|gramref| (LP|COMMA) REFWORD )? COMMA? RP?
refwords: ge_pref? REFNUMWORD | PREFSUFXR | ge_pref? REFWORD LBL ge_pref? REFWORD
homref: HOMREF
gramref: GRAMREF
xrsense: cit (metamark | qm | (etym | biblref) metamark?) | oedref
parenvidexr: LP (vide|compare) refword RP
parenxr.6: PARENXR | LP gramgrp OF refword RP
!equals_variant_xr: (REFLBL | "pp., ") ge_pref? VARIANT ((infgramgrp | gramgrp) OF) refword



sense_section: firstsense othersenses*
firstsense: (government | usage |sense_poet_symb |ge_pref |etym)* ( cit (metamark | qm |inflect_var| (etym | (biblref| biblref bibl|parenvidexr)) metamark?) | oedref)
othersenses: (usage| sense_poet_symb |ge_pref| parenbibl| etym |gramgrp|government)* (cit (metamark | qm |inflect_var| (etym | biblref) metamark?) | oedref)

cit: parenxr? quote (gramgrp | orth_variant | parenxr)* (qm? bibl | parenbibl)*
quote: (TRANSLATION def_ref?|usage|gloss|qmsense|government)+
bibl: (poet_symb |ge_pref)* author? (SOURCE | SOURCE_NUM | parenbibl)+  etc? sourcevar? msref?
sourcevar: SRCVAR
msref: MSREF
parenbibl: LP ((poet_symb |ge_pref)* author? (SOURCE|SOURCE_NUM)+  etc? sourcevar? msref?) DOT_SEP? RP COMMA?
oedref: OEDREF
gloss: GLOSS
qmsense: QMSENSE (SOURCE RP COMMA)?
qm: QM (metamark | COMMA)? | lbl QM
usage.7: (LP? ((usglbl gramgrp+)|(usglbl (WORD COMMA?)+ etc?)) RP?) | (LP USGPREP RP COMMA?)
!government: LP? valency? usglbl+ (case ("pers."|"thing")?)+ (lbl valency)? (lbl WORD)? RP? COMMA?
usglbl: USGLBL+
author.5: AUTH
etc: /(etc\.|_etc\._);?/
def_ref: DEFREF

metamark: COLON_SEP | semicolsep | DOT_SEP parenbibl?
semicolsep: SEMICOL_SEP

!etym: "[" ( (vide | compare)? qm? oldengword* (vide | compare)? (oedref |qm | gramgrp)* oldengword* langword* synonym* sqbr_dash_variant* biblref?) "]"
vide: VIDE
compare: COMPARE
langword: LANG (WORD | COMMA WORD)+ SEMICOL_SEP? | LANG SEMICOL_SEP? | lbl LANG
oldengword: WORD ROM_NUM? (bibl|parenbibl)? (COLON_SEP | SEMICOL_SEP)? COMMA?
!biblref: ("(" vide bibl lbl? (oedref|bibl)? ")") | vide bibl
synonym: reflbl SYN qm? parenbibl?
!sqbr_dash_variant: "= " SQBRDASHVAR qm? parenbibl?

editorcomm: EDCOMM

COLON_SEP: /:/
SEMICOL_SEP: /;/
DOT_SEP: /\./
COMMA: /,/
QM: /\?|\(\?\)/
LP:/\(/
RP:/\)/

ROM_NUM: /\s?[IV]{1,4}\./

COLLOC.5: /((?<=\.\s)(?![IV]{1,4}\.)([+±āæÆǣēīōðȳūüA-Za-z\.]+([+±āæÆǣēīōðȳūüA-Za-z\.\)\()]+)?,\s)?[+±āæÆǣēīōðȳūüA-Za-z\.]+([+±āæÆǣēīōðȳūüA-Za-z\.\)\()]+)?(?!\spp\.\s)(\s[+±āæÆǣēīōðȳūüa-z\.]+([+±āæÆǣēīōðȳūüa-z\.\)\()]+)?){1,3}(;\s([+±āæÆǣēīōðȳūüa-z\.]+([+±āæÆǣēīōðȳūüa-z\.\)\()]+)?,\s)?[+±āæÆǣēīōðȳūüa-z\.]+([+±āæÆǣēīōðȳūüa-z\.\)\()]+)?(\s[+±āæÆǣēīōðȳūüa-z\.]+([+±āæÆǣēīōðȳūüa-z\.\)\()]+)?){1,3})*(?!as\ssb\.|[IV]{1,4}\.))|((?<=\.'\s)(?![IV]{1,4}\.|as\ssb\.|[a-z]\.\s[a-z]\.\s)([+±āæÆǣēīōðȳūüa-zA-Z\.]+,\s)?[+±āæÆǣēīōðȳūüa-zA-Z\.]+(\s[+±āæÆǣēīōðȳūüa-zA-Z\.]+){1,2}(?!as\ssb\.|[IV]{1,4}\.))/
DOTSCOLLOC.6: /(([+±āæÆǣēīōðȳūüa-zA-Z\.]+\s)|([+±āæÆǣēīōðȳūüa-zA-Z\]+\([+±āæÆǣēīōðȳūüa-zA-Z\]+\)[+±āæÆǣēīōðȳūüa-zA-Z\.]+\s))?[+±āæÆǣēīōðȳūüa-zA-Z]+\.\.\.[+±āæÆǣēīōðȳūüa-zA-Z]+(?!as\ssb\.|[IV]{1,4}\.)/
ONEWORD: /((?<=\.\s)(?![IV]{1,4}\.|as\ssb\.)[-+±āæÆǣēīōðȳūüa-zA-Z][+±āæÆǣēīōðȳūüa-zA-Z]+)|((?<=\.'\s)(?![IV]{1,4}\.|as\ssb\.)[+±āæÆǣēīōðȳūüa-zA-Z][+±āæÆǣēīōðȳūüa-zA-Z]+)/

WORD: /(?!as\ssb\.|[IV]{1,4}\.)[āäæÐÆǣēīōöðȳūüa-zA-Z\-\*\(\)]+/

POET_SYMB: /[†‡],?(?=\s)|[†‡],?(?=([#_]?[ÆA-Z]))/
SNS_POET_SYMB: /[†‡](?=_)|\([†‡]\)/
GE_PREF: /(?!as\ssb\.|[IV]{1,4}\.)\+/
GE_OPT: /(?!as\ssb\.|[IV]{1,4}\.)±/

SUBST.20: /(?<=(\.\s|:\s|;\s))\(?(used\s)?(as\s)?sb\.\)?\s?=?/


VARIANT: /(?<!\.\s)\??(=\s)?[-*āæǣēīōœ̄ðȳūüa-z]+[)(-āæǣēīōðȳūüa-z]*[-āæǣēīōðȳūüa-z)]+[?,;]?/
INFVARIANT: /(?<=(\.\s|,\s))(=\s)?(?!(?:often|rare|only|in|and|or|also|from|but)\b)[-āæǣēīōœ̄ðȳūüa-z]+[)(-āæǣēīōðȳūüa-z]+[-āæǣēīōðȳūüa-z]+(,\s(?!(pret|pres|sg|pl|sing|imperat|subj|impers)\b)[-āæǣēīōœ̄ðȳūüa-z]+[)(-āæǣēīōðȳūüa-z]+[-āæǣēīōðȳūüa-z]+)*\??/
SPELLVAR: /\s\(((=\s)?(?!(sv\^)\b)[āæǣēīōœ̄ðȳūüa-z-]{1,6}(\^[0-5]{1})?\??)((,|;)\s([āæǣēœ̄īōðȳūüa-z-]{1,4}(\^[0-5]{1})?))*\??\)/

GEN: /\(?[mnf]{1,3}[.?]{1,2}\)?\s?/
NODOTGEN.1:/[mnf]{1,3}/
POS: /\(?(interj\.|interrog\.\sparticle|accented\sverbal\sprefix|subst\.|sv\.|wv\.|\bsv\b|\bwv\b|sb\.|vb\.|anv\.|swv\.|adj\.|adv\.|prep\.|pron\.|ptc\.|pp\.|num\.|conj\.),?\)?\s?/
VERB_INFL_TYPE: /\^[0-9]\)?/
CASE.2:/(?!and|in)([nagdi]{1,2}\.?|[agdi]{1,2}(?!f\.\s|m\.\s))[;,]?\s?/
SINGLECASE: /dat\.|gen\./
NUM:/(sbpl\.|sg\.|sing\.|pl\.|(?<!\s)[sp]\.?)\,?\s?/
TNS:/(pret\.|pres\.),?\s?/
PERS:/[1-3]\.?,?\s?/
MOOD: /(ind\.|imperat\.|subj\.),?\s?/
DGR: /\(?(comp\.|sup\.|superl\.)\)?,?\s?/
DECL.5: /\(?(indecl\.|strong|wk\.)\)? | [sw](?=(f|m|n))/
VALEN: /\(?(tr\.|intr\.|refl\.|pers\.\sand\simpers\.|impers\.|pers\.|tr\.\sintr\.)\)?,?\s?/
OF: /of/
OR: /_or_/
LBL.5: /(and|or|also|from|but)(?=\s)/
USGLBL.10: /(occl\.|often|rare|only|in|but\susu\.|usu\.|rarely|esp\.|w\.\s?|used\sas)(?=\s)/
USGPREP: /æt|on|of|tō|fram|be|wið/

REFLBL: /==|=|v\.\salso|v\.|\?=/
REFWORD: /(?!as\ssb\.|[IV]{1,4}\.)[A-ZāæÐÆǣēīōðȳūüa-z-*?]+([āæÐÆǣēīōðȳūüa-z-*?)()]+[āæÐÆǣēīōðȳūüa-z-*?]+)?/
REFNUMWORD: /(\([1-3]\)\s_?[āæÆǣēīōðȳūüa-zA-Z\-\^0-9\*]+_?)(,|;|(\s([IV]{1,4}\.,?;?)))\s(\([1-3]\)\s(?!pret\.|pres\.)[+±āæÆǣēīōðȳūüa-zA-Z\-\^0-9\*]+(,|;|(\s([IV]{1,4}\.,?;?)))*\s?)*\.?/
HOMREF: /(?<!\.\s)[IV]{1,4}\.(\sand\s[IV]{1,4}\.)?/
GRAMREF: /\(?(interj\.|interrog\.\sparticle|accented\sverbal\sprefix|subst\.|sv\.|sb\.|vb\.|anv\.|swv\.|adj\.|adv\.|prep\.|pron\.|ptc\.|pp\.|num\.|conj\.),?\)?\s?/
PREFSUFXR: /[āæǣēīōðȳūüa-z\(\)-]+(,\s[āæǣēīōðȳūüa-z\(\)-]+)+[?!.]?/

TRANSLATION.1: /'?(_|\(_|_\()'?.*?_[',!]*/
GLOSS.3: /(((?<=_\s)\((i\.e\.\s)?['a-z-.0-9A-Z]+(\s[?a-z-.0-9A-Z]+)*\),?)|(\(['a-z-.0-9A-Z]+(\s[?a-z-.0-9A-Z]+)*\)(?=\s_)),?)|\(gram\.\)/
QMSENSE: /\(.*?\?.*?_.*?_\),?|\(_.*?_\s?\?\s?\)?,?/
DEFREF: /(?!as\ssb\.|[IV]{1,4}\.)[āäæÐÆǣēīōöðȳūüa-z\-\*\(\)]+,?/

SOURCE.5: /[#_]?[ÆA-Z][A-Za-z]{,4}[#_]?[,;?]?\s?/
SOURCE_NUM: /((([0-9·^´#]+)[a-z]?(\s\([0-9]+\)[a-z]?)?[,;]?)|(\(([0-9·^´,#]+)[a-z]?(\s\([0-9]+\)[a-z]?)?[,;]?\)))(\[0-9a-z]+\])?/
SRCVAR: /(?<=\s)\([-āæǣēīōðȳūüa-z]{1,6}(\^[0-9])?\)[,;?]?/
MSREF: /\([A-Z][a-z]+\.\s([A-Za-z]\s)*([xiv]{1,4})\)/
AUTH: /\((Tupper)\)/

OEDREF: /\s?'_.*?_(\^[0-9])?[.,]?';?\s?/
VIDE: /v\.\salso|v\.\s|V\.\s/
COMPARE: /cp\./
LANG: /_[A-Z][A-Za-z]*\._\s?/
PARENXR.2: /\(\??=\s[+±āæÆǣēīōðȳūüa-zA-Z*\?_]{4,}(\)|;?\s[ÆA-Za-z]*\s[\^0-9·•]*\)),?/
SYN: /(?!as\ssb\.|[IV]{1,4}\.)[āäæÐÆǣēīōöðȳūüa-zA-Z\*\(\)]+/
SQBRDASHVAR: /-[āäæÐÆǣēīōöðȳūüa-zA-Z\*\(\)]+|[āäæÐÆǣēīōöðȳūüa-zA-Z\*\(\)]+-/

EDCOMM: /\[\[.*?\]\]/

%ignore " "
%import common.NEWLINE
%ignore NEWLINE     
"""

def format_tree_simple(tree, indent=0):
    """
    Format a parse tree
    """
    if isinstance(tree, Tree):
        result = "  " * indent + str(tree.data)
        if tree.children:
            for child in tree.children:
                if isinstance(child, Tree):
                    result += "\n" + format_tree_simple(child, indent + 1)
                else:
                    result += "\t" + str(child)
        return result
    else:
        return "  " * indent + str(tree)

class DictionaryTransformer(Transformer):
    """
    The TEI transformer:
      
    """

    XML_NS = "http://www.w3.org/XML/1998/namespace"

    _ENTRY_NUM_SOURCES = {"OEG", "Chr"}

    _LINE_ONLY_SOURCES = {
        
        "Alm", "Cra", "Dom", "Fin", "Gen", "Sol", "Jud", "GnE", "Jul", "Mod",
        "Deor", "reat", "Hell", "Leas", "Part", "Rood", "Ruin", "Sat", "Seaf",
        "Soul", "Wald", "hale", "Wid", "Wif",
        "Ph", "An", "Ap", "Az", "Br", "Cr", "Da", "Gn", "El", "Ex", "Gu", "Hu",
        "Ma", "Pa", "Wa", "Wy",
    }

    _POS_MAP = {
        "adj.": "adjective",
        "adv.": "adverb",
        "interj.": "interjection",
        "interrog. particle": "interrogative particle",
        "accented verbal prefix": "accented verbal prefix",
        "subst.": "noun",
        "sb.": "noun",
        "vb.": "verb",
        "sv.": "strong verb",
        "wv.": "weak verb",
        "sv": "strong verb",
        "wv": "weak verb",
        "swv.": "strong-weak verb",
        "anv.": "anomalous verb",
        "ptc.": "participle",
        "pp.": "past participle",
        "num.": "numeral",
        "conj.": "conjunction",
        "prep.": "preposition",
        "pron.": "pronoun",
    }

    def __init__(self):
        super().__init__()
        # per-entry state captured via tokens
        self._lemma = None          # first WORD in entry
        self._prefix = None         # '+', '±', or None
        self._has_qm = False        # did we see QM?
        self._variants = []          # remember orthographic variants for this entry
        ET.register_namespace('xml', self.XML_NS)


    """
    HELPERS
        
    """
    # ---------------- safety net for undefined elements ----------------
    def __default__(self, data, children, meta):
        # Flatten pass-through so unimplemented rules never break anything
        flat = []
        for ch in children:
            if ch is None:
                continue
            if isinstance(ch, (list, tuple)):
                flat.extend([x for x in ch if x is not None])
            else:
                flat.append(ch)
        return flat
    
    def _make_pos_gram(self, inner_text: str) -> ET.Element:
        """
        inner_text is the POS token content with any surrounding parentheses removed
        (e.g., 'adj.' or 'sv.'). We'll keep the original spelling in element text,
        and map to a normalized @value via _POS_MAP (fallback: cleaned inner_text).
        """
        txt = inner_text.strip().rstrip(",")
        norm = txt.lower()
        val = self._POS_MAP.get(norm)
        if val is None and norm.endswith("."):
            val = self._POS_MAP.get(norm[:-1])
        if val is None:
            val = norm.replace(".", "")
        g = ET.Element("gram", {"type": "pos", "value": val})
        g.text = txt
        return g
    
    def _roman_to_int(self, roman: str) -> int:
        roman = roman.upper().strip()
        values = {"I": 1, "V": 5, "X": 10}
        total, prev = 0, 0
        for ch in reversed(roman):
            v = values.get(ch, 0)
            if v < prev:
                total -= v
            else:
                total += v
                prev = v
        return total
    
    def _parse_source_numbers(self, s: str, src_code: str | None = None):
        """
        - [123] or (123)      -> <citedRange unit="clause">...</citedRange>
        - 29·                 -> <biblScope unit="volume">29·</biblScope>
        - ^411                -> <citedRange unit="line">^411</citedRange>
        - 23a / 23b           -> <biblScope unit="folio">23a</biblScope>
        - #n#12 / 12n         -> <biblScope unit="footnote">...</biblScope>
        - plain 411:
            * if src in _ENTRY_NUM_SOURCES -> <citedRange unit="entry">
            * elif src in _LINE_ONLY_SOURCES -> <citedRange unit="line">
            * else -> <biblScope unit="page">
        """
        s = (s or "").strip()
        if not s:
            return []

        
        parts = re.findall(
            r'\[[0-9]+\]'          # [clause]
            r'|\([0-9]+\)'         # (clause)
            r'|[0-9]+·'            # volume with middle dot
            r'|\^[0-9]+'           # line with caret
            r'|[0-9]+[ab]'         # folio (a/b)
            r'|#n#[0-9]+'          # footnote style #n#12
            r'|[0-9]+n'            # footnote style 12n
            r'|[0-9]+'             # plain number
            , s
        )

        out = []
        for p in parts:
            if re.fullmatch(r'\[[0-9]+\]|\([0-9]+\)', p):
                el = ET.Element("citedRange", {"unit": "clause"})
                el.text = p
            elif p.endswith("·"):
                el = ET.Element("biblScope", {"unit": "volume"})
                el.text = p
            elif p.startswith("^"):
                el = ET.Element("citedRange", {"unit": "line"})
                el.text = p
            elif re.fullmatch(r'[0-9]+[ab]', p):
                el = ET.Element("biblScope", {"unit": "folio"})
                el.text = p
            elif re.fullmatch(r'#n#[0-9]+|[0-9]+n', p):
                el = ET.Element("biblScope", {"unit": "footnote"})
                el.text = p
            elif re.fullmatch(r'[0-9]+', p):
                # SOURCE-AWARE choice for ambiguous plain numbers
                norm_src = (src_code or "").strip()
                if norm_src in self._ENTRY_NUM_SOURCES:
                    el = ET.Element("citedRange", {"unit": "entry"})
                elif norm_src in self._LINE_ONLY_SOURCES:
                    el = ET.Element("citedRange", {"unit": "line"})
                else:
                    el = ET.Element("biblScope", {"unit": "page"})
                el.text = p
            else:
                # Fallback if something slips through
                el = ET.Element("citedRange", {"unit": "locator"})
                el.text = p

            out.append(el)
        return out
    
    def _replace_nth_vowel(self, word: str, repl: str, n: int) -> str:
        """
        Replace the n-th *vowel cluster* (1-based) in 'word' with 'repl'.
        A vowel cluster is one or more adjacent vowel characters (ea, eo, ǣ, etc.).
        If n is out of range, fall back to the first cluster.
        """
        vowels = set("aAeEiIoOuUyYāĀæÆǣǢēĒīĪōŌȳȲūŪ")
        clusters = []
        i = 0
        while i < len(word):
            if word[i] in vowels:
                j = i + 1
                while j < len(word) and word[j] in vowels:
                    j += 1
                clusters.append((i, j))  # [start, end) of this vowel cluster
                i = j
            else:
                i += 1

        if not clusters:
            return word  # nothing to replace

        # clamp to [1, len(clusters)]
        if n < 1 or n > len(clusters):
            n = 1

        start, end = clusters[n - 1]
        return word[:start] + repl + word[end:]
    
    def _is_pure_vowel_string(self, s: str) -> bool:
        """
        True if 's' contains only vowel letters (incl. macrons/diacritics).
        Items with consonants/hyphens (e.g., 'al-', 'æl-') return False.
        """
        vowels = set("aAeEiIoOuUyYāĀæÆǣǢēĒīĪōŌȳȲūŪ")
        return all(ch in vowels for ch in s)


    def _parse_spellvar_items(self, raw: str):
        """
        raw is the SPELLVAR token text like '(i, y)' or '(eo^1, e^2)' (possibly spaces).
        Returns a list of dicts: [{"letters": "eo", "slot": 1, "sep": ","}, ...]
        where 'sep' is the following separator for this item (',' or ';' or ')' for the last).
        """
       
        s = raw.strip()
        # keep only the content inside the outer parentheses
        if s.startswith("(") and s.endswith(")"):
            core = s[1:-1].strip()
        else:
            core = s

        # Split on comma/semicolon but keep separators
        parts = re.split(r"\s*([,;])\s*", core)
        # parts = [item1, sep1, item2, sep2, item3, ...]
        items = []
        i = 0
        while i < len(parts):
            item = parts[i].strip()
            sep = ")"
            if i+1 < len(parts):
                sep = parts[i+1]  # ',' or ';'
                i += 2
            else:
                i += 1

            # extract letters + optional ^n
            m = re.match(r"([A-Za-zāæǣēīōȳūüöœĀÆǢĒĪŌȲŪÜÖŒ\-]+)(?:\^(\d+))?\??$", item)
            if m:
                letters = m.group(1)
                slot = int(m.group(2)) if m.group(2) else 1
            else:
                letters, slot = item, 1

            items.append({"letters": letters, "slot": slot, "sep": sep})
        return items

    def _make_full_orth(self, txt: str, prefix_symbol: str | None) -> ET.Element:
        """
        Build an <orth> for a *full* form (not a partial/vowel replacement).
        Handle cases like "bicni(g)end" which means both "bicniend" and "bicnigend".
        If prefix_symbol is '+': expand="ge-<txt>" 
        If prefix_symbol is '±': expand="<txt>, ge-<txt>"
        """
        txt = (txt or "").strip()
        
        # Parse parenthetical optional parts in the word
        # e.g., "bicni(g)end" -> ["bicniend", "bicnigend"]
        def expand_parens(word):
           
            if '(' not in word:
                return [word]
            # Find first parenthetical group
            m = re.search(r'\(([^)]*)\)', word)
            if not m:
                return [word]
            before = word[:m.start()]
            inside = m.group(1)
            after = word[m.end():]
            # Two variants: with and without the parenthetical content
            without = before + after
            with_it = before + inside + after
            # Recursively handle multiple parentheses
            results = []
            for variant in [without, with_it]:
                results.extend(expand_parens(variant))
            return results
        
        base_forms = expand_parens(txt)
        
        # Apply prefix logic
        if prefix_symbol == '+':
            expanded = ", ".join(f"ge-{form}" for form in base_forms)
            orth = ET.Element("orth", {"extent": "full", "expand": expanded})
            lbl = ET.SubElement(orth, "lbl", {"expand": "ge-"})
            lbl.text = "+"
            ET.SubElement(orth, "seg").text = txt
        elif prefix_symbol == '±':
            # Include both with and without ge- for each base form
            all_forms = base_forms + [f"ge-{form}" for form in base_forms]
            expanded = ", ".join(all_forms)
            orth = ET.Element("orth", {"extent": "full", "expand": expanded})
            lbl = ET.SubElement(orth, "lbl", {"expand": "ge-_optional"})
            lbl.text = "±"
            ET.SubElement(orth, "seg").text = txt
        else:
            orth = ET.Element("orth")
            if len(base_forms) > 1:
                orth.set("expand", ", ".join(base_forms))
            orth.text = txt
        
        return orth
        
    def _is_likely_orth_variant(self, variant_text: str) -> bool:
        """
        Determine if a variant is likely a full orthographic variant rather than
        a vowel substitution. Returns True if:
        - Length is similar to lemma (within 2 characters)
        - Has significant consonant overlap with lemma
        - OR contains parentheses indicating optional parts
        """
        if not self._lemma:
            return False
        
        # If variant contains parentheses, it's definitely an orth variant
        if '(' in variant_text or ')' in variant_text:
            return True
        
        # Compare lengths
        len_diff = abs(len(variant_text) - len(self._lemma))
        if len_diff > 2:
            return False
        
        # Check consonant overlap
        consonants = set("ðbcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ")
        variant_consonants = [c for c in variant_text if c in consonants]
        lemma_consonants = [c for c in self._lemma if c in consonants]
        
        # If consonant structure is very similar, it's likely an orth variant
        if variant_consonants and lemma_consonants:
            common = sum(1 for v, l in zip(variant_consonants, lemma_consonants) if v == l)
            if common / min(len(variant_consonants), len(lemma_consonants)) > 0.7:
                return True
        
        return False   
    
    def _is_abbrev_of_lemma(self, token_without_prefix: str) -> bool:
        """
        True when token looks like an abbreviation of the current lemma, e.g. 'h.'
        for lemma 'habban',  (any leading substring + dot).
        """
        tok = (token_without_prefix or "").strip()
        if not tok.endswith("."):
            return False
        base = tok[:-1]  # drop trailing dot
        if not base or not self._lemma:
            return False
        return self._lemma.lower().startswith(base.lower())

    def _token_to_id_part(self, raw_token: str) -> str:
        """
        Convert a collocation token to its xml:id component:
        '+word' -> 'ge-word'
        '±word' -> 'word'
        'word'  -> 'word'
        If the token is an abbreviation of the lemma (e.g. 'h.' for 'habban'),
        use the *lemma* as the base (and apply the same +/± rules).
        """
        import re
        t = (raw_token or "").strip()
        if not t:
            return t

        # pull off + / ±
        prefix = None
        if t[0] in ("+", "±"):
            prefix = t[0]
            core = t[1:].strip()
        else:
            core = t

        if self._is_abbrev_of_lemma(core):
            base = self._lemma or core
        else:
            base = re.sub(r"[,:;!?]+$", "", core)

        if prefix == "+":
            return f"ge-{base}"
        return base
    
    def _expand_adv_lice(self, lemma: str) -> str:
        """
        Build the adverb in -līce from the entry lemma + any known -lic variants.

        Priority:
        1) If lemma ends with -lic or -lic. → replace with -līce
        2) Else, if we saw a variant ending in 'lic' and starting with '-' (e.g. '-fullic'):
        - If lemma is hyphenated (e.g. 'georn-ful'), keep the base before the last hyphen
            and join the variant without the leading '-' and with 'lic'→'līce':
            'georn-' + 'fullic'→'fullīce' => 'georn-fullīce'
        3) Else, if lemma ends with 'ful' → lemma + 'līce'
        4) Fallback → lemma + 'līce' (crude but ensures presence)
        """
        L = (lemma or "").rstrip(".")
        # 1) direct -lic on lemma
        for suf in ("-lic", "lic"):
            if L.endswith(suf):
                return L[: -len(suf)] + "līce"

        # 2) look for suffix variant like "-fullic"
        for v in self._variants:
            v_clean = v.strip()
            if v_clean.startswith("-") and v_clean.endswith("lic"):
                core = v_clean[1:-3] + "līce"  # remove leading '-', swap lic→līce
                if "-" in L:
                    left, _right = L.rsplit("-", 1)
                    return f"{left}-{core}"
                else:
                    return L + core

        # 3) common pattern: '-ful' adjectives
        if L.endswith("ful"):
            return L + "līce"

        # 4) fallback
        return L + "līce"


    """
    TOKENS
      
    """

    @v_args(inline=True)
    def WORD(self, tok):
        if self._lemma is None:
            self._lemma = str(tok).strip()
        return tok

    @v_args(inline=True)
    def GE_PREF(self, tok):  # '+'
        if self._lemma is None and self._prefix is None:
            self._prefix = '+'
        return tok

    @v_args(inline=True)
    def GE_OPT(self, tok):   # '±'
        if self._lemma is None and self._prefix is None:
            self._prefix = '±'
        return tok
    

    @v_args(inline=True)
    def QM(self, tok):
        return {"_qm": True}

    
    @v_args(inline=True)
    def POET_SYMB(self, tok):
        """
        Turn † / ‡ into a <usg> element.
        † → expand="attested in poetic texts only"
        ‡ → expand="attested in poetical texts only, and once only"
        """
        sym = str(tok).strip().rstrip(",")
        usg = ET.Element("usg", {"type": "textType"})
        if sym == "†":
            usg.set("expand", "attested in poetic texts only")
        elif sym == "‡":
            usg.set("expand", "attested in poetical texts only, and once only")
        else:
            usg.set("expand", "poetic")
        usg.text = sym
        return usg
    
    @v_args(inline=True)
    def ROM_NUM(self, tok):
       
        text = str(tok).strip()
        roman = text.rstrip(".").strip()
        n = self._roman_to_int(roman)
        return {"_rom_text": text, "_roman": roman, "_n": n}

    # ---------------- for senses ----------------
    @v_args(inline=True)
    def TRANSLATION(self, tok):
        """
        Drop underscores and split on parenthetical segments.
        Example: "bill, beak, trunk (of an elephant)," ->
        <quote>bill, beak, trunk</quote>
        <gloss>(of an elephant),</gloss>
        If no parentheses, return a single <quote>.
        """
        text = str(tok)
        text = text.replace("_", "").strip()

        parts = []
        i = 0
        for m in re.finditer(r'\([^)]*\),?', text):
            before = text[i:m.start()].strip()
            if before:
                q = ET.Element("quote")
                q.text = before
                parts.append(q)
            g = ET.Element("gloss")
            g.text = m.group(0).strip()
            parts.append(g)
            i = m.end()

        tail = text[i:].strip()
        if tail:
            q = ET.Element("quote")
            q.text = tail
            parts.append(q)

        if not parts:
            q = ET.Element("quote"); q.text = text
            return q
        return parts
    
    @v_args(inline=True)
    def GLOSS(self, tok):
        g = ET.Element("gloss")
        g.text = str(tok).strip()  
        return g

    @v_args(inline=True)
    def COLON_SEP(self, tok):
        m = ET.Element("metamark", {"function": "senseSeparator"})
        m.text = ":"
        return m

    @v_args(inline=True)
    def SEMICOL_SEP(self, tok):
        m = ET.Element("metamark", {"function": "senseSeparator"})
        m.text = ";"
        return m

    @v_args(inline=True)
    def DOT_SEP(self, tok):
        m = ET.Element("metamark")
        m.text = "."
        return m
    
    # ---------------- BIBL ----------------  
    @v_args(inline=True)
    def SOURCE(self, tok):
        """
        Examples: '_Bo,', 'WG;', '#Æ', 'ES'
        - strip underscores and # for both the TEI @source and the displayed <title>
        - keep trailing comma/semicolon in the <title> text
        """
        raw = str(tok).strip()
        clean = raw.replace("_", "").replace("#", "").strip()
        title = clean
        code = clean.rstrip(",;?.:").strip()
        return {"_src_code": code, "_src_title": title}

    @v_args(inline=True)
    def SOURCE_NUM(self, tok):
        return {"_srcnum": str(tok).strip()}


    # ---------------- GRAM. INFO ----------------         
    @v_args(inline=True)
    def GEN(self, tok):
        """
        Examples of tok text (single token, may include parens and ?/.):
        'm.' 'nf.' '(m.)' '(mf?)' 'm?' '(nf. )'
        """
        raw = str(tok).strip()

        left_paren  = raw.startswith("(")
        right_paren = raw.endswith(")")
        inner = raw[1:-1].strip() if (left_paren and right_paren) else raw.strip("()").strip()

        # Detect uncertainty (question mark anywhere in the token)
        has_q = "?" in inner

        # Remove '?' for the displayed text 
        display = inner.replace("?", "").strip()

        # Build @value from letters in the display text (order-preserving)
        letters = [ch for ch in display if ch in "mnf"]
        label_map = {"m": "masculine", "n": "neuter", "f": "feminine"}
        values = ", ".join(label_map[c] for c in letters) if letters else ""

        gram = ET.Element("gram", {"type": "gender", "value": values})
        gram.text = display  

        out = []
        if left_paren:
            pc = ET.Element("pc"); pc.text = "("
            out.append(pc)

        out.append(gram)

        if has_q:
            note = ET.Element("note", {"cert": "low", "resp": "author"})
            note.text = "?"
            out.append(note)

        if right_paren:
            pc = ET.Element("pc"); pc.text = ")"
            out.append(pc)

        return out
    
    # --- handle gender without trailing dot (e.g., "m", "mf", "nf") ---
    @v_args(inline=True)
    def NODOTGEN(self, tok):
        inner = str(tok).strip()            
        letters = [ch for ch in inner if ch in "mnf"]
        label_map = {"m": "masculine", "n": "neuter", "f": "feminine"}
        values = ", ".join(label_map[c] for c in letters) if letters else ""
        gram = ET.Element("gram", {"type": "gender", "value": values})
        gram.text = inner                
        return gram
    
    @v_args(inline=True)
    def POS(self, tok):
        raw = str(tok).strip()
        left_paren  = raw.startswith("(")
        right_paren = raw.endswith(")")
        inner = raw[1:-1].strip() if (left_paren and right_paren) else raw.strip("()").strip()
        inner = inner.rstrip(",")  

        gram = self._make_pos_gram(inner)

        out = []
        if left_paren:
            pc = ET.Element("pc"); pc.text = "("
            out.append(pc)

        out.append(gram)

        if right_paren:
            pc = ET.Element("pc"); pc.text = ")"
            out.append(pc)

        return out
    
    @v_args(inline=True)
    def REFLBL(self, tok):
        # e.g., '=', '==', 'v.', 'v. also', '?='
        return str(tok).strip()

    @v_args(inline=True)
    def REFWORD(self, tok):
        return str(tok).strip()
    
    @v_args(inline=True)
    def COLLOC(self, tok):
        # Full collocation phrase, e.g. "tō āhte"
        return str(tok).strip()

    @v_args(inline=True)
    def ONEWORD(self, tok):
        # A single word, possibly with a leading '+' or '±', e.g. "±lǣred"
        return str(tok).strip()

    # ---------------- RULES ----------------
    def headword(self, children):

        out, has_qm = [], False
        for ch in children:
            if isinstance(ch, dict) and ch.get("_qm"):
                has_qm = True
            else:
                out.append(ch)
        if has_qm:
            out.append({"_headword_qm": True})
        return out if out else None

    def qm(self, children):

        out, saw = [], False
        for ch in children:
            if isinstance(ch, dict) and ch.get("_qm"):
                saw = True
            else:
                out.append(ch)
        if saw:
            out.append({"_qm": True})
        return out if out else {"_qm": True}


    def gramgrp(self, children):
        """
        Wrap any returned <gram> into a single <gramGrp>.
        If a gender is present and there is NO explicit POS, add an implicit
        <gram type="pos" value="noun"/> 
        """
        items = []
        for ch in children:
            if isinstance(ch, ET.Element) and ch.tag in ("gram", "pc", "note"):
                items.append(ch)
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, ET.Element) and z.tag in ("gram", "pc", "note"):
                        items.append(z)

        if not items:
            return None

        has_gender = any(e.tag == "gram" and e.get("type") == "gender" for e in items)
        has_pos    = any(e.tag == "gram" and e.get("type") == "pos"    for e in items)

        # Insert implicit noun POS 
        if has_gender and not has_pos:
            pos_noun = ET.Element("gram", {"type": "pos", "value": "noun"})
            insert_idx = 0
            for i, e in enumerate(items):
                if e.tag == "pc" and (e.text or "").strip() == "(":
                    insert_idx = i
                    break
            items.insert(insert_idx, pos_noun)

        grp = ET.Element("gramGrp")
        for e in items:
            grp.append(e)
        return grp
    
    def infgramgrp(self, children):
        """
        Wrap the inflectional grams into <gramGrp>. 
        """
        grams = []
        for ch in children:
            if isinstance(ch, ET.Element) and ch.tag == "gram":
                grams.append(ch)
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, ET.Element) and z.tag == "gram":
                        grams.append(z)

        if not grams:
            return None

        grp = ET.Element("gramGrp")
        grp.append(ET.Element("gram", {"type": "pos", "value": "verb"}))
        for g in grams:
            grp.append(g)
        return grp

    
    def tense(self, children):
        """
        e.g. 'pres.' -> <gram type="tense" value="present">pres.</gram>
            'pret.' -> <gram type="tense" value="preterite">pret.</gram>
        """
        t = "".join(str(c) for c in children).strip()
        m = {
            "pres.": "present",
            "pret.": "preterite",
            "past": "past",
            "fut.": "future",
        }
        val = m.get(t.lower(), t.rstrip(".").lower())
        g = ET.Element("gram", {"type": "tense", "value": val})
        g.text = t
        return g

    def person(self, children):
        """
        e.g. '3' -> <gram type="person" value="third">3</gram>
        """
        t = "".join(str(c) for c in children).strip()
        pmap = {"1": "first", "2": "second", "3": "third"}
        val = pmap.get(t, t)
        g = ET.Element("gram", {"type": "person", "value": val})
        g.text = t
        return g

    def number(self, children):
        """
        Normalize number tokens to TEI values.
        Accepts: 'sg.', 's.', 'sing.', 'pl.', 'p.', 'sg', 'pl', 's', 'p'
        → value='singular' / 'plural'
        """
        t = "".join(str(c) for c in children).strip()
        t_clean = t.rstrip(",").strip()
        k = t_clean.lower()

        mapping = {
            "sg.": "singular", "sg": "singular", "s.": "singular", "s": "singular", "sing.": "singular",
            "pl.": "plural",   "pl": "plural",   "p.": "plural",   "p": "plural",   "sbpl.": "plural",
        }
        val = mapping.get(k)
        if val is None:
            # Fallbacks: strip a trailing dot and try again
            k2 = k.rstrip(".")
            val = mapping.get(k2, k2)  # last resort: pass through cleaned token

        g = ET.Element("gram", {"type": "number", "value": val})
        g.text = t_clean
        return g

    
    def spell_var(self, children):
        """
        SPELLVAR token looks like "(eo^1, o^1; æ^2; æ^3)" or "(i, y)" etc.
        We:
        - split into items, preserving separators (',' / ';') and final ')'
        - compute @expand only when the item is pure vowels
        - write exact visible text into <seg>, including '(' for first, the letters,
            optional superscript <lbl>, and trailing punctuation/comma/semicolon/')'
        Returns a list of <form type="variant">...</form> elements.
        """
        if not children:
            return None

        raw = str(children[0]).strip()

        # Check if this is actually an orth_variant misclassified as spell_var
        # e.g., "(gearu)" should be orth_variant, not spell_var
        inner = raw[1:-1] if raw.startswith("(") and raw.endswith(")") else raw
        
        # If it looks like a full word variant, treat it as orth_variant
        if self._is_likely_orth_variant(inner):
            f = ET.Element("form", {"type": "variant"})
            # Handle parenthesized full variant
            if raw.startswith("(") and raw.endswith(")"):
                f.text = "("
                orth = self._make_full_orth(inner, None)
                f.append(orth)
                orth.tail = ")"
            else:
                orth = self._make_full_orth(inner, None)
                f.append(orth)
            return f

       
        # Split items, keeping separators (comma/semicolon). The last match's sep may be ''.
        items = []
        for m in re.finditer(r'\s*([^,;]+?)\s*([,;]|$)', inner):
            item = m.group(1).strip()   # e.g., "eo^1", "o^1", "æ^2"
            sep = m.group(2)            # ',', ';', or '' for the last one
            if item:
                items.append((item, sep))

        variants = []
        for idx, (item, sep) in enumerate(items):
            # Extract letters and optional superscript number (^n)
            m = re.match(r'^(.+?)(?:\^(\d+))?$', item)
            letters = (m.group(1) or "").strip()
            sup = m.group(2)  # e.g., "1", "2", or None
            slot = int(sup) if sup else 1

            # Compute expand based on vowel replacement AND prefix
            expanded_forms = []
            if self._is_pure_vowel_string(letters):
                base_expanded = self._replace_nth_vowel(self._lemma, letters, slot)
                # If lemma has ± prefix, include both forms
                if self._prefix == '±':
                    expanded_forms = [base_expanded, f"ge-{base_expanded}"]
                elif self._prefix == '+':
                    expanded_forms = [f"ge-{base_expanded}"]
                else:
                    expanded_forms = [base_expanded]

            # Build <form><orth><seg> ... </seg></orth></form>
            f = ET.Element("form", {"type": "variant"})
            orth_attrs = {"extent": "part"}
            if expanded_forms:
                orth_attrs["expand"] = ", ".join(expanded_forms)
            orth = ET.SubElement(f, "orth", orth_attrs)
            seg = ET.SubElement(orth, "seg")

            # Build the text content properly
            if idx == 0:
                # First item: include opening parenthesis
                seg.text = "(" + letters
            else:
                # Subsequent items: just the letters
                seg.text = letters

            if sup:
                # Add superscript as a child
                lbl = ET.SubElement(seg, "lbl", {"rend": "sup"})
                lbl.text = sup
                # Add punctuation as tail of lbl
                if idx < len(items) - 1:
                    # Not the last item: add separator (comma or semicolon)
                    lbl.tail = sep if sep else ","
                else:
                    # Last item: close the parenthesis
                    lbl.tail = ")"
            else:
                # No superscript: add punctuation directly to seg.text
                if idx < len(items) - 1:
                    # Not the last item: add separator
                    seg.text += sep if sep else ","
                else:
                    # Last item: close the parenthesis
                    seg.text += ")"

            variants.append(f)

        return variants if variants else None
    
    def orth_variant(self, children):
        """
        Matches:
        (", "|"-") ge_pref? VARIANT+
        | LP lbl? ge_pref? VARIANT+ bibl? RP
        Important: comma-separated variants after lemma do NOT inherit prefix, 
        only variants with explicit prefix symbols get prefixes.
        """
        # Detect which branch we're in and collect pieces
        sep_symbol = None         # ',' or '-' if first branch used
        in_parens = False         # True if LP ... RP branch
        local_prefix = None       # '+', '±', or None from this orth_variant
        variants = []             # raw VARIANT token texts
        for ch in children:
            if isinstance(ch, Token):
                s = str(ch).strip()
                if ch.type == "LP" or s.startswith("("):
                    in_parens = True
                elif s.startswith(","):
                    sep_symbol = ","
                elif s == "-":
                    sep_symbol = "-"
                elif ch.type == "VARIANT":
                    variants.append(s)
                elif ch.type == "GE_PREF":
                    local_prefix = '+' # This handles GE_PREF directly under orth_variant
                elif ch.type == "GE_OPT":
                    local_prefix = '±' # This handles GE_OPT directly under orth_variant
            elif isinstance(ch, Tree):
                if ch.data == "ge_pref": # This handles GE_PREF inside a ge_pref tree
                    for gc in ch.children:
                        if isinstance(gc, Token):
                            if gc.type == "GE_PREF":
                                local_prefix = '+' # Correctly set prefix from ge_pref tree
                            elif gc.type == "GE_OPT":
                                local_prefix = '±' # Correctly set prefix from ge_pref tree
                else:
                    for gc in ch.children:
                        if isinstance(gc, Token) and gc.type == "VARIANT":
                            variants.append(str(gc).strip())

            # This handles the case where ge_pref is optional and becomes a list of tokens
            elif isinstance(ch, list):
                for item in ch:
                    if isinstance(item, Token):
                        s_item = str(item).strip()
                        if item.type == "GE_PREF":
                            local_prefix = '+' # Handle GE_PREF found inside the list
                        elif item.type == "GE_OPT":
                            local_prefix = '±' # Handle GE_OPT found inside the list
                    elif isinstance(item, Tree) and item.data == "ge_pref": # Also check for ge_pref tree inside list
                        for gc in item.children:
                            if isinstance(gc, Token):
                                if gc.type == "GE_PREF":
                                    local_prefix = '+' # Handle GE_PREF inside ge_pref tree inside list
                                elif gc.type == "GE_OPT":
                                    local_prefix = '±' # Handle GE_OPT inside ge_pref tree inside list
                    elif isinstance(item, Token) and item.type == "VARIANT": # Also check for VARIANT inside list
                         variants.append(str(item).strip())

        # Clean VARIANT texts
        variants = [re.sub(r'[;,]\s*$', '', v).strip() for v in variants if v.strip()]
        # remember raw variant strings (including leading '-' if present)
        for _v in variants:
            if _v:
                self._variants.append(_v.strip(",;"))

        # Comma-separated variants don't inherit prefix - only use local prefix
        effective_prefix = local_prefix if local_prefix else None
        out = []
        # If this orth_variant started with ", ", mark that the lemma needs a trailing comma
        if sep_symbol == ",":
            out.append({"_lemma_punct": ","})

        # Parenthesized variant: ONE form
        if in_parens:
            vtxt = " ".join(variants).strip()
            f = ET.Element("form", {"type": "variant"})
            f.text = "("
            orth = self._make_full_orth(vtxt, effective_prefix)
            f.append(orth)
            orth.tail = ")"
            out.append(f)
            return out if out else None

        # Separator branch: one <form> per VARIANT
        for vtxt in variants:
            f = ET.Element("form", {"type": "variant"})
            orth = self._make_full_orth(vtxt, effective_prefix)
            f.append(orth)
            out.append(f)

        return out if out else None

    def form(self, children):
        
        out = []
        for ch in children:
            if isinstance(ch, ET.Element):
                out.append(ch)
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, ET.Element):
                        out.append(z)
        return out if out else None
    
    def bibl(self, children):
        """
        Grammar shape (simplified): (poet_symb | ge_pref)* author? SOURCE+ parenbibl? SOURCE_NUM? ...
        - create ONE <bibl> per SOURCE
        - attach SOURCE_NUM (if present) to the LAST created <bibl>
        - ignore author/poet_symb/ge_pref for now 
        """
        src_items = []
        tail_num = None

        for ch in children:
            if isinstance(ch, dict) and "_src_code" in ch:
                src_items.append(ch)
            elif isinstance(ch, dict) and "_srcnum" in ch:
                tail_num = ch["_srcnum"]
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, dict) and "_src_code" in z:
                        src_items.append(z)
                    elif isinstance(z, dict) and "_srcnum" in z:
                        tail_num = z["_srcnum"]

        bibls = []
        for i, s in enumerate(src_items):
            b = ET.Element("bibl", {"type": "attestation", "source": f"#{s['_src_code']}"})
            title = ET.SubElement(b, "title")
            title.text = s["_src_title"]  # keep comma/semicolon
            bibls.append(b)

        if tail_num and bibls:
            last_code = src_items[-1]["_src_code"] if src_items else None
            for el in self._parse_source_numbers(tail_num, src_code=last_code):
                bibls[-1].append(el)

        return bibls if len(bibls) > 1 else (bibls[0] if bibls else None)
    
    def parenbibl(self, children):
        """
        simply return the inner bibl element(s) for now.
        """
        out = []
        for ch in children:
            if isinstance(ch, ET.Element) and ch.tag == "bibl":
                out.append(ch)
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, ET.Element) and z.tag == "bibl":
                        out.append(z)
        if not out:
            return None
        return out if len(out) > 1 else out[0]
    
    def hom_entry(self, children):
        """
        <entry xml:id="LEMMA_n" type="homonymicEntry" xml:lang="ang" n="I">
        <lbl type="homNum">I.</lbl>
        ... (elements of this hom, in source order) ...
        </entry>
        """
        info = None
        items = []
        for ch in children:
            if isinstance(ch, dict) and "_n" in ch:
                info = ch
            elif isinstance(ch, (list, tuple)):
                items.extend(ch)
            elif ch is not None:
                items.append(ch)

        if info is None:
            return None

        lemma = self._lemma or "UNKNOWN"
        n = info["_n"]
        roman_text = info["_rom_text"].strip()
        roman_only = info["_roman"]

        hom_id = f"{lemma}_{n}"
        hom = ET.Element("entry", {
            f"{{{self.XML_NS}}}id": hom_id,
            "type": "homonymicEntry",
            f"{{{self.XML_NS}}}lang": "ang",
            "n": roman_only
        })
        ET.SubElement(hom, "lbl", {"type": "homNum"}).text = roman_text

        # sense-id rewriter 
        base = lemma
        old_prefix = f"{base}."
        new_prefix = f"{base}_{n}."

        def _rewrite_ids(elem):
            if elem.tag == "sense":
                sid = elem.get(f"{{{self.XML_NS}}}id")
                if sid and sid.startswith(old_prefix):
                    elem.set(f"{{{self.XML_NS}}}id", sid.replace(old_prefix, new_prefix, 1))
            for child in list(elem):
                if isinstance(child, ET.Element):
                    _rewrite_ids(child)

        # Preserve original order of usg/gramGrp/sense; hold trailing '.' to end
        ordered = []
        trailing_dots = []

        def _ordered_collect(obj):
            if isinstance(obj, ET.Element):
                if obj.tag in ("usg", "gramGrp", "xr", "sense", "metamark"):
                    ordered.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _ordered_collect(z)

        for it in items:
            _ordered_collect(it)

        for e in ordered:
            if e.tag == "metamark" and (e.text or "").strip() == ".":
                trailing_dots.append(e)      # append later
                continue
            if e.tag == "sense":
                _rewrite_ids(e)
            hom.append(e)

        for d in trailing_dots:
            hom.append(d)

        return hom

   
    def quote(self, children):
        out = []
        buf = []

        def flush_buf():
            if buf:
                q = ET.Element("quote")
                q.text = " ".join(buf).strip()
                if q.text:
                    out.append(q)
                buf.clear()

        for ch in children:
            if isinstance(ch, str):
                buf.append(ch)
            elif isinstance(ch, ET.Element) and ch.tag in ("quote", "gloss"):
                flush_buf()
                out.append(ch)
            elif isinstance(ch, (list, tuple)):
                for z in ch:
                    if isinstance(z, ET.Element) and z.tag in ("quote", "gloss"):
                        flush_buf()
                        out.append(z)
                    elif isinstance(z, str):
                        buf.append(z)

        flush_buf()
        if not out:
            return None
        return out if len(out) > 1 else out[0]


    def cit(self, children):
        """
        cit: ... quote ... (qm? bibl | parenbibl)*

        Emit:
        <cit type="translation" xml:lang="en">
        <quote>...</quote>
        <note cert="low" resp="author">?</note>   # only if qm occurred here
        <bibl ...>...</bibl>*
        </cit>
        """
        cit_el = ET.Element("cit", {
            "type": "translation",
            f"{{{self.XML_NS}}}lang": "en"
        })

        # Collect in order and detect qm marker(s)
        elements = []   # quotes/gloss/bibl in order
        qm_here  = False

        def take(obj):
            nonlocal qm_here
            if isinstance(obj, dict) and obj.get("_qm"):
                qm_here = True
            elif isinstance(obj, ET.Element) and obj.tag in ("quote", "gloss", "bibl"):
                elements.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    take(z)

        for ch in children:
            take(ch)

        # Insert the note right after the last <quote>/<gloss> and before the first <bibl>
        if qm_here:
            note = ET.Element("note", {"cert": "low", "resp": "author"})
            note.text = "?"
            first_bibl_idx = next((i for i, e in enumerate(elements) if e.tag == "bibl"), None)
            if first_bibl_idx is None:
                elements.append(note)
            else:
                elements.insert(first_bibl_idx, note)

        for el in elements:
            cit_el.append(el)

        return cit_el if list(cit_el) else None


    def firstsense(self, children):
        """
        Return 
          - <cit> blocks
          - <metamark> 
        """
        out = []
        for ch in children:
            if isinstance(ch, ET.Element) and ch.tag in ("cit", "metamark"):
                out.append(ch)
            elif isinstance(ch, list):
                out.extend([z for z in ch if isinstance(z, ET.Element) and z.tag in ("cit", "metamark")])
        return out

    def othersenses(self, children):
        return self.firstsense(children)

    def sense_section(self, children):
        """
        Build senses.
        
        """
        seq = []
        for ch in children:
            if isinstance(ch, ET.Element) and ch.tag in ("cit", "metamark"):
                seq.append(ch)
            elif isinstance(ch, list):
                for z in ch:
                    if isinstance(z, ET.Element) and z.tag in ("cit", "metamark"):
                        seq.append(z)

        chunks, current, seps = [], [], []
        trailing_dot = False

        for node in seq:
            if node.tag == "metamark":
                sym = (node.text or "").strip()
                if sym in (":", ";"):
                    chunks.append(current[:]); seps.append(sym); current.clear()
                elif sym == ".":
                    trailing_dot = True  
            else:
                current.append(node)

        if current:
            chunks.append(current[:])

        base = self._lemma or "UNKNOWN"

        def _dot_meta():
            m = ET.Element("metamark")  
            m.text = "."
            return m

        # single sense
        if len(chunks) <= 1:
            sense = ET.Element("sense", {f"{{{self.XML_NS}}}id": f"{base}.1"})
            for node in (chunks[0] if chunks else []):
                if isinstance(node, ET.Element) and node.tag == "cit":
                    sense.append(node)
            return [sense, _dot_meta()] if trailing_dot else sense

        # multiple subsenses with wrapper and separators
        wrapper = ET.Element("sense", {f"{{{self.XML_NS}}}id": f"{base}.1"})
        for i, nodes in enumerate(chunks, start=1):
            inner = ET.Element("sense", {f"{{{self.XML_NS}}}id": f"{base}.1.{i}"})
            for node in nodes:
                if isinstance(node, ET.Element) and node.tag == "cit":
                    inner.append(node)
            wrapper.append(inner)
            if i < len(chunks):
                sep = seps[i-1] if i-1 < len(seps) else ":"
                m = ET.Element("metamark", {"function": "senseSeparator"})
                m.text = sep
                wrapper.append(m)

        return [wrapper, _dot_meta()] if trailing_dot else wrapper
    
    def reflbl(self, children):
        # Build <lbl> from the REFLBL token text
        txt = ""
        for ch in children:
            if isinstance(ch, str):
                txt = ch
                break
        if not txt:
            return None
        el = ET.Element("lbl")
        el.text = txt
        return el
    
    def refword(self, children):
       
        ref_txt = ""
        for ch in children:
            if isinstance(ch, str):
                ref_txt = ch
                break
        if not ref_txt:
            return None

        wclean = re.sub(r'[.,;:)]+$', '', ref_txt.strip())

        ref = ET.Element("ref", {"target": f"#{wclean}", "type": "entry"})
        ref.text = wclean
        return ref
    
    def simple_xr(self, children):
        """
        simple_xr: ... reflbl (refword | refwords) ...
        For now we only use reflbl + the first refword.
        """
        xr = ET.Element("xr", {"type": "related", "expand": "orthographic variant"})
        lbl_el, ref_el = None, None

        def pick(el):
            nonlocal lbl_el, ref_el
            if isinstance(el, ET.Element):
                if el.tag == "lbl" and lbl_el is None:
                    lbl_el = el
                elif el.tag == "ref" and ref_el is None:
                    ref_el = el
            elif isinstance(el, (list, tuple)):
                for z in el:
                    pick(z)

        for ch in children:
            pick(ch)

        if lbl_el is not None:
            xr.append(lbl_el)
        if ref_el is not None:
            xr.append(ref_el)

        return xr if list(xr) else None
    
    def xr_section(self, children):
        """
        Grammar: usglbl? parenbibl? infgramgrp OF refword parenxr? ( ... )? '.'?
        Build the inflected-form cross-ref:
        <gramGrp>...</gramGrp>
        <xr type="related" expand="inflected form">
            <lbl>of</lbl>
            <ref target="#...">...</ref>
        </xr>
        Return [gramGrp, xr] in source order.
        """
        gramgrp = None
        ref_el = None
        ordered = []

        def take(el):
            nonlocal gramgrp, ref_el
            if isinstance(el, ET.Element):
                if el.tag == "gramGrp":
                    gramgrp = el
                    ordered.append(el)
                elif el.tag == "ref":
                    ref_el = el
            elif isinstance(el, (list, tuple)):
                for z in el:
                    take(z)

        for ch in children:
            take(ch)

        xr = None
        if ref_el is not None:
            xr = ET.Element("xr", {"type": "related", "expand": "inflected form"})
            ET.SubElement(xr, "lbl").text = "of"  # OF token; always 'of' here
            xr.append(ref_el)
            ordered.append(xr)

        return ordered if ordered else None
    
    def adv_word(self, children):
        """
        Grammar yields: 'adv.' then a WORD like '-līce', possibly commas, bibl, and/or a sense_section.
        We turn it into a payload dict so relatedentry() can build the related entry.
        """
        suffix = None
        payload_children = []  # senses/bibl/metamark collected inside adv_word

        def take(obj):
            nonlocal suffix
            if isinstance(obj, Token):                 
                s = str(obj).strip()
                if s.startswith("-") and "līce" in s:
                    suffix = s
            elif isinstance(obj, str):                 
                s = obj.strip()
                if s.startswith("-") and "līce" in s:
                    suffix = s
            elif isinstance(obj, ET.Element):
                if obj.tag in ("sense", "bibl", "metamark"):
                    payload_children.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    take(z)

        for ch in children:
            take(ch)

        if not suffix:
            suffix = "-līce"

        return {"_related_type": "adv_lice", "suffix": suffix, "content": payload_children}

    
    def collocation(self, children):
        """
        Build a simple payload we can read in relatedentry().
        We expect exactly one COLLOC token string here.
        """
        text = ""
        for ch in children:
            if isinstance(ch, str) and ch:
                text = ch
                break
        if not text:
            return None
        return {"_related_type": "collocation", "text": text}

    def oneword(self, children):
        """
        ONEWORD may include a leading '+' or '±' that the grammar doesn't split.
        We detect it here and strip it from the surface, returning the symbol.
        """
        word = ""
        for ch in children:
            if isinstance(ch, str) and ch:
                word = ch.strip()
                break
        if not word:
            return None

        prefix = None
        if word.startswith("±"):
            prefix, word = "±", word[1:].strip()
        elif word.startswith("+"):
            prefix, word = "+", word[1:].strip()

        return {"_related_type": "oneword", "text": word, "prefix": prefix}
    
    def relatedentry(self, children):
        """
        Collocation:
        - Build one <orth> per token (honor + / ±, abbreviations to <ref type="oRef">).
        - xml:id is tokens joined by '_', but:
            * '+' → 'ge-' in id
            * '±' removed from id
            * abbreviations (e.g. '+h.') become lemma (with ge- if '+')
        Oneword:
        - xml:id is the word; if prefix is '+', use 'ge-<word>'; if '±', just <word>.
        """
        # ---- find the payload (collocation or oneword) ----
        payload = None
        rest = []  # other children (e.g., sense_section)
        for ch in children:
            if isinstance(ch, dict) and ch.get("_related_type") in ("collocation", "oneword", "adv_lice"):
                payload = ch
            else:
                rest.append(ch)

        if not payload:
            return None

        main_base = self._lemma or "UNKNOWN"

        # --------------------------------------------------------------------
        # Adverb-in -līce branch (from adv_word)
        # --------------------------------------------------------------------
        if payload["_related_type"] == "adv_lice":
            sfx = payload.get("suffix") or "-līce"
            base = self._lemma or "UNKNOWN"
            expanded = self._expand_adv_lice(base)  # compute xml:id and orth@expand

            rel = ET.Element("entry", {
                f"{{{self.XML_NS}}}id": expanded,
                "type": "relatedEntry",
                f"{{{self.XML_NS}}}lang": "ang",
            })

            # Per spec: include adj. in gramGrp
            ggr = ET.SubElement(rel, "gramGrp")
            g = ET.SubElement(ggr, "gram", {"type": "pos", "value": "adjective"})
            g.text = "adj."

            # Lemma form with part-orth and seg '-līce', expand to the full adverb
            f = ET.SubElement(rel, "form", {"type": "lemma"})
            orth = ET.SubElement(f, "orth", {"extent": "part", "expand": expanded})
            ET.SubElement(orth, "seg").text = sfx 

            # --- rewrite sense ids from lemma-based -> related-entry-based ---
            content = list(payload.get("content", []))
            old_prefix = f"{base}."
            new_prefix = f"{expanded}."

            def _rewrite_ids(elem):
                if isinstance(elem, ET.Element):
                    if elem.tag == "sense":
                        sid = elem.get(f"{{{self.XML_NS}}}id")
                        if sid and sid.startswith(old_prefix):
                            elem.set(f"{{{self.XML_NS}}}id", sid.replace(old_prefix, new_prefix, 1))
                    for c in list(elem):
                        _rewrite_ids(c)

            for node in content:
                _rewrite_ids(node)
                rel.append(node)

            return rel

        # --------------------------------------------------------------------
        # Collocation branch
        # --------------------------------------------------------------------
        if payload["_related_type"] == "collocation":
            coll_txt = payload["text"]
            tokens = coll_txt.split()

            # ----- xml:id (prefix-normalized, abbrev-aware) -----
            id_parts = [self._token_to_id_part(t) for t in tokens]
            rel_id = "_".join(p for p in id_parts if p)

            # Build <entry> and <form type="collocation">
            rel = ET.Element("entry", {
                f"{{{self.XML_NS}}}id": rel_id,
                "type": "relatedEntry",
                f"{{{self.XML_NS}}}lang": "ang",
            })
            f = ET.SubElement(rel, "form", {"type": "collocation"})

            # Build one <orth> per token, with +/±, and abbreviations
            for t in tokens:
                token_prefix = None
                if t and t[0] in ("+", "±"):
                    token_prefix = t[0]
                    core = t[1:].strip()
                else:
                    core = t

                if self._is_abbrev_of_lemma(core):
                    base_word = self._lemma
                    if token_prefix == "+":
                        orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"ge-{base_word}"})
                        ET.SubElement(orth, "lbl", {"expand": "ge-"}).text = "+"
                        seg = ET.SubElement(orth, "seg")
                        ET.SubElement(seg, "ref", {"type": "oRef"}).text = core
                    elif token_prefix == "±":
                        orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"{base_word}, ge-{base_word}"})
                        ET.SubElement(orth, "lbl", {"expand": "ge-_optional"}).text = "±"
                        seg = ET.SubElement(orth, "seg")
                        ET.SubElement(seg, "ref", {"type": "oRef"}).text = core
                    else:
                        orth = ET.SubElement(f, "orth")
                        ET.SubElement(orth, "ref", {"type": "oRef"}).text = core
                else:
                    base_word = core
                    if token_prefix == "+":
                        orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"ge-{base_word}"})
                        ET.SubElement(orth, "lbl", {"expand": "ge-"}).text = "+"
                        ET.SubElement(orth, "seg").text = base_word
                    elif token_prefix == "±":
                        orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"{base_word}, ge-{base_word}"})
                        ET.SubElement(orth, "lbl", {"expand": "ge-_optional"}).text = "±"
                        ET.SubElement(orth, "seg").text = base_word
                    else:
                        orth = ET.SubElement(f, "orth")
                        orth.text = base_word

            # ---- collect senses/metamarks, then rewrite ids ----
            ordered = []
            trailing_dots = []

            def _collect(obj):
                if isinstance(obj, ET.Element):
                    if obj.tag in ("form", "usg", "gramGrp", "sense", "metamark"):
                        ordered.append(obj)
                elif isinstance(obj, (list, tuple)):
                    for z in obj:
                        _collect(z)

            for piece in rest:
                _collect(piece)

            old_prefix = f"{main_base}."
            new_prefix = f"{rel_id}."

            def _rewrite_ids(elem):
                if elem.tag == "sense":
                    sid = elem.get(f"{{{self.XML_NS}}}id")
                    if sid and sid.startswith(old_prefix):
                        elem.set(f"{{{self.XML_NS}}}id", sid.replace(old_prefix, new_prefix, 1))
                for c in list(elem):
                    if isinstance(c, ET.Element):
                        _rewrite_ids(c)

            for e in ordered:
                if e.tag == "metamark" and (e.text or "").strip() == ".":
                    trailing_dots.append(e)
                    continue
                if e.tag == "sense":
                    _rewrite_ids(e)
                rel.append(e)

            for d in trailing_dots:
                rel.append(d)

            return rel

        # --------------------------------------------------------------------
        # Oneword branch
        # --------------------------------------------------------------------
        word = payload["text"]  # already stripped of any prefix by the collector

        if payload.get("prefix") == "+":
            rel_id = f"ge-{word}"
        else:
            rel_id = word

        rel = ET.Element("entry", {
            f"{{{self.XML_NS}}}id": rel_id,
            "type": "relatedEntry",
            f"{{{self.XML_NS}}}lang": "ang",
        })

        f = ET.SubElement(rel, "form", {"type": "lemma"})
        if payload.get("prefix") == "+":
            orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"ge-{word}"})
            ET.SubElement(orth, "lbl", {"expand": "ge-"}).text = "+"
            ET.SubElement(orth, "seg").text = word
        elif payload.get("prefix") == "±":
            orth = ET.SubElement(f, "orth", {"extent": "prefix", "expand": f"{word}, ge-{word}"})
            ET.SubElement(orth, "lbl", {"expand": "ge-_optional"}).text = "±"
            ET.SubElement(orth, "seg").text = word
        else:
            orth = ET.SubElement(f, "orth")
            orth.text = word

        # collect senses etc. and rewrite ids to use rel_id
        ordered = []
        trailing_dots = []

        def _collect2(obj):
            if isinstance(obj, ET.Element):
                if obj.tag in ("form", "usg", "gramGrp", "sense", "metamark"):
                    ordered.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _collect2(z)

        for piece in rest:
            _collect2(piece)

        old_prefix = f"{main_base}."
        new_prefix = f"{rel_id}."

        def _rewrite_ids2(elem):
            if elem.tag == "sense":
                sid = elem.get(f"{{{self.XML_NS}}}id")
                if sid and sid.startswith(old_prefix):
                    elem.set(f"{{{self.XML_NS}}}id", sid.replace(old_prefix, new_prefix, 1))
            for c in list(elem):
                if isinstance(c, ET.Element):
                    _rewrite_ids2(c)

        for e in ordered:
            if e.tag == "metamark" and (e.text or "").strip() == ".":
                trailing_dots.append(e)
                continue
            if e.tag == "sense":
                _rewrite_ids2(e)
            rel.append(e)

        for d in trailing_dots:
            rel.append(d)

        return rel

    # ---------------- build the entry ----------------
    def entry(self, children):
        lemma = self._lemma or "UNKNOWN"
        prefix = self._prefix
        has_qm = self._has_qm

        entry = ET.Element("entry", {
            f"{{{self.XML_NS}}}id": lemma,
            "type": "mainEntry",
            f"{{{self.XML_NS}}}lang": "ang",
        })
        form = ET.SubElement(entry, "form", {"type": "lemma"})
        orth = ET.SubElement(form, "orth")

        if prefix == '+':
            orth.set("extent", "full")
            orth.set("expand", f"ge-{lemma}")
            lbl = ET.SubElement(orth, "lbl", {"expand": "ge-"})
            lbl.text = "+"
            ET.SubElement(orth, "seg").text = lemma
        elif prefix == '±':
            orth.set("extent", "full")
            orth.set("expand", f"{lemma}, ge-{lemma}")
            lbl = ET.SubElement(orth, "lbl", {"expand": "ge-_optional"})
            lbl.text = "±"
            ET.SubElement(orth, "seg").text = lemma
        else:
            orth.text = lemma

        # add a lemma-level note (...resp=author...) if the headword carried a qm
        headword_qm = False
        def detect_headword_qm(obj):
            nonlocal headword_qm
            if headword_qm:
                return
            if isinstance(obj, dict) and obj.get("_headword_qm"):
                headword_qm = True
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    detect_headword_qm(z)

        for ch in children:
            detect_headword_qm(ch)

        if headword_qm:
            ET.SubElement(form, "note", {"cert": "low", "resp": "author"}).text = "?"

        # Look for a request to add punctuation after the lemma orth (from orth_variant)
        lemma_punct = None
        def _find_punct(obj):
            nonlocal lemma_punct
            if lemma_punct:
                return
            if isinstance(obj, dict) and "_lemma_punct" in obj:
                lemma_punct = obj["_lemma_punct"]
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _find_punct(z)
        for ch in children:
            _find_punct(ch)

        if lemma_punct:
            orth.tail = (orth.tail or "") + lemma_punct

        # Append entry-level <usg> and <gramGrp> in the order they appear
        post_form_ordered = []


        def _collect_post_form(obj):
            if isinstance(obj, ET.Element):
                if obj.tag in ("form", "usg", "gramGrp", "xr"):
                    post_form_ordered.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _collect_post_form(z)

        for ch in children:
            _collect_post_form(ch)

        for el in post_form_ordered:
            entry.append(el)

        # append any <sense> elements produced by sense_section()
        trailing_entry_dots = []

        def _collect(obj):
            if isinstance(obj, ET.Element):
                if obj.tag == "sense":
                    entry.append(obj)
                elif obj.tag == "metamark" and (obj.text or "").strip() == ".":
                    trailing_entry_dots.append(obj)  # place after all senses
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _collect(z)

        for ch in children:
            _collect(ch)
        
        for dot in trailing_entry_dots:
            entry.append(dot)

        def _collect_nested_entries(obj, acc):
            if isinstance(obj, ET.Element) and obj.tag == "entry":
                t = (obj.get("type") or "").strip()
                if t in ("homonymicEntry", "relatedEntry"):
                    acc.append(obj)
            elif isinstance(obj, (list, tuple)):
                for z in obj:
                    _collect_nested_entries(z, acc)

        nested_entries = []
        for ch in children:
            _collect_nested_entries(ch, nested_entries)

        for e in nested_entries:
            entry.append(e)


        # clear state for next entry
        self._lemma = None
        self._prefix = None
        self._has_qm = False
        self._variants = []

        # return pretty XML string
        rough = ET.tostring(entry, encoding="unicode")
        pretty = minidom.parseString(rough).toprettyxml(indent="  ", newl="\n")
        pretty = pretty.split('\n', 1)[1]  
        return pretty.strip()

    def start(self, children):
        for ch in children:
            if isinstance(ch, str) and ch.strip().startswith("<entry"):
                return ch
        fallback = ET.Element("entry", {
            f"{{{self.XML_NS}}}id": "UNKNOWN",
            "type": "mainEntry",
            f"{{{self.XML_NS}}}lang": "ang",
        })
        pretty = minidom.parseString(ET.tostring(fallback, encoding="unicode")).toprettyxml(indent="  ", newl="\n")
        return pretty.split('\n', 1)[1].strip()


class DictionaryParser:
    """
   parser class for dictionary entries.
    """

    def __init__(self):
        try:
            self.parser = Lark(GRAMMAR, parser='earley', debug=False)
            self.transformer = DictionaryTransformer()
            print("Parser initialized successfully!")
        except Exception as e:
            print(f"Error initializing parser: {e}")
            self.parser = None
            self.transformer = None
    
    @staticmethod
    def _safe_comment_text(s: str) -> str:
        return (s or "").replace("--", "—")
    
    @staticmethod
    def _strip_ws(elem):

        if elem.text is not None and elem.text.strip() == "":
            elem.text = None
        for c in list(elem):
            DictionaryParser._strip_ws(c)
            if c.tail is not None and c.tail.strip() == "":
                c.tail = None

    def parse_text(self, text):
        """
        Parse dictionary entry text and return structured data.

        Args:
            text (str): Raw dictionary entry text

        Returns:
            dict: Parsed dictionary entry structure
        """
        if not self.parser:
            return {"error": "Parser not initialized"}

        try:
            # Clean and normalize text
            cleaned_text = (
                text
                .replace('\u00A0', ' ')  # Non-breaking space
                .replace('\u2018', "'")   # Left single quote
                .replace('\u2019', "'")   # Right single quote
                .replace('\u201C', '"')   # Left double quote
                .replace('\u201D', '"')   # Right double quote
                .replace('\n', ' ')       # Replace newlines with spaces
                .replace('\r', ' ')       # Replace carriage returns with spaces
            )
            
            # Normalize multiple spaces to single space
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            parse_tree = self.parser.parse(cleaned_text)


            if self.transformer:
                transformed_result = self.transformer.transform(parse_tree)
                return {
                    "success": True, 
                    "parse_tree": parse_tree,  
                    "transformed": transformed_result,
                    "cleaned_text": cleaned_text
                }
            else:
                return {
                    "success": True, 
                    "parse_tree": parse_tree,
                    "transformed": None,
                    "cleaned_text": cleaned_text
                }

        except ParseError as e:
            return {"success": False, "error": f"Parse error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

    def parse_dictionary_file(self, filename):
        """
        Parse the file containing any number of entries and create output files.
        
        Args:
            filename (str): Path to the dictionary file
            
        Returns:
            dict: Dictionary with parsing statistics
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return {"error": f"File not found: {filename}"}
        except Exception as e:
            return {"error": f"Error reading file: {e}"}

        # Split entries by double newlines 
        entries = [entry.strip() for entry in content.split('\n\n') if entry.strip()]
        
        total_entries = len(entries)
        successful_parses = 0
        failed_entries = []
        
        # Create base filename for output files
        base_name = os.path.splitext(filename)[0]
        parse_trees_file = f"{base_name}_parse_trees.txt"
        transformed_file = f"{base_name}_transformed.txt"
        failed_file = f"{base_name}_failed.txt"
        
        print(f"Processing {total_entries} entries...")
        print(f"Output files will be:")
        print(f"  - Parse trees: {parse_trees_file}")
        print(f"  - Transformed results: {transformed_file}")
        print(f"  - Failed entries: {failed_file}")
        
        # Process entries and collect results
        successful_results = []
        
        for i, entry in enumerate(entries):
            if i % 100 == 0:
                print(f"Processed {i}/{total_entries} entries")
                
            result = self.parse_text(entry)
            
            if result["success"]:
                successful_parses += 1
                successful_results.append({
                    "entry_number": i + 1,
                    "original_text": entry,
                    "cleaned_text": result.get("cleaned_text", ""),
                    "parse_tree": result["parse_tree"],
                    "transformed_result": result["transformed"]
                })
            else:
                failed_entries.append({
                    "entry_number": i + 1,
                    "entry_text": entry,
                    "error": result["error"],
                })
        
        # Calculate final statistics
        success_rate = (successful_parses / total_entries) * 100 if total_entries > 0 else 0

        def _indent_block(s: str, pad: str = '      '):  
            lines = s.splitlines()
            return '\n'.join((pad + ln if ln.strip() else ln) for ln in lines)
        
        # Write parse trees file
        with open(parse_trees_file, 'w', encoding='utf-8') as trees_f:
            trees_f.write("PARSE TREES FOR SUCCESSFULLY PARSED ENTRIES\n")
            trees_f.write("=" * 50 + "\n")
            trees_f.write(f"Total entries processed: {total_entries}\n")
            trees_f.write(f"Successfully parsed: {successful_parses}\n")
            trees_f.write(f"Success rate: {success_rate:.2f}%\n")
            trees_f.write("=" * 50 + "\n\n")
            
            for result_data in successful_results:
                trees_f.write(f"ENTRY #{result_data['entry_number']}\n")
                trees_f.write("-" * 20 + "\n")
                trees_f.write(f"Entry text: {result_data['original_text']}\n\n")
                trees_f.write("Parse tree:\n")
                trees_f.write(format_tree_simple(result_data['parse_tree']))
                trees_f.write("\n\n" + "=" * 50 + "\n\n")
        

        # --- Write transformed results file ---
        from xml.etree import ElementTree as ET

        NS = "http://www.tei-c.org/ns/1.0"
        ET.register_namespace("", NS)

        # Build TEI skeleton
        tei = ET.Element(f"{{{NS}}}TEI", {"type": "lex-0"})
        teiHeader = ET.SubElement(tei, f"{{{NS}}}teiHeader")
        fileDesc = ET.SubElement(teiHeader, f"{{{NS}}}fileDesc")
        titleStmt = ET.SubElement(fileDesc, f"{{{NS}}}titleStmt")
        ET.SubElement(titleStmt, f"{{{NS}}}title")
        publicationStmt = ET.SubElement(fileDesc, f"{{{NS}}}publicationStmt")
        ET.SubElement(publicationStmt, f"{{{NS}}}publisher")
        availability = ET.SubElement(publicationStmt, f"{{{NS}}}availability")
        ET.SubElement(availability, f"{{{NS}}}licence")

        profileDesc = ET.SubElement(teiHeader, f"{{{NS}}}profileDesc")
        langUsage = ET.SubElement(profileDesc, f"{{{NS}}}langUsage")
        ET.SubElement(langUsage, f"{{{NS}}}language",
                    {"role": "sourceLanguage", "ident": "ang"})

        text = ET.SubElement(tei, f"{{{NS}}}text")
        body = ET.SubElement(text, f"{{{NS}}}body")

        # Add the stats as an XML comment INSIDE <body>
        stats_banner = (
            "TRANSFORMED RESULTS FOR SUCCESSFULLY PARSED ENTRIES\n"
            + "="*50 + "\n"
            + f"Total entries processed: {total_entries}\n"
            + f"Successfully parsed: {successful_parses}\n"
            + f"Success rate: {success_rate:.2f}%\n"
            + "="*50
        )
        body.append(ET.Comment(stats_banner))

        # Append each entry as parsed XML
        for r in successful_results:
            # entry-level comment
            entry_comment = f"ENTRY #{r['entry_number']}\n--------------------\nEntry text: {self._safe_comment_text(r['original_text'])}"
            body.append(ET.Comment(entry_comment))

            # parse the entry string to an element
            el = ET.fromstring(r["transformed_result"])
            self._strip_ws(el)          
            body.append(el)

        ET.indent(tei, space="  ")

        final_xml = ET.tostring(tei, encoding="utf-8", xml_declaration=True).decode("utf-8")

        pi_block = (
            '<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml"\n'
            '\tschematypens="http://purl.oclc.org/dsdl/schematron"?>\n'
            '<?xml-model href="https://raw.githubusercontent.com/DARIAH-ERIC/lexicalresources/master/Schemas/TEILex0/out/TEILex0.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
        )

        with open(transformed_file, "w", encoding="utf-8") as trans_f:

            decl, rest = final_xml.split("\n", 1)
            trans_f.write(decl + "\n" + pi_block + rest)


        
        # Write failed entries file
        with open(failed_file, 'w', encoding='utf-8') as failed_f:
            failed_f.write("FAILED ENTRIES WITH ERROR MESSAGES\n")
            failed_f.write("=" * 50 + "\n")
            failed_f.write(f"Total entries processed: {total_entries}\n")
            failed_f.write(f"Failed to parse: {len(failed_entries)}\n")
            failed_f.write(f"Failure rate: {100 - success_rate:.2f}%\n")
            failed_f.write("=" * 50 + "\n\n")
            
            for failed_entry in failed_entries:
                failed_f.write(f"ENTRY #{failed_entry['entry_number']}\n")
                failed_f.write("-" * 20 + "\n")
                failed_f.write(f"Original text: {failed_entry['entry_text']}\n\n")
                error_lines = failed_entry['error'].split('\n')
                if len(error_lines) > 50:
                    limited_error = '\n'.join(error_lines[:50]) + '\n... (error message truncated - showing first 50 lines)'
                else:
                    limited_error = failed_entry['error']
                failed_f.write(f"Error: {limited_error}\n")
                failed_f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"\nFiles created successfully!")
        print(f"  - {parse_trees_file}: {successful_parses} parse trees")
        print(f"  - {transformed_file}: {successful_parses} transformed entries")
        print(f"  - {failed_file}: {len(failed_entries)} failed entries")
        
        return {
            "total_entries": total_entries,
            "successful_parses": successful_parses,
            "failed_parses": len(failed_entries),
            "success_rate_percentage": round(success_rate, 2),
            "output_files": {
                "parse_trees": parse_trees_file,
                "transformed": transformed_file,
                "failed": failed_file
            }
        }
    
    def _extract_problematic_element(self, error_msg):
        """
        Extract the problematic element from the error message.
        
        Args:
            error_msg (str): The error message from parsing
            
        Returns:
            str: The problematic element or pattern
        """
        # Try to extract the unexpected token or pattern from common error patterns
        if "Unexpected token" in error_msg:
            match = re.search(r"Unexpected token Token\('(\w+)', '([^']+)'\)", error_msg)
            if match:
                return f"Token: {match.group(1)} ('{match.group(2)}')"
        
        if "Expected" in error_msg:
            match = re.search(r"Expected: (.+?)(?:\n|$)", error_msg)
            if match:
                return f"Expected: {match.group(1).strip()}"
        
        # Return error msg
        return error_msg

    def parse_file(self, filename):
        """
        Parse dictionary entries from a file.

        Args:
            filename (str): Path to the file containing dictionary entries

        Returns:
            dict: Parsed results
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_text(content)
        except FileNotFoundError:
            return {"error": f"File not found: {filename}"}
        except Exception as e:
            return {"error": f"Error reading file: {e}"}

    def get_parse_tree_only(self, text):
        """
        Get just the parse tree without transformation (useful for debugging).

        Args:
            text (str): Raw dictionary entry text

        Returns:
            str: Pretty-printed parse tree
        """
        if not self.parser:
            return "Parser not initialized"
        
        try:
            cleaned_text = (
                text
                .replace('\u00A0', ' ')
                .replace('\u2018', "'")
                .replace('\u2019', "'")
                .replace('\u201C', '"')
                .replace('\u201D', '"')
                .replace('\n', ' ')       
                .replace('\r', ' ')       
            )
            
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            parse_tree = self.parser.parse(cleaned_text)
            return format_tree_simple(parse_tree)
        except ParseError as e:
            return f"Parse error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

def main():
    """
    Main function for batch processing dictionary files.
    """
    parser = DictionaryParser()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"Processing dictionary file: {filename}")
        
        results = parser.parse_dictionary_file(filename)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return
        
        print("\n" + "="*50)
        print("PARSING RESULTS")
        print("="*50)
        print(f"Total entries: {results['total_entries']}")
        print(f"Successfully parsed: {results['successful_parses']}")
        print(f"Failed to parse: {results['failed_parses']}")
        print(f"Success rate: {results['success_rate_percentage']}%")
        
        print("\nOutput files created:")
        for file_type, filename in results['output_files'].items():
            print(f"  - {file_type}: {filename}")
            
    else:
        print("To process a dictionary file, run:")
        print("python dictionary_parser.py entries.txt")

if __name__ == "__main__":
    main()