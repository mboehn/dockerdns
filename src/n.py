#!/usr/bin/env python3

import json

from environs import Env
import docker
import dns.tsigkeyring
import dns.tsig
import dns.update
import dns.query


TSIG_ALG=dns.tsig.HMAC_SHA512
LABELPREFIX='org.nuxis.dockerdns'


class DockerHandler(object):

    def __init__(self):
        env = Env()
        env.read_env()

        self._ns = env('DOCKERDNS_NS')
        self._ttl = 300
        self._dnszone = env('DOCKERDNS_ZONE')
        self._tsigkeyname = env('DOCKERDNS_TSIGKEY')
        self._tsigsecret = env('DOCKERDNS_TSIGSECRET')
        self._tsigkeyring = dns.tsigkeyring.from_text(
            {
                self._tsigkeyname : self._tsigsecret
            }
        )

        self._docker = docker.from_env()
        self._update = dns.update.Update(
            zone=self._dnszone,
            keyring=self._tsigkeyring,
            keyalgorithm=TSIG_ALG
            )
        
        # stores active containers here for debug
        self._view = {}


    def add_container(self, container):
        enable = container.labels.get(f'{LABELPREFIX}.enable', False)
        hostname = container.labels.get(f'{LABELPREFIX}.hostname', None)
        target = container.labels.get(f'{LABELPREFIX}.target', None)
        rtype = container.labels.get(f'{LABELPREFIX}.rtype', None)
        if enable and hostname and target and rtype:
            self._view[container.id] = {
                'hostname': hostname,
                'target': target,
                'rtype': rtype
            }
            self._update.add(hostname, self._ttl, rtype, target)
            dns.query.tcp(self._update, self._ns)
            print(f"adding container {container.short_id} ({container.name}) ({hostname} {self._ttl} {rtype} {target})")
            return True
        return False


    def remove_container(self, container):
        if container.id not in self._view:
            return False
        hostname = self._view[container.id]['hostname']
        target = self._view[container.id]['target']
        rtype = self._view[container.id]['rtype']
        del self._view[container.id]
        self._update.delete(hostname, rtype, target)
        dns.query.tcp(self._update, self._ns)
        print(f"removing container {container.short_id} ({container.name}) ({hostname} {rtype} {target})")
        return True


    def get_containers(self):
        for container in self._docker.containers.list():
            if container.status == 'running':
                if container.labels.get(f'{LABELPREFIX}.enable', False):
                    self.add_container(container)


    def run_events(self):
        for event in self._docker.events():
            jevent = json.loads(event)
            if jevent.get('Type', 'container') == 'container':
                status = jevent.get('status', None)
                if status == 'start':
                    #print(jevent)
                    self.add_container(self._docker.containers.get(jevent['id']))
                elif status == 'die':
                    #print(jevent)
                    self.remove_container(self._docker.containers.get(jevent['id']))


    def run(self):
        print("checking existing containers")
        self.get_containers()
        print("listening for docker events")
        self.run_events()


def main():
    handler = DockerHandler()
    handler.run()


if __name__ == "__main__":
    main()