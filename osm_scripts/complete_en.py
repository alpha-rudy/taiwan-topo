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

def annotate(obj):
    if 'name' in obj.tags and not 'name:en' in obj.tags:
        new_obj = obj.replace()
        d = dict(obj.tags)
        
        # Skip if name is empty
        if not d['name'] or not d['name'].strip():
            return obj
        
        # Check for existing romanization tags
        if LANG == 'zh':
            if 'name:zh_pinyin' in obj.tags:
                d['name:en'] = d['name:zh_pinyin']
                # print(f"pinyin/en (existing): {d['name']} -> {d['name:en']}")
            elif d['name'].isascii():
                d['name:en'] = d['name']
                # print(f"en/en: {d['name']} -> {d['name:en']}")
            elif has_hanzi2reading:
                # Chinese romanization (default)
                try:
                    d['name:en'] = ' '.join(pinyin(s).capitalize() for s in reading.get(d['name']))
                    # print(f"zh/en: {d['name']} -> {d['name:en']}")
                except Exception:
                    # If romanization fails, skip this entry
                    d['name:en'] = d['name']
                    return obj
        elif LANG == 'ja':
            if 'name:ja_rm' in obj.tags or 'name:ja-Latn' in obj.tags:
                d['name:en'] = d.get('name:ja_rm', d.get('name:ja-Latn', ''))
                # print(f"rm/en (existing): {d['name']} -> {d['name:en']}")
            elif d['name'].isascii():
                d['name:en'] = d['name']
                # print(f"en/en: {d['name']} -> {d['name:en']}")
            elif has_pykakasi:
                # Japanese romanization
                try:
                    result = kakasi.convert(d['name'])
                    romanized = ' '.join(item['hepburn'].capitalize() for item in result if item['hepburn'])
                    if romanized:
                        # Normalize spaces
                        romanized = ' '.join(romanized.split())
                        # Fix parentheses spacing
                        romanized = romanized.replace('( ', '(').replace(' )', ')')
                        d['name:en'] = romanized
                        # print(f"ja/en: {d['name']} -> {d['name:en']}")
                    else:
                        d['name:en'] = d['name']
                except (IndexError, KeyError, Exception):
                    # If romanization fails, skip this entry
                    d['name:en'] = d['name']
                    return obj
        elif LANG == 'ne':
            if 'name:ne_rm' in obj.tags or 'name:ne-Latn' in obj.tags:
                d['name:en'] = d.get('name:ne_rm', d.get('name:ne-Latn', ''))
                # print(f"rm/en (existing): {d['name']} -> {d['name:en']}")
            elif d['name'].isascii():
                d['name:en'] = d['name']
                # print(f"en/en: {d['name']} -> {d['name:en']}")
            elif has_nepali_roman:
                # Nepali romanization
                try:
                    # 'nr' refers to 'import nepali_roman as nr'
                    raw_roman = nr.romanize_text(d['name'])
                    
                    # Split, capitalize each word, and join to match the style of other languages
                    if raw_roman:
                        d['name:en'] = ' '.join(word.capitalize() for word in raw_roman.split())
                        # print(f"ne/en: {d['name']} -> {d['name:en']}")
                    else:
                        d['name:en'] = d['name']
                except Exception:
                    # If romanization fails, skip this entry
                    return obj
        elif LANG == 'hi':
            if 'name:hi_rm' in obj.tags or 'name:hi-Latn' in obj.tags:
                d['name:en'] = d.get('name:hi_rm', d.get('name:hi-Latn', ''))
                # print(f"rm/en (existing): {d['name']} -> {d['name:en']}")
            
            else:
                # 1. Try to extract Latin/English part (handles "Name - LocalName" and already-romanized text)
                # Matches: Latin chars (incl accents), numbers, common punctuation, occurring together
                latin_re = r'[A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\s\.\,\-\(\)\'\&]+'
                matches = re.findall(latin_re, d['name'])
                
                # Combine matches and clean up
                candidate = " ".join(matches).strip()
                # Remove common connector patterns like " - " at the ends, or multiple spaces
                candidate = re.sub(r'\s+', ' ', candidate)
                candidate = re.sub(r'^[\-\s]+|[\-\s]+$', '', candidate)
                
                # Validate the candidate
                is_valid_latin = False
                if candidate:
                     # Check if candidate has at least some actual letters (not just "123" or "-")
                     if any(c.isalpha() for c in candidate):
                         # If the extracted part is substantial relative to original name, 
                         # or it's definitely a name (len > 3)
                         if len(candidate) > 2:
                             d['name:en'] = candidate
                             # print(f"hi(extract)/en: {d['name']} -> {d['name:en']}")
                             is_valid_latin = True
                
                if not is_valid_latin:
                    if has_indic_transliteration:
                        # Hindi romanization fallback
                        try:
                            # 2. Check for Chinese characters first (common in border regions)
                            if has_hanzi2reading and any('\u4e00' <= char <= '\u9fff' for char in d['name']):
                                try:
                                    d['name:en'] = ' '.join(pinyin(s).capitalize() for s in reading.get(d['name']))
                                    # print(f"hi(zh)/en: {d['name']} -> {d['name:en']}")
                                except Exception:
                                    pass
                            else:
                                # 3. Handle Tibetan (Wylie)
                                if has_pyewts and any('\u0F00' <= char <= '\u0FFF' for char in d['name']):
                                    try:
                                        # Use pyewts for high-quality Wylie transliteration
                                        wylie = wylie_converter.toWylie(d['name'])
                                        if wylie and wylie != d['name']:
                                            # Wylie often comes out lowercase, capitalize words
                                            d['name:en'] = ' '.join(word.capitalize() for word in wylie.split())
                                            # print(f"bo/en: {d['name']} -> {d['name:en']}")
                                            
                                            # If extracting mixed resulted in success, return
                                            return new_obj # We modify 'obj' via 'd' and 'new_obj' construction below, so we need to continue or carefully return
                                            # Actually logic here is nested deep. Let's just break out successful.
                                    except Exception:
                                        pass

                                # 4. Generic fallback for Urdu/Arabic/Unknown using unidecode
                                # Check for Arabic block 0600-06FF or Extended Arabic
                                if has_unidecode and (any('\u0600' <= char <= '\u06FF' for char in d['name']) or \
                                   # Check if we still haven't found a romanization for other scripts
                                   any(ord(c) > 127 for c in d['name'])):
                                     
                                     # Try unidecode as a last resort for anything non-ASCII
                                     try:
                                         ud_roman = unidecode(d['name'])
                                         if ud_roman and ud_roman.strip() and ud_roman != d['name']:
                                             # Clean up unidecode output
                                             ud_roman = ' '.join(word.capitalize() for word in ud_roman.split())
                                             candidate = apply_urdu_replacements(ud_roman)
                                             d['name:en'] = candidate
                                             # print(f"auto/en: {d['name']} -> {d['name:en']}")
                                             # Success, skip next steps
                                             pass
                                     except Exception:
                                         pass

                                # 5. Try Devanagari transliteration (remaining cases)
                                if 'name:en' not in d:
                                    raw_roman = transliterate(d['name'], sanscript.DEVANAGARI, sanscript.IAST)
                                    
                                    # Split, capitalize each word, and join to match the style of other languages
                                    if raw_roman and raw_roman != d['name']:
                                        d['name:en'] = ' '.join(word.capitalize() for word in raw_roman.split())
                                        # print(f"hi/en: {d['name']} -> {d['name:en']}")
                        except Exception:
                            # If romanization fails, skip this entry
                            # print(f"Warning: name:en failed: {d['name']}")
                            return obj
                        except Exception:
                            # If romanization fails, skip this entry
                            # print(f"Warning: name:en failed: {d['name']}")
                            return obj
                    else:
                        return obj
        else:
            d['name:en'] = d['name']
            return obj

        new_obj.tags = d
        return new_obj
    else:
        return obj

class Complete_en_Handler(osmium.SimpleHandler):
    def __init__(self, writer):
        super(Complete_en_Handler,self).__init__()
        self.writer = writer

    def node(self,n):
        self.writer.add_node(annotate(n))

    def way(self, w):
        self.writer.add_way(annotate(w))

    def relation(self,r):
        self.writer.add_relation(annotate(r))

writer = osmium.SimpleWriter(sys.argv[2])
Complete_en_Handler(writer).apply_file(sys.argv[1])
writer.close()
