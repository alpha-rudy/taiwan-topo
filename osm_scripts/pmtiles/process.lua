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

-- ---------------------------------------------------------------------------
-- lookup tables
-- ---------------------------------------------------------------------------

local hiking_networks = { iwn=true, nwn=true, rwn=true, lwn=true, uwn=true }
local cycle_networks  = { icn=true, ncn=true, rcn=true, lcn=true, ucn=true, mtb=true }

local water_natural    = { water=true, sea=true, bay=true, wetland=true, spring=false }
local landcover_natural= { wood=true, scrub=true, grassland=true, heath=true,
                           bare_rock=true, scree=true, fell=true, glacier=true }
local landcover_landuse= { forest=true, farmland=true, farmyard=true, meadow=true,
                           grass=true, orchard=true, residential=true,
                           industrial=true, commercial=true, cemetery=true,
                           quarry=true, reservoir=false }
local landcover_leisure= { park=true, nature_reserve=true, garden=true,
                           golf_course=true, pitch=true }

local waterway_class   = { river=true, stream=true, canal=true, drain=true, ditch=true }

-- highway class -> minzoom
local highway_minzoom = {
    motorway=8, trunk=8, primary=9, secondary=10, tertiary=11,
    unclassified=12, residential=12, service=13, living_street=13,
    track=12, path=13, footway=13, cycleway=13, steps=14, pedestrian=13,
    bridleway=13, via_ferrata=13
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
    local natural = Find("natural")
    local ele = Find("ele")
    local is_peak = (natural == "peak" or natural == "volcano" or
                     natural == "saddle" or Find("mountain_pass") == "yes")
    if is_peak or ele ~= "" then
        Layer("ele_point", false)
        if is_peak then Attribute("class", natural ~= "" and natural or "mountain_pass")
        else Attribute("class", "ele_marker") end
        set_names()
        local elenum = tonumber(ele)
        if elenum ~= nil then
            AttributeNumeric("ele", math.floor(elenum + 0.5))
            -- higher summits/markers appear earlier
            local z = 14
            if elenum >= 3000 then z = 11
            elseif elenum >= 2000 then z = 12
            elseif elenum >= 1000 then z = 13 end
            MinZoom(is_peak and z or math.max(z, 12))
        else
            MinZoom(is_peak and 12 or 14)
        end
        if not is_peak then return end
        -- a named peak is worth keeping as POI too? keep it single-layer.
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
        Attribute("network", hknet ~= "" and hknet or "highlight")
        set_names()
        MinZoom(11)
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
        if Find("tunnel") ~= "" then Attribute("tunnel", "yes") end
        if Find("bridge") ~= "" then Attribute("bridge", "yes") end
        local sac = Find("sac_scale")
        if sac ~= "" then Attribute("sac_scale", sac) end
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
