import osmium
import sys
from hanzi2reading.reading import Reading
from hanzi2reading.pinyin import get as pinyin

reading = Reading()

def annotate(obj):
    if 'name' in obj.tags and not 'name:en' in obj.tags:
        new_obj = obj.replace()
        d = dict(obj.tags)
        if 'name:zh_pinyin' in obj.tags:
            d['name:en'] = d['name:zh_pinyin']
        else:
            d['name:en'] = ' '.join(pinyin(s).capitalize() for s in reading.get(d['name']))
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
