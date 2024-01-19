function Meta(meta)
    replace_base_domain = tostring(meta.replace_base_domain[1].text)
    replace_rel_path = tostring(meta.replace_rel_path[1].text)
end

-- pandoc Link object: replace the .qmd in the target with .html
function Link(link)
    -- replace .qmd with .html in target
    -- replace beginning with replace_base_domain, accounting for / and ./ in paths
    -- e.g. ./overview.qmd -> {replace_rel_path}/get-started/overview.html
    -- e.g. /index.qmd -> {replace_base_domain}/index.html
    -- e.g. https://example.com -> https://example.com
    if link.target:match("%.qmd$") or link.target:match("%.qmd#.*$") then
        link.target = link.target:gsub("%.qmd", ".html")
        if link.target:match("^%./") then
            link.target = link.target:gsub("^%./", replace_base_domain .. replace_rel_path .. "/")
        end
        if link.target:match("^/") then
            link.target = link.target:gsub("^/", replace_base_domain .. "/")
        end
        -- if target does not start with http, do same as above
        if not link.target:match("^http") then
            link.target = replace_base_domain .. replace_rel_path .. "/" .. link.target
        end
    end

    return link
end

return {
    {
        Meta = Meta
    },
    {
        Link = Link
    }
}
