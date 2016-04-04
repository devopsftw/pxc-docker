#!/usr/bin/python3 -u

import os
import time
import json
import requests

class App:
    service = None

    base_url = 'http://127.0.0.1:8500/'

    _sid = None

    def __init__(self, service = None):
        self.service = service

    def createSession(self):
        data = {
            'Name': self.service,
            'TTL': '10s',
        }
        response = requests.put(self.base_url + 'v1/session/create',
                json = data)
        self._sid = response.json()['ID']

    def renewSession(self):
        response = requests.put(self.base_url
                + 'v1/session/renew/' + self._sid)
        response.raise_for_status()

    def acquireLock(self):
        key = self.getKeyName()
        r = requests.put(self.base_url + 'v1/kv/' + key,
                params = { 'acquire' : self._sid })

    def releaseLock(self):
        key = self.getKeyName()
        r = requests.put(self.base_url + 'v1/kv/' + key,
                params = { 'release' : self._sid })

    def getKeyName(self):
        return 'election:' + self.service

    def getKeyData(self):
        key = self.getKeyName()
        r = requests.get(self.base_url + 'v1/kv/' + key)
        if (r.status_code != 200):
            return { }
        return r.json()[0]

    def renewTTL(self):
        requests.get(self.base_url + 'v1/agent/check/pass/leader')

    def canParticipate(self):
        r = requests.get(self.base_url + 'v1/agent/checks')
        if r.status_code != 200:
            return False
        checks = r.json()
        if len(checks) == 0:
            return False
        for checkId, data in checks.items():
            if data['Status'] != 'passing' and checkId != 'leader':
                return False
        return True

    def run(self):
        if (self.service is None):
            raise Exception("service not defined")

        self.createSession()
        print('sid is', self._sid)

        start_time = time.time()
        while True:
            self.renewSession()
            if self.canParticipate():
                self.acquireLock()
                keyData = self.getKeyData()
                if 'Session' in keyData.keys() and keyData['Session'] == self._sid:
                    print('is leader')
                    self.renewTTL()
                else:
                    print('not leader')
            else:
                self.releaseLock()
            time.sleep(5.0 - (time.time() - start_time) % 5.0)

# run app
app = App(service = os.getenv('CLUSTER_NAME'))
try:
    app.run()
except KeyboardInterrupt:
    pass
