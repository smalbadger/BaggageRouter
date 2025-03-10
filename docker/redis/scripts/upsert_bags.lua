-- KEYS[1]: The key prefix for bags
-- ARGV[1..N]: Serialized bag JSON objects
local prefix = KEYS[1]
local results = {}

for i, bag_json in ipairs(ARGV) do
    local bag = cjson.decode(bag_json)
    redis.call('HSET', prefix .. ':' .. bag.id, 'flights', cjson.encode(bag.flights))
end

return #ARGV 