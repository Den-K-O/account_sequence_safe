from odoo import models
from datetime import date
from calendar import monthrange

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_next_sequence_name(self):
        """Compute the next available name efficiently."""
        self.ensure_one()
        if self.name and self.name != '/':
            return self.name

        journal = self.journal_id
        if not journal or not self.date:
            return '/'

        year = self.date.year
        month = self.date.month

        # Base format prefix (without seq)
        prefix = f"{journal.code}/{year:04d}/{month:02d}/"

        # Find the highest sequence number already used
        last_move = self.search(
            [('journal_id', '=', journal.id),
             ('name', 'like', prefix + '%')],
            order='name desc',
            limit=1
        )

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

    def _post(self, soft=True):
        res = False
        try:
            res = super()._post(soft)
        except:
            for move in self:
                if move.name == '/':
                    move.name = move._get_next_sequence_name()
            res =  super()._post(soft)
        finally:
            return res
