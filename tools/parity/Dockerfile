FROM rockylinux@sha256:d7be1c094cc5845ee815d4632fe377514ee6ebcf8efaed6892889657e5ddaaa6
# Adapted from CESNET/ipfixprobe docker/Dockerfile (source checked 2026-10-25).
# Container-only dependencies. The parity runner disables networking/capabilities
# and explicitly opens the known offline fixture, never a live interface.
ARG IPFIXPROBE_VERSION=5.8.0-20260901120711.el9
RUN --mount=type=cache,target=/var/cache/dnf dnf -y install dnf-plugins-core epel-release \
    && dnf copr -y enable @CESNET/ipfixprobe \
    && dnf -y install ipfixprobe-${IPFIXPROBE_VERSION} ipfixprobe-input-pcap-${IPFIXPROBE_VERSION} \
    && rpm -qa | sort > /usr/share/netembed-package-manifest.txt \
    && dnf clean all
ENTRYPOINT ["/usr/bin/ipfixprobe"]
