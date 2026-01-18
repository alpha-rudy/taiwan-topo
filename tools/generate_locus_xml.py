import os
import click

# Configuration
MAP_ZIP_TEMPLATE = "AW3D30_OSM_{REGION}_TOPO_Rudy_locus.zip"
STYLE_ZIP = "MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip"
STYLE_DEST = "MOI_OSM_Taiwan_TOPO_Rudy_style.zip"
HGT_ZIP_TEMPLATE = "{REGION_LOWER}_hgtmix.zip"
HGT_DEST_TEMPLATE = "{REGION_LOWER}_hgt.zip"

PROVIDERS = {
    "cedric": "https://rudymap.tw/",
    "happyman": "https://map.happyman.idv.tw/rudy/",
    "kcwu": "https://moi.kcwu.csie.org/"
}

VARIANTS = ["all", "map", "dem", "upgrade"]

def get_xml_content(variant, base_url, region, region_lower):
    map_zip = MAP_ZIP_TEMPLATE.format(REGION=region)
    hgt_zip = HGT_ZIP_TEMPLATE.format(REGION_LOWER=region_lower)
    hgt_dest = HGT_DEST_TEMPLATE.format(REGION_LOWER=region_lower)

    xml = "<?xml version='1.0' encoding='UTF-8'?>\n<locusActions>\n"
    
    # Map Download
    if variant in ["all", "map", "upgrade"]:
        tags = "extract|deleteSource"
        if variant in ["map", "upgrade"]:
             tags += "|refreshMap"

        xml += f"""  <download>
    <source><![CDATA[{base_url}{map_zip} ]]></source>
    <dest><![CDATA[/mapsVector/{map_zip} ]]></dest>
    <after>{tags}</after>
  </download>\n"""

    # Style Download
    if variant in ["all", "upgrade"]:
        # Style usually before map or in middle, typically no 'after' action in 'all' xml
        xml += f"""  <download>
    <source><![CDATA[{base_url}{STYLE_ZIP}]]></source>
    <dest><![CDATA[/mapsVector/_themes/{STYLE_DEST}]]></dest>
  </download>\n"""

    # HGT Download
    if variant in ["all", "dem"]:
        tags = "extract|deleteSource|refreshMap"
        xml += f"""  <download>
    <source><![CDATA[{base_url}{hgt_zip}]]></source>
    <dest><![CDATA[/data/srtm/{hgt_dest}]]></dest>
    <after>{tags}</after>
  </download>\n"""

    xml += "</locusActions>\n"
    return xml

@click.command()
@click.option('--suite', required=True, help='The suite name (region_lower), e.g., kashmir, annapurna')
def main(suite):
    region_lower = suite.lower()
    region = suite.capitalize()
    
    output_dir = f"auto-install/locus/{region}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Generating Locus XML for suite: {suite} (Region: {region}) in {output_dir}")

    for provider, url in PROVIDERS.items():
        for variant in VARIANTS:
            filename = f"{region_lower}_{variant}-{provider}.xml"
            path = os.path.join(output_dir, filename)
            
            map_zip = MAP_ZIP_TEMPLATE.format(REGION=region)
            
            # Corrections for specific order matching Annapurna exactly
            if variant == "upgrade":
                # Manual override for upgrade to match order: Style first, then Map
                content = "<?xml version='1.0' encoding='UTF-8'?>\n<locusActions>\n"
                content += f"""  <download>
    <source><![CDATA[{url}{STYLE_ZIP}]]></source>
    <dest><![CDATA[/mapsVector/_themes/{STYLE_DEST}]]></dest>
  </download>\n"""
                content += f"""  <download>
    <source><![CDATA[{url}{map_zip} ]]></source>
    <dest><![CDATA[/mapsVector/{map_zip} ]]></dest>
    <after>extract|deleteSource|refreshMap</after>
  </download>\n"""
                content += "</locusActions>\n"
            else:
                content = get_xml_content(variant, url, region, region_lower)
            
            with open(path, "w") as f:
                f.write(content)
            print(f"Generated {path}")

if __name__ == "__main__":
    main()
