"""
tagfilter
checks which entries in input file should be forwarded to output database
"""


class TagFilter:
    def __init__(self, filter_file):
        self.valid_tags = []
        self._by_key = {}
        with open(filter_file, 'r') as f:
            for line in f:
                if not line.startswith('#') and len(line) > 2:
                    parts = line.strip().split('=')
                    if len(parts) >= 2:
                        k, v = parts[0], parts[1]
                        priority = len(self.valid_tags)
                        self.valid_tags.append([k, v])
                        val_map = self._by_key.setdefault(k, {})
                        if v not in val_map:
                            val_map[v] = (priority, (k, v))

    def tag_matched(self, tags):
        by_key = self._by_key
        best_prio = None
        best_pair = None
        for k, v in tags.items():
            val_map = by_key.get(k)
            if val_map is not None:
                hit = val_map.get(v)
                if hit is not None and (best_prio is None or hit[0] < best_prio):
                    best_prio = hit[0]
                    best_pair = hit[1]
        return best_pair
