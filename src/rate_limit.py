import os
import time
import random
import redis as redis_lib
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LIMIT_DAY = int(os.getenv("LIMIT_DAY", "400"))
LIMIT_NIGHT = int(os.getenv("LIMIT_NIGHT", "700"))
NIGHT_START = int(os.getenv("NIGHT_START", "0"))
NIGHT_END = int(os.getenv("NIGHT_END", "6"))
RATE_LIMIT_BUCKET_KEY = os.getenv("RATE_LIMIT_BUCKET_KEY", "portal:api:bucket:v1")

_redis_client = None

# Atomic token bucket: avoids race conditions across multiple workers.
# State stored as Redis hash: {tokens: float, ts: int ms}.
_LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(bucket[1])
local ts = tonumber(bucket[2])

if tokens == nil or ts == nil then
    tokens = capacity
    ts = now_ms
end

local elapsed = math.max(0, (now_ms - ts) / 1000.0)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
    redis.call('EXPIRE', key, 3600)
    return {1, math.floor(tokens), 0}
else
    local wait_ms = math.ceil(((requested - tokens) / refill_rate) * 1000)
    redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
    redis.call('EXPIRE', key, 3600)
    return {0, math.floor(tokens), wait_ms}
end
"""

_lua_sha = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def current_limit():
    hour = datetime.now().hour
    return LIMIT_NIGHT if NIGHT_START <= hour < NIGHT_END else LIMIT_DAY


def _get_lua_sha(r):
    global _lua_sha
    if _lua_sha is None:
        _lua_sha = r.script_load(_LUA_TOKEN_BUCKET)
    return _lua_sha


def try_consume_token(r, key):
    limit = current_limit()
    refill_rate = limit / 60.0
    capacity = float(limit)
    now_ms = int(time.time() * 1000)
    sha = _get_lua_sha(r)
    result = r.evalsha(sha, 1, key, now_ms, refill_rate, capacity, 1)
    return bool(int(result[0])), int(result[2])


def wait_for_quota(key=None):
    if key is None:
        key = RATE_LIMIT_BUCKET_KEY
    r = get_redis()
    while True:
        allowed, wait_ms = try_consume_token(r, key)
        if allowed:
            return
        time.sleep((wait_ms + random.uniform(0, 50)) / 1000.0)
