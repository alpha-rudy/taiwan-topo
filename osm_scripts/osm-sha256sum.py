#!/usr/bin/env python3
"""
Compute a canonical hash of OSM data.

Only considers:
- Element type (node/way/relation)
- Element ID
- Coordinates (for nodes)
- Tags (key-value pairs)
- Member references (for ways and relations)

Ignores:
- File format (pbf/o5m/xml)
- Element order (assumes sorted by ID)
- Timestamps, versions, changesets, users
- Deleted elements

Optimized version: streams data directly to hasher without storing in memory.
Assumes elements are sorted by ID within each type.
"""

import osmium
import sys
import hashlib
import time

class OSMHasher(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.hasher = hashlib.sha256()
        self.last_node_id = -1
        self.last_way_id = -1
        self.last_rel_id = -1
        self.node_count = 0
        self.way_count = 0
        self.rel_count = 0
        self.started_ways = False
        self.started_relations = False
        
    def node(self, n):
        if n.deleted:
            return
        
        # Assert ordering
        if n.id <= self.last_node_id:
            print(f"WARNING: Node {n.id} out of order (previous: {self.last_node_id})", file=sys.stderr)
        self.last_node_id = n.id
        
        if self.node_count == 0:
            self.hasher.update(b'NODES\n')
        
        # Format: n<id>:<lat>:<lon>:<tag1=val1>:<tag2=val2>
        line = f"n{n.id}:{n.location.lat:.7f}:{n.location.lon:.7f}"
        
        # Sort tags for consistency
        if n.tags:
            line += ''.join(f":{k}={v}" for k, v in sorted((t.k, t.v) for t in n.tags))
        
        self.hasher.update(line.encode('utf-8') + b'\n')
        self.node_count += 1
    
    def way(self, w):
        if w.deleted:
            return
        
        # Assert ordering
        if w.id <= self.last_way_id:
            print(f"WARNING: Way {w.id} out of order (previous: {self.last_way_id})", file=sys.stderr)
        self.last_way_id = w.id
        
        if not self.started_ways:
            self.hasher.update(b'WAYS\n')
            self.started_ways = True
        
        # Format: w<id>:<ref1,ref2,...>:<tag1=val1>:<tag2=val2>
        refs = ','.join(str(n.ref) for n in w.nodes) if w.nodes else ''
        line = f"w{w.id}:{refs}"
        
        # Sort tags for consistency
        if w.tags:
            line += ''.join(f":{k}={v}" for k, v in sorted((t.k, t.v) for t in w.tags))
        
        self.hasher.update(line.encode('utf-8') + b'\n')
        self.way_count += 1
    
    def relation(self, r):
        if r.deleted:
            return
        
        # Assert ordering
        if r.id <= self.last_rel_id:
            print(f"WARNING: Relation {r.id} out of order (previous: {self.last_rel_id})", file=sys.stderr)
        self.last_rel_id = r.id
        
        if not self.started_relations:
            self.hasher.update(b'RELATIONS\n')
            self.started_relations = True
        
        # Format: r<id>:<type1:ref1:role1,type2:ref2:role2,...>:<tag1=val1>
        member_str = ','.join(f"{m.type}:{m.ref}:{m.role}" for m in r.members) if r.members else ''
        line = f"r{r.id}:{member_str}"
        
        # Sort tags for consistency
        if r.tags:
            line += ''.join(f":{k}={v}" for k, v in sorted((t.k, t.v) for t in r.tags))
        
        self.hasher.update(line.encode('utf-8') + b'\n')
        self.rel_count += 1
    
    def get_hash(self):
        """Get the computed hash"""
        return self.hasher.hexdigest()

def main():
    if len(sys.argv) < 2:
        print("Usage: osm-sha256sum.py <input.osm.pbf|input.o5m> [output.txt]", file=sys.stderr)
        print("\nCompute canonical hash of OSM file.", file=sys.stderr)
        print("Two files with same hash contain identical OSM data.", file=sys.stderr)
        print("\nOptimized version: assumes elements are sorted by ID.", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Reading {input_file}...", file=sys.stderr)
    start_time = time.time()
    
    hasher = OSMHasher()
    hasher.apply_file(input_file)
    
    read_time = time.time() - start_time
    
    print(f"Processed: {hasher.node_count} nodes, {hasher.way_count} ways, {hasher.rel_count} relations", file=sys.stderr)
    print(f"Time: {read_time:.2f}s ({(hasher.node_count + hasher.way_count + hasher.rel_count)/read_time:.0f} elements/s)", file=sys.stderr)
    
    hash_value = hasher.get_hash()
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(hash_value + '\n')
        print(f"Hash written to {output_file}", file=sys.stderr)
    
    print(hash_value)
    return 0

if __name__ == '__main__':
    sys.exit(main())