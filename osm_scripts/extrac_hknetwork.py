# -*- coding: utf-8 -*-
import sys
from lxml import etree
import json


hknetworks = []


def add_tag(node, key, value):
    tag = etree.SubElement(node, 'tag')
    tag.attrib['k'] = key
    tag.attrib['v'] = value


def parse_relation(relation):
    # remove all name:zh, ref:zh tags, used only name and ref tags
    if len(relation.xpath("tag[@k='type'][@v='route']")) == 0:
        return
    if len(relation.xpath("tag[@k='route'][@v='hiking']")) == 0:
        return
    name = relation.find("tag[@k='name']")
    if name is None:
        return
    network = relation.find("tag[@k='network']")
    if network is None:
        return
    members = relation.xpath("member[@type='way']")
    if len(members) == 0:
        return

    hknetworks.append({
        "name": name.get("v"),
        "network": network.get("v"),
        "members": [m.get("ref") for m in members]
    })
    return

xml = etree.parse(sys.stdin)

osm = xml.getroot()

for i in osm:
    if i.tag == 'relation':
        parse_relation(i)
    osm.remove(i)

print json.dumps(hknetworks, indent=2, separators=(',', ': '), encoding="utf-8")
