Elevate themes read me:
***********************

1. Installation & usage:
   English
   German
   
2. Changelog

3. Licenses


-------------------------------------------------------------------------
INSTALLATION & USAGE
-------------------------------------------------------------------------

ENGLISH:
********

OruxMaps:
---------

Quick install (recommended):
- Open http://www.openandromaps.org/en/legend/elevate-mountain-hike-theme in a browser on your android device
- Press on "OruxMaps" in the column "Install in Android" below "Downloads" in the "Elevate 4" table

Choose map style (essential):
- In OruxMaps use the maps icon in top menu bar and "Mapsforge theme" to choose the map theme (Elevate or Elements)
- Use the maps icon and "Tweak mapsforge theme" to choose the map style (hiking, cycling, city, mountainbike) and (de-)select overlays

Manual install (advanced):
- Please make sure you downloaded "Elevate4.zip"
- If it's an update of existing Elevate map themes: remove all old files and folders
- Unzip Elevate4.zip with an Android file explorer to "../oruxmaps/mapstyles/" on your SD-Card or internal memory (depending on your device)
- You can choose your own path for theme files in OruxMaps via "...", "Global settings", "Maps", "Mapsforge settings" and "Mapsforge themes"
- Choose map style as above


Locus:
------

Quick install (recommended):
- Open http://www.openandromaps.org/en/legend/elevate-mountain-hike-theme in a browser on your android device
- Press on "Locus" in the column "Install in Android" below "Downloads" in the "Elevate 4" table

Choose map style (essential):
- For choosing the map theme in Locus use the blue button on the bottom left side of the map for "Map content" and press "Map themes" (if not available press "Menu", "Settings", "Maps", "Panels & Buttons", "Left Actions Panel", check "Map content") 
- Touch the name of the map theme, "Elevate" or "Elements" for multiligual maps (V4), "Elevate LE" or "Elements LE" for single language maps (V3) (if necessary hit "Show more" below "Internal themes")
- For choosing map styles (hiking, cycling, city, mountainbike) and overlays, a menu pops up when choosing the map theme. To change again later, just use "Map themes" again.

Manual install (advanced):
- Please make sure you downloaded "Elevate4_Locus.zip"
- If it's an update of existing Elevate map theme files: remove all old files and folders
- Unzip Elevate4_Locus.zip with an Android file explorer to "../Locus/mapsVector/_themes/" on your SD-Card or internal memory (depending on your device)
- Choose map style as above

If you have problems, your directory structure should look something like this for Locus:

../Locus/mapsVector/_themes/
                            ele_res/*.svg
                            Elements/Elements.xml
                            Elevate/Elevate.xml
                            Elements LE/Elements LE.xml
                            Elevate LE/Elevate LE.xml

-------------------------------------------------------------------------

DEUTSCH:
********

OruxMaps:
---------

Schnellinstallation (empfohlen):
- Öffne http://www.openandromaps.org/kartenlegende/elevation-hike-theme in einem Browser auf dem Android Gerät
- Drücke auf "OruxMaps" in der Spalte "Installieren unter Android" unterhalb von "Downloads" in der "Elevate 4" Tabelle

Kartenstil wählen (wichtig):
- In OruxMaps das Karten-Symbol in der oberen Menüleiste auswählen, dann "Mapsforge-Thema" benutzen um das Kartenthema auszuwählen (Elevate oder Elements)
- Benutze das Karten-Symbol und "Mapsforge-Thema optimieren" um den Kartenstil auszuwählen und Overlays an- oder abzuschalten

Manuelle Installation (fortgeschritten):
- Bitte darauf achten, dass die heruntergeladene Datei "Elevate4.zip" heißen sollte
- Wenn es ein Update von bisherigen Elevate Kartenthemen ist: lösche alle alten Dateien und Ordner
- Entpacke Elevate4.zip mit einem Android Datei Explorer nach "../oruxmaps/mapstyles/" auf der SD-Karte oder im internen Speicher (kommt auf das Gerät an)
- Man kann selbst in OruxMaps auch den Pfad zu den Kartenthemen festlegen, via "Menü", "Globale Einstellungen", "Karten", "Mapsforge-Einstellungen" und "Mapsforge-Themen"
- Kartenstil wählen siehe oben

Locus:
------

Schnellinstallation (empfohlen):
- Öffne http://www.openandromaps.org/kartenlegende/elevation-hike-theme in einem Browser auf dem Android Gerät
- Drücke auf "Locus" in der Spalte "Installieren unter Android" unterhalb von "Downloads" in der "Elevate 4" Tabelle

Kartenstil wählen (wichtig):
- Um den Kartenstil auszuwählen benutze in Locus den blauen Button für "Karteninhalt" unten links bei der Karte und drücke auf "Thema der Karte" (wenn nicht vorhanden, drücke "Menü", "Einstellungen", "Karten", "Bedienleisten & Knöpfe", "Aktivitätenliste", Haken bei "Karteninhalt" setzen)
- Wähle dann den Namen des Kartenthemas, also "Elevate"/"Elements" für mehrsprachige Karten (V4) oder "Elevate LE"/"Elements LE" für einsprachige Karten (V3) (wenn nötig, berühre "mehr..." am Ende von "Interne Themen")
- Um Kartenstile und Overlays zu ändern erscheint ein weiteres Menü wenn das Kartenthema ausgewählt wird. Um diese später zu ändern, einfach wieder "Thema der Karte" benutzen. 

Manuelle Installation (fortgeschritten):
- Bitte darauf achten dass die heruntergeladene Datei "Elevate4_Locus.zip" heißen sollte (oder die L/XL Varianten, für die gilt das unten Stehende entsprechend)
- Wenn es ein Update von bisherigen Elevate Kartenthemen ist: lösche alle alten Dateien und Ordner
- Entpacke Elevate4_Locus.zip mit einem Android Datei Explorer nach "../Locus/mapsVector/_themes/" auf der SD-Karte oder im internen Speicher (kommt auf das Gerät an)
- Kartenstil wählen siehe oben

Wenn Probleme auftreten, die Ordnerstruktur sollte in etwas so aussehen:

../Locus/mapsVector/_themes/
                            ele_res/*.svg
                            Elegant/Elegant.xml
                            Elements/Elements.xml
                            Elements LE/Elements LE.xml
                            Elevate LE/Elevate LE.xml


-------------------------------------------------------------------------
CHANGELOG
-------------------------------------------------------------------------
4.1.2 10/10/16
- added waymarks for _right foregrounds, embankment=yes, separate rendering for sac_scale=difficult_alpine_hiking
- changed rendering of dyke/embankment, retaining_wall, golf_course, admin-borders, trail_visibility combinations (now: excellent+good, intermediate, bad+horrible+no), crevasse, crater
- fixes for waymarks

4.1.1 25/09/16
- changed rendering of waymark captions, optimized hiking route rendering
- fixed a bug in tunnel definitions

4.1.0.1 14/09/16
- fixed Locus conversion error for Elements
- Locus: added rounded curves for contour lines

4.1.0 14/09/16
- added waymark symbols for maps from late August 2016 and later
- new rendering of hiking routes
- new trail_visibility rendering/combinations, new rendering of tracks without tracktype
- reduced symbol size to match better those of Elevate 3 PNG versions
- added: man_made=dyke/embankment/groyne
- fixed MTBS1 and MTBS3 rendering for tracks, dy for tunnels, Locus: limited village names in Elevate LE to ZL 12+ (this time for real)

4.0.1 31/07/16
- reduced width of roads/buildings for less excessive scaling on very high dpi devices
- increased width of highway=pedestrian
- Locus: fixed rendering of most symbol captions at ZL 17+, limited village names in Elevate LE to ZL 12+
- some name changes in the overlay menu

4.0 10/07/16
- one size only: SVG version which scales with screen density is now default (instead of various sizes, removed those)
- new SVG patterns that scale with screen density, changed pattern zoom behavior
- new MTB mapstyle: new rendering for mtb_scale_uphill, added trail_visibility to paths, removed mtb_scale from highways with bicycle=no
- reworked routes: separate colors for international and national routes (same for hiking and cycling - blue and green), new low zoom rendering for hiking routes on paths, optimized route rendering
- reworked access markings: separate pattern colors for access=private (orange) and access=no (red), more complex filtering of access rules on highways, new access patterns
- Locus: added "dp" to all values for adjusting to screen density, added standard V4 version, renamed Locus edition with "LE"
- added tourism=apartment, zoom-min to some bridges and tunnels, separate rendering for private playgrounds, natural=cape/crater/bay/peninsula/fjord/canyon, place=islet/archipelago/sea/ocean, areas for highway=track/steps, names for highway areas, bicycle=no for areas, low zoom tunnels, areas for archaeological_site, natural=hot_spring, shop=mall
- changed low zoom captions, cycle and hike nodes, captions for protected areas, symbol for tourism=chalet, cliff rendering, motorway_junction caption, high zoom hiking routes on cycleways, moved observation tower to outdoor overlay, removed viewpoint from towers, rendering for sac_scale 5/6, limited capital to certain places, removed sled pistes from cycling mapstyle, optimized emphasized cycleways, removed bridges from tunnels, changed cycleway=track to cycleway=cw_track, removed amenity=drinking_water with drinking_water=no, optimized highway area rendering

3.1.6 16/03/16
- changed leisure=track to leisure=ls_track, larger symbol/earlier ZL for amenity=bus_station
- corrected SVG scale factor for public transport network stations, removed SVG scaling in Locus PNG versions
- removed leisure=ls_track from highways/tourism, moved highway=raceway upwards, moved residential landuse etc. to level 12+

3.1.5 07/03/16
- added caravan_site to low zoom markers, border for admin_level=3, natural=crevasse, low zoom markers for cities/capitals
- changed admin borders, rendering of some place names, rendering of low zoom (inter)national routes, moved low zoom highways to level 11 and lower, reduced caption/symbol distance for small SVG symbols (non-Locus), optimized very low zooms
- corrected spanish translation for overlay menus
- Locus: moved protected area borders to zoom level 16 because of rendering issues

3.1.4.1 10/02/16
- fixed path/footway rendering rules

3.1.3 09/02/16
- limited bicycle=no marking to relevant highways in cycling style
- restructured path rendering rules, fixed some missing trail_visibility information for path/footway without sac_scale in hiking style, fixed color for cycleway with foot=yes without surface information in hiking
- added bicycle access information for path/footway in hiking/city style, added weak priority for ele captions, leisure=picnic_table
- Locus: moved most captions for symbols to zoom level 17 and higher because of missing priorities/different collision management/missing dy on areas in Locus

3.1.2 10/01/16
- added oneway:bicycle=no for cycling style (turquoise arrow added where cycling is allowed in opposite direction of oneway streets), name captions in city style for retail/commercial/industrial/brownfield/garages/construction/greenfield, name caption for residential/farmyard/farm landuses
- changed ZL for high zoom forest/wood/desert captions

3.1.1 10/11/15
- optimized SVG symbols, rerendered PNG symbols
- changed rendering of tracks, rendering of routes at ZL 12+13, color of contour lines, rendering of pipelines
- added shop=travel_agency, new symbol for pub, amenity=bar

3.1.0 08/10/15
- low zoom areas are now much more usable: names for states and mountain ranges/areas are displayed, names of lakes/glaciers/woods/mountain ranges/protected for larger areas are displayed earlier and for smaller areas later (differs for city style)
- it's easier to distinguish between routes and highways as colors are optimized: (inter)national cycling routes are now violet, regional are red (already changed mtb routes and colors of major highways in earlier versions)
- improved Elements: limited symbols and captions somewhat to make low zooms less random and more usable
- added place=state, natural=mountain_range, natural=mountain_area for low zooms, bboxweight for poly_labels, zoom-min for ditch/stream/drain/river/canal/railway/pier/runway/apron/taxiway, different colors for some landscape names, small ford symbol for Elements low zooms
- changed rendering of settlement names, zoom-min for island captions/forest areas, low zoom hiking/cycling routes, captions & rendering of protected areas
- fixed rendering of low zoom motorway tunnels, volcano low zoom captions

3.0.6 19/09/15
- changed rendering for footways/paths without sac_scale for hiking style: brown means unpaved path/footway (or path without surface information); grey means paved path/footway (or footway without surface information)
- Locus: changed tunnels to Elevate 2 style (as dy isn't working properly on ways)
- corrected surface width for some highways
- limited national hiking/cycling routes to ZL8
- changed low to mid zoom rendering of highway refs, rendering of basin borders, (inter)national hiking routes on paths, colors of major highways, rendering of bridleways, zoom-min for bridges, track cores, xsd location
- removed leisure=track from ski pistes
- added glacier border, zoom-min for pistes, low zoom motorway tunnels, memorial types
- viewpoint now in both tourism and outdoor overlays

3.0.5 07/08/15
- added trail_visibility rendering to path/footway without sac_scale, added access=no for various items (rendered like access=private)
- added closed=yes to landcover and water areas (incl. fallback option) to avoid some rendering issues with double tagging on ways and relations
- changed access=no to access=acc_no for maps starting 30/07/15

3.0.4 19/07/15
- made contour lines optional for city style, disabled by default
- some items are now in several overlays (fuel in shops & cars, aerial ways in public transport & outdoor, alpine huts in outdoor & accommodation, toll in car & cycling style)
- changed rendering for path/footway in city style, color for mtb routes so that they distinguish better from roads, rendering for low zoom routes
- added kissing_gate, turnstile

3.0.3 23/06/15
- Locus: added .nomedia for map style chooser symbols
- removed cycleway=track/lane from footway/track/path/motorway
- added border to riverbank/natural=water, cycling: symbol for private/no bike gates starting zoom 15
- reduced area borders slightly
- optimized low zoom highways, low zoom local hiking routes, mid zoom street names

3.0.2 07/06/15
- Locus: uses now mapsforge 0.5 map styles including switchable overlays
- Locus optimizations: simplified some SVG symbols, moved building captions, new theme switcher icons
- added priority/display to street names/route refs

3.0.1 26/05/15
- added Locus version with limited support of new abilities and no switchable overlays
- added outline to SVG symbols for better perceptibility
- changed display of public transport stations, now analogous to public transport network of city style
- optimized low zoom rendering - no highway casings until level 13, changed cores until level 12, added various zoom-mins, changed border/railway rendering
- added bordertext for protected areas on high zooms, names for trunks/motorways, bic_designated/ft_designated, theme icons for Locus theme selector, slight transparency for white caption outlines
- removed underscores from filenames, some mapsforge 0.3 style file paths, basin/water caption from fountain, borders for some landcovers, pois with information=* from tourism=information
- changed rendering order for areas/pedestrian highways, rendering of fountain/basin/reservoir/drain/canal/aerialway, rendering of landscape names, rendering of waterway=dam, rendering of waterway names, rendering of cycleways with no surface information, rendering of runways
- moved ski pistes below paths

3.0.0 29/03/15
- switched to mapsforge rendertheme-v4, only compatible with apps supporting mapsforge 0.5 and higher, optimized for mapsforge 0.5.1
- added svg version, optimized for 320dpi
- added mapsforge styles (hiking, city, cycling), removed variations Elevelo & Elegant
- Elements now has the same styles as Elevate, the only difference is most zoom mins and low zoom markers are removed
- moved all symbols and captions in switchable overlays with english, french, german, italian and spanish labels
- separate style and overlay ids for all styles, layers and theme variation, so settings are remembered for each style/theme in OruxMaps
- replaced all dy for symbols with symbol-id/position
- made settlement names/routes/mtb tags switchable
- added switchable strong hiking/cycling routes for zoom level 14+
- city: added public transport routes overlay
- cycling: added emphasized cycling ways with surface information, changed cycling route colors
- added different zoom mins for different styles for some symbols
- transformed paths/footways to cycleways if bicycle=yes (cycling), transformed cycleways to footways with cycling marker if foot=yes (hiking/city)
- added priorities/display, map-background-outside, highway=emergency_access_point, natural=shingle, place=quarter, place=neighbourhood, place=farm, power=plant, station=subway, capital=2/4, cycleway=track/lane, transparency for sand/aerodrome/university/sea, pattern for bicycle=no on highways, access for highway areas, access=destination for parking
- changed low zoom markers, rendering for cliffs/ridges/aerialways, rendering for route refs, network rendering order, changed rendering for MTB-scale 5+6, separate rendering for railway=disused & abandoned, font size for contour lines text zl 16+, rendering of lock/dock/pier/bridleway/swimming_pool, limited toll to highways, rendering for places, captions for dam/weir/dock/lock, colors for post_box/atm/bank/fuel, simplified tracks for zoom 12/13, symbols for place_of_worship unknown/sports shop/gondola/cable_car/railway funicular, rendering of path/track etc. names, rendering of tunnels
- removed landcover with tunnel=yes, some building keys for POIs, limits for symbols eliminating captions on ways (unnecessary with mf 0.5)
- some clean-up, fine tuning and other changes I forgot

2.4.1 25/01/15
- added separate color for regional cycling routes (violet)
- removed place_of_worship from historic (like wayside_shrine)

2.4.0 04/01/15
- new appearance - changed rendering/colors for: buildings/wall/retaining_wall/dam etc., most highways/motorways/cycleways/motorway junctions/highway refs, tram, platforms, bridges, retail/military/industrial/school etc. landuses, place names, admin borders, peak names, pattern for pedestrian roads/areas, runways/aerodrome/helipad, powerlines, some fine-tuning
- improved routes: added separate color for local hiking routes (yellow), better visibility of route refs, some fine-tuning
- improved low zoom markers, major highway casings, bridges
- added separate rendering for MTB-scale 5+6, water_well, ele for cave_entrance, inhabited landuses color for lower zooms, taxiway bridges
- loosened dy value for OruxMaps so higher dpi themes can be used on lower dpi devices (e.g. 240dpi on 160dpi) and font-size a bit enlarged with OruxMaps setting
- limited paths/footway/steps/MTB-scale to zoom 13+
- removed POI areas with tunnel=yes
- combined all accompanying .txt-files

2.3.0.1 15/12/14
- fixed sea area problems when used with Locus maps

2.3.0 18/11/14
- added themes optimized for OruxMaps 6
- optimized rendering for mapsforge 0.4+
- moved large patterns to lower zoom levels
- changed motorway_junction, peak rendering zoom 13 and lower, track casings
- added map border

2.2.4 29/10/14
- Elegant: removed low zoom markers and limited peaks to zoom 14+ for better overview
- add zoom-min for military areas/waterways/polylabels, captions for ditch/drain, tunnel for railway=abandoned
- changed city and town name sizes at lower zoom levels, rendering retaining_wall, zoom-min for barriers for Elegant and Elevate, rendering of park etc. captions, rendering railway=abandoned
- removed bridge for areas 

2.2.3 17/09/14
- added pattern for glacier, name for weir/lock, leaf_type, railway=abandoned/disused, aerialway=goods, symbol for drag_lift 
- new rendering for wall, retaining_wall, dam, weir, dock, lock
- some changes for Elevelo (removed sled/nordic pistes, MTB scale perceptibility improvement, more contrast in route colors)
- simplified track intervals
- reduced generator:source to the more visible ones
- changed most nodes to any
- removed members-only huts from low zoom marker for alpine huts

2.2.2 05/08/14
- changed file/folder names so that it's easier to guess the use of the theme (added hiking/cycling/city/backcountry)
- added sport=climbing, separate symbol for emergency=phone, circles to hiking/cycling nodes
- made surface coloring more visible

2.2.1 19/06/14
- removed leisure=park from protected areas, wrong rendering of motorway_junction numbers at Zoom 19+
- added ways for towers, oneway=-1, ferry_terminal, defibrillator
- changed trail_visibility value combinations

2.2.0 01/06/14
- optimized rendering at zoom 12 and 13 for place names
- limited poi symbols to zoom 14 and larger and added low zoom markers (zoom 12+13) for important pois
- included MTB-scale in Elevelo (not in Elements because of sac_scale)
- added symbol for farmyard, archaeological_site, wayside_shrine, tundra
- removed green overlay for protected areas at lower zooms
- changed priority for camp_sites/caravan_sites, rendering for landfill, contour lines at lower zooms, rendering of surface

2.1.2 11/05/14
- added zoom-min for huts, name for tourism=information without information details 
- improved motorway_junction, aeroway symbols
- removed surface coloring for major highways

2.1.1 04/05/14
- Elements: removed zoom-min for shelter caption, green overlay for protected areas
- fixed grave_yard caption
- added surface coloring to highways (except path, track, byway, bridleway, motorway)
- adjusted some dy for Java map viewers

2.1.0 19/03/14
- new variation: Elements with cycling & hiking routes and little zoom-mins - for sparsely populated/mapped areas
- added emergency phone, mini_roundabout, desert, vending=bicycle_tube, religion=buddhist/shinto/hindu, border_control, raceway, bus_guideway, helipad area
- improved contour lines, closed piste areas
- changed MTB routes to orange
- some clean-up & restructuring & zoom-min changes

2.0.1 09/03/14
- fixed tertiary_link, ele for summits, ford on nodes
- added buildings to captions, symbol for sports_centre
- some clean-up & zoom-min changes

2.0.0 22/02/14
- new theme sizes: L for xhdpi (300+) and XL for xxhdpi (450+) devices
- new variation: Elevelo with cycling routes instead of hiking routes, therefore no cyling routes in other variants anymore
- completely reworked symbol set: unified & optimized, lots of modifications, different glow
- new symbols for bench, geyser, info terminal, railway crossings, sports shop, train station, via ferrata, waterfall, aerialways, information office
- new larger patterns at zoom 16+
- new cemetary pattern, reworked fell/heath/marsh/rock/scree/scrub pattern
- new rendering for military areas/swimming areas
- added drinking_water for fountains, toll highways, fords
- improved hknetworks on tracks
- removed locus bug workaround (bug is fixed in Locus 2.19)
- switch to one ressource folder with relative paths for Locus themes
- some clean-up and fine-tuning

1.3.1 01/02/14
- improved pattern protected_area z16+, rendering of safety measures ways, wetland pattern, zoom-min for landcover, hike nodes, piste:downhill
- added name for graveyard/cemetery, .nomedia file, slight indicator for sac_scale T5/T6, earlier names for camp_site/caravan_site
- removed cycle networks at zoom 11-14 in Elegant

1.3.0 12/01/14
- new rendering of hiking routes, many thanks to Maki for inspiration!
- new folder name for symbols/patterns, separate download for easier installation on Locus
- added trail_visibility, winter_room for alpine_huts, rendering of various POI ways without building tag, market_place, chalet, barrier=block, shelter_type, separate color for farmland, waterway bridges
- improved rendering of hkr refs, rendering of tunnels, safety_rope and ladder symbol, rendering of safety measures way, rock pattern, oneway symbol, leisure=track, ridge/arete, highway=track
- changed early appearance of alpine_hut names (reason: too often wrong tagged), width of highway=cycleway/service, core color cycleway, color of waterways/bodies of water, pipeline caption color, footway/bridge/barrier color, color for various POI areas
- moved POI name block for better priorities, adjusted some POI zoom-min
- removed transparency from beach/sand, coastline, transparency of bodies of water at zoom till 13, alpine_hut without name
- better "glow" for non-sjjb symbols
- workarounds for Locus "~"-Bug on nodes
- some fine-tuning

1.2.1 25/12/13
- improved rendering of sled pistes, school/college/university areas, historic buildings/areas, biergarten area, tourism=attraction, spring rendering
- removed swimming symbol from swimming_pools with sport=swimming
- reduced font-size for path etc. names
- refined forest pattern, rock pattern

1.2.0 17/12/13
- new subtheme "Elegant" for cities (without hiking routes and less obtrusive paths/footways)
- new rendering for cycle networks, blue borders on highways
- names for nearly every symbol starting zoom 18
- added lots of shops, name for restaurant nodes, name for pipelines, waterways/pipelines in tunnels, symbol for tourism=information without further details, closed=no to networks
- simplified place_of_worship etc. and more clean-up
- improved viewpoints, railway ways, access patterns, rock pattern, swimming_pool/swimming/water_park, public transport stations, highway casings, protected area pattern zoom 14+
- changed rendering for tourist attraction ways/areas/added area pattern, bridges, walls
- reduced zoom-min for barrier, bus_stop/tram_stop/railway halt captions
- installation instructions included
- lots of fine-tuning

1.1.3 01/12/13
- changed tourism information to any, area colors: industrial etc./school etc./retail, lowered level of residential/industrial etc./retail 
- improved attraction, pedestrian area/highway, bus_stop/tram_stop captions, swimming_pool
- turned some nodes into any, added memorial/monument area
- joined nature_reserve/national_park/protected_area for new handling in OAM
- added safety_rope, rungs, ladder

1.1.2 23/11/13
- improved leisure areas, nature_reserve, access patterns, highway=construction, construction bridges, rendering of motorway junctions and motorway refs, tunnels, conflicting refs/names of highways, highway areas
- added motorway junction names, zoom-min at way tourism attraction captions, transparency to buildings zoom-min=17
- removed city circles, tunnel platforms
- simplified shops, highway captions
- less transparency in patterns

1.1.1 17/11/13
- fixed meadow names
- added motorway junctions
- changed highway=construction
- changed orchard/protected area names to poly labels

1.1.0 15/11/13
- massive code clean-up and restructuring, lots of fine-tuning
- reduced and adjusted landuse/area colors
- new wood/forest patterns, incl. coniferous/deciduous
- hiking routes enhanced rendering on tracks/paths, now visible on roads
- improved: turning circles, highway refs, places, places of worship, tourism attraction, tracks, barrier ways, cliffs, landfill/quarry, tourist information, pier, bridges, tunnels, streets, administrative borders, dam, dock, weir, lock, walls, steps, suburb, river/stream/canal/ditch width
- added: isolated_dwelling, grassland, tourism attraction, orchard, vineyard, spring drinking_water no/yes, doctors, geyser, coastline, nordic pistes, gorge, water_point, wayside_cross, polylabels: forest/orchard, waterfall, rapids, symbol parking_private, police, slipway, museum, lighthouse, aeroway gate, golf, shooting, embassy, zoo, ele to places, ele/name to guidepost/viewpoint, ruins/castle area, summit:cross, pipeline, weir symbol, generator, alpine_hut access, ele to lots of amenities/spring/place_of_worship, ele to bodies of water, sac_scale to steps
- changed mountain pass/building text color to be in line with general coloring, changed peak/place color
- changed symbols for bench, picnic_site, bus stop, tram stop
- added serif italic font style for landscape information etc.
- some fixes for Locus

1.0.7 15/10/13
- removed: startoffset, tree limit rule
- less transparency for areas
- alpine_hut icon without zoom restriction again
- less obstrusive nature_reserve pattern
- better visibility for fell pattern

1.0.6 12/10/13
- added zoom restriction to some amenities/aerial ways
- reduced transparency for water, added transparency for reservoirs

1.0.5 12/10/13
- transparency in landuses/patterns
- changed some caption colors
- smaller sled pistes
- new rendering for bridleways
- optimized route refs/names

1.0.4 05/10/13
- code clean-up
- adjusted zoom restriction and sizes for various captions
- optimized swimming/spa etc.
- added historic symbols
- removed area for closed cliffs
- more transparency in wood pattern

1.0.1-1.03 30/09/13 
- zoom restriction for alpine_hut icon
- zoom restriction for elevation information
- bug fix

1.0 30/09/13 
- first public release


-------------------------------------------------------------------------
LICENSES
-------------------------------------------------------------------------

Elevate theme family
********************
including Elevate & Elements

by Tobias Kuehn
Contact: http://www.eartrumpet.net/contact/

Mapsforge theme for OpenAndroMaps
formerly based on OpenAndroMaps HC


License:
********

This theme is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License: http://creativecommons.org/licenses/by-nc-sa/3.0/

This means you can feel free to reuse everything I made if you stick to those conditions:
- attribute the origin (for example: "symbols/patterns/code based on Elevate theme by Tobias Kühn, http://www.openandromaps.org/en/legend/elevate-mountain-hike-theme")
- don't use it for commercial purposes, that means for example you are not allowed to include (also parts) or directly download with a commercial app; if in doubt contact me
- if you use some of my work it has to be under the same license
- have a look at the licenses of the resources I used below, those can differ - please also stick to those

I'm always happy to hear someone can use my work, so it would be nice if you contact me to let me know 


Symbols and patterns licenses:
******************************

- all patterns, symbols for cliff, geyser, ladder, oneways, peaks, railway_crossings, ridge, rungs, safety_rope, via ferrata, volcano, waterfall, wilderness hut, goods_lift, drag_lift, bridge_movable, turnstile, hot spring, public transport, cities, apartment and modifications/adaptions of other symbols by Tobias Kuehn - CC BY NC SA 3.0 license
- most symbols: http://www.sjjb.co.uk/mapicons - CC-0 license
- waymark symbols based on: Locus internal theme, Apache License
- rapids and chemist symbols are adaptions of original symbols from: http://mapicons.nicolasmollet.com - CC BY SA 3.0 license
- sport shop contains a modification of an original symbol from: http://openclipart.org/detail/173952/shoe-by-spacefem-173952 - Public Domain
- cable_car, chair_lift, gondola, rail_funicular are modifications of original symbols from: http://wiki.openstreetmap.org/wiki/Template:Aerialway/doc - CC BY SA 2.0 license
- bench is a modification of an original symbol from: http://wiki.openstreetmap.org/wiki/File:Amenity_Bench-br.svg - Public Domain
- farmyard, emergency_access_point: http://osm-icons.org - CC-0 by Markus59
- defibrillator, water_well: http://osm-icons.org - CC BY SA 2.0 license by Msemm


