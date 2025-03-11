-- KEYS[1]: The key prefix for bags
-- ARGV[1]: JSON array of serialized bag objects
local prefix = KEYS[1]
local results = {}
local counter_key = prefix .. ':count'

-- Initialize counter if it doesn't exist
if redis.call('EXISTS', counter_key) == 0 then
    redis.call('SET', counter_key, 0)
end

local bags = cjson.decode(ARGV[1])
for _, bag_json in ipairs(bags) do
    local bag = bag_json  -- Already decoded
    -- Store bag info
    local is_new = redis.call('HSET', prefix .. ':id:' .. bag.id, 
        'flights', cjson.encode(bag.flights))
    if is_new > 0 then
        redis.call('INCR', counter_key)
    end
end

return #bags 