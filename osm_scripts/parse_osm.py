# -*- coding: utf-8 -*-
import sys
from lxml import etree
import json


def round_float(value):
    try:
        return str(int(round(float(value))))
    except ValueError:
        return None


def add_tag(node, key, value):
    tag = etree.SubElement(node, 'tag')
    tag.attrib['k'] = key
    tag.attrib['v'] = value


def parse_node(node):
    # remove all name:zh, ref:zh tags, used only name and ref tags
    zh_tag = node.find("tag[@k='name:zh']")
    if zh_tag is not None:
        node.remove(zh_tag)
    zh_tag = node.find("tag[@k='ref:zh']")
    if zh_tag is not None:
        node.remove(zh_tag)

    # test if a peak node
    peak_tags = node.xpath("tag[@k='natural' and @v='peak']")
    if len(peak_tags) == 0:
        return

    # proceed peak node
    name_tag = node.find("tag[@k='name']")
    ref_tag = node.find("tag[@k='ref']")
    if ref_tag is not None:
        if u'百岳#' in ref_tag.attrib['v'] and name_tag is not None:
            if u'小百岳#' in ref_tag.attrib['v']:
                add_tag(node, 'zl', '2')
            else:
                if name_tag.attrib['v'] in [u'玉山', u'北大武山', u'雪山']:
                    add_tag(node, 'zl', '0')
                else:
                    add_tag(node, 'zl', '1')
            ref_tag.attrib['v'] = u'({})'.format(ref_tag.attrib['v'])
        else:
            node.remove(ref_tag)

    ele_tag = node.find("tag[@k='ele']")
    if ele_tag is not None and name_tag is not None:
        ele = round_float(ele_tag.attrib['v'])
        if ele is not None:
            name_tag.attrib['v'] = u'{}, {}m'.format(name_tag.attrib['v'], ele)

    return


def parse_way(way):
    way_id = way.get("id")
    for hknetwork in hknetworks:
        if way_id in hknetwork["members"]:
            ref_tag = way.find("tag[@k='ref']")
            if ref_tag is None:
                if len(hknetwork["name"]) != 0:
                    add_tag(way, "ref", hknetwork["name"])
            else:
                if len(hknetwork["name"]) != 0:
                    ref_tag.attrib['v'] = u'{}'.format(hknetwork["name"])
            add_tag(way, "hknetwork", hknetwork["network"])
            break


hknetworks = json.load(open("./hknetworks.json"))

xml = etree.parse(sys.stdin)
osm = xml.getroot()

for i in osm:
    if i.tag == 'node':
        parse_node(i)
    elif i.tag == 'way':
        parse_way(i)

xml.write(sys.stdout, encoding='utf-8', method='xml', pretty_print=True, xml_declaration=True)
