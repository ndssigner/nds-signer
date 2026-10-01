# NDS-Signer - native replacements for SeedSigner's gui/screens/psbt_screens.py
# (same class names and keyword arguments, see screen.py). The top screen
# shows the amounts like upstream's BtcAmount (denomination setting, network
# units and colours) and addresses like its FormattedAddress.
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.screens.screen import ButtonListScreen, define_generic_screens


def amount_text(sats):
    digits, unit, _color = nds_ui.format_btc(sats)
    return "%s %s" % (digits, unit)


class _TxScreen(ButtonListScreen):
    """Transaction screens name the network even on mainnet."""

    SHOW_MAINNET = True


class PSBTOverviewScreen(_TxScreen):
    """The amount spent, then recipients, fee, change and inputs."""

    def top_blocks(self):
        warn = nds_ui.theme_color("WARNING_COLOR") if self.is_high_fee_tx else None
        blocks = [("label", _("Spend")), ("amount", self.spend_amount), ("space", 8),
                  ("kv", _("Recipients"), str(len(self.destination_addresses or []))),
                  ("kv", _("Fee"), amount_text(self.fee_amount), warn),
                  ("kv", _("Change"), amount_text(self.change_amount)),
                  ("kv", _("Inputs"), str(self.num_inputs))]
        if self.num_self_transfer_outputs:
            blocks.append(("kv", _("Self-transfers"), str(self.num_self_transfer_outputs)))
        if self.has_op_return:
            blocks.append(("kv", "OP_RETURN", _("yes")))
        if self.is_high_fee_tx:
            blocks += [("space", 4), ("status", "warning", _("High fee!"))]
        return blocks


class PSBTMathScreen(_TxScreen):
    """Inputs - recipients - fee = change, as a sum."""

    def top_blocks(self):
        warn = nds_ui.theme_color("WARNING_COLOR") if self.is_high_fee_tx else None
        blocks = [("kv", _("Inputs"), amount_text(self.input_amount)),
                  ("kv", "– " + _("Recipients"), amount_text(self.spend_amount)),
                  ("kv", "– " + _("Fee"), amount_text(self.fee_amount), warn),
                  ("rule",),
                  ("kv", "= " + _("Change"), amount_text(self.change_amount))]
        if self.is_high_fee_tx:
            blocks += [("space", 6), ("status", "warning", _("High fee!"))]
        return blocks


class PSBTAddressDetailsScreen(_TxScreen):
    def top_blocks(self):
        return [("amount", self.amount), ("space", 10), ("address", self.address or "")]


class PSBTChangeDetailsScreen(_TxScreen):
    def top_blocks(self):
        blocks = [("amount", self.amount), ("space", 6), ("address", self.address or ""),
                  ("space", 6)]
        if self.fingerprint:
            blocks.append(("label", "%s · %s" % (self.fingerprint, self.derivation_path or "")))
        if self.is_change_addr_verified:
            blocks.append(("status", "success", _("Address verified!")))
        else:
            blocks.append(("status", "warning", _("Address not verified")))
        return blocks


class PSBTOpReturnScreen(_TxScreen):
    def top_blocks(self):
        data = self.op_return_data
        try:
            text = data.decode()
        except Exception:
            text = repr(data)
        return [("label", "OP_RETURN"), ("space", 4), ("text", text)]


class PSBTFinalizeScreen(_TxScreen):
    """Like upstream: the sign icon and the approval prompt."""

    def top_blocks(self):
        from seedsigner.gui.components import GUIConstants as GC
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        return [("icon", Icons.SIGN, GC.INFO_COLOR), ("space", 6),
                ("text", _("Click to approve this transaction"))] + nds_ui.low_battery_blocks()


define_generic_screens(globals(), "psbt_screens")
