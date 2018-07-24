#!/usr/bin/env python3

import yaml
import time
import requests
import threading
import logging
import signal
import sys


''' Handle loading of configuration file'''
class Configurator:

    def __init__(self, filepath="./config.yaml"):
        self.filepath = filepath
        self.config = {}
        self.load()

    def load(self):
        with open(self.filepath, 'r') as stream:
          try:
            self.config = yaml.load(stream)
          except yaml.YAMLError as exc:
            print(exc)

    def get_config(self):
        return self.config


''' Handle instantiation of data structure and execution of logic'''
class Controller:

    endpoints = []
    exiting = False

    def __init__(self, config):
        self.gateway = config.get('gateway')
        self.request_timeout = config.get('request_timeout', 5)
        for endpoint in config.get('endpoints'):
       	    self.create_endpoint(endpoint)

    def create_endpoint(self, endpoint):
        e = Endpoint(endpoint.get('name'), endpoint.get('scheme', 'http'), endpoint.get('host', 'localhost'), endpoint.get('port', 9100), endpoint.get('path', '/metrics'), endpoint.get('interval', 30))
        logging.debug('Created endpoint {} as {}'.format(e.get_name(), e.get_url()))
        self.endpoints.append(e)

    def shutdown(self, sig, frame):
        logging.info("Received SIGINT, shutting down gracefully...")
        self.exiting = True

    def execute(self):
        threads = {}
        while(not self.exiting):
          current_time = time.time()
          for endpoint in self.endpoints:
            if current_time >= endpoint.get_nextscrape() and (not threads.get(endpoint.get_name(), False) or not threads.get(endpoint.get_name()).is_alive()):
              logging.debug('Spawning thread for {}'.format(endpoint.get_name()))
              request_thread = threading.Thread(target=self.do_request, name=("requestthread-{}".format(endpoint.get_name())), args=(endpoint.get_url(), endpoint.get_name(), endpoint.get_labels()))
              threads.update({endpoint.get_name(): request_thread})
              request_thread.start()
              endpoint.update_nextscrape()
          time.sleep(1)

    def do_request(self, uri, job, labels=[]):
        logging.debug("Making request to {}\n".format(uri))
        try:
            metrics = requests.get(url = uri)
            metrics.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            logging.error("Unable to query metrics from: {}".format(uri))
            return
        try:
            send_request = requests.post("{}/metrics/jobs/{}".format(self.gateway, job), data=metrics.text, timeout=self.request_timeout)
            logging.info('Metrics pushed for {}'.format(uri))
        except requests.exceptions.ConnectionError as e:
            logging.error("Unable to send metrics for: {}".format(uri))


class Endpoint:
    def __init__(self, name, scheme, host, port, path, interval):
        self.name = name
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.interval = interval
        self.labels = []
        self.nextscrape = time.time()

    def get_name(self):
        return self.name

    def get_url(self):
        return "{}://{}:{}{}".format(self.scheme, self.host, self.port, self.path)

    def get_interval(self):
        return self.interval

    def get_labels(self):
        return self.labels;

    def get_nextscrape(self):
        return self.nextscrape

    def update_nextscrape(self):
        self.nextscrape = time.time() + self.interval


def __main__():
    config = Configurator().get_config()
    logging.basicConfig(
      filename=config.get('log_file', None),
      level=getattr(logging, config.get('log_level', 'INFO').upper()),
      format=config.get('log_format','%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s'),
    )
    controller = Controller(config)
    signal.signal(signal.SIGINT, controller.shutdown)
    controller.execute()

__main__()
