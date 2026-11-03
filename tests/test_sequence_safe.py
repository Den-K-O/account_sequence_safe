from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSequenceSafe(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.journal = cls.company_data["default_journal_misc"]

    def _entry(self, date):
        return self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.journal.id,
            "date": date,
            "line_ids": [
                (0, 0, {"name": "d", "account_id": self.company_data["default_account_revenue"].id, "debit": 10.0}),
                (0, 0, {"name": "c", "account_id": self.company_data["default_account_expense"].id, "credit": 10.0}),
            ],
        })

    def _move_date_behind_odoos_back(self, move, date):
        """Reproduce prod data: a numbered entry whose date sits in another month."""
        self.env["base"].flush()
        self.env.cr.execute("UPDATE account_move SET date = %s WHERE id = %s", (date, move.id))
        self.env["account.move"].invalidate_cache()

    def test_normal_numbering_untouched(self):
        moves = self._entry("2026-11-05") + self._entry("2026-11-06")
        moves._post(soft=False)
        prefix = "MISC/2026/11/"
        self.assertEqual(moves.mapped("name"), [prefix + "0001", prefix + "0002"])

    def test_skips_name_held_by_entry_dated_in_other_month(self):
        first = self._entry("2026-11-05")
        first._post(soft=False)
        self.assertEqual(first.name, "MISC/2026/11/0001")
        self._move_date_behind_odoos_back(first, "2026-10-20")

        second = self._entry("2026-11-06")
        second._post(soft=False)  # without the module: unique sequence error
        self.assertEqual(second.name, "MISC/2026/11/0002")
        self.assertEqual(second.sequence_number, 2)

        third = self._entry("2026-11-07")
        third._post(soft=False)
        self.assertEqual(third.name, "MISC/2026/11/0003")

    def test_batch_post_skips_taken_and_stays_unique(self):
        base = self._entry("2026-11-01")
        base._post(soft=False)
        hidden = self._entry("2026-11-02")
        hidden._post(soft=False)
        self.assertEqual(hidden.name, "MISC/2026/11/0002")
        self._move_date_behind_odoos_back(hidden, "2026-10-20")

        batch = self._entry("2026-11-10") + self._entry("2026-11-11")
        batch._post(soft=False)
        self.assertEqual(batch.mapped("name"), ["MISC/2026/11/0003", "MISC/2026/11/0004"])

    def test_batch_numbers_follow_dates_whatever_the_recordset_order(self):
        base = self._entry("2026-11-01")
        base._post(soft=False)
        hidden = self._entry("2026-11-02")
        hidden._post(soft=False)
        self._move_date_behind_odoos_back(hidden, "2026-10-20")

        later = self._entry("2026-11-11")
        earlier = self._entry("2026-11-10")
        (later + earlier)._post(soft=False)
        self.assertEqual(earlier.name, "MISC/2026/11/0003")
        self.assertEqual(later.name, "MISC/2026/11/0004")

    def test_draft_number_is_skipped_and_reposting_keeps_name(self):
        first = self._entry("2026-11-05")
        first._post(soft=False)
        first.button_draft()
        self._move_date_behind_odoos_back(first, "2026-10-20")

        second = self._entry("2026-11-06")
        second._post(soft=False)
        self.assertEqual(second.name, "MISC/2026/11/0002")
        # Re-posting the old entry keeps its number and does not clash.
        first.write({"date": fields.Date.to_date("2026-11-05")})
        first._post(soft=False)
        self.assertEqual(first.name, "MISC/2026/11/0001")

    def test_cancelled_number_is_skipped(self):
        first = self._entry("2026-11-05")
        first._post(soft=False)
        first.button_draft()
        first.button_cancel()
        self._move_date_behind_odoos_back(first, "2026-10-20")

        second = self._entry("2026-11-06")
        second._post(soft=False)
        self.assertEqual(second.name, "MISC/2026/11/0002")

    def test_prenamed_draft_getting_same_taken_name_is_bumped(self):
        """A draft numbered while its period was empty gets the same, taken, name back on post."""
        hidden = self._entry("2026-11-05")
        hidden._post(soft=False)
        self._move_date_behind_odoos_back(hidden, "2026-10-20")

        draft = self._entry("2026-11-06")
        self.assertEqual(draft.name, "MISC/2026/11/0001")  # period looks empty to Odoo
        draft._post(soft=False)
        self.assertEqual(draft.name, "MISC/2026/11/0002")

    def test_draft_edits_do_not_bump(self):
        hidden = self._entry("2026-11-05")
        hidden._post(soft=False)
        self._move_date_behind_odoos_back(hidden, "2026-10-20")

        draft = self._entry("2026-11-06")
        # Only posting checks for taken numbers; drafts keep Odoo's name.
        self.assertEqual(draft.name, "MISC/2026/11/0001")
        self.assertEqual(draft.state, "draft")
