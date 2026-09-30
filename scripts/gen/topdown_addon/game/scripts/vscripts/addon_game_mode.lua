-- A custom game that only shows the map from straight above, for scripts/gen/capture_map.py:
-- no fog of war, no day / night, no creeps, the hero and couriers hidden; the console command
-- "topdown_cam <x> <y> <distance>" points every client's camera straight down at (x, y) from <distance>.

if TopDown == nil then
    TopDown = class({})
end

function Activate()
    local gm = GameRules:GetGameModeEntity()
    -- a second per stage: all of them at 0 left the client on its loading screen
    GameRules:SetHeroSelectionTime(1)
    GameRules:SetStrategyTime(1)
    GameRules:SetShowcaseTime(0)
    GameRules:SetPreGameTime(100000)          -- stays before the horn: no lane creeps, no neutrals
    GameRules:SetCustomGameSetupAutoLaunchDelay(1)
    GameRules:SetCustomGameSetupTimeout(1)
    GameRules:SetTimeOfDay(0.5)               -- noon
    gm:SetFogOfWarDisabled(true)
    gm:SetUnseenFogOfWarEnabled(false)
    gm:SetDaynightCycleDisabled(true)
    gm:SetCustomGameForceHero("npc_dota_hero_wisp")
    gm:SetCameraZRange(10, 200000)
    ListenToGameEvent("npc_spawned", function(ev)
        local u = EntIndexToHScript(ev.entindex)
        if u and (u:IsHero() or u:IsCourier()) then
            u:AddNoDraw()
        end
    end, nil)
    Convars:RegisterCommand("topdown_cam", function(_, x, y, dist)
        CustomGameEventManager:Send_ServerToAllClients("topdown_cam",
            { x = tonumber(x), y = tonumber(y), dist = tonumber(dist) or 6000 })
    end, "point the camera straight down at x y from a distance", 0)
    -- units the map picture must not show (the owner 2026-10-01: Roshan's health bar): heroes, couriers,
    -- Roshan, Tormentors, creeps; buildings, outposts, watchers, lotus pools, gates and shrines stay
    Convars:RegisterCommand("topdown_hide", function()
        local n = 0
        local units = FindUnitsInRadius(DOTA_TEAM_NEUTRALS, Vector(0, 0, 0), nil, 40000,
            DOTA_UNIT_TARGET_TEAM_BOTH, DOTA_UNIT_TARGET_ALL,
            DOTA_UNIT_TARGET_FLAG_INVULNERABLE + DOTA_UNIT_TARGET_FLAG_OUT_OF_WORLD
                + DOTA_UNIT_TARGET_FLAG_MAGIC_IMMUNE_ENEMIES + DOTA_UNIT_TARGET_FLAG_NOT_ILLUSIONS,
            FIND_ANY_ORDER, false)
        for _, u in pairs(units) do
            local name = u:GetUnitName() or ""
            if u:IsHero() or u:IsCourier() or name:find("roshan") or name:find("miniboss")
                or name:find("creep") or name:find("neutral") then
                u:AddNoDraw()
                n = n + 1
            end
        end
        print("TOPDOWN_HIDDEN " .. n)
    end, "hide heroes, couriers, Roshan, Tormentors and creeps", 0)
    -- a point_camera with its own field of view, as SFM's narrow lens: the client looks through it
    Convars:RegisterCommand("topdown_pointcam", function(_, x, y, z, fov)
        if TopDown.cam == nil or TopDown.fov ~= fov then       -- the lens is set at spawn: a new fov, a new camera
            if TopDown.cam then UTIL_Remove(TopDown.cam) end
            TopDown.cam = SpawnEntityFromTableSynchronous("point_camera",
                { origin = "0 0 0", angles = "90 90 0", FOV = fov or "10", ZFar = "200000" })
            TopDown.fov = fov
        end
        TopDown.cam:SetAbsOrigin(Vector(tonumber(x), tonumber(y), tonumber(z)))
        TopDown.cam:SetAngles(90, 90, 0)
        CustomGameEventManager:Send_ServerToAllClients("topdown_pointcam", { ent = TopDown.cam:entindex() })
        print("TOPDOWN_POINTCAM " .. TopDown.cam:entindex())
    end, "look through a point_camera at x y z with a field of view", 0)
    print("TOPDOWN_READY")
end
