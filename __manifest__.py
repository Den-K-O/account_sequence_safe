# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Sequence Safe",
    "version": "14.0.2.0.0",
    "category": "Accounting",
    "summary": "Skip journal entry numbers that are already taken",
    "description": """
When Odoo numbers a journal entry, it only looks at entries of the same
journal dated in the same period. An entry whose date was moved to another
month keeps its old number, which Odoo then hands out again and posting fails
with "Posted journal entry must have an unique sequence number per company".

When an entry is posted and Odoo gives it a number, this module checks that
number against all other entries of the journal (any state) and moves on to
the next free number when it is already taken. It hooks Odoo's own numbering,
so it covers every posting path (invoices, stock valuation, MRP, ...).
Names set explicitly by code or imports are not changed.
    """,
    "author": "Den K",
    "website": "https://kochut.org",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [],
    "installable": True,
    "application": False,
}
