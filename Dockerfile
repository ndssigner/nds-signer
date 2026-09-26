# NDS-Signer reproducible build environment.
# The base image is pinned by digest so every build uses the exact same toolchain.
# To upgrade: pick a new tag at https://hub.docker.com/r/devkitpro/devkitarm/tags
# and update both the tag and the digest below.
FROM devkitpro/devkitarm:20260610@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5

# Reproducibility: fixed timestamps and locale for any tool that embeds them.
ENV SOURCE_DATE_EPOCH=0 \
    LC_ALL=C.UTF-8 \
    TZ=UTC

WORKDIR /source

CMD ["make"]
