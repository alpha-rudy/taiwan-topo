-- process.lua - tilemaker profile for the Taiwan-TOPO custom PMTiles schema.
--
-- Input is $(MAPSFORGE_PBF): the already-prepared, region-clipped, name-enriched
-- OSM PBF that the Mapsforge build consumes. Hiking/cycle network tags
-- (hknetwork / network / highlight) and contour/elevation ways are already
-- injected onto features by the upstream pipeline (process_osm.py + the
-- elevation PBF), so they are handled here as plain way/node tags.
--
-- Layer set and zoom thresholds mirror osm_scripts/tag-mapping.xml (the
-- Mapsforge tag mapping), clamped to the PMTiles maxzoom of 14.
--
-- API: tilemaker v3 global-function style (Find / Layer / Attribute / MinZoom).

-- Only nodes carrying one of these keys are passed to node_function (perf).
node_keys = {
    "place", "ele", "natural", "amenity", "tourism", "shop", "historic",
    "man_made", "leisure", "information", "mountain_pass", "emergency",
    "barrier", "highway", "railway", "aerialway"
}

-- ---------------------------------------------------------------------------
-- helpers
-- ---------------------------------------------------------------------------

-- Copy localized names produced upstream (name / name:en / name:zh).
local function set_names()
    local n = Find("name")
    if n ~= "" then Attribute("name", n) end
    local en = Find("name:en")
    if en ~= "" then Attribute("name_en", en) end
    local zh = Find("name:zh")
    if zh ~= "" then Attribute("name_zh", zh) end
end

local function in_set(value, set)
    return value ~= "" and set[value] == true
end

-- hiking POIs: (key, value) -> MapLibre minzoom, from MOI_OSM.xml's first zoom
-- for the symbol and tag-mapping.xml's zoom-appear, whichever is later, minus one
local hiking_poi_zoom = {
    tourism = { alpine_hut=12, wilderness_hut=12, camp_site=12, viewpoint=13, information=13 },
    amenity = { shelter=12, drinking_water=13, toilets=13 },
    natural = { spring=13 },
    man_made = { water_well=13 },
    highway = { trailhead=14 },
    information = { guidepost=14, trail_milestone=14 },
}
local hiking_poi_keys = { "tourism", "amenity", "natural", "man_made", "highway", "information",
                          "shelter_type", "drinking_water", "access", "reservation",
                          "winter_room", "tower", "checkpoint:type", "highlight" }

-- Values tag-mapping.xml keeps, per key (equivalent-values included), mapped
-- to their zoom-appear (0 when the mapping gives none): Mapsforge drops every
-- other value, and the theme's rules are written for what is left. Read from
-- the mapping itself, next to this directory, so the two cannot drift apart.
local tag_mapping_xml = (function()
    local dir = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") or "."
    local f = assert(io.open(dir .. "/../tag-mapping.xml", "r"), "tag-mapping.xml not found")
    local xml = f:read("*a")
    f:close()
    return xml
end)()

local function read_mapping(section)
    local body = assert(tag_mapping_xml:match("<" .. section .. ">(.-)</" .. section .. ">"),
                        "no <" .. section .. "> in tag-mapping.xml")
    local m, canon = {}, {}
    for tag in body:gmatch("<osm%-tag%s[^>]*>") do
        -- attributes are quoted with ' or " (both occur in tag-mapping.xml)
        local k = tag:match("key=[\"']([^\"']*)[\"']")
        local v = tag:match("value=[\"']([^\"']*)[\"']")
        if k and v then
            local za = tonumber(tag:match("zoom%-appear=[\"']([^\"']*)[\"']")) or 0
            m[k] = m[k] or {}
            canon[k] = canon[k] or {}
            m[k][v] = za
            canon[k][v] = v
            local eq = tag:match("equivalent%-values=[\"']([^\"']*)[\"']")
            if eq then for e in eq:gmatch("[^,]+") do m[k][e] = za; canon[k][e] = v end end
        end
    end
    return m, canon
end

-- poi_canon maps a raw value to the value Mapsforge stores for it (an
-- equivalent value such as amenity=clinic is stored as hospital).
local poi_mapping, poi_canon = read_mapping("pois")
local way_mapping, way_canon = read_mapping("ways")

-- Road and railway keys the theme tests, stored as Mapsforge stores them (the
-- tag mapping's main value, e.g. surface=paved as smooth_paved) and only when
-- the mapping keeps the value.
local way_detail_keys = { "surface", "service", "cycleway", "foot", "ford", "embankment" }
local function set_way_details(keys)
    for _, k in ipairs(keys) do
        local cv = way_canon[k] and way_canon[k][Find(k)]
        if cv ~= nil then Attribute(k, cv) end
    end
end

-- tunnel / bridge as the theme reads them: present for any value but "no";
-- closed for the theme's closed="yes|no" rules (a raceway or platform drawn as
-- a ring is an area there, not a line)
local function set_tunnel_bridge()
    local tunnel, bridge = Find("tunnel"), Find("bridge")
    if tunnel ~= "" and tunnel ~= "no" then Attribute("tunnel", "yes") end
    if bridge ~= "" and bridge ~= "no" then Attribute("bridge", "yes") end
    if IsClosed() then Attribute("closed", "yes") end
end

local function hiking_poi_minzoom()
    local z = nil
    for k, vals in pairs(hiking_poi_zoom) do
        local mz = vals[Find(k)]
        if mz ~= nil and (z == nil or mz < z) then z = mz end
    end
    return z
end

-- Generic POIs the theme labels: (key, value) -> the first Mapsforge zoom of
-- the value's caption in MOI_OSM.xml (hiking style and the overlays it turns
-- on). Mapsforge shows a POI only when the tag mapping keeps it and the theme
-- draws it, so the other POIs (shops, restaurants, air-raid shelters, ...) are
-- left out of the tiles.
local generic_poi_theme_zoom = {
    amenity = {
        bench=14, bicycle_rental_Moovo=15, bicycle_rental_YouBike=15, bus_station=14, cinema=14,
        college=14, doctors=14, drinking_water=14, embassy=14, ferry_terminal=14,
        fire_station=14, fountain=14, hospital=14, kindergarten=14, library=14, pharmacy=14,
        place_of_worship=14, police=14, recycling=14, school=14, shelter=13, shower=14,
        telephone=14, theatre=14, toilets=14, university=14, water_point=14
    },
    tourism = {
        alpine_hut=13, attraction=14, camp_site=13, information=14, museum=14, picnic_site=14,
        picnic_table=14, viewpoint=13, wilderness_hut=13, zoo=14
    },
    historic = {
        archaeological_site=14, castle=14, memorial=14, monument=14, ruins=14, wayside_cross=14,
        wayside_shrine=14
    },
    man_made = {
        communications_tower=14, lighthouse=14, summit_board=7, tower=14, water_well=14,
        windmill=14
    },
    leisure = {
        golf=14, golf_course=14, picnic_site=14, picnic_table=14, playground=14, slipway=14,
        sports_centre=14, stadium=14, water_park=14
    },
    information = {
        board=14, guidepost=14, mobile=14, office=14, terminal=14, trail_milestone=15
    },
    emergency = {
        defibrillator=14, landing_site=14, phone=14
    },
    barrier = {
        border_control=14
    },
}

-- Areas the theme fills (MOI_OSM.xml area rules, hiking style): key -> the
-- values Mapsforge stores for them. A closed way or multipolygon with one of
-- these goes to the landcover layer with every key in landcover_attr_keys the
-- theme's rules test, stored as Mapsforge stores it (tag mapping main value).
local landcover_theme = {
    ["landuse"] = {
        ["allotments"]=true, ["brownfield"]=true, ["cemetery"]=true, ["commercial"]=true,
        ["construction"]=true, ["farm"]=true, ["farmland"]=true, ["farmyard"]=true,
        ["forest"]=true, ["grass"]=true, ["greenfield"]=true, ["industrial"]=true,
        ["landfill"]=true, ["meadow"]=true, ["orchard"]=true, ["quarry"]=true, ["railway"]=true,
        ["recreation_ground"]=true, ["residential"]=true, ["retail"]=true,
        ["village_green"]=true, ["vineyard"]=true, ["wood"]=true
    },
    ["natural"] = {
        ["beach"]=true, ["cliff"]=true, ["crater"]=true, ["crevasse"]=true, ["desert"]=true,
        ["fell"]=true, ["glacier"]=true, ["grassland"]=true, ["heath"]=true, ["marsh"]=true,
        ["rock"]=true, ["sand"]=true, ["scree"]=true, ["scrub"]=true, ["shingle"]=true,
        ["wetland"]=true, ["wood"]=true
    },
    ["leisure"] = {
        ["common"]=true, ["dog_park"]=true, ["garden"]=true, ["golf_course"]=true,
        ["park"]=true, ["pitch"]=true, ["playground"]=true, ["sports_centre"]=true,
        ["stadium"]=true, ["swimming_pool"]=true, ["water_park"]=true
    },
    ["amenity"] = {
        ["college"]=true, ["doctors"]=true, ["fountain"]=true, ["grave_yard"]=true,
        ["parking"]=true, ["place_of_worship"]=true, ["restaurant"]=true, ["school"]=true,
        ["shelter"]=true, ["theatre"]=true, ["toilets"]=true, ["university"]=true
    },
    ["aeroway"] = {
        ["aerodrome"]=true, ["apron"]=true, ["helipad"]=true, ["runway"]=true, ["terminal"]=true
    },
    ["tourism"] = {
        ["alpine_hut"]=true, ["attraction"]=true, ["camp_site"]=true, ["caravan_site"]=true,
        ["hostel"]=true, ["hotel"]=true, ["picnic_site"]=true, ["zoo"]=true
    },
    ["power"] = {
        ["generator"]=true, ["plant"]=true, ["station"]=true
    },
    ["sport"] = {
        ["shooting"]=true, ["swimming"]=true, ["tennis"]=true
    },
    ["historic"] = {
        ["archaeological_site"]=true, ["castle"]=true, ["memorial"]=true, ["monument"]=true,
        ["ruins"]=true
    },
    ["man_made"] = {
        ["embankment"]=true, ["pier"]=true
    },
    ["shop"] = {
        ["bakery"]=true, ["beverages"]=true, ["bicycle"]=true, ["car"]=true,
        ["convenience"]=true, ["doityourself"]=true, ["mall"]=true, ["sports"]=true,
        ["supermarket"]=true
    },
    ["railway"] = {
        ["station"]=true
    },
    ["information"] = {
        ["office"]=true
    },
    ["piste:type"] = {
        ["downhill"]=true, ["sled"]=true
    },
    ["emergency"] = {
        ["landing_site"]=true
    },
}
local landcover_attr_keys = {
    "landuse", "natural", "leisure", "amenity", "aeroway", "tourism", "power", "sport",
    "historic", "man_made", "shop", "railway", "information", "piste:type", "emergency", "wood",
    "leaf_type", "access", "boundary"
}

-- ---------------------------------------------------------------------------
-- lookup tables
-- ---------------------------------------------------------------------------

local hiking_networks = { iwn=true, nwn=true, rwn=true, lwn=true, uwn=true }
local trail_sac_scale = { hiking=true, mountain_hiking=true, demanding_mountain_hiking=true,
                          alpine_hiking=true, demanding_alpine_hiking=true, difficult_alpine_hiking=true }
local trail_visibility = { excellent=true, good=true, intermediate=true, bad=true, horrible=true, no=true }
local tracktypes = { grade1=true, grade2=true, grade3=true, grade4=true, grade5=true }
local trail_access = { destination=true, private=true, no=true }
local cycle_networks  = { icn=true, ncn=true, rcn=true, lcn=true, ucn=true, mtb=true }

-- sea and nosea are the land/sea mask, as in the Mapsforge build: the frame is
-- one natural=sea polygon and the land is drawn back over it from natural=nosea
-- polygons (tools/sealand-creator.sh). Both go to the water layer with their
-- class, and style.json paints nosea in the land colour right after sea.
local water_natural    = { water=true, sea=true, nosea=true, bay=true, spring=false }
local waterway_class   = { river=true, stream=true, canal=true, drain=true, ditch=true }
local waterway_minzoom = { river=6, canal=9, stream=11, drain=11, ditch=11 }

-- highway class -> minzoom. Trails and tracks (path, footway, steps,
-- bridleway, byway, track) use the tag mapping's zoom-appear minus one:
-- MapLibre's 512 px tiles show at zoom Z what Mapsforge's 256 px tiles show at
-- Z+1, and the style draws them from there. The other classes are unchanged.

-- place class -> minzoom
local place_minzoom = {
    country=4, state=5, region=6, county=7, city=7, town=9,
    village=11, hamlet=12, suburb=11, neighbourhood=13, locality=13,
    isolated_dwelling=14, island=8, islet=12
}

-- ---------------------------------------------------------------------------
-- contour handling
-- ---------------------------------------------------------------------------

-- Each contour_* key carries an "elevation_*" class. MinZoom is the OSM tag
-- mapping's zoom-appear (osm_scripts/tag-mapping.xml) CLAMPED to the tile
-- maxzoom of 14: intervals that the Mapsforge theme only draws above z14
-- (160m at 15, 80m at 16, ext minor at 15) are still stored in the z14 tiles
-- so the style can reveal them via client overzoom, exactly like Mapsforge
-- stores them in its base-14 zoom interval. The "interval" + "class"
-- attributes let style.json reproduce the per-zoom contour rules.
local contour_specs = {
    { key="contour_ext",   zoom={ elevation_major=8,  elevation_medium=12, elevation_sub=14, elevation_minor=14 } },
    { key="contour_1280m", zoom={ elevation_major=11 } },
    { key="contour_640m",  zoom={ elevation_major=13, elevation_medium=13 } },
    { key="contour_320m",  zoom={ elevation_major=14, elevation_medium=14, elevation_minor=14 } },
    { key="contour_160m",  zoom={ elevation_major=14, elevation_medium=14, elevation_minor=14 } },
    { key="contour_80m",   zoom={ elevation_major=14, elevation_medium=14, elevation_minor=14 } },
}

local function handle_contour()
    for _, spec in ipairs(contour_specs) do
        local cls = Find(spec.key)
        if cls ~= "" then
            local z = spec.zoom[cls]
            if z ~= nil then
                Layer("contour", false)
                Attribute("class", cls)
                Attribute("interval", spec.key)
                MinZoom(z)
            end
            return true   -- a contour way is only a contour
        end
    end
    return false
end

-- ---------------------------------------------------------------------------
-- node entry point
-- ---------------------------------------------------------------------------

function node_function()
    -- places (labels)
    local place = Find("place")
    if place ~= "" then
        Layer("place", false)
        Attribute("class", place)
        set_names()
        local cap = Find("capital")
        if cap ~= "" then Attribute("capital", cap) end
        MinZoom(place_minzoom[place] or 13)
        return
    end

    -- peaks / elevation markers
    -- The summit name lives on man_made=summit_board, not on the peak:
    -- process_osm.py writes "<name>, <ele>m" there with zl (0 = 玉山, 雪山主峰,
    -- 北大武山; 1 = 百岳; 2 = 小百岳) and cat, and strips the name (and,
    -- near a board, the ele) from natural=peak. Survey points carry a
    -- descriptive name ("三等三角點 6303") that the Mapsforge theme does not
    -- print. style.json draws them with the theme's symbols and captions.
    local natural = Find("natural")
    local ele = Find("ele")
    local man_made = Find("man_made")
    local is_board = (man_made == "summit_board")
    local is_peak = (natural == "peak" or natural == "volcano" or
                     natural == "saddle" or Find("mountain_pass") == "yes")
    local elenum = tonumber(ele)
    if is_board or is_peak then
        Layer("ele_point", false)
        local zl = tonumber(Find("zl"))
        if is_board then
            Attribute("class", "summit_board")
            if zl ~= nil then AttributeNumeric("zl", zl) end
            local cat = Find("cat")
            if cat ~= "" then Attribute("cat", cat) end
        else
            Attribute("class", natural ~= "" and natural or "mountain_pass")
        end
        if Find("is_in") == "taiwan" then Attribute("is_in", "taiwan") end
        set_names()
        if elenum ~= nil then AttributeNumeric("ele", math.floor(elenum + 0.5)) end
        -- The first MapLibre zoom the theme draws them at (Mapsforge zoom - 1):
        -- boards by zl, named peaks and volcanoes at 11, the other peaks at 12.
        if is_board then
            if zl == 0 then MinZoom(6)
            elseif zl == 1 or zl == 2 then MinZoom(9)
            else MinZoom(11) end
        elseif natural == "volcano" or Find("name") ~= "" then MinZoom(11)
        else MinZoom(12) end
        return
    end

    -- hiking POIs, drawn with the theme's symbols. They carry the raw tags the
    -- theme tests; MinZoom is the later of the theme's first zoom and the tag
    -- mapping's zoom-appear, minus one (MapLibre zoom = Mapsforge zoom - 1).
    local hz = hiking_poi_minzoom()
    if hz ~= nil then
        Layer("poi", false)
        for _, k in ipairs(hiking_poi_keys) do
            local v = Find(k)
            if v ~= "" and poi_mapping[k] and poi_mapping[k][v] then Attribute(k, v) end
        end
        -- class / subclass as for the other POIs, so the plain name label can
        -- still show the subtypes the icon layers do not draw
        for _, k in ipairs({ "amenity", "tourism", "man_made", "information", "highway", "natural" }) do
            local v = Find(k)
            if v ~= "" then
                Attribute("class", k)
                Attribute("subclass", v)
                break
            end
        end
        local zl = tonumber(Find("zl"))
        if zl ~= nil then AttributeNumeric("zl", zl) end
        if elenum ~= nil then AttributeNumeric("ele", math.floor(elenum + 0.5)) end
        set_names()
        MinZoom(hz)
        return
    end

    -- other elevation markers and survey points
    if ele ~= "" then
        Layer("ele_point", false)
        Attribute("class", man_made == "survey_point" and "survey_point" or "ele_marker")
        set_names()
        if elenum ~= nil then AttributeNumeric("ele", math.floor(elenum + 0.5)) end
        MinZoom(12)
        return
    end

    -- generic POIs: the first key whose value the theme labels, looked up by
    -- the value Mapsforge stores. They show from the later of the theme's
    -- caption zoom and the tag mapping's zoom-appear, minus one (MapLibre zoom
    -- = Mapsforge zoom - 1). Tiles stop at 14, so a later zoom is carried as
    -- minzoom for style.json to test.
    local poi_keys = { "amenity", "tourism", "shop", "historic", "man_made",
                       "leisure", "information", "emergency", "barrier" }
    for _, k in ipairs(poi_keys) do
        local v = Find(k)
        local za = poi_mapping[k] and poi_mapping[k][v]
        local cv = poi_canon[k] and poi_canon[k][v]
        local tz = cv and generic_poi_theme_zoom[k] and generic_poi_theme_zoom[k][cv]
        if tz ~= nil and za ~= nil then
            local z = math.max(tz, za) - 1
            Layer("poi", false)
            Attribute("class", k)
            Attribute("subclass", v)
            set_names()
            MinZoom(math.min(z, 14))
            if z > 14 then AttributeNumeric("minzoom", z) end
            return
        end
    end
end

-- ---------------------------------------------------------------------------
-- way entry point
-- ---------------------------------------------------------------------------

function way_function()
    -- contours first (dense, cheap to reject)
    if handle_contour() then return end

    local highway  = Find("highway")
    local railway  = Find("railway")
    local waterway = Find("waterway")
    local natural  = Find("natural")
    local landuse  = Find("landuse")
    local leisure  = Find("leisure")
    local boundary = Find("boundary")
    local hknet    = Find("hknetwork")
    local cycnet   = Find("network")
    local highlight= Find("highlight")

    -- hiking routes (member ways carry hknetwork / highlight from process_osm.py)
    if in_set(hknet, hiking_networks) or highlight == "yes" then
        Layer("hiking_route", false)
        if in_set(hknet, hiking_networks) then Attribute("network", hknet) end
        if highlight == "yes" then Attribute("highlight", "yes") end
        local ref = Find("ref")
        if ref ~= "" then Attribute("ref", ref) end
        -- the theme draws routes only where the way is not a tunnel
        local rt = Find("tunnel")
        if rt ~= "" and rt ~= "no" then Attribute("tunnel", "yes") end
        set_names()
        MinZoom(10)   -- tag mapping: hknetwork / highlight appear at 11 (config.json allows 10)
        -- a hiking way may also be a path; fall through to draw the way too
    end

    -- cycle routes
    if in_set(cycnet, cycle_networks) then
        Layer("cycle_route", false)
        Attribute("network", cycnet)
        set_names()
        MinZoom(12)
    end

    -- water areas
    if in_set(natural, water_natural) or landuse == "reservoir" or
       landuse == "basin" or Find("waterway") == "riverbank" then
        Layer("water", true)
        Attribute("class", natural ~= "" and natural or landuse)
        return
    end

    -- waterways (lines)
    if in_set(waterway, waterway_class) then
        Layer("waterway", false)
        Attribute("class", waterway)
        set_names()
        -- tag-mapping.xml zoom-appear minus one (MapLibre zoom = Mapsforge zoom - 1)
        MinZoom(waterway_minzoom[waterway])
        return
    end

    -- land use and land cover areas the theme fills, and buildings
    if IsClosed() or IsMultiPolygon() then
        local lz = nil   -- earliest zoom-appear of a key the theme fills
        for k, vals in pairs(landcover_theme) do
            local raw = Find(k)
            local cv = way_canon[k] and way_canon[k][raw]
            if cv ~= nil and vals[cv] then
                local za = way_mapping[k][raw]
                if za == 0 then za = 14 end
                if lz == nil or za < lz then lz = za end
            end
        end
        local b = Find("building")
        local bv = way_canon.building[b]
        if lz ~= nil then
            Layer("landcover", true)
            for _, k in ipairs(landcover_attr_keys) do
                local cv = way_canon[k] and way_canon[k][Find(k)]
                if cv ~= nil then Attribute(k, cv) end
            end
            if bv ~= nil then Attribute("building", bv) end
            -- the theme's parent rules also test tunnel and area
            local t = Find("tunnel")
            if t ~= "" and t ~= "no" then Attribute("tunnel", "yes") end
            if way_canon.area[Find("area")] ~= nil then Attribute("area", "yes") end
            -- tiles stop at 14: a later zoom is carried as minzoom for style.json
            MinZoom(math.min(lz - 1, 14))
            if lz - 1 > 14 then AttributeNumeric("minzoom", lz - 1) end
        end
        if bv ~= nil then
            Layer("building", true)
            local h = way_canon.historic[Find("historic")]
            if h ~= nil then Attribute("historic", h) end
            MinZoom(way_mapping.building[b] - 1)
        end
    end

    -- boundaries: only what tag-mapping.xml keeps, from its zoom-appear
    -- minus one. boundary=administrative itself is disabled there; admin
    -- borders come in through admin_level (2, 4-8: no villages).
    local bz, al = nil, nil
    if boundary == "administrative" then
        al = way_canon.admin_level[Find("admin_level")]
        if al ~= nil then bz = way_mapping.admin_level[Find("admin_level")] end
    elseif way_canon.boundary[boundary] ~= nil then
        bz = way_mapping.boundary[boundary]
    end
    if bz ~= nil then
        Layer("boundary", false)
        Attribute("class", way_canon.boundary[boundary] or boundary)
        if al ~= nil then Attribute("admin_level", al) end
        local pc = Find("protect_class")
        if pc ~= "" then Attribute("protect_class", pc) end
        set_names()
        MinZoom(bz - 1)
        return
    end
    if boundary == "administrative" then return end

    -- transportation (roads / trails / rail / aerialway)
    -- roads and trails: only the values tag-mapping.xml keeps, from its
    -- zoom-appear minus one (MapLibre zoom = Mapsforge zoom - 1)
    local hz = way_mapping.highway[highway]
    if hz ~= nil then
        Layer("transportation", false)
        Attribute("class", highway)
        set_names()
        set_tunnel_bridge()
        if Find("area") == "yes" then Attribute("area", "yes") end
        set_way_details(way_detail_keys)
        -- the tag values the Mapsforge theme tests for trails and tracks; other
        -- values are dropped by tag-mapping.xml, so they are left out here too
        local sac = Find("sac_scale")
        if trail_sac_scale[sac] then Attribute("sac_scale", sac) end
        local tv = Find("trail_visibility")
        if trail_visibility[tv] then Attribute("trail_visibility", tv) end
        local tt = Find("tracktype")
        if tracktypes[tt] then Attribute("tracktype", tt) end
        local access = Find("access")
        if trail_access[access] then Attribute("access", access) end
        MinZoom(hz - 1)
        return
    end
    -- railways: only the values tag-mapping.xml keeps, as in the Mapsforge map
    -- (no proposed, construction or razed lines)
    local rz = way_mapping.railway[railway]
    if rz ~= nil then
        Layer("transportation", false)
        Attribute("class", "railway")
        Attribute("subclass", way_canon.railway[railway])   -- e.g. monorail as narrow_gauge
        set_names()
        set_tunnel_bridge()
        if Find("area") == "yes" then Attribute("area", "yes") end
        set_way_details({ "gauge" })
        MinZoom(rz - 1)   -- rail from 6, the others from 11
        return
    end
    local aerialway = Find("aerialway")
    if aerialway ~= "" then
        Layer("transportation", false)
        Attribute("class", "aerialway")
        Attribute("subclass", aerialway)
        set_names()
        MinZoom(12)
        return
    end
end
