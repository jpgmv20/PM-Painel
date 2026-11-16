FROM debian:trixie-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash ca-certificates curl dnsutils iproute2 iputils-ping mtr-tiny nmap \
        net-tools netcat-openbsd procps tcpdump traceroute \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color
WORKDIR /tmp
CMD ["sleep", "infinity"]
