#!/usr/bin/env python
import os, sys, requests, json, base64, time, random, collections
from multiprocessing import Process, Pipe

# TODO: use conf
ARRIVAL_INTERVAL_MEAN = 1
ARRIVAL_INTERVAL_DEV = 0.5

def conf():
    if conf.val == None:
        with open('static/config.json') as f:
            conf.val = json.loads(f.read())
    return conf.val
conf.val = None

def db_b64():
    with open('examples/tyler.db') as f:
        return base64.b64encode(f.read())

class User():
    def __init__(self):
        self.url = conf()['url']
        self.fbid = 0
        self.db = db_b64()
        self.ops = [
            {'fn': self.OP_fetch_words, 'freq': 1},
            {'fn': self.OP_upload, 'freq': 1},
            {'fn': self.OP_stats, 'freq': 10},
            {'fn': self.OP_practice, 'freq': 50},
        ]
        self.freq_tot = sum(map(lambda op: op['freq'], self.ops))
        self.stats = {'ops': 0, 
                      'latency-sum': 0.0}

    def post(self, op, data):
        print op
        data['op'] = op
        data['fbid'] = self.fbid

        t0 = time.time()
        # TODO: support skip mode to make sure client isn't overwhelmed
        r = requests.post(self.url, data=json.dumps(data))
        t1 = time.time()

        self.stats['ops'] += 1
        self.stats['latency-sum'] += (t1-t0)

        return r.text

    # TODO: verify results
    def OP_fetch_words(self):
        self.post('fetch_words', {})

    def OP_upload(self):
        self.post('upload', {'db': self.db})

    def OP_stats(self):
        self.post('stats', {})

    def OP_practice(self):
        self.post('practice', {}) # TODO: use actual values

    def do_op(self, op):
        fn = op['fn']
        fn()

    def rand_op(self):
        r = random.randrange(0, self.freq_tot)
        for op in self.ops:
            if r <= op['freq']:
                self.do_op(op)
                break
            r -= op['freq']

    def run(self):
        for i in range(10): # TODO: until particular time
            delay = max(random.normalvariate(ARRIVAL_INTERVAL_MEAN,
                                             ARRIVAL_INTERVAL_DEV), 0)
            # TODO: subtract out time spent on last req
            time.sleep(delay)
            self.rand_op()
        return self.stats

# child
def run(conn):
    u = User()
    results = u.run()
    conn.send(results)
    conn.close()

# parent
def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=run, args=(child_conn,))
    p.start()
    print parent_conn.recv()
    p.join()

if __name__ == '__main__':
    main()
