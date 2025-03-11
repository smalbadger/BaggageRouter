-- KEYS[1]: flights prefix
-- KEYS[2]: bags prefix
-- ARGV[1]: current timestamp
-- ARGV[2]: window size in seconds (600 for 10 minutes)

local flights_prefix = KEYS[1]
local bags_prefix = KEYS[2]
local current_time = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_time = current_time + window

-- Get all flights arriving within the window
local work_items = {}
local error_message = ''

-- Get flights from sorted set by arrival time and move them to arrived set
local flight_ids = redis.call('ZRANGEBYSCORE', flights_prefix .. ':arrival_times', '-inf', max_time, 'LIMIT', 0, 100)
if #flight_ids > 0 then
    -- Move flights to arrived set with their arrival times
    for _, flight_id in ipairs(flight_ids) do
        local arrival_time = redis.call('ZSCORE', flights_prefix .. ':arrival_times', flight_id)
        redis.call('ZADD', flights_prefix .. ':arrived', arrival_time, flight_id)
        redis.call('ZREM', flights_prefix .. ':arrival_times', flight_id)
    end
else
    error_message = 'no flights arriving in the next 10 minutes'
end

for _, flight_id in ipairs(flight_ids) do
    local flight_key = flights_prefix .. ':id:' .. flight_id
    local flight_hash = redis.call('HGETALL', flight_key)
    
    -- Convert array to hash table
    local hash_table = {}
    for i = 1, #flight_hash, 2 do
        hash_table[flight_hash[i]] = flight_hash[i + 1]
    end
    
    -- Convert hash to table
    local flight = {
        id = flight_id,
        arrival_time = tonumber(hash_table['arrival_time']),
        bags = hash_table['bags'] and cjson.decode(hash_table['bags']) or {}
    }
    
    -- Get bags for this flight
    local bags = {}
    for _, bag_id in ipairs(flight.bags) do
        local bag_key = bags_prefix .. ':id:' .. bag_id
        local bag_hash = redis.call('HGETALL', bag_key)
        
        -- Set default departure time to -10 by default
        local departure_time = -10
        
        -- Only process if bag exists
        if #bag_hash > 0 then
            -- Convert array to hash table
            local bag_table = {}
            for i = 1, #bag_hash, 2 do
                bag_table[bag_hash[i]] = bag_hash[i + 1]
            end
            local bag = {
                id = bag_id,
                flights = cjson.decode(bag_table['flights'] or '[]')
            }

            if #bag.flights <= 0 then
                error_message = 'bag has no flights'
                departure_time = -2
            else
                -- Find this flight's position in the bag's itinerary
                for i, flight_id in ipairs(bag.flights) do
                    if flight_id == flight.id then
                        -- Check if there are any more flights after this one
                        if i == #bag.flights then
                            departure_time = 0  -- No more flights after this one
                        else
                            -- Check if next flight exists
                            local next_flight_hash = redis.call('HGETALL', flights_prefix .. ':id:' .. bag.flights[i+1])
                            if #next_flight_hash == 0 then
                                departure_time = -3  -- Next flight doesn't exist yet
                            else
                                -- Get arrival time of current flight as departure time for next flight
                                departure_time = flight.arrival_time
                            end
                        end
                        break
                    end
                end
            end
        else
            error_message = 'bag not found with key ' .. bag_key
            departure_time = -1
        end
        
        -- Always add the bag with its departure time (-1: no bag, -2: next flight missing, 0: final destination, >0: valid time)
        bags[bag_id] = departure_time
    end
    
    -- Add work item if there are bags
    if next(bags) then
        table.insert(work_items, cjson.encode({
            id = flight.id,
            arrival_time = flight.arrival_time,
            bags = bags
        }))
    end
end

return cjson.encode({
    work_items = work_items,
    error_message = error_message
})