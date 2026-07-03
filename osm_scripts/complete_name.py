import osmium
import sys
import os
import re
import sqlite3
import unicodedata
from functools import lru_cache

# Import Chinese romanization
try:
    from hanzi2reading.reading import Reading
    from hanzi2reading.pinyin import get as pinyin
    reading = Reading()
    has_hanzi2reading = True
    # print("Using hanzi2reading for Chinese romanization")
except ImportError:
    has_hanzi2reading = False

# Import Japanese romanization
try:
    import pykakasi
    kakasi = pykakasi.kakasi()
    has_pykakasi = True
    # print("Using pykakasi for Japanese romanization")
except ImportError:
    has_pykakasi = False

# Import Japanese romanization (janome as fallback)
try:
    from janome.tokenizer import Tokenizer as JanomeTokenizer
    janome_tokenizer = JanomeTokenizer()
    has_janome = True
    # print("Using janome for Japanese romanization fallback")
except ImportError:
    has_janome = False

# Import Nepal romanization
try:
    import nepali_roman as nr
    has_nepali_roman = True
    # print("Using nepali_roman for Nepali romanization")
except ImportError:
    has_nepali_roman = False

# Import Hindi romanization
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    has_indic_transliteration = True
    # print("Using indic_transliteration for Hindi romanization")
except ImportError:
    has_indic_transliteration = False

# Import Russian romanization
try:
    import cyrtranslit
    has_cyrtranslit = True
    # print("Using cyrtranslit for Russian romanization")
except ImportError:
    has_cyrtranslit = False

# Import various romanization tools
try:
    from unidecode import unidecode
    has_unidecode = True
    # print("Using unidecode for generic romanization fallback")
except ImportError:
    has_unidecode = False

try:
    import pyewts
    wylie_converter = pyewts.pyewts()
    has_pyewts = True
    # print("Using pyewts for Tibetan romanization")
except ImportError:
    has_pyewts = False

# Import OpenCC for Simplified -> Traditional (Taiwan) conversion of name:zh
try:
    import opencc
    _opencc_s2twp = opencc.OpenCC('s2twp')
    has_opencc = True
    # print("Using OpenCC s2twp for Simplified->Traditional conversion")
except Exception:
    has_opencc = False

# OpenCC jp2t: Japanese shinjitai kanji -> Traditional (for name:zh from name:ja).
# Only the official opencc wheel ships jp2t; degrade to no-op if unavailable.
try:
    _opencc_jp2t = opencc.OpenCC('jp2t')
    has_opencc_jp2t = True
except Exception:
    has_opencc_jp2t = False

# Import PyICU for generic any-script -> Latin transliteration (name:en fallback).
# Better quality than unidecode for Hangul/Thai/Arabic/Greek; unidecode remains
# the fallback when PyICU is not installed.
try:
    import icu
    _icu_any_latin = icu.Transliterator.createInstance('Any-Latin')
    _icu_latin_ascii = icu.Transliterator.createInstance('Latin-ASCII')
    has_icu = True
except Exception:
    has_icu = False

# Determine native script language from environment variable or default to zh
NATIVE_LANG = os.environ.get('NATIVE_LANG', 'zh')

# =============================================================================
# Offline Wikidata label cache (optional, built by build_wikidata_cache.py).
# Runtime is fully offline and O(1): we open the SQLite read-only once and look
# up labels by the object's wikidata=Q... tag. If the cache file is absent the
# pipeline behaves exactly as before (has_wikidata=False).
# =============================================================================
WIKIDATA_CACHE = os.environ.get('WIKIDATA_CACHE', '')
_wikidata_conn = None
has_wikidata = False
if WIKIDATA_CACHE and os.path.exists(WIKIDATA_CACHE):
    try:
        _wikidata_conn = sqlite3.connect(f'file:{WIKIDATA_CACHE}?mode=ro', uri=True)
        has_wikidata = True
        # print(f"Using Wikidata label cache: {WIKIDATA_CACHE}")
    except Exception:
        _wikidata_conn = None
        has_wikidata = False

_QID_RE = re.compile(r'^Q\d+$')


def wikidata_label(tags, lang, key='wikidata'):
    """Return a cached Wikidata label for tags[key], or None.

    lang must be 'en' or 'zh' (internal, not user input -> safe to interpolate).
    The 'zh' column is already Traditional/Taiwan (normalized at cache-build time).
    key may also be 'brand:wikidata'; values can be ';'-separated QID lists, in
    which case the first valid QID is used.
    """
    if not has_wikidata:
        return None
    for part in tags.get(key, '').split(';'):
        qid = part.strip()
        if _QID_RE.match(qid):
            break
    else:
        return None
    try:
        cur = _wikidata_conn.execute(
            f"SELECT {lang} FROM labels WHERE qid = ?", (qid,))
        row = cur.fetchone()
        if row and row[0]:
            label = row[0]
            if key != 'wikidata':
                # Brand labels sometimes carry a disambiguator suffix,
                # e.g. "Bamiyan (連鎖餐廳)" - not part of the name
                label = _WP_PAREN_RE.sub('', label).strip() or label
            return label
    except Exception:
        pass
    return None


# Trailing parenthetical disambiguation in Wikipedia titles: "玉山 (臺灣)" -> "玉山"
_WP_PAREN_RE = re.compile(r'\s*[(（][^()（）]*[)）]\s*$')


def wikipedia_title(tags, lang):
    """Extract the article title for lang from wikipedia tags, or None.

    Handles both forms: wikipedia=<lang>:<title> and wikipedia:<lang>=<title>.
    The title itself is a curated name in that language (fully offline), with
    any trailing parenthetical disambiguation stripped.
    """
    v = tags.get('wikipedia', '').strip()
    if v.lower().startswith(lang + ':'):
        title = v[len(lang) + 1:]
    else:
        title = tags.get('wikipedia:' + lang, '').strip()
    if not title:
        return None
    title = _WP_PAREN_RE.sub('', title.replace('_', ' ')).strip()
    return title or None


@lru_cache(maxsize=65536)
def to_traditional(text):
    """Convert Simplified Chinese to Traditional (Taiwan, s2twp). No-op if unavailable."""
    if not text or not has_opencc:
        return text
    try:
        return _opencc_s2twp.convert(text)
    except Exception:
        return text


@lru_cache(maxsize=65536)
def to_traditional_jp(text):
    """Convert Japanese shinjitai kanji to Traditional (jp2t). No-op if unavailable."""
    if not text or not has_opencc_jp2t:
        return text
    try:
        return _opencc_jp2t.convert(text)
    except Exception:
        return text


# Japanese kanji place names often embed a possessive/counter kana between Han
# characters. Chinese renderings conventionally map ノ/の -> 之 and drop ヶ/ヵ/ケ
# (芦ノ湖 -> 蘆之湖, 青木ケ原 -> 青木原). Applied before the Chinese+Latin-only check,
# so names with any other kana are still rejected.
_JA_TO_ZH_TRANS = str.maketrans({'ノ': '之', 'の': '之',
                                 'ヶ': None, 'ヵ': None, 'ケ': None})


def ja_name_to_zh(text):
    """Derive a name:zh candidate from a Japanese kanji name, or None.

    Maps ノ/の -> 之, drops ヶ/ヵ/ケ, requires the result to be Chinese+Latin
    only, then converts shinjitai -> Traditional (jp2t) and normalizes with s2twp.
    """
    if not text:
        return None
    t = text.translate(_JA_TO_ZH_TRANS)
    if is_chinese_latin_only(t):
        return to_traditional(to_traditional_jp(t))
    return None


def _strip_diacritics(text):
    """Strip combining marks (e.g. pinyin tone marks: Yú -> Yu)."""
    nfd = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return unicodedata.normalize('NFC', stripped)


def _is_han_char(ch):
    """True for CJK ideographs (Chinese / Japanese kanji)."""
    return ('\u4e00' <= ch <= '\u9fff') or ('\u3400' <= ch <= '\u4dbf')

# Dictionary for Urdu/Hindi common terms correction
URDU_REPLACEMENTS = {
    'Shry': 'Shri',
    'Prtp': 'Pratap',
    'Khlj': 'College',
    'Msjd': 'Masjid',
    'N`mn': 'Numan',  # Approximate
    'Sr': 'Sir',
    'Syd': 'Syed',
    'Abd': 'Abad',
    'Sykhttr': 'Sector',
    'Sry': 'Sri',
    'Ngr': 'Nagar',
    'Rylwy': 'Railway',
    'Sttyshn': 'Station',
    'Qdy': 'Qazi',
    'Bg': 'Bagh',
    'Sl': 'Asal',      # Asal (Actual)
    'Zmyny': 'Zamini', # Zamini (Ground)
    'Pwzyshn': 'Position',
    "Ly'n": 'Line',
    'Ly\'n': 'Line'    # Duplicate for safety with escape chars
}

def apply_urdu_replacements(text):
    words = text.split()
    new_words = []
    for w in words:
        # Check capitalized version in dict
        if w in URDU_REPLACEMENTS:
            new_words.append(URDU_REPLACEMENTS[w])
        elif w.capitalize() in URDU_REPLACEMENTS:
             new_words.append(URDU_REPLACEMENTS[w.capitalize()])
        else:
            new_words.append(w)
    return ' '.join(new_words)


# =============================================================================
# Romanization helper functions for each language
# =============================================================================

def _romanize_han_run(run):
    """Romanize a pure-Han run to tone-free, space-joined, capitalized pinyin."""
    segments = reading.get(run)
    if not segments:
        return None
    roman = ' '.join(pinyin(s).capitalize() for s in segments)
    roman = _strip_diacritics(roman).strip()
    return roman or None


@lru_cache(maxsize=65536)
def romanize_zh(text):
    """Romanize Chinese text using hanzi2reading.

    Splits the text into Han / non-Han runs so that interspersed digits and Latin
    (e.g. the "101" in "臺北101") are preserved verbatim instead of being dropped,
    and strips pinyin tone diacritics (Yú -> Yu) for clean English-reader output.
    Non-Han runs that are themselves non-ASCII (e.g. kana in a mixed name) are
    transliterated with unidecode so no non-Latin text leaks into the result.
    """
    if not has_hanzi2reading:
        return None
    try:
        parts = []
        run = ''
        run_is_han = None
        for ch in text:
            ih = _is_han_char(ch)
            if run_is_han is None:
                run, run_is_han = ch, ih
            elif ih == run_is_han:
                run += ch
            else:
                parts.append((run, run_is_han))
                run, run_is_han = ch, ih
        if run:
            parts.append((run, run_is_han))

        out = []
        for run, is_han in parts:
            if is_han:
                roman = _romanize_han_run(run)
                if roman:
                    out.append(roman)
            else:
                piece = run.strip()
                if piece and not piece.isascii() and has_unidecode:
                    piece = unidecode(piece).strip()
                if piece:
                    out.append(piece)
        result = ' '.join(' '.join(out).split())
        return result if result and is_latin_text(result) else None
    except Exception:
        return None


def romanize_ja(text):
    """Romanize Japanese text using pykakasi."""
    if not has_pykakasi:
        return None
    try:
        result = kakasi.convert(text)
        romanized = ' '.join(item['hepburn'].capitalize() for item in result if item['hepburn'])
        if romanized:
            # Normalize spaces
            romanized = ' '.join(romanized.split())
            # Fix parentheses spacing
            romanized = romanized.replace('( ', '(').replace(' )', ')')
            if is_latin_text(romanized):
                return romanized
    except Exception:
        pass
    return None


def romanize_ja_janome(text):
    """Romanize Japanese text using janome (fallback for pykakasi)."""
    if not has_janome:
        return None
    try:
        # Katakana to romaji mapping
        katakana_romaji = {
            'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o',
            'カ': 'ka', 'キ': 'ki', 'ク': 'ku', 'ケ': 'ke', 'コ': 'ko',
            'サ': 'sa', 'シ': 'shi', 'ス': 'su', 'セ': 'se', 'ソ': 'so',
            'タ': 'ta', 'チ': 'chi', 'ツ': 'tsu', 'テ': 'te', 'ト': 'to',
            'ナ': 'na', 'ニ': 'ni', 'ヌ': 'nu', 'ネ': 'ne', 'ノ': 'no',
            'ハ': 'ha', 'ヒ': 'hi', 'フ': 'fu', 'ヘ': 'he', 'ホ': 'ho',
            'マ': 'ma', 'ミ': 'mi', 'ム': 'mu', 'メ': 'me', 'モ': 'mo',
            'ヤ': 'ya', 'ユ': 'yu', 'ヨ': 'yo',
            'ラ': 'ra', 'リ': 'ri', 'ル': 'ru', 'レ': 're', 'ロ': 'ro',
            'ワ': 'wa', 'ヲ': 'wo', 'ン': 'n',
            'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
            'ザ': 'za', 'ジ': 'ji', 'ズ': 'zu', 'ゼ': 'ze', 'ゾ': 'zo',
            'ダ': 'da', 'ヂ': 'ji', 'ヅ': 'zu', 'デ': 'de', 'ド': 'do',
            'バ': 'ba', 'ビ': 'bi', 'ブ': 'bu', 'ベ': 'be', 'ボ': 'bo',
            'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po',
            'キャ': 'kya', 'キュ': 'kyu', 'キョ': 'kyo',
            'シャ': 'sha', 'シュ': 'shu', 'ショ': 'sho',
            'チャ': 'cha', 'チュ': 'chu', 'チョ': 'cho',
            'ニャ': 'nya', 'ニュ': 'nyu', 'ニョ': 'nyo',
            'ヒャ': 'hya', 'ヒュ': 'hyu', 'ヒョ': 'hyo',
            'ミャ': 'mya', 'ミュ': 'myu', 'ミョ': 'myo',
            'リャ': 'rya', 'リュ': 'ryu', 'リョ': 'ryo',
            'ギャ': 'gya', 'ギュ': 'gyu', 'ギョ': 'gyo',
            'ジャ': 'ja', 'ジュ': 'ju', 'ジョ': 'jo',
            'ビャ': 'bya', 'ビュ': 'byu', 'ビョ': 'byo',
            'ピャ': 'pya', 'ピュ': 'pyu', 'ピョ': 'pyo',
            'ッ': '', 'ー': '',  # Handle small tsu and long vowel mark
        }
        
        words = []
        for token in janome_tokenizer.tokenize(text):
            reading = token.reading
            if reading and reading != '*':
                # Convert katakana reading to romaji
                romaji = ''
                i = 0
                while i < len(reading):
                    # Check for two-character combinations first
                    if i + 1 < len(reading) and reading[i:i+2] in katakana_romaji:
                        romaji += katakana_romaji[reading[i:i+2]]
                        i += 2
                    elif reading[i] in katakana_romaji:
                        romaji += katakana_romaji[reading[i]]
                        i += 1
                    else:
                        romaji += reading[i]
                        i += 1
                if romaji:
                    words.append(romaji.capitalize())
            else:
                # No reading available, keep original
                words.append(token.surface)
        
        if words:
            result = ' '.join(words)
            # Normalize spaces
            result = ' '.join(result.split())
            result = result.replace('( ', '(').replace(' )', ')')
            if is_latin_text(result):
                return result
    except Exception:
        pass
    return None


_DEVANAGARI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')


def romanize_ne(text):
    """Romanize Nepali text using nepali_roman.

    nepali_roman passes non-Devanagari characters through unchanged (and keeps
    Devanagari digits), so the output is validated: translate the digits and
    reject any result that is not Latin.
    """
    if not has_nepali_roman:
        return None
    try:
        raw_roman = nr.romanize_text(text)
        if raw_roman:
            roman = ' '.join(word.capitalize() for word in raw_roman.split())
            roman = roman.translate(_DEVANAGARI_DIGITS)
            if is_latin_text(roman):
                return roman
    except Exception:
        pass
    return None


def romanize_hi(text):
    """Romanize Hindi/Devanagari text using indic_transliteration."""
    if not has_indic_transliteration:
        return None
    try:
        raw_roman = transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
        if raw_roman and raw_roman != text:
            roman = ' '.join(word.capitalize() for word in raw_roman.split())
            roman = roman.translate(_DEVANAGARI_DIGITS)
            if is_latin_text(roman):
                return roman
    except Exception:
        pass
    return None


def romanize_bo(text):
    """Romanize Tibetan text using pyewts (Wylie transliteration)."""
    if not has_pyewts:
        return None
    try:
        wylie = wylie_converter.toWylie(text)
        if wylie and wylie != text:
            roman = ' '.join(word.capitalize() for word in wylie.split())
            if is_latin_text(roman):
                return roman
    except Exception:
        pass
    return None


@lru_cache(maxsize=65536)
def romanize_generic(text):
    """Generic any-script romanization fallback: PyICU first, then unidecode."""
    # PyICU Any-Latin: much better Hangul/Thai/Arabic/Greek quality than unidecode
    if has_icu:
        try:
            roman = _icu_any_latin.transliterate(text)
            # Drop the soft/hard-sign marks Any-Latin emits for Cyrillic (ʹ ʺ)
            # BEFORE Latin-ASCII turns them into apostrophes; real apostrophes
            # in the input are untouched (Gorbolʹnica -> Gorbolnica)
            roman = roman.replace('ʹ', '').replace('ʺ', '')
            roman = _icu_latin_ascii.transliterate(roman)
            # Only accept a complete transliteration (no non-Latin leftovers)
            if roman and roman.strip() and roman != text and is_latin_text(roman):
                return ' '.join(word.capitalize() for word in roman.split())
        except Exception:
            pass
    if not has_unidecode:
        return None
    try:
        ud_roman = unidecode(text)
        if ud_roman and ud_roman.strip() and ud_roman != text:
            ud_roman = ' '.join(word.capitalize() for word in ud_roman.split())
            return apply_urdu_replacements(ud_roman)
    except Exception:
        pass
    return None


def _capitalize_token(word):
    """Capitalize the first letter of each hyphen-separated part of a word,
    skipping leading punctuation (quotes); the rest is lowercased."""
    parts = []
    for part in word.split('-'):
        for i, ch in enumerate(part):
            if ch.isalpha():
                part = part[:i] + ch.upper() + part[i + 1:].lower()
                break
        parts.append(part)
    return '-'.join(parts)


def romanize_ru(text):
    """Romanize Russian/Cyrillic text using cyrtranslit.

    cyrtranslit renders ь/ъ (and the tail of ы) as apostrophes - drop them for
    clean map labels (Кичи-Балык -> Kichi-Balyk, not Kichi-baly'k).
    """
    if not has_cyrtranslit:
        return None
    try:
        result = cyrtranslit.to_latin(text, "ru")
        if result and result != text:
            result = result.replace("'", "")
            roman = ' '.join(_capitalize_token(w) for w in result.split())
            if is_latin_text(roman):
                return roman
    except Exception:
        pass
    return None


def extract_latin_part(text):
    """Extract Latin/English parts from mixed-script text."""
    # Matches: Latin chars (incl accents), numbers, common punctuation
    latin_re = r'[A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\s\.\,\-\(\)\'\&]+'
    matches = re.findall(latin_re, text)
    
    # Combine matches and clean up
    candidate = " ".join(matches).strip()
    candidate = re.sub(r'\s+', ' ', candidate)
    candidate = re.sub(r'^[\-\s]+|[\-\s]+$', '', candidate)
    
    # Validate the candidate
    if candidate and any(c.isalpha() for c in candidate) and len(candidate) > 2:
        return candidate
    return None


def has_chinese_chars(text):
    """Check if text contains Chinese characters."""
    return any('\u4e00' <= char <= '\u9fff' for char in text)


def is_chinese_latin_only(text):
    """Check if text contains only Chinese and Latin characters (no Japanese kana)."""
    if not text:
        return False
    for char in text:
        # Allow ASCII (includes Latin letters, digits, punctuation)
        if ord(char) < 128:
            continue
        # Allow Latin Extended (accented Latin characters)
        if '\u00C0' <= char <= '\u00FF':  # Latin-1 Supplement
            continue
        if '\u0100' <= char <= '\u017F':  # Latin Extended-A
            continue
        if '\u0180' <= char <= '\u024F':  # Latin Extended-B
            continue
        # Allow CJK Unified Ideographs (Chinese characters / Japanese Kanji)
        if '\u4e00' <= char <= '\u9fff':
            continue
        # Allow CJK Unified Ideographs Extension A
        if '\u3400' <= char <= '\u4dbf':
            continue
        # Allow CJK Symbols and Punctuation
        if '\u3000' <= char <= '\u303F':
            continue
        # Reject halfwidth katakana explicitly - it sits inside the Halfwidth
        # and Fullwidth Forms block allowed below
        if '\uFF66' <= char <= '\uFF9F':
            return False
        # Allow Halfwidth and Fullwidth Forms
        if '\uFF00' <= char <= '\uFFEF':
            continue
        # Any other character (including Japanese Hiragana/Katakana) means it's not Chinese+Latin only
        return False
    return True


def has_devanagari_chars(text):
    """Check if text contains Devanagari (Nepali/Hindi) characters."""
    return any('\u0900' <= char <= '\u097F' for char in text)


def has_tibetan_chars(text):
    """Check if text contains Tibetan characters."""
    return any('\u0F00' <= char <= '\u0FFF' for char in text)


def has_arabic_chars(text):
    """Check if text contains Arabic/Urdu characters."""
    return any('\u0600' <= char <= '\u06FF' for char in text)


def has_cyrillic_chars(text):
    """Check if text contains Cyrillic characters."""
    return any('\u0400' <= char <= '\u04FF' for char in text)


def has_non_ascii(text):
    """Check if text contains non-ASCII characters."""
    return any(ord(c) > 127 for c in text)


# =============================================================================
# Language-specific romanization by name:$lang tag
# =============================================================================

def _existing_roman_tag(tags, keys, romanizer=None):
    """Return the first usable pre-existing romanization tag value.

    Mappers sometimes put kana readings or even the original script in these
    tags, so the value is validated; a non-Latin value is fed through the
    language's romanizer instead of being trusted verbatim.
    """
    for k in keys:
        v = tags.get(k, '').strip()
        if v:
            if is_latin_text(v):
                return v
            if romanizer:
                roman = romanizer(v)
                if roman:
                    return roman
    return None


def romanize_by_lang_tag(tags):
    """
    Priority 1: Try to romanize using name:$lang tag with language-specific module.
    Returns romanized string or None if not applicable.
    """
    if NATIVE_LANG == 'zh':
        # Check for existing romanization tags
        roman = _existing_roman_tag(
            tags, ('name:zh_pinyin', 'name:zh-Latn-pinyin', 'name:zh-Latn'), romanize_zh)
        if roman:
            return roman
        # Try romanizing name:zh
        if 'name:zh' in tags:
            # If already ASCII, return as-is
            if tags['name:zh'].isascii():
                return tags['name:zh']
            if has_hanzi2reading:
                return romanize_zh(tags['name:zh'])
    
    elif NATIVE_LANG == 'ja':
        # Check for existing romanization tags
        roman = _existing_roman_tag(
            tags, ('name:ja_rm', 'name:ja-Latn'),
            lambda v: romanize_ja(v) or romanize_ja_janome(v))
        if roman:
            return roman
        # Try romanizing name:ja
        if 'name:ja' in tags:
            if tags['name:ja'].isascii():
                return tags['name:ja']
            if has_pykakasi:
                return romanize_ja(tags['name:ja'])
    
    elif NATIVE_LANG == 'ne':
        # Check for existing romanization tags
        roman = _existing_roman_tag(tags, ('name:ne_rm', 'name:ne-Latn'), romanize_ne)
        if roman:
            return roman
        # Try romanizing name:ne
        if 'name:ne' in tags:
            if tags['name:ne'].isascii():
                return tags['name:ne']
            if has_nepali_roman:
                return romanize_ne(tags['name:ne'])
        # Try name:hi as fallback (Hindi and Nepali both use Devanagari)
        if 'name:hi' in tags:
            if tags['name:hi'].isascii():
                return tags['name:hi']
            # Try nepali_roman first (works for Devanagari)
            if has_nepali_roman:
                result = romanize_ne(tags['name:hi'])
                if result:
                    return result
            # Try indic_transliteration as fallback
            if has_indic_transliteration:
                return romanize_hi(tags['name:hi'])
    
    elif NATIVE_LANG == 'hi':
        # Check for existing romanization tags
        roman = _existing_roman_tag(tags, ('name:hi_rm', 'name:hi-Latn'), romanize_hi)
        if roman:
            return roman
        # Try romanizing name:hi
        if 'name:hi' in tags:
            if tags['name:hi'].isascii():
                return tags['name:hi']
            if has_indic_transliteration:
                return romanize_hi(tags['name:hi'])

    elif NATIVE_LANG == 'ru':
        # Check for existing romanization tags
        roman = _existing_roman_tag(tags, ('name:ru_rm', 'name:ru-Latn'), romanize_ru)
        if roman:
            return roman
        # Try romanizing name:ru
        if 'name:ru' in tags:
            if tags['name:ru'].isascii():
                return tags['name:ru']
            if has_cyrtranslit:
                return romanize_ru(tags['name:ru'])

    return None


def romanize_by_zh_tag(tags):
    """
    Priority 2: Try to romanize using name:zh tag with hanzi2reading.
    Returns romanized string or None if not applicable.
    """
    if 'name:zh' in tags:
        # If already ASCII, return as-is
        if tags['name:zh'].isascii():
            return tags['name:zh']
        if has_hanzi2reading:
            return romanize_zh(tags['name:zh'])
    return None


def romanize_by_combined_rules(name):
    """
    Priority 3: Assume 'name' is in $lang and use combined rules.
    Returns romanized string or None if romanization fails.
    """
    # If name is already ASCII, return as-is
    if name.isascii():
        return name
    
    # If name is Latin-based (e.g. "Häagen-Dazs"), return as-is. Anything else
    # (Hangul, Thai, Greek, kana, ... - not just the scripts with dedicated
    # romanizers) must go through romanization below.
    if is_latin_text(name):
        return name
    
    if NATIVE_LANG == 'zh':
        if has_chinese_chars(name):
            result = romanize_zh(name)
            if result:
                return result
            # Fall back to Latin extraction if romanization fails
            latin_part = extract_latin_part(name)
            if latin_part:
                return latin_part
        # Non-Chinese scripts (Hangul, Thai, ...) or failed romanization:
        # generic transliteration so non-Latin text never leaks into name:en
        return romanize_generic(name) or name
    
    elif NATIVE_LANG == 'ja':
        result = romanize_ja(name)
        if result:
            return result
        # Fall back to janome for Japanese romanization
        result = romanize_ja_janome(name)
        if result:
            return result
        # Fall back to Latin extraction if romanization fails
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        return romanize_generic(name) or name
    
    elif NATIVE_LANG == 'ne':
        # Only feed Devanagari to nepali_roman - it mangles other scripts
        if has_devanagari_chars(name):
            result = romanize_ne(name)
            if result:
                return result
        # Fall back to Latin extraction if romanization fails
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        return romanize_generic(name) or name
    
    elif NATIVE_LANG == 'hi':
        # Try Devanagari transliteration
        result = romanize_hi(name)
        if result:
            return result

        # Try Tibetan characters
        if has_tibetan_chars(name):
            result = romanize_bo(name)
            if result:
                return result

        # Try Arabic/Urdu using generic unidecode
        if has_arabic_chars(name) or has_non_ascii(name):
            result = romanize_generic(name)
            if result:
                return result
        
        # Try Chinese characters (common in border regions)
        if has_chinese_chars(name):
            result = romanize_zh(name)
            if result:
                return result
        
        # Try to extract Latin part from mixed text
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        
        return None

    elif NATIVE_LANG == 'ru':
        if has_cyrillic_chars(name):
            result = romanize_ru(name)
            if result:
                return result
        # Fall back to Latin extraction if romanization fails
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        return romanize_generic(name) or name

    else:
        # Unknown language - try generic romanization
        return romanize_generic(name) or name

    return None

def is_latin_text(text):
    """Check if text is already Latin-based (ASCII or accented Latin characters)."""
    if not text:
        return False
    for char in text:
        # Allow ASCII
        if ord(char) < 128:
            continue
        # Allow Latin Extended-A, Latin Extended-B, Latin Extended Additional
        if '\u00C0' <= char <= '\u00FF':  # Latin-1 Supplement (accented chars)
            continue
        if '\u0100' <= char <= '\u017F':  # Latin Extended-A
            continue
        if '\u0180' <= char <= '\u024F':  # Latin Extended-B
            continue
        if '\u1E00' <= char <= '\u1EFF':  # Latin Extended Additional
            continue
        if char == '\u00B7':  # Middle dot (common name separator)
            continue
        if '\u2010' <= char <= '\u2027':  # Typographic dashes/quotes (\u2013 \u2014 ' ' " " \u2026)
            continue
        # Any other character means it's not purely Latin
        return False
    return True


# name:<lang> tags usable as a last-resort name source (excludes non-name keys
# like name:signed=no or name:etymology:wikidata)
_NAME_LANG_RE = re.compile(r'^name:[a-z]{2,3}(?:-[A-Za-z0-9]+)*$')

# Only objects that already carry some name tag are processed: we complete
# names, never invent labels for deliberately unnamed objects (e.g. street
# trees tagged wikipedia=ja:<species> would otherwise all get species labels).
PROCESSED_NAMES = {'name', 'name:en', 'name:ja', 'name:zh', 'name:cn', 'name:ne', 'name:hi', 'name:ru',
                   'name:zh-Hant', 'name:zh-Hant-TW', 'name:zh-TW', 'name:zh-HK',
                   'name:zh-Hans', 'name:zh-CN'}

# Per-source fill counters, reported at the end of a run. Keyed as
# STATS['name:en']['<source>'] -> count of objects whose tag was filled from <source>.
from collections import Counter
STATS = {'name:en': Counter(), 'name:zh': Counter()}


def complete_name_en(d):
    """
    Complete name:en tag if missing.

    Priority for generating name:en:
    1. Wikidata 'en' label (via wikidata=Q... tag) - canonical English exonym
    2. English Wikipedia article title (wikipedia=en:... tag, offline)
    3. int_name (OSM international name) if Latin
    4. name is already Latin - copy to name:en
    5. brand:wikidata 'en' label (chain-store POIs; loses any branch suffix)
    6. name:$lang (by $lang related python module)
    7. name:zh (by hanzi2reading)
    8. name assumed as $lang (by combined rules)

    Returns (value, source) where source names the rule that produced the value,
    or (None, None) if not generated.
    """
    # Priority 1: Wikidata English label (canonical exonym, e.g. "Yushan",
    # "Taipei 101"). Labels are occasionally mis-curated (native script or
    # fullwidth punctuation as "en"): NFKC-normalize, then require Latin.
    name_en = wikidata_label(d, 'en')
    if name_en:
        name_en = unicodedata.normalize('NFKC', name_en)
        if is_latin_text(name_en):
            return name_en, 'wikidata'

    # Priority 2: English Wikipedia article title (curated exonym, fully offline)
    wp_en = wikipedia_title(d, 'en')
    if wp_en and is_latin_text(wp_en):
        return wp_en, 'wikipedia'

    # Priority 3: int_name (international name) if Latin
    int_name = d.get('int_name', '').strip()
    if int_name and is_latin_text(int_name):
        return ' '.join(int_name.split()), 'int_name'

    # Priority 4: If name is already Latin, copy it directly (normalize spaces)
    if 'name' in d and d['name'] and is_latin_text(d['name'].strip()):
        return ' '.join(d['name'].split()), 'latin_name'

    # Priority 5: brand:wikidata English label (clean brand name; the local
    # branch suffix, if any, is dropped - still better than romanization)
    name_en = wikidata_label(d, 'en', key='brand:wikidata')
    if name_en:
        name_en = unicodedata.normalize('NFKC', name_en)
        if is_latin_text(name_en):
            return name_en, 'brand'

    # Priority 6: Try name:$lang with language-specific module
    name_en = romanize_by_lang_tag(d)
    if name_en:
        return name_en, 'romanize'

    # Priority 7: Try name:zh with hanzi2reading (if not already tried for zh)
    if NATIVE_LANG != 'zh':
        name_en = romanize_by_zh_tag(d)
        if name_en:
            return name_en, 'romanize'

    # Priority 8: Assume 'name' is in $lang and use combined rules
    if 'name' in d and d['name'] and d['name'].strip():
        name_en = romanize_by_combined_rules(d['name'].strip())
        if name_en:
            return name_en, 'romanize'

    # Priority 9: last resort - use any other name:<lang> tag (e.g. an object
    # tagged only with name:ru), copied if Latin, otherwise generically
    # transliterated. Sorted for determinism.
    for k in sorted(d):
        if k != 'name:en' and _NAME_LANG_RE.match(k):
            v = d[k].strip()
            if not v:
                continue
            if is_latin_text(v):
                return ' '.join(v.split()), 'other_name'
            name_en = romanize_generic(v)
            if name_en:
                return name_en, 'other_name'

    return None, None


def complete_name_zh(d):
    """
    Complete name:zh tag if missing. Produces Traditional Chinese (Taiwan).

    Priority order depends on NATIVE_LANG:
    - NATIVE_LANG=zh (Taiwan): wikidata(zh) -> wikipedia(zh title) -> name (if CJK/Latin)
                               -> name:zh-Hant* -> name:zh-Hans*(->Trad) -> name:cn(->Trad)
                               -> name:ja (filtered, jp2t) -> brand:wikidata(zh) -> name:en
    - All others:              wikidata(zh) -> wikipedia(zh title) -> name:zh-Hant*
                               -> name:zh-Hans*(->Trad) -> name:cn(->Trad)
                               -> name:ja (filtered, jp2t) -> name (if CJK/Latin)
                               -> brand:wikidata(zh) -> name:en
    where name:zh-Hant* = first of name:zh-Hant / name:zh-Hant-TW / name:zh-TW / name:zh-HK
    and   name:zh-Hans* = first of name:zh-Hans / name:zh-CN

    Returns (value, source), or (None, None) when nothing sensible is derivable (the
    raw mapper 'name' is intentionally NOT used as a last resort - downstream
    name-tag-lists fall back to 'name' themselves).
    """
    # Extract and normalize tag values (None if empty or missing)
    name = d.get('name', '').strip() or None
    name_cn = d.get('name:cn', '').strip() or None
    name_en = d.get('name:en', '').strip() or None

    # zh script-subtag variants: Traditional ones are usable directly,
    # Simplified ones after s2twp conversion
    def first_tag(*keys):
        for k in keys:
            v = d.get(k, '').strip()
            if v:
                return v
        return None

    name_hant = first_tag('name:zh-Hant', 'name:zh-Hant-TW', 'name:zh-TW', 'name:zh-HK')
    name_hans = first_tag('name:zh-Hans', 'name:zh-CN')
    name_hans_t = to_traditional(name_hans) if name_hans else None

    # name:ja is usable after kana mapping (ノ->之 etc.) if the rest is
    # Chinese+Latin only; shinjitai is converted to Traditional (広沢 -> 廣澤)
    name_ja = ja_name_to_zh(d.get('name:ja', '').strip())

    # Wikidata Traditional-Chinese label (already normalized to Traditional in the cache)
    wd_zh = wikidata_label(d, 'zh')

    # Chinese Wikipedia article title from the wikipedia tag (curated, offline)
    wp_zh = wikipedia_title(d, 'zh')
    wp_zh = to_traditional(wp_zh) if wp_zh and is_chinese_latin_only(wp_zh) else None

    # brand:wikidata Traditional-Chinese label (chain-store POIs)
    brand_zh = wikidata_label(d, 'zh', key='brand:wikidata')

    # name is only usable as name:zh if CJK/Latin only (no kana/Cyrillic/etc.).
    # In ja mode the raw name IS Japanese: kana-map and convert shinjitai too;
    # elsewhere just normalize to Traditional in case the mapper used Simplified.
    if NATIVE_LANG == 'ja':
        name_filtered = ja_name_to_zh(name)
    else:
        name_filtered = to_traditional(name) if name and is_chinese_latin_only(name) else None

    # name:cn is Simplified -> convert to Traditional (Taiwan)
    name_cn_t = to_traditional(name_cn) if name_cn else None

    if NATIVE_LANG == 'zh':
        candidates = [(wd_zh, 'wikidata'), (wp_zh, 'wikipedia'), (name_filtered, 'name'),
                      (name_hant, 'name:zh-Hant'), (name_hans_t, 'name:zh-Hans'),
                      (name_cn_t, 'name:cn'), (name_ja, 'name:ja'),
                      (brand_zh, 'brand'), (name_en, 'name:en')]
    else:
        candidates = [(wd_zh, 'wikidata'), (wp_zh, 'wikipedia'),
                      (name_hant, 'name:zh-Hant'), (name_hans_t, 'name:zh-Hans'),
                      (name_cn_t, 'name:cn'), (name_ja, 'name:ja'),
                      (name_filtered, 'name'), (brand_zh, 'brand'), (name_en, 'name:en')]

    for value, source in candidates:
        if value:
            return value, source
    return None, None


def annotate(obj):
    """
    Annotate object by completing the name:en and name:zh tags only.

    1. Complete name:en tag if missing
    2. Complete name:zh tag if missing
    The original 'name' tag is left untouched (downstream name-tag-lists read
    name:en / name:zh and fall back to 'name' themselves).
    """
    d = dict(obj.tags)
    if len(d) == 0:
        return obj
    if not any(k in PROCESSED_NAMES for k in d.keys()):
        return obj

    modified = False

    # Step 1: Complete name:en tag if missing
    if 'name:en' not in d:
        name_en, source = complete_name_en(d)
        if name_en:
            d['name:en'] = name_en
            STATS['name:en'][source] += 1
            modified = True
        else:
            print(f"fail name:en: {d}")

    # Step 2: Complete name:zh tag if missing
    if 'name:zh' not in d:
        name_zh, source = complete_name_zh(d)
        if name_zh:
            d['name:zh'] = name_zh
            STATS['name:zh'][source] += 1
            modified = True
        else:
            print(f"fail name:zh: {d}")

    if modified:
        new_obj = obj.replace()
        new_obj.tags = d
        return new_obj

    return obj

class Complete_name_Handler(osmium.SimpleHandler):
    def __init__(self, writer):
        super(Complete_name_Handler,self).__init__()
        self.writer = writer

    def node(self,n):
        self.writer.add_node(annotate(n))

    def way(self, w):
        self.writer.add_way(annotate(w))

    def relation(self,r):
        self.writer.add_relation(annotate(r))


def print_stats():
    """Report how many objects each tag was filled for, broken down by source."""
    # Stable, priority-ordered source list (union of both tags' sources)
    order = ['wikidata', 'wikipedia', 'int_name', 'latin_name', 'brand', 'romanize',
             'other_name', 'name', 'name:zh-Hant', 'name:zh-Hans', 'name:cn', 'name:ja', 'name:en']
    print("=== complete_name.py fill summary (NATIVE_LANG=%s, wikidata=%s) ==="
          % (NATIVE_LANG, 'on' if has_wikidata else 'off'), file=sys.stderr)
    for tag in ('name:en', 'name:zh'):
        counts = STATS[tag]
        total = sum(counts.values())
        wd = counts.get('wikidata', 0)
        breakdown = ', '.join(
            f"{src} {counts[src]}" for src in order if counts.get(src))
        print(f"{tag}: filled {total} (wikidata hits {wd})"
              + (f" [{breakdown}]" if breakdown else ""), file=sys.stderr)


# =============================================================================
# Parallel processing (multiprocessing across all cores).
#
# Two passes over the input:
#   pass 1: read-only scan; objects carrying a name tag (matched C++-side by
#           KeyFilter) are shipped as plain tag dicts to a worker pool that
#           computes the missing name:en / name:zh values.
#   pass 2: rewrite the file; objects without name tags are forwarded to the
#           writer inside libosmium (handler_for_filtered), named objects get
#           their computed additions applied.
# Completion is a pure function of an object's own tags, so the output is
# identical to the serial path. NAME_WORKERS=1 forces the serial path.
# =============================================================================

_BATCH_SIZE = 8192


def _worker_init():
    """Pool initializer: reopen the SQLite cache (a connection inherited
    through fork must not be reused)."""
    global _wikidata_conn, has_wikidata
    _wikidata_conn = None
    has_wikidata = False
    if WIKIDATA_CACHE and os.path.exists(WIKIDATA_CACHE):
        try:
            _wikidata_conn = sqlite3.connect(f'file:{WIKIDATA_CACHE}?mode=ro', uri=True)
            has_wikidata = True
        except Exception:
            pass


def _complete_batch(items):
    """Worker: compute tag additions for a batch of (kind, id, tags) items."""
    out = []
    stats = {'name:en': Counter(), 'name:zh': Counter()}
    for kind, oid, d in items:
        add = {}
        if 'name:en' not in d:
            value, source = complete_name_en(d)
            if value:
                add['name:en'] = value
                stats['name:en'][source] += 1
            else:
                print(f"fail name:en: {d}")
        if 'name:zh' not in d:
            # name:zh completion must see the just-filled name:en (same order
            # as the serial annotate())
            value, source = complete_name_zh({**d, **add})
            if value:
                add['name:zh'] = value
                stats['name:zh'][source] += 1
            else:
                print(f"fail name:zh: {d}")
        if add:
            out.append((kind, oid, add))
    return out, stats


def _obj_kind(o):
    if isinstance(o, osmium.osm.Node):
        return 'n'
    if isinstance(o, osmium.osm.Way):
        return 'w'
    return 'r'


def _name_filter():
    import osmium.filter
    return osmium.filter.KeyFilter(*PROCESSED_NAMES)


def run_parallel(infile, outfile, workers):
    from multiprocessing import Pool

    # Pass 1: collect tag dicts of objects needing completion, compute in pool
    additions = {}
    with Pool(workers, initializer=_worker_init) as pool:
        pending = []
        batch = []
        for o in osmium.FileProcessor(infile).with_filter(_name_filter()):
            if 'name:en' in o.tags and 'name:zh' in o.tags:
                continue
            batch.append((_obj_kind(o), o.id, dict(o.tags)))
            if len(batch) >= _BATCH_SIZE:
                pending.append(pool.apply_async(_complete_batch, (batch,)))
                batch = []
        if batch:
            pending.append(pool.apply_async(_complete_batch, (batch,)))
        for res in pending:
            out, stats = res.get()
            for kind, oid, add in out:
                additions[(kind, oid)] = add
            for tag, counts in stats.items():
                STATS[tag].update(counts)

    # Pass 2: rewrite; unnamed objects bypass Python entirely
    writer = osmium.SimpleWriter(outfile)
    fp = osmium.FileProcessor(infile).with_filter(_name_filter())
    fp.handler_for_filtered(writer)
    for o in fp:
        add = additions.get((_obj_kind(o), o.id))
        if add:
            d = dict(o.tags)
            d.update(add)
            writer.add(o.replace(tags=d))
        else:
            writer.add(o)
    writer.close()


if __name__ == '__main__':
    infile, outfile = sys.argv[1], sys.argv[2]
    workers = int(os.environ.get('NAME_WORKERS', '0')) or os.cpu_count() or 1
    if workers > 1 and hasattr(osmium, 'FileProcessor'):
        run_parallel(infile, outfile, workers)
    else:
        writer = osmium.SimpleWriter(outfile)
        Complete_name_Handler(writer).apply_file(infile)
        writer.close()
    print_stats()
