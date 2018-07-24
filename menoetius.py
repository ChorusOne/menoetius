#!/usr/bin/env python3
''' Menoetius (Ancient Greek: Brother of Prometheus) to scrape endpoints and
    push to a pushgateway.
    Useful when firewall restrictions prohibit a pull-based methodlogy but you
    wish to harness the awesomeness of Prometheusself.

    Version: 0.1.0

    TODO: add support for labels.
    TODO: allow support for custom hostnames (i.e. not localhost); metrics can
          currently be fetched from alternate hostnames, but will not be
          reflected as such in Prometheus itself.
'''

import time
import threading
import logging
import signal
import yaml
import requests


class Configurator:
    ''' Handle loading of configuration file'''

    def __init__(self, filepath="./config.yaml"):
        self.filepath = filepath
        self.config = {}
        self.load()

    def load(self):
        ''' Load the config from yaml and create a dict. '''
        with open(self.filepath, 'r') as stream:
            try:
                self.config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def get_config(self):
        ''' Return the configuration dict. '''
        return self.config


class Controller:
    ''' Handle instantiation of data structure and execution of logic'''

    endpoints = []
    exiting = False

    def __init__(self, config):
        self.gateway = config.get('gateway')
        self.request_timeout = config.get('request_timeout', 5)
        for endpoint in config.get('endpoints'):
            self.create_endpoint(endpoint)

    def create_endpoint(self, endpoint_config):
        '''  Create an endpoint data structure from config '''
        endpoint = Endpoint(endpoint_config.get('name'),
                            endpoint_config.get('scheme', 'http'),
                            endpoint_config.get('host', 'localhost'),
                            endpoint_config.get('port', 9100),
                            endpoint_config.get('path', '/metrics'),
                            endpoint_config.get('interval', 30)
                            )
        logging.debug('Created endpoint {} as {}'.format(endpoint.get_name(),
                                                         endpoint.get_url()))
        self.endpoints.append(endpoint)

    def shutdown(self, sig, frame):
        ''' Signal handler for SIGINT '''
        logging.info("Received SIGINT, shutting down gracefully...")
        self.exiting = True

    def execute(self):
        ''' Main logic execution loop, iterates indefinitely until interrupted. '''
        threads = {}
        while not self.exiting:
            current_time = time.time()
            for endpoint in self.endpoints:
                if current_time >= endpoint.get_nextscrape() and (not threads.get(endpoint.get_name(), False) or not threads.get(endpoint.get_name()).is_alive()):
                    logging.debug('Spawning thread for {}'.format(endpoint.get_name()))
                    request_thread = threading.Thread(target=self.do_request, name=("requestthread-{}".format(endpoint.get_name())), args=(endpoint.get_url(), endpoint.get_name(), endpoint.get_labels()))
                    threads.update({endpoint.get_name(): request_thread})
                    request_thread.start()
                    endpoint.update_nextscrape()
            time.sleep(1)

    def do_request(self, uri, job, labels):
        ''' Handle scraping and pushing requests; executed as a separate thread. '''
        logging.debug("Making request to {}\n".format(uri))
        try:
            metrics = requests.get(url=uri)
            metrics.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            logging.error("Unable to query metrics from: {}".format(uri))
            return
        try:
            send_request = requests.post("{}/metrics/jobs/{}".format(self.gateway, job), data=metrics.text, timeout=self.request_timeout)
            logging.info('Metrics pushed for {}'.format(uri))
        except requests.exceptions.ConnectionError as exc:
            logging.error("Unable to send metrics for: {}".format(uri))


class Endpoint:
    ''' Endpoint data structure. '''

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
        ''' Return the endpoint name '''
        return self.name

    def get_url(self):
        ''' Assemble and return the endpoint URL '''
        return "{}://{}:{}{}".format(self.scheme, self.host, self.port, self.path)

    def get_interval(self):
        ''' Fecth the scrape interval '''
        return self.interval

    def get_labels(self):
        ''' Return any labels associated with this endpoint. '''
        return self.labels

    def get_nextscrape(self):
        ''' Return the time at which the endpoint should next be scraped. '''
        return self.nextscrape

    def update_nextscrape(self):
        ''' Update the scrape time (now+interval). '''
        self.nextscrape = time.time() + self.interval


def __main__():
    ''' Initialise and run the application. '''
    config = Configurator().get_config()
    logging.basicConfig(
        filename=config.get('log_file', None),
        level=getattr(logging, config.get('log_level', 'INFO').upper()),
        format=config.get('log_format', '%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s'),
    )
    controller = Controller(config)
    signal.signal(signal.SIGINT, controller.shutdown)
    controller.execute()

__main__()
