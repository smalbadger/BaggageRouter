-- KEYS[1]: The key prefix for flights
-- ARGV[1]: JSON array of serialized flight objects
local prefix = KEYS[1]
local results = {}
local counter_key = prefix .. ':count'

-- Initialize counter if it doesn't exist
if redis.call('EXISTS', counter_key) == 0 then
    redis.call('SET', counter_key, 0)
end

local flights = cjson.decode(ARGV[1])
for _, flight_json in ipairs(flights) do
    local flight = flight_json  -- Already decoded
    -- Store flight info
    local is_new = redis.call('HSET', prefix .. ':id:' .. flight.id, 
        'departure_time', flight.departure_time,
        'arrival_time', flight.arrival_time,
        'bags', cjson.encode(flight.bags))
    
    -- Update arrival time index
    redis.call('ZADD', prefix .. ':arrival_times', flight.arrival_time, flight.id)
    -- Increment counter if this is a new flight
    if is_new > 0 then
        redis.call('INCR', counter_key)
    end
end

return #flights 