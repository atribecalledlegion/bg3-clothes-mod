-- Puts the Monado (I) into the camp chest, once per save.
--
-- The Monado mod only hands the weapon out when the tadpole quest is accepted, so a save that
-- was already past that point never gets it. This adds the same root template (Monado.pak,
-- RootTemplates: "Monado") straight to the camp chest instead.
--
-- The camp chest only exists while the camp level is loaded, so this waits for the party to be
-- in camp (or the save to load there) and retries for a few seconds while the level streams in.
-- The console command `!monado_to_chest` runs it again by hand.

local MONADO = "07a37604-4f72-4fe5-ada3-f431a3596826"

-- vanilla root templates of the camp chest (Shared.pak: CONT_PlayerCampChest_A..D, CampChest)
local CHEST_TEMPLATES = {
    "96eab9d1-74b1-42f7-b1ad-061a9fcea8c4",
    "f68b5862-887c-4adf-b9f8-bb29e4d73b0f",
    "b5de2260-8e6b-4c2f-91eb-6f3133682a2f",
    "9b293d36-29f0-460c-bc81-2bdd4610a478",
    "38641122-f00a-4b36-94e6-47d95813f1de",
}

local RETRIES, RETRY_MS = 8, 2500

PersistentVars = {}

local function log(msg)
    Ext.Utils.Print("[MonadoCampChest] " .. msg)
end

local function isChestTemplate(id)
    for _, t in ipairs(CHEST_TEMPLATES) do
        if id == t then return true end
    end
    return false
end

local function findCampChest()
    local ok, items = pcall(Ext.Entity.GetAllEntitiesWithComponent, "ServerItem")
    if not ok or not items then
        log("could not list items: " .. tostring(items))
        return nil
    end
    for _, e in ipairs(items) do
        local uuid = e.Uuid and e.Uuid.EntityUuid
        if uuid then
            local okT, tid = pcall(function() return e.ServerItem.Template.Id end)
            if okT and tid and isChestTemplate(tid) then
                return uuid
            end
            -- fallback: Osiris returns "<TemplateName>_<template guid>"
            local okG, full = pcall(Osi.GetTemplate, uuid)
            if okG and type(full) == "string" then
                for _, t in ipairs(CHEST_TEMPLATES) do
                    if full:find(t, 1, true) then return uuid end
                end
            end
        end
    end
    return nil
end

local function hasMonado(chest)
    local ok, found = pcall(Osi.GetItemByTemplateInInventory, MONADO, chest)
    return ok and found ~= nil and found ~= "" and found ~= "NULL_00000000-0000-0000-0000-000000000000"
end

local function attempt(n)
    if PersistentVars.done then return end
    local chest = findCampChest()
    if chest then
        if not hasMonado(chest) then
            Osi.TemplateAddTo(MONADO, chest, 1, 1)
        end
        if hasMonado(chest) then
            PersistentVars.done = true
            log("Monado is in the camp chest (" .. chest .. ")")
            return
        end
        log("chest " .. chest .. " found, but the Monado did not appear in it (is the Monado mod enabled?)")
    end
    if n < RETRIES then
        Ext.Timer.WaitFor(RETRY_MS, function() attempt(n + 1) end)
    elseif not chest then
        log("no camp chest loaded; it will be tried again the next time the party is in camp")
    end
end

Ext.Events.SessionLoaded:Subscribe(function()
    Ext.Timer.WaitFor(RETRY_MS, function() attempt(1) end)
end)

Ext.Osiris.RegisterListener("LevelGameplayStarted", 2, "after", function()
    Ext.Timer.WaitFor(RETRY_MS, function() attempt(1) end)
end)

Ext.Osiris.RegisterListener("TeleportedToCamp", 1, "after", function()
    Ext.Timer.WaitFor(RETRY_MS, function() attempt(1) end)
end)

Ext.RegisterConsoleCommand("monado_to_chest", function()
    PersistentVars.done = false
    attempt(1)
end)
