# menoetius
Scrape and Push Daemon for Prometheus


## What is Menoetius?

Menoetius is a small python application that will, given a config file, scrape Prometheus /metrics endpoints and push the scraped data on a schedule to a PushGateway.

This essentially allows us to run entire Prometheus clusters to a push-model, as opposed to the standard pull-model usage.

In most scenarios, this is not required - however, if security rules do not permit read access into certain subnets/host/environments (for example, monitoring hosts in restrictive subnet from a less restricted subnet), but those hosts are free to connect out, then the push-model is perfectly suited.

Prometheus provides the PushGateway, that can have metrics pushed to it and be itself scraped by Prometheus - but to our knowledge, no such utility exists to push the output from /metrics endpoints to this gateway, leaving the push gateway more suited to custom metrics / batch scripts, etc. Until Menoetius.


## Why Menoetius?

In Greek mythology, Menoetius was the brother of Prometheus. Epimitheus was already taken by a Prometheus-related project. That's enough of a tenuous link for me :)

## Pronunciation

Men-ee-te-us

