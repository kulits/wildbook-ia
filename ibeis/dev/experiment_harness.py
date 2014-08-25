from __future__ import absolute_import, division, print_function
# Python
import sys
import textwrap
# Scientific
import numpy as np
# Tools
import utool
# IBEIS
from ibeis import params
from ibeis.dev import experiment_helpers as eh
from ibeis.dev import experiment_printres

print, print_, printDBG, rrr, profile = utool.inject(
    __name__, '[expt_harn]', DEBUG=False)

BATCH_MODE = '--nobatch' not in sys.argv
NOMEMORY   = '--nomemory' in sys.argv
QUIET      = '--quiet' in sys.argv
TESTRES_VERBOSITY = 2 - (2 * QUIET)
NOCACHE_TESTRES =  utool.get_flag('--nocache-testres', False)
TEST_INFO = True
STRICT = utool.STRICT


@profile
def get_qx2_bestrank(ibs, qaids, nTotalQueries, nPrevQueries, cfglbl):
    """
    Runs queries of a specific configuration returns the best rank of each query

    qaids - query annotation ids
    """
    daids = ibs.get_recognition_database_aids()

    # NEW STUFF
    qaid2_qres = ibs._query_chips(qaids, daids)
    qx2_bestranks = [[qaid2_qres[qaid].get_best_gt_rank(ibs)] for qaid in qaids]
    return qx2_bestranks


#-----------
#@utool.indent_func('[harn]')
@profile
def test_configurations(ibs, qaid_list, test_cfg_name_list, fnum=1):
    # Test Each configuration
    if not QUIET:
        print(textwrap.dedent("""
        [harn]================
        [harn] experiment_harness.test_configurations()""").strip())

    qaids = qaid_list

    # Grab list of algorithm configurations to test
    #cfg_list = eh.get_cfg_list(test_cfg_name_list, ibs=ibs)
    cfg_list, cfgx2_lbl = eh.get_cfg_list_and_lbls(test_cfg_name_list, ibs=ibs)
    cfgx2_lbl = np.array(cfgx2_lbl)
    if not QUIET:
        print('[harn] Testing %d different parameters' % len(cfg_list))
        print('[harn]         %d different chips' % len(qaids))

    # Preallocate test result aggregation structures
    sel_cols = params.args.sel_cols  # FIXME
    sel_rows = params.args.sel_rows  # FIXME
    sel_cols = [] if sel_cols is None else sel_cols
    sel_rows = [] if sel_rows is None else sel_rows

    nCfg     = len(cfg_list)   # number of configurations (cols)
    nQuery   = len(qaids)  # number of queries (rows)

    mat_list = []
    #ibs._init_query_requestor()

    dbname = ibs.get_dbname()
    testnameid = dbname + ' ' + str(test_cfg_name_list)
    msg = textwrap.dedent('''
    ---------------------
    [harn] TEST_CFG %d/%d: ''' + testnameid + '''
    ---------------------''')
    mark_prog = utool.simple_progres_func(TESTRES_VERBOSITY, msg, '+')
    # Run each test configuration
    # Query Config / Col Loop
    daids = ibs.get_recognition_database_aids()
    nTotalQueries  = nQuery * nCfg  # number of quieries to run in total
    with utool.Timer('experiment_harness'):
        for cfgx, query_cfg in enumerate(cfg_list):
            if not QUIET:
                mark_prog(cfgx + 1, nCfg)
                print(query_cfg.get_cfgstr())
            cfglbl = cfgx2_lbl[cfgx]
            ibs.set_query_cfg(query_cfg)
            # Set data to the current config
            nPrevQueries = nQuery * cfgx  # number of pervious queries
            # Run the test / read cache
            with utool.Indenter('[%s cfg %d/%d]' % (dbname, cfgx + 1, nCfg)):
                qx2_bestranks = get_qx2_bestrank(ibs, qaids, nTotalQueries, nPrevQueries, cfglbl)
            if not NOMEMORY:
                mat_list.append(qx2_bestranks)
            # Store the results
    if not QUIET:
        print('[harn] Finished testing parameters')
    if NOMEMORY:
        print('ran tests in memory savings mode. exiting')
        return
    experiment_printres.print_results(ibs, qaids, daids, cfg_list,
                                          mat_list, testnameid, sel_rows,
                                          sel_cols, cfgx2_lbl=cfgx2_lbl)
