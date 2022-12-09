inventory = {}
traverse = 'topdown'

-- from https://stackoverflow.com/a/7615129/1144523
function str_split (inputstr, sep)
  if sep == nil then
    sep = "%s"
  end
  local t={}
  for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
          table.insert(t, str)
  end
  return t
end


function Meta(meta)
  for k, v in pairs(meta.interlinks.sources) do
    local json = quarto.json.decode(read_file_contents(v.fallback))
    for inv_k, inv_v in pairs(json.items) do
        inventory[inv_v.name] = inv_v
    end
  end

  -- print(quarto.utils.dump(inventory))

end


-- Reformat all heading text
function Header(el)
  el.content = pandoc.Emph(el.content)
  return el
end

function Code(el)
  if el.attr.classes:find("ref") == nil then
    return el
  end

  if el.text:find("^~") then
    prefix = "~"
    ref_name = el.text:sub(2)
    splits = str_split(el.text, "%.")
    out_name = splits[#splits]
  else
    prefix = ""
    ref_name = el.text
    out_name = el.text
  end

  dst = inventory[ref_name]
  -- print(type(ref_name))
  -- print("DST ====")
  -- print(quarto.utils.dump(inventory))
  if dst ~=  nil then
    return pandoc.Link(out_name, dst.uri)
  end

  return el
end

function Pandoc(doc)
  -- write your setup code here
end

function map(tbl, fn)
    local result = {}
    for k, v in pairs(tbl) do
        result[k] = fn(v)
    end
    return result
end

function read_file_contents(file)
  local f = io.open(pandoc.utils.stringify(file), "r")
  if f == nil then
    error("Error resolving " .. target .. "- unable to open file " .. file)
    os.exit(1)
  end
  local contents = f:read("*all")
  f:close()
  return contents
end
