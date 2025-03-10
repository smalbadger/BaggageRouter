-- KEYS[1]: The key prefix for flights
-- ARGV[1..N]: Serialized flight JSON objects
local prefix = KEYS[1]
local results = {}

for i, flight_json in ipairs(ARGV) do
    local flight = cjson.decode(flight_json)
    -- Store flight info
    redis.call('HSET', prefix .. ':' .. flight.id, 
        'departure_time', flight.departure_time,
        'arrival_time', flight.arrival_time,
        'bags', cjson.encode(flight.bags))
    
    -- Update arrival time index
    redis.call('ZADD', prefix .. ':arrival_times', flight.arrival_time, flight.id)
end

return #ARGV 