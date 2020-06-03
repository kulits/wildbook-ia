"""
AUTOGENERATED ON 10:10:32 2019/05/29
AutogenCommandLine:
    python -m wbia.control.STAGING_SCHEMA --test-autogen_staging_schema --force-incremental-db-update --write
    python -m wbia.control.STAGING_SCHEMA --test-autogen_staging_schema --force-incremental-db-update --diff=1
    python -m wbia.control.STAGING_SCHEMA --test-autogen_staging_schema --force-incremental-db-update
"""
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut

(print, rrr, profile) = ut.inject2(__name__)

# =======================
# Schema Version Current
# =======================


VERSION_CURRENT = '1.1.1'


def update_current(db, ibs=None):
    db.add_table('metadata', [
        ('metadata_rowid',               'INTEGER PRIMARY KEY'),
        ('metadata_key',                 'TEXT'),
        ('metadata_value',               'TEXT'),
    ],
        docstr='''
        The table that stores permanently all of the metadata about the
        database (tables, etc)
        ''',
        superkeys=[('metadata_key',)],
    )

    db.add_table('reviews', [
        ('review_rowid',                   'INTEGER PRIMARY KEY'),
        ('review_uuid',                    'UUID NOT NULL'),
        ('annot_1_rowid',                  'INTEGER NOT NULL'),
        ('annot_2_rowid',                  'INTEGER NOT NULL'),
        ('review_count',                   'INTEGER NOT NULL'),
        ('review_evidence_decision',       'INTEGER'),
        ('review_server_end_time_posix',   'INTEGER'),
        ('review_user_identity',           'TEXT'),
        ('review_tags',                    'TEXT'),
        ('review_user_confidence',         'INTEGER'),
        ('review_client_start_time_posix', 'INTEGER'),
        ('review_client_end_time_posix',   'INTEGER'),
        ('review_server_start_time_posix', 'INTEGER'),
        ('review_meta_decision',           'INTEGER'),
        ('review_metadata_json',           'TEXT'),
    ],
        docstr='''
        Used to store completed user review states of two matched annotations
        ''',
        superkeys=[('annot_1_rowid', 'annot_2_rowid', 'review_count')],
    )

    db.add_table('tests', [
        ('test_rowid',                   'INTEGER PRIMARY KEY'),
        ('test_uuid',                    'UUID'),
        ('test_user_identity',           'TEXT'),
        ('test_challenge_json',          'TEXT'),
        ('test_response_json',           'TEXT'),
        ('test_result',                  'INTEGER'),
        ('test_time_posix',              "INTEGER DEFAULT (CAST(STRFTIME('%s', 'NOW', 'UTC') AS INTEGER))"),
    ],
        docstr='''
        Used to store tests given to the user, their responses, and their
        results
        ''',
        superkeys=[('test_uuid',)],
    )
