"""
tagfilter
checks which entries in input file should be forwarded to output database
"""
class TagFilter:
    def __init__(self, filter_file):
        self.valid_tags = []
        with open(filter_file,'r') as f:
            line = f.readline()
            while line:
                if not line.startswith('#') and len(line) > 2:
                    self.valid_tags.append(line.strip().split('='))
                line = f.readline()            

    def tag_matched(self, tags):
        for tag in self.valid_tags:
            if tag[0] in tags.keys():
                if tag[1] == tags.get(tag[0], ''):
                    return (tag[0], tag[1])
        return None
