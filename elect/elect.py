#!/usr/bin/python3 -u

import time, os, logging
import consul
from consul import tornado as ConsulTornado
from tornado import gen
import tornado

logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s')
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

class App:
    cluster_name = None

    consul_host = 'localhost'

    _sid = None

    is_registered = False

    def __init__(self, cluster_name=None):
        self.cluster_name = cluster_name
        self.io_loop = tornado.ioloop.IOLoop.current()
        self.consul_tornado = ConsulTornado.Consul(host=self.consul_host)

    @gen.coroutine
    def ensure_session(self):
        if self._sid == None:
            self._sid = yield self.create_session()
        else:
            try:
                yield self.consul_tornado.session.renew(self._sid)
            except consul.NotFound:
                logger.error('session not found, trying to recreate')
                self._sid = yield self.create_session()
        return True

    @gen.coroutine
    def create_session(self):
        sid = yield self.consul_tornado.session.create(self.cluster_name, ttl=10, behavior='delete', lock_delay=0)
        logger.debug('session created: %s', sid)
        return sid

    @gen.coroutine
    def acquire_lock(self):
        logger.debug('acquire lock on key "%s" with session "%s"', self.get_key_name(), self._sid)
        result = yield self.consul_tornado.kv.put(self.get_key_name(), os.getenv('HOSTNAME'), acquire=self._sid)
        return result

    @gen.coroutine
    def release_lock(self):
        self.consul_tornado.kv.put(self.get_key_name(), '', release=self._sid)

    def get_key_name(self):
        return 'election:' + self.cluster_name

    def get_service_name(self):
        return self.cluster_name + '-leader'

    def get_check_name(self):
        return 'service:' + self.get_service_name()

    def renew_ttl(self):
        yield self.consul_tornado.agent.check.ttl_pass(self.get_check_name())

    @gen.coroutine
    def can_participate(self):
        checks = yield self.consul_tornado.agent.checks()
        for checkId, data in checks.items():
            if data['Status'] != 'passing' and checkId != self.get_check_name():
                return False
        return True

    @gen.coroutine
    def register(self):
        logger.debug('registering as leader')
        check = { 'ttl' : '10s', 'status' : 'passing' }
        res = yield self.consul_tornado.agent.service.register(self.get_service_name(), check = check)
        self.is_registered = True

    @gen.coroutine
    def deregister(self):
        if not self.is_registered:
            return
        logger.debug('deregister leader')
        yield self.consul_tornado.agent.service.deregister(self.get_service_name())
        self.is_registered = False

    @gen.coroutine
    def elect(self):
        # wait a bit before starting
        yield gen.sleep(10)
        logger.info('start election routine')
        while True:
            tick = gen.sleep(5)
            yield self.ensure_session()
            can_participate, has_lock = yield [ self.can_participate(), self.acquire_lock() ]
            logger.debug('can participate: %s, has lock: %s', can_participate, has_lock)
            if can_participate and has_lock:
                self.register()
                self.renew_ttl()
            else:
                self.deregister()
                self.release_lock()
            yield tick

    def run(self):
        if (self.cluster_name is None):
            raise Exception("CLUSTER_NAME not defined")
        self.io_loop.run_sync(self.elect)

# run app
if __name__ == '__main__':
    app = App(cluster_name = os.getenv('CLUSTER_NAME'))
    try:
        app.run()
    except KeyboardInterrupt:
        pass
