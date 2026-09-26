# NDS-Signer - deliberately unusable `random` module.
#
# NDS-Signer never uses a PRNG: seeds come from user entropy only (dice rolls).
# embit imports `random` for key generation helpers that the signer must never
# call; if anything ever does, fail loudly instead of producing a weak key.


def _refuse(*args, **kwargs):
    raise NotImplementedError("random is disabled on NDS-Signer (no PRNG)")


getrandbits = randrange = randint = choice = random = uniform = seed = _refuse
