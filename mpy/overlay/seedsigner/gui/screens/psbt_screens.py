# NDS-Signer - native replacements for SeedSigner's gui/screens/psbt_screens.py
# (same class names and keyword arguments, see screen.py).
from gettext import gettext as _

from seedsigner.gui.screens.screen import ButtonListScreen, define_generic_screens
from seedsigner.gui import nds_ui


def sats(amount):
    """Thousands-separated sats, as SeedSigner shows them."""
    s = str(int(amount))
    groups = []
    while len(s) > 3:
        groups.insert(0, s[-3:])
        s = s[:-3]
    groups.insert(0, s)
    return ",".join(groups) + " sats"


class PSBTOverviewScreen(ButtonListScreen):
    def top_lines(self):
        lines = [
            "%s %s" % (_("Spend:"), sats(self.spend_amount)),
            "%s %s" % (_("Fee:"), sats(self.fee_amount)),
            "%s %s" % (_("Change:"), sats(self.change_amount)),
            "",
            "%s %d" % (_("Inputs:"), self.num_inputs),
            "%s %d" % (_("Recipients:"), len(self.destination_addresses or [])),
        ]
        if self.num_self_transfer_outputs:
            lines.append("%s %d" % (_("Self-transfers:"), self.num_self_transfer_outputs))
        if self.has_op_return:
            lines.append("OP_RETURN")
        if self.is_high_fee_tx:
            lines += ["", "/!\\ " + _("High fee!")]
        return lines


class PSBTMathScreen(ButtonListScreen):
    def top_lines(self):
        return [
            "%s %s" % (_("Inputs:"), sats(self.input_amount)),
            "%s %s" % (_("Recipients:"), sats(self.spend_amount)),
            "%s %s" % (_("Fee:"), sats(self.fee_amount)),
            "%s %s" % (_("Change:"), sats(self.change_amount)),
        ] + (["", "/!\\ " + _("High fee!")] if self.is_high_fee_tx else [])


class PSBTAddressDetailsScreen(ButtonListScreen):
    def top_lines(self):
        return [sats(self.amount), ""] + nds_ui.wrap(self.address or "")


class PSBTChangeDetailsScreen(ButtonListScreen):
    def top_lines(self):
        lines = [sats(self.amount), ""] + nds_ui.wrap(self.address or "") + [""]
        if self.fingerprint:
            lines.append("%s %s" % (_("Fingerprint:"), self.fingerprint))
        if self.derivation_path:
            lines += nds_ui.wrap(self.derivation_path)
        lines.append(_("Address verified!") if self.is_change_addr_verified
                     else "/!\\ " + _("Address not verified"))
        return lines


class PSBTOpReturnScreen(ButtonListScreen):
    def top_lines(self):
        data = self.op_return_data
        try:
            text = data.decode()
        except Exception:
            text = repr(data)
        return nds_ui.wrap(text)


class PSBTFinalizeScreen(ButtonListScreen):
    def top_lines(self):
        return ["", _("Sign this transaction?")]


define_generic_screens(globals(), "psbt_screens")
