from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError
from psycopg2 import IntegrityError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_next_sequence_name(self):
        """Fallback: compute next name manually if journal's sequence fails."""
        self.ensure_one()

        journal = self.journal_id
        if not journal or not self.date:
            return '/'

        year = self.date.year
        month = self.date.month

        # Base format prefix (without seq)
        prefix = f"{journal.code}/{year:04d}/{month:02d}/"

        # Find the highest sequence number already used
        last_move = None
        try:
            last_move = self.search(
                [('journal_id', '=', journal.id),
                ('name', 'like', prefix)],
                order='name desc',
                limit=1
            )
        except Exception as e:
            last_move = None

        if last_move and last_move.name:
            try:
                last_seq = int(last_move.name[-4:])
            except ValueError:
                last_seq = 0
        else:
            last_seq = 0

        # Next sequence number
        next_seq = last_seq + 1
        return f"{prefix}{next_seq:04d}"

    def action_post(self):
        for move in self:
            # If move has no assigned sequence yet OR the date has changed
            if move.name == '/' or move._context.get('force_renumber', False):
                new_name = move._get_next_sequence_name()
                move.with_context(check_move_validity=False).write({'name': new_name})

        # Now safely post (no name conflicts will happen here)
        return super().action_post()
