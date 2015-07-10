#!/usr/bin/env python

import argparse
import dns.resolver
import logging
import random
import re
import requests
import yaml


# arguments
parser = argparse.ArgumentParser(description='Python script to update domains on dns.he.net.')
parser.add_argument('configfile', help='set config file')
parser.add_argument('-v', '--verbose', action='store_true', help='set log to DEBUG')
parser.add_argument('-l', '--logfile', help='set log file')
args = parser.parse_args()


# logging
log = logging.getLogger('dnsHEnet-update')
if args.logfile:
    FORMAT = '%(asctime)-15s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=args.logfile, format=FORMAT)
else:
    FORMAT = '%(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
if args.verbose:
    log.setLevel(logging.DEBUG)


# configuration
with open(args.configfile, "r") as ymlfile:
    cfg = yaml.load(ymlfile)


# function - get external IP
def getExternalIP(urls):
    url = urls[random.randint(0,len(urls)-1)]
    ipPattern = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    response = requests.get(url)
    ip = re.findall(ipPattern, response.text)[0]
    log.debug("Got external IP %s from %s." % (ip, url))
    return str(ip)


# function - get IP of domain record
def getRecordIP(domains):
    domain = dict(domains[0])
    domain, password = domain.popitem()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']
    try:
        answer = resolver.query(domain)
        ip = answer[0]
    except:
        log.error("DNS query failed for %s" % domain)

    log.debug("Got A record IP %s from %s." % (ip, domain))
    return str(ip)


# function - update domains
def updateDNS(domains):
    for item in domains:
        host, password = item.popitem()
        url = "https://dyn.dns.he.net/nic/update?hostname=%s&password=%s" % (host, password)
        response = requests.get(url, verify=False)
        log.debug("Response from dyn.dns.he.net: %s." % response.text)
    return True


#
if cfg is None:
    log.error('Config file is empty.')
    exit(1)

if 'ipcheck_urls' in cfg:
    urls = cfg['ipcheck_urls']
    externalIP = getExternalIP(urls)
else:
    log.error("Config file: No urls are given to check external IP.")
    exit(1)

if 'domains' in cfg:
    domains = cfg['domains']
    recordIP = getRecordIP(domains)
else:
    log.error("Config file: No domains are given.")
    exit(1)

if externalIP != recordIP:
    log.info("IP has changed. Update domains...")
    updateDNS(domains)
