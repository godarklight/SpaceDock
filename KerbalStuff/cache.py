from time import time

class Cache:
    #Amount of time to keep something cached
    cache_time = 60
    #Amount of time before deleting stale cached data entirely
    cache_expire = 600


    def __init__(self):
        #Cache state
        self.cache_data = {}
        self.cache_data_time = {}
        self.last_cache_expire = 0


    def get_key(self, key, renewFunction):
        currentTime = time()
        if (not key in self.cache_data):
            self.update_key(key, renewFunction)
        if (currentTime - self.cache_data_time[key] > Cache.cache_time):
            self.update_key(key, renewFunction)
        returnData = self.cache_data[key]
        if (currentTime - self.last_cache_expire > Cache.cache_expire):
            self.expire_cache()
        return returnData


    def update_key(self, key, renewFunction):
        self.cache_data[key] = renewFunction()
        self.cache_data_time[key] = time()


    def expire_cache(self):
        deleteTime = time() - Cache.cache_expire
        keyList = list(self.cache_data.keys())
        for key in keyList:
            if (self.cache_data_time[key] < deleteTime):
                del self.cache_data[key]
                del self.cache_data_time[key]
