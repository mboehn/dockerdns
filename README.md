# dockerdns
Uses RFC2136 and container labels to update DNS records.
It's not fully tested, probably leaves a lot of mess if stopped unplanned and probably overwrites everything in its path.

Configuration is done via environment variables as shown below. Also uses docker connection settings from environment variable. TTL hardcoded to 300, could easily be a variable. TSIG key algorithm is hardcoded to HMAC-SHA512.

    DOCKERDNS_ZONE="example.com." # have not tested without trailing dot
    DOCKERDNS_NS="192.0.2.1"  #  must be IP-address, could add resolving myself but haven't done it
    DOCKERDNS_TSIGKEY="key.name"  # name of key
    DOCKERDNS_TSIGSECRET="b64 secret==" # secret


Add these labels to the containers

    org.nuxis.dockerdns.enable=true
    org.nuxis.dockerdns.hostname=www
    org.nuxis.dockerdns.target=192.0.2.2
    org.nuxis.dockerdns.rtype=A
