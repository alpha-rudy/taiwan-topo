import osmium
import sys
import os
import re

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

# Determine language from environment variable or default to zh
LANG = os.environ.get('LANG_CODE', 'zh')

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

def romanize_zh(text):
    """Romanize Chinese text using hanzi2reading."""
    if not has_hanzi2reading:
        return None
    try:
        segments = reading.get(text)
        if not segments:
            return None
        result = ' '.join(pinyin(s).capitalize() for s in segments)
        return result if result else None
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
    if LANG == 'zh':
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
    
    elif LANG == 'ja':
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
    
    elif LANG == 'ne':
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
    
    elif LANG == 'hi':
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
    if not has_chinese_chars(name) and not has_tibetan_chars(name) and not has_arabic_chars(name):
        # Check for Devanagari (Hindi/Nepali), Japanese kana, etc.
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in name)
        has_japanese_kana = any(('\u3040' <= char <= '\u309F') or ('\u30A0' <= char <= '\u30FF') for char in name)
        if not has_devanagari and not has_japanese_kana:
            return name
    
    if LANG == 'zh':
        if has_chinese_chars(name):
            result = romanize_zh(name)
            if result:
                return result
            # Fall back to Latin extraction if romanization fails
            latin_part = extract_latin_part(name)
            if latin_part:
                return latin_part
        return name
    
    elif LANG == 'ja':
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
    
    elif LANG == 'ne':
        result = romanize_ne(name)
        if result:
            return result
        # Fall back to Latin extraction if romanization fails
        latin_part = extract_latin_part(name)
        if latin_part:
            return latin_part
        return name
    
    elif LANG == 'hi':
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


PROCESSED_NAMES = {'name', 'name:en', 'name:ja', 'name:zh', 'name:cn', 'name:ne', 'name:hi'}

def complete_name_en(d):
    """
    Complete name:en tag if missing.
    
    Priority for generating name:en:
    1. name is already Latin - copy to name:en
    2. name:$lang (by $lang related python module)
    3. name:zh (by hanzi2reading)
    4. name assumed as $lang (by combined rules)
    
    Returns the name:en value or None if not generated.
    """
    name_en = None
    
    # Priority 1: If name is already Latin, copy it directly (normalize spaces)
    if 'name' in d and d['name'] and is_latin_text(d['name'].strip()):
        name_en = ' '.join(d['name'].split())
    
    # Priority 2: Try name:$lang with language-specific module
    if name_en is None:
        name_en = romanize_by_lang_tag(d)
    
    # Priority 3: Try name:zh with hanzi2reading (if not already tried for zh)
    if name_en is None and LANG != 'zh':
        name_en = romanize_by_zh_tag(d)
    
    # Priority 4: Assume 'name' is in $lang and use combined rules
    if name_en is None and 'name' in d and d['name'] and d['name'].strip():
        name_en = romanize_by_combined_rules(d['name'].strip())
    
    return name_en


def complete_name(d):
    """
    Complete/replace name tag based on priority order (depends on LANG).
    
    Priority order:
    - LANG=zh: "name", "name:zh", "name:cn", "name:ja" (if Chinese+Latin only), "name:en"
    - LANG=ja: "name:zh", "name:cn", "name", "name:ja" (if Chinese+Latin only), "name:en"
    - Others:  "name:zh", "name:cn", "name:ja" (if Chinese+Latin only), "name" (if Chinese+Latin only), "name:en", "name"
    
    Note: name:ja is only used if it contains only Chinese and Latin characters (no Japanese kana).
    
    Returns the name value or None if not found.
    """
    # Extract and normalize tag values (None if empty or missing)
    name = d.get('name', '').strip() or None
    name_zh = d.get('name:zh', '').strip() or None
    name_cn = d.get('name:cn', '').strip() or None
    name_en = d.get('name:en', '').strip() or None
    
    # name:ja is only valid if it contains only Chinese+Latin (no Japanese kana)
    name_ja_raw = d.get('name:ja', '').strip() or None
    name_ja = name_ja_raw if name_ja_raw and is_chinese_latin_only(name_ja_raw) else None
    
    if LANG == 'zh':
        # Priority: name, name:zh, name:cn, name:ja (filtered), name:en
        return name or name_zh or name_cn or name_ja or name_en
    
    elif LANG == 'ja':
        # Priority: name:zh, name:cn, name, name:ja (filtered), name:en
        return name_zh or name_cn or name or name_ja or name_en
    
    else:
        # Priority: name:zh, name:cn, name:ja (filtered), name (if Chinese+Latin only), name:en, name (fallback)
        name_filtered = name if name and is_chinese_latin_only(name) else None
        if name_zh:
            return f"{name_zh} ({name_en})" if name_en else name_zh
        return name_cn or name_ja or name_filtered or name_en or name


def annotate(obj):
    """
    Annotate object with name and name:en tags.
    
    1. Complete name:en tag if missing (do this first)
    2. Complete/replace name tag based on LANG-specific priority (uses name:en)
    """
    d = dict(obj.tags)
    if len(d) == 0:
        return obj
    if not any(k in PROCESSED_NAMES for k in d.keys()):
        return obj
    
    modified = False
    
    # Step 1: Complete name:en tag if missing (do this first so complete_name can use it)
    if 'name:en' not in d:
        name_en = complete_name_en(d)
        if name_en:
            d['name:en'] = name_en
            modified = True
        else:
            print(f"fail name:en: {d}")
    
    # Step 2: Complete/replace name tag (now uses the completed name:en)
    new_name = complete_name(d)
    if new_name:
        if new_name != d.get('name', ''):
            d['name'] = new_name
            modified = True
    else:
        print(f"fail name: {d}")
    
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

writer = osmium.SimpleWriter(sys.argv[2])
Complete_name_Handler(writer).apply_file(sys.argv[1])
writer.close()
