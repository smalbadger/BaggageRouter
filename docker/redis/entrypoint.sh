#!/bin/sh
redis-cli FLUSHALL
exec redis-server 