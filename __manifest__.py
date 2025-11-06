# Copyright 2022 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Sequence Safe',
    'version': '14.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Automatically skip duplicate journal entry sequence numbers',
    'description': """
    This module overrides account.move numbering to automatically iterate
    to the next free sequence number if a duplicate exists.
    Prevents manual resequencing and errors when changing accounting dates.
    """,
    "author": "Den K",
    "website": "https://kochut.org",
    'depends': ['account'],
    'data': [],
    'installable': True,
    'application': False,
}
