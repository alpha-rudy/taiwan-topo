import osmium
import sys
import os

# Import Chinese romanization
try:
    from hanzi2reading.reading import Reading
    from hanzi2reading.pinyin import get as pinyin
    reading = Reading()
    has_hanzi2reading = True
except ImportError:
    has_hanzi2reading = False

# Import Japanese romanization
try:
    import pykakasi
    kakasi = pykakasi.kakasi()
    has_pykakasi = True
except ImportError:
    has_pykakasi = False

# Determine language from environment variable or default to zh
LANG = os.environ.get('LANG_CODE', 'zh')

def annotate(obj):
    if 'name' in obj.tags and not 'name:en' in obj.tags:
        new_obj = obj.replace()
        d = dict(obj.tags)
        
        # Skip if name is empty
        if not d['name'] or not d['name'].strip():
            return obj
        
        # Check for existing romanization tags
        if 'name:zh_pinyin' in obj.tags:
            d['name:en'] = d['name:zh_pinyin']
        elif 'name:ja_rm' in obj.tags or 'name:ja-Latn' in obj.tags:
            d['name:en'] = d.get('name:ja_rm', d.get('name:ja-Latn', ''))
        elif LANG == 'ja' and has_pykakasi:
            # Japanese romanization
            try:
                result = kakasi.convert(d['name'])
                romanized = ' '.join(item['hepburn'].capitalize() for item in result if item['hepburn'])
                if romanized:
                    d['name:en'] = romanized
            except (IndexError, KeyError, Exception):
                # If romanization fails, skip this entry
                return obj
        elif has_hanzi2reading:
            # Chinese romanization (default)
            try:
                d['name:en'] = ' '.join(pinyin(s).capitalize() for s in reading.get(d['name']))
            except Exception:
                # If romanization fails, skip this entry
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
