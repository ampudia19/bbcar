import threading
import random
from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, wait, as_completed

class MyProcessor():
    def __init__(self):
        # self.initsocket(host, port)
        self._id = random.randint(0, 100)

    def __call__(self, i):
        print("current id: {}".format(self._id))
        return self._id * i

def main():
    # with ThreadPoolExecutor(max_workers=5) as executor:
    #     func = MyProcessor()
    #     futures = [executor.submit(func, i) for i in range(15)]
    #     for f in as_completed(futures):
    #         pass
    threads = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(MyProcessor(), i) for i in range(15)]
        for f in as_completed(futures):
            threads.append(f)
    return threads

f = main()