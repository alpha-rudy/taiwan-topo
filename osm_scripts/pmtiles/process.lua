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

-- Values tag-mapping.xml keeps on POIs, per key (equivalent-values included):
-- Mapsforge drops every other value, and the theme's rules are written for
-- what is left, so the hiking POIs carry only these. Read from the mapping
-- itself, next to this directory, so the two cannot drift apart.
local poi_mapping = (function()
    local dir = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") or "."
    local f = assert(io.open(dir .. "/../tag-mapping.xml", "r"), "tag-mapping.xml not found")
    local xml = f:read("*a")
    f:close()
    local pois = assert(xml:match("<pois>(.-)</pois>"), "no <pois> in tag-mapping.xml")
    local m = {}
    for tag in pois:gmatch("<osm%-tag%s[^>]*>") do
        local k = tag:match("key='([^']*)'")
        local v = tag:match("value='([^']*)'")
        if k and v then
            m[k] = m[k] or {}
            m[k][v] = true
            local eq = tag:match("equivalent%-values='([^']*)'")
            if eq then for e in eq:gmatch("[^,]+") do m[k][e] = true end end
        end
    end
    return m
end)()

local function hiking_poi_minzoom()
    local z = nil
    for k, vals in pairs(hiking_poi_zoom) do
        local mz = vals[Find(k)]
        if mz ~= nil and (z == nil or mz < z) then z = mz end
    end
    return z
end

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
local water_natural    = { water=true, sea=true, nosea=true, bay=true, wetland=true, spring=false }
local landcover_natural= { wood=true, scrub=true, grassland=true, heath=true,
                           bare_rock=true, scree=true, fell=true, glacier=true }
local landcover_landuse= { forest=true, farmland=true, farmyard=true, meadow=true,
                           grass=true, orchard=true, residential=true,
                           industrial=true, commercial=true, cemetery=true,
                           quarry=true, reservoir=false }
local landcover_leisure= { park=true, nature_reserve=true, garden=true,
                           golf_course=true, pitch=true }

local waterway_class   = { river=true, stream=true, canal=true, drain=true, ditch=true }

-- highway class -> minzoom. Trails and tracks (path, footway, steps,
-- bridleway, byway, track) use the tag mapping's zoom-appear minus one:
-- MapLibre's 512 px tiles show at zoom Z what Mapsforge's 256 px tiles show at
-- Z+1, and the style draws them from there. The other classes are unchanged.
local highway_minzoom = {
    motorway=8, trunk=8, primary=9, secondary=10, tertiary=11,
    unclassified=12, residential=12, service=13, living_street=13,
    track=12, path=12, footway=12, cycleway=13, steps=12, pedestrian=13,
    bridleway=11, byway=12, via_ferrata=13
}

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

    -- generic POIs
    local poi_keys = { "amenity", "tourism", "shop", "historic", "man_made",
                       "leisure", "information", "emergency", "barrier" }
    for _, k in ipairs(poi_keys) do
        local v = Find(k)
        if v ~= "" then
            Layer("poi", false)
            Attribute("class", k)
            Attribute("subclass", v)
            set_names()
            MinZoom(13)
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
        local z = (waterway == "river") and 9 or 12
        MinZoom(z)
        return
    end

    -- landcover areas
    if in_set(natural, landcover_natural) or in_set(landuse, landcover_landuse)
       or in_set(leisure, landcover_leisure) then
        Layer("landcover", true)
        local cls = (natural ~= "" and landcover_natural[natural]) and natural
                 or (landuse ~= "" and landcover_landuse[landuse]) and landuse
                 or leisure
        Attribute("class", cls)
        return
    end

    -- boundaries (national parks, protected areas, admin)
    if boundary == "national_park" or boundary == "protected_area" or
       boundary == "administrative" then
        Layer("boundary", false)
        Attribute("class", boundary)
        local pc = Find("protect_class")
        if pc ~= "" then Attribute("protect_class", pc) end
        local al = Find("admin_level")
        if al ~= "" then Attribute("admin_level", al) end
        set_names()
        MinZoom(boundary == "administrative" and 8 or 9)
        return
    end

    -- transportation (roads / trails / rail / aerialway)
    if highway ~= "" then
        Layer("transportation", false)
        Attribute("class", highway)
        set_names()
        local tunnel, bridge = Find("tunnel"), Find("bridge")
        if tunnel ~= "" and tunnel ~= "no" then Attribute("tunnel", "yes") end
        if bridge ~= "" and bridge ~= "no" then Attribute("bridge", "yes") end
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
        MinZoom(highway_minzoom[highway] or 13)
        return
    end
    if railway ~= "" then
        Layer("transportation", false)
        Attribute("class", "railway")
        Attribute("subclass", railway)
        set_names()
        MinZoom(11)
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
