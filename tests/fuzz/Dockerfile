# clang with libFuzzer, for tests/fuzz (Apple's clang ships without it)
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends clang libclang-rt-14-dev make \
    && rm -rf /var/lib/apt/lists/*
