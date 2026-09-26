# Prints SeedSigner's PSBTParser summary of the test PSBT. Runs unmodified
# on CPython (reference) and on the DSi (MicroPython) so outputs can be diffed.
from embit.psbt import PSBT
from seedsigner.models.psbt_parser import PSBTParser
from seedsigner.models.seed import Seed
from seedsigner.models.settings import SettingsConstants


def summary(psbt_b64, mnemonic):
    parser = PSBTParser(p=PSBT.from_string(psbt_b64), seed=Seed(mnemonic.split()),
                        network=SettingsConstants.TESTNET)
    lines = [
        "spend_amount %d" % parser.spend_amount,
        "change_amount %d" % parser.change_amount,
        "fee_amount %d" % parser.fee_amount,
        "num_inputs %d" % parser.num_inputs,
        "num_destinations %d" % parser.num_destinations,
        "num_change_outputs %d" % parser.num_change_outputs,
        "destination_addresses %s" % ",".join(parser.destination_addresses),
        "is_high_fee %s" % parser.is_high_fee,
    ]
    return "\n".join(lines)
