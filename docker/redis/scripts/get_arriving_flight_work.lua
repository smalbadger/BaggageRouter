-- KEYS[1]: flights prefix
-- KEYS[2]: bags prefix
-- ARGV[1]: current timestamp
-- ARGV[2]: window size in seconds (600 for 10 minutes)

local flights_prefix = KEYS[1]
local bags_prefix = KEYS[2]
local current_time = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_time = current_time + window

-- Get all flights arriving in the next 10 minutes
local arriving_flights = redis.call('ZRANGEBYSCORE', 
    flights_prefix .. ':arrival_times', 
    current_time, 
    max_time)

local result = {}

for _, flight_id in ipairs(arriving_flights) do
    local flight_key = flights_prefix .. ':' .. flight_id
    local flight_data = redis.call('HGETALL', flight_key)
    
    if #flight_data > 0 then
        local flight = {}
        for i = 1, #flight_data, 2 do
            flight[flight_data[i]] = flight_data[i + 1]
        end
        
        local bags = cjson.decode(flight.bags)
        local work = {
            id = flight_id,
            arrival_time = tonumber(flight.arrival_time),
            bags = {}
        }
        
        -- For each bag, get its flights and determine next flight
        for _, bag_id in ipairs(bags) do
            local bag_flights = redis.call('HGET', bags_prefix .. ':' .. bag_id, 'flights')
            if bag_flights then
                bag_flights = cjson.decode(bag_flights)
                -- Find current flight index
                for i, bag_flight_id in ipairs(bag_flights) do
                    if bag_flight_id == flight_id and i < #bag_flights then
                        -- Get next flight's departure time
                        local next_flight = redis.call('HGET', 
                            flights_prefix .. ':' .. bag_flights[i + 1], 
                            'departure_time')
                        if next_flight then
                            work.bags[bag_id] = tonumber(next_flight)
                        end
                        break
                    end
                end
            end
        end
        
        table.insert(result, cjson.encode(work))
    end
end

return result 