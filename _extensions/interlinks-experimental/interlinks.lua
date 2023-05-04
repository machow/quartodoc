local function read_json(filename)
    local file = io.open(filename, "r")
    if file == nil then
        return nil
    end
    local str = file:read("a")
    file:close()
    return quarto.json.decode(str)
end

local inventory = {}

function lookup(search_object)
    print("search object: ")
    quarto.utils.dump(search_object)
    for _, inventory in ipairs(inventory) do
        for _, item in ipairs(inventory.items) do
            if item.name ~= search_object.name then
                goto continue
            end

            if search_object.role and item.role ~= search_object.role then
                goto continue
            end

            if search_object.domain and item.domain ~= search_object.domain then
                goto continue
            else
                print("Found")
                quarto.utils.dump(item)
                return item
            end

            ::continue::
        end
    end
end

function mysplit (inputstr, sep)
    if sep == nil then
            sep = "%s"
    end
    local t={}
    for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
            table.insert(t, str)
    end
    return t
end

local function normalize_role(role)
    if role == "func" then
        return "function"
    end
    return role
end

local function build_search_object(str)
    quarto.utils.dump(str)
    local starts_with_colon = str:sub(1, 1) == ":"
    local search = {}
    if starts_with_colon then
        local t = mysplit(str, ":")
        if #t == 2 then
            search.role = normalize_role(t[1])
            search.name = t[2]:match("%%60(.*)%%60")
        elseif #t == 3 then
            search.domain = t[1]
            search.role = normalize_role(t[2])
            search.name = t[3]:match("%%60(.*)%%60")
        else
            -- TODO: handle external inventory files
            print("couldn't parse this link: " .. str)
            return {}
        end
    else
        search.name = str:match("%%60(.*)%%60")
    end

    if search.name == nil then
        print("couldn't parse this link: " .. str)
        return {}
    end

    if search.name:sub(1, 1) == "~" then
        search.shortened = true
        search.name = search.name:sub(2, -1)
    end
    return search
end

function report_broken_link(link, search_object, replacement)
    -- TODO: how to unescape html elements like [?
    return pandoc.Code(pandoc.utils.stringify(link.content))
end

function Link(link)
    -- do not process regular links ----
    if not link.target:match("%%60") then
        return link
    end

    -- lookup item ----
    local search = build_search_object(link.target)
    local item = lookup(search)

    -- determine replacement, used if no link text specified ----
    local original_text = pandoc.utils.stringify(link.content)
    local replacement = search.name
    if search.shortened then
        local t = mysplit(search.name, ".")
        replacement = t[#t]
    end

    -- set link text ----
    if original_text == "" then
        link.content = replacement
    end

    -- report broken links ----
    if item == nil then
        return report_broken_link(link, search)
    end
    link.target = item.uri:gsub("%$$", search.name)


    return link
end

function fixup_json(json, prefix)
    for _, item in ipairs(json.items) do
        item.uri = prefix .. item.uri
    end
    table.insert(inventory, json)
end

return {
    {
        Meta = function(meta)
            local json
            local prefix
            for k, v in pairs(meta.interlinks.sources) do
                json = read_json(quarto.project.offset .. "/_inv/" .. k .. "_objects.json")
                prefix = pandoc.utils.stringify(v.url)
                fixup_json(json, prefix)
                table.insert(inventory, json)
            end
            json = read_json(quarto.project.offset .. "/objects.json")
            if json ~= nil then
                fixup_json(json, "/")
                table.insert(inventory, json)
            end
        end
    },
    {
        Link = Link
    }
}
