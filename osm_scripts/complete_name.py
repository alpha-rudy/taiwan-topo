import osmium
import sys
import os
import re
import sqlite3
import unicodedata

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


def wikidata_label(tags, lang):
    """Return a cached Wikidata label for tags['wikidata'], or None.

    lang must be 'en' or 'zh' (internal, not user input -> safe to interpolate).
    The 'zh' column is already Traditional/Taiwan (normalized at cache-build time).
    """
    if not has_wikidata:
        return None
    qid = tags.get('wikidata', '').strip()
    if not qid or not _QID_RE.match(qid):
        return None
    try:
        cur = _wikidata_conn.execute(
            f"SELECT {lang} FROM labels WHERE qid = ?", (qid,))
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return None


def to_traditional(text):
    """Convert Simplified Chinese to Traditional (Taiwan, s2twp). No-op if unavailable."""
    if not text or not has_opencc:
        return text
    try:
        return _opencc_s2twp.convert(text)
    except Exception:
        return text


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


def romanize_zh(text):
    """Romanize Chinese text using hanzi2reading.

    Splits the text into Han / non-Han runs so that interspersed digits and Latin
    (e.g. the "101" in "臺北101") are preserved verbatim instead of being dropped,
    and strips pinyin tone diacritics (Yú -> Yu) for clean English-reader output.
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
                if piece:
                    out.append(piece)
        result = ' '.join(' '.join(out).split())
        return result or None
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
            return result
    except Exception:
        pass
    return None


def romanize_ne(text):
    """Romanize Nepali text using nepali_roman."""
    if not has_nepali_roman:
        return None
    try:
        raw_roman = nr.romanize_text(text)
        if raw_roman:
            return ' '.join(word.capitalize() for word in raw_roman.split())
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
            return ' '.join(word.capitalize() for word in raw_roman.split())
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
            return ' '.join(word.capitalize() for word in wylie.split())
    except Exception:
        pass
    return None


def romanize_generic(text):
    """Generic romanization fallback using unidecode."""
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


def romanize_ru(text):
    """Romanize Russian/Cyrillic text using cyrtranslit."""
    if not has_cyrtranslit:
        return None
    try:
        result = cyrtranslit.to_latin(text, "ru")
        if result and result != text:
            return ' '.join(word.capitalize() for word in result.split())
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
        # Allow Halfwidth and Fullwidth Forms
        if '\uFF00' <= char <= '\uFFEF':
            continue
        # Any other character (including Japanese Hiragana/Katakana) means it's not Chinese+Latin only
        return False
    return True


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

def romanize_by_lang_tag(tags):
    """
    Priority 1: Try to romanize using name:$lang tag with language-specific module.
    Returns romanized string or None if not applicable.
    """
    if NATIVE_LANG == 'zh':
        # Check for existing romanization tag
        if 'name:zh_pinyin' in tags:
            return tags['name:zh_pinyin']
        # Try romanizing name:zh
        if 'name:zh' in tags:
            # If already ASCII, return as-is
            if tags['name:zh'].isascii():
                return tags['name:zh']
            if has_hanzi2reading:
                return romanize_zh(tags['name:zh'])
    
    elif NATIVE_LANG == 'ja':
        # Check for existing romanization tags
        if 'name:ja_rm' in tags:
            return tags['name:ja_rm']
        if 'name:ja-Latn' in tags:
            return tags['name:ja-Latn']
        # Try romanizing name:ja
        if 'name:ja' in tags:
            if tags['name:ja'].isascii():
                return tags['name:ja']
            if has_pykakasi:
                return romanize_ja(tags['name:ja'])
    
    elif NATIVE_LANG == 'ne':
        # Check for existing romanization tags
        if 'name:ne_rm' in tags:
            return tags['name:ne_rm']
        if 'name:ne-Latn' in tags:
            return tags['name:ne-Latn']
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
        if 'name:hi_rm' in tags:
            return tags['name:hi_rm']
        if 'name:hi-Latn' in tags:
            return tags['name:hi-Latn']
        # Try romanizing name:hi
        if 'name:hi' in tags:
            if tags['name:hi'].isascii():
                return tags['name:hi']
            if has_indic_transliteration:
                return romanize_hi(tags['name:hi'])

    elif NATIVE_LANG == 'ru':
        # Check for existing romanization tags
        if 'name:ru_rm' in tags:
            return tags['name:ru_rm']
        if 'name:ru-Latn' in tags:
            return tags['name:ru-Latn']
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
    
    # If name is Latin-based (no CJK/Devanagari/etc.), return as-is
    # This handles cases like "Häagen-Dazs" with accented Latin characters
    if not has_chinese_chars(name) and not has_tibetan_chars(name) and not has_arabic_chars(name) and not has_cyrillic_chars(name):
        # Check for Devanagari (Hindi/Nepali), Japanese kana, etc.
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in name)
        has_japanese_kana = any(('\u3040' <= char <= '\u309F') or ('\u30A0' <= char <= '\u30FF') for char in name)
        if not has_devanagari and not has_japanese_kana:
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
        return name
    
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
        return name
    
    elif NATIVE_LANG == 'ne':
        result = romanize_ne(name)
        if result:
            return result
        # Fall back to Latin extraction if romanization fails
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        return name
    
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
        return name

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
        # Any other character means it's not purely Latin
        return False
    return True


PROCESSED_NAMES = {'name', 'name:en', 'name:ja', 'name:zh', 'name:cn', 'name:ne', 'name:hi', 'name:ru'}

# Per-source fill counters, reported at the end of a run. Keyed as
# STATS['name:en']['<source>'] -> count of objects whose tag was filled from <source>.
from collections import Counter
STATS = {'name:en': Counter(), 'name:zh': Counter()}


def complete_name_en(d):
    """
    Complete name:en tag if missing.

    Priority for generating name:en:
    1. Wikidata 'en' label (via wikidata=Q... tag) - canonical English exonym
    2. int_name (OSM international name) if Latin
    3. name is already Latin - copy to name:en
    4. name:$lang (by $lang related python module)
    5. name:zh (by hanzi2reading)
    6. name assumed as $lang (by combined rules)

    Returns (value, source) where source names the rule that produced the value,
    or (None, None) if not generated.
    """
    # Priority 1: Wikidata English label (canonical exonym, e.g. "Yushan", "Taipei 101")
    name_en = wikidata_label(d, 'en')
    if name_en:
        return name_en, 'wikidata'

    # Priority 2: int_name (international name) if Latin
    int_name = d.get('int_name', '').strip()
    if int_name and is_latin_text(int_name):
        return ' '.join(int_name.split()), 'int_name'

    # Priority 3: If name is already Latin, copy it directly (normalize spaces)
    if 'name' in d and d['name'] and is_latin_text(d['name'].strip()):
        return ' '.join(d['name'].split()), 'latin_name'

    # Priority 4: Try name:$lang with language-specific module
    name_en = romanize_by_lang_tag(d)
    if name_en:
        return name_en, 'romanize'

    # Priority 5: Try name:zh with hanzi2reading (if not already tried for zh)
    if NATIVE_LANG != 'zh':
        name_en = romanize_by_zh_tag(d)
        if name_en:
            return name_en, 'romanize'

    # Priority 6: Assume 'name' is in $lang and use combined rules
    if 'name' in d and d['name'] and d['name'].strip():
        name_en = romanize_by_combined_rules(d['name'].strip())
        if name_en:
            return name_en, 'romanize'

    return None, None


def complete_name_zh(d):
    """
    Complete name:zh tag if missing. Produces Traditional Chinese (Taiwan).

    Priority order depends on NATIVE_LANG:
    - NATIVE_LANG=zh (Taiwan): wikidata(zh) -> name (if CJK/Latin) -> name:cn(->Trad)
                               -> name:ja (filtered) -> name:en
    - All others:              wikidata(zh) -> name:zh -> name:cn(->Trad)
                               -> name:ja (filtered) -> name (if CJK/Latin) -> name:en

    Returns (value, source), or (None, None) when nothing sensible is derivable (the
    raw mapper 'name' is intentionally NOT used as a last resort - downstream
    name-tag-lists fall back to 'name' themselves).
    """
    # Extract and normalize tag values (None if empty or missing)
    name = d.get('name', '').strip() or None
    name_zh = d.get('name:zh', '').strip() or None
    name_cn = d.get('name:cn', '').strip() or None
    name_en = d.get('name:en', '').strip() or None

    # name:ja is only valid if it contains only Chinese+Latin (no Japanese kana)
    name_ja_raw = d.get('name:ja', '').strip() or None
    name_ja = name_ja_raw if name_ja_raw and is_chinese_latin_only(name_ja_raw) else None

    # Wikidata Traditional-Chinese label (already normalized to Traditional in the cache)
    wd_zh = wikidata_label(d, 'zh')

    # name is only usable as name:zh if CJK/Latin only (no kana/Cyrillic/etc.);
    # normalize to Traditional in case the mapper used Simplified.
    name_filtered = to_traditional(name) if name and is_chinese_latin_only(name) else None

    # name:cn is Simplified -> convert to Traditional (Taiwan)
    name_cn_t = to_traditional(name_cn) if name_cn else None

    if NATIVE_LANG == 'zh':
        candidates = [(wd_zh, 'wikidata'), (name_filtered, 'name'),
                      (name_cn_t, 'name:cn'), (name_ja, 'name:ja'), (name_en, 'name:en')]
    else:
        candidates = [(wd_zh, 'wikidata'), (name_zh, 'name:zh'), (name_cn_t, 'name:cn'),
                      (name_ja, 'name:ja'), (name_filtered, 'name'), (name_en, 'name:en')]

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
    order = ['wikidata', 'int_name', 'latin_name', 'romanize',
             'name', 'name:zh', 'name:cn', 'name:ja', 'name:en']
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


if __name__ == '__main__':
    writer = osmium.SimpleWriter(sys.argv[2])
    Complete_name_Handler(writer).apply_file(sys.argv[1])
    writer.close()
    print_stats()
