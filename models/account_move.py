import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Key in the transaction-wide cursor cache holding ids of moves being posted
# for the first time. The name recompute does not reliably run with the
# context of ``_post`` (it uses the env of whoever flushes), so the cursor
# cache is used to pass this information along.
_FIRST_POST_KEY = "account_sequence_safe.first_post_ids"


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        pending = self.env.cr.cache.setdefault(_FIRST_POST_KEY, set())
        added = set(self.filtered(lambda m: not m.posted_before).ids) - pending
        pending |= added
        try:
            return super()._post(soft=soft)
        finally:
            pending -= added

    def _compute_name(self):
        """Let Odoo number the moves, then skip numbers already in use.

        Odoo looks for the last number only among moves of the same journal
        whose *date* is in the same period (month/year). A move whose date was
        moved to another period keeps its old name, so that name is invisible
        to the lookup and gets handed out again, which then fails with
        "Posted journal entry must have an unique sequence number per company".

        Odoo's row lock in ``_get_last_sequence`` still serialises concurrent
        posts, so skipping taken names here keeps numbering race-free.
        """
        previous = {move: move.name for move in self}
        super()._compute_name()
        first_post = self.env.cr.cache.get(_FIRST_POST_KEY, set())
        to_check = self.filtered(
            lambda m: m.state == "posted"
            and m.name and m.name != "/"
            and (m.id in first_post or m.name != previous.get(m))
        )
        if to_check:
            to_check._sequence_safe_skip_taken_names()

    def _sequence_safe_skip_taken_names(self):
        """Give every move in ``self`` a number not used by any other move of its journal.

        "Used" means any other move of the journal with the same prefix and
        number, whatever its state or type: drafts and cancelled moves that
        hold a number would clash again when (re)posted.
        """
        self.flush([self._sequence_field, "sequence_number", "sequence_prefix"])
        own_ids = tuple(self.ids) or (0,)
        taken = {}  # (journal_id, prefix) -> set of numbers in use

        for move in self.sorted(lambda m: (m.date, m.ref or "", m.id)):
            key = (move.journal_id.id, move.sequence_prefix)
            if key not in taken:
                self.env.cr.execute(
                    """
                    SELECT sequence_number FROM account_move
                    WHERE journal_id = %s AND sequence_prefix = %s AND id NOT IN %s
                    """,
                    (key[0], key[1], own_ids),
                )
                taken[key] = {row[0] for row in self.env.cr.fetchall()}
            numbers = taken[key]

            if move.sequence_number in numbers:
                seq_format, values = move._get_sequence_format_param(move.name)
                seq = values["seq"]
                while seq in numbers:
                    seq += 1
                values["seq"] = seq
                new_name = seq_format.format(**values)
                _logger.warning(
                    "account_sequence_safe: %s is already used in journal %s, using %s instead",
                    move.name, move.journal_id.code, new_name,
                )
                move.name = new_name
                move._compute_split_sequence()
            numbers.add(move.sequence_number)
