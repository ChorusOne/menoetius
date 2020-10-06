# Menoetius
## Version: 0.2.1

### What is Menoetius

Menoetius is a small python application that will, given a config file, scrape Prometheus /metrics endpoints and push the scraped data on a schedule to a PushGateway.

This essentially allows us to run entire Prometheus clusters to a push-model, as opposed to the standard pull-model usage.

In most scenarios, this is not required - however, if security rules do not permit read access into certain subnets/host/environments (for example, monitoring hosts in restrictive subnet from a less restricted subnet), but those hosts are free to connect out, then the push-model is perfectly suited.

Prometheus provides the PushGateway, that can have metrics pushed to it and be itself scraped by Prometheus - but to our knowledge, no such utility exists to push the output from /metrics endpoints to this gateway, leaving the push gateway more suited to custom metrics / batch scripts, etc. Until Menoetius.

#### Why Menoetius?

In Greek mythology, Menoetius was the brother of Prometheus. Epimitheus was already taken by a Prometheus-related project. That's enough of a tenuous link for me :)

#### Pronunciation

Men-ee-te-us

### Installation

Install, using your operating system's package manager, `python3` and `pip3-python`.

The follow these simple instructions:

1. Clone the contents of this repository (into `/srv/menoetius`, for example). This will be referred to herein as the 'application root'.
* From your application root, run `pip3 install -r requirements.txt`
* Create `config.yaml` file in the application root (see 'Configuration' section below)
* Run `python3 ./menoetius.py` (or run as a service, see 'Running Menoetius as a service' section below)

### Configuration
Menoetius has a small number of configurable items, all of which can be configured by way of a YAML file in the application root; or a path of your choosing using the `MENOETIUS_CONFIG_PATH` environment variable.

Example configuration:
```
gateway: http://prometheus.example.com:9091
log_level: info
log_format: "%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s"
log_file: menoetius.log
request_timeout: 5
endpoints:
  - name: monitor
    scheme: http
    host: localhost
    port: 9100
    path: /metrics
    interval: 5
    hostname: host.domain.com
    labels:
      arbitrary_label: foo
      other_label: bar
help_overrides:
  go_memstats_sys_bytes: Number of bytes obtained by system.
```

#### gateway
**(no default; REQUIRED)**

This is the http(s) address of your Prometheus pushgateway, that you want Menoetius to push all metrics to.

#### log_level
**(default: info)**

The minimum log level for which messages should be emitted to the log file. Standard Python logging module log levels: debug, info, warning, error, critical (see: https://docs.python.org/3/library/logging.html)

#### log_format
**(default: "%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s")**

The log format of messages emitted to the log file. Standard Python logging module log format (see: https://docs.python.org/3/library/logging.html)

#### log_file
**(default: menoetius.log)**

The path of the log file. Can be relative (to the application root) or absolute.

#### request_timeout
**(default: 5)**

The number of seconds allowed to elapse before the POST request to the push gateway will timeout.

#### help_overrides
**(no default; not required)**

Prometheus pushgateway will emit a log for every push it receives where the HELP label for a metric doesn't exactly match the HELP label for metrics of the same name that it has received from other sources. An example of this is the `go_memstats_sys_bytes` internal Go metric, for which the HELP label changes between versions 0.8.0 and 0.9.0 of the Prometheus golang client (see: https://github.com/prometheus/client_golang/commit/9a6b9d3ddfdffd6edd5cccc94cc6623821c87075#diff-c7cee965d0cb37a1f58780f5184a17ba).

The `help_overrides` setting allows us to optionally define a map of metric names and strings with which to override the HELP labels for those metrics.

#### endpoints
**(no default; REQUIRED)**

The `endpoints` setting is a list of endpoints that Menoetius will poll for metrics.

Each `endpoint` is a map comprising fhe follow settings:

##### name
**(no default; REQUIRED)**

A user friendly label to identify the source of the metrics; it is used as the value of `job` within Prometheus.

##### scheme
**(default: http)**

The scheme Menoetius will use to scrape metrics; supports any scheme supported by Python's `requests` module (see: http://python-requests.org)

##### host
**(default: localhost)**

The hostname of the endpoint Menoetius will scrape for metrics.

##### port
**(default: 9100)**

The port of the endpoint Menoetius will scrape for metric (9100 = node_exporter)

##### path
**(default: /metrics)**

The path of the endpoint Menoetius will scrape for metrics.

##### interval
**(default: 30)**

The number of seconds that will elapse between repeated requests. Subsequent requests will not execute if a previous request is still running.

##### hostname
**(default: `<FQDN of the host>`)**

The hostname with which we wish to associate the pushed metrics; it forms the `instance` value within Prometheus.

By default this is the output from `getfqdn()` method on the Python `socket` module, unless overridden here.

##### labels
**(no default; not required)**

An optional map of additional labels to apply to metrics from the given endpoint.





### Running Menoetius as a service

We recommend running Menoetius as a systemd service.

Create a text file at `/etc/systemd/system/menoetius.service`, and paste in the following content:

```
[Unit]
Description=menoetius
After=syslog.target network.target
[Service]

Type=simple
RemainAfterExit=no
WorkingDirectory=/srv/menoetius
User=prometheus
Group=prometheus
ExecStart=/usr/bin/python3 /srv/menoetius/menoetius.py

[Install]
WantedBy=multi-user.target
```

The command `sudo systemctl enable menoetius.service` and `sudo systemctl start menoetius.service` will
enable the service at boot, and start the service running respectively.
