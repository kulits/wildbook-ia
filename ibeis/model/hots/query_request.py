from __future__ import absolute_import, division, print_function
from ibeis.model.hots import neighbor_index, score_normalization
from ibeis.model import Config
import copy
import six
import utool as ut
import numpy as np
(print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[qreq]')


def new_ibeis_query_request(ibs, qaid_list, daid_list, cfgdict=None):
    """
    ibeis entry point to create a new query request object

    CommandLine:
        python -m ibeis.model.hots.query_request --test-new_ibeis_query_request

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.query_request import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(db='PZ_MTEST')
        >>> qaids = [1]
        >>> daids = [1, 2, 3, 4, 5]
        >>> cfgdict = {'sv_on': False, 'fg_weight': 1.0, 'featweight_on': True}
        >>> # Execute test
        >>> qreq_ = new_ibeis_query_request(ibs, qaids, daids, cfgdict=cfgdict)
        >>> # Check Results
        >>> print(qreq_.qparams.query_cfgstr)
        >>> assert qreq_.qparams.fg_weight == 1.0, (
        ...    'qreq_.qparams.fg_weight = %r ' % qreq_.qparams.fg_weight)
        >>> assert qreq_.qparams.sv_on is False, (
        ...     'qreq_.qparams.sv_on = %r ' % qreq_.qparams.sv_on)
        >>> datahashid = qreq_.get_data_hashid()
        >>> dbname = ibs.get_dbname()
        >>> result = dbname + datahashid
        >>> print(result)
        PZ_MTEST_DUUIDS((5)q87ho9a0@9s02imh)

    Example2:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.query_request import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(db='NAUT_test')
        >>> qaids = [1]
        >>> daids = [1, 2, 3, 4, 5]
        >>> cfgdict = {'sv_on': True, 'fg_weight': 1.0, 'featweight_on': True}
        >>> # Execute test
        >>> qreq_ = new_ibeis_query_request(ibs, qaids, daids, cfgdict=cfgdict)
        >>> # Check Results.
        >>> # Featweight should be off because there is no Naut detector
        >>> print(qreq_.qparams.query_cfgstr)
        >>> assert qreq_.qparams.fg_weight == 0.0, (
        ...    'qreq_.qparams.fg_weight = %r ' % qreq_.qparams.fg_weight)
        >>> assert qreq_.qparams.sv_on is True, (
        ...     'qreq_.qparams.sv_on = %r ' % qreq_.qparams.sv_on)
        >>> datahashid = qreq_.get_data_hashid()
        >>> dbname = ibs.get_dbname()
        >>> result = dbname + datahashid
        >>> print(result)
        NAUT_test_DUUIDS((5)4e972cjxcj30a8u1)

    """
    if ut.NOT_QUIET:
        print(' --- New IBEIS QRequest --- ')
    cfg     = ibs.cfg.query_cfg
    qresdir = ibs.get_qres_cachedir()
    cfgdict = {} if cfgdict is None else cfgdict.copy()
    # <HACK>
    unique_species = apply_species_with_detector_hack(ibs, cfgdict)
    # </HACK>
    qparams = QueryParams(cfg, cfgdict)
    # FIXME: SYSTEM
    quuid_list = ibs.get_annot_uuids(qaid_list)
    duuid_list = ibs.get_annot_uuids(daid_list)
    qreq_ = QueryRequest(qaid_list, quuid_list,
                         daid_list, duuid_list,
                         qparams, qresdir, ibs)
    if ut.NOT_QUIET:
        print(' * query_cfgstr = %s' % (qreq_.qparams.query_cfgstr,))
    qreq_.unique_species = unique_species  # HACK
    return qreq_


def apply_species_with_detector_hack(ibs, cfgdict):
    """
    HACK turns of featweights if they cannot be applied
    """
    from ibeis import constants as const
    unique_species = ibs.get_database_species()
    # turn off featureweights when not absolutely sure they are ok to us,)
    species_with_detectors = (
        const.Species.ZEB_GREVY,
        const.Species.ZEB_PLAIN,
    )
    candetect = (
        len(unique_species) == 1 and
        unique_species[0] in species_with_detectors
    )
    if not candetect:
        print('HACKING FG_WEIGHT OFF (database species is not supported)')
        if len(unique_species) != 1:
            print('  * len(unique_species) = %r' % len(unique_species))
        else:
            print('  * unique_species = %r' % (unique_species,))
        print('  * valid species = %r' % (species_with_detectors,))
        #cfg._featweight_cfg.featweight_on = 'ERR'
        cfgdict['featweight_on'] = 'ERR'
    return unique_species


#def qreq_shallow_copy(qreq_, qx=None, dx=None):
#    #[qx:qx + 1]
#    #[qx:qx + 1]
#    qreq_copy  = QueryRequest(qaid_list, quuid_list, daid_list, duuid_list,
#                              qreq_.qparams, qreq_.qresdir, qreq_.ibs)
#    qreq_copy.unique_species = qreq_.unique_species  # HACK
#    qreq_copy.ibs = qreq_.ibs
#    return qreq_copy


@six.add_metaclass(ut.ReloadingMetaclass)
class QueryRequest(object):
    def __init__(qreq_, qaid_list, quuid_list, daid_list, duuid_list, qparams,
                 qresdir, ibs):
        # Reminder:
        # lists and other objects are functionally equivalent to pointers
        qreq_.unique_species = None  # num categories
        qreq_.internal_qspeciesid_list = None  # category species id label list
        #qreq_.internal_qnid_list = None  # individual name id label list
        qreq_.internal_qaids = None
        qreq_.internal_daids = None
        #qreq_.internal_qidx  = None
        #qreq_.internal_didx  = None
        #qreq_.internal_qvecs_list = None
        #qreq_.internal_qkpts_list = None
        #qreq_.internal_dkpts_list = None
        #qreq_.internal_qgid_list  = None
        #qreq_.internal_qnid_list  = None
        # Handle to parent IBEIS Controller
        # THIS SHOULD BE OK BUT MAYBE IBS SHOULD BE REMOVED FROM THE
        # PICTURE AFTER THE QREQ IS BUILT?
        qreq_.ibs = ibs
        # The nearest neighbor mechanism
        qreq_.indexer = None
        # The scoring normalization mechanism
        qreq_.normalizer = None
        # Hacky metadata
        qreq_.metadata = {}
        # DEPRICATE?
        #qreq_.aid2_nid = None
        qreq_.hasloaded = False
        qreq_.internal_quuids = None
        qreq_.internal_duuids = None

        # Set values
        qreq_.qparams = qparams   # Parameters relating to pipeline execution
        qreq_.qresdir = qresdir
        qreq_.set_external_daids(daid_list, duuid_list)
        qreq_.set_external_qaids(qaid_list, quuid_list)

    def shallowcopy(qreq_, qx=None, dx=None):
        """
        Creates a copy of qreq with the same qparams object and a subset of the qx
        and dx objects.
        used to generate chunks of vsone queries

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.model.hots.query_request import *  # NOQA
            >>> import ibeis
            >>> qreq_, ibs = get_test_qreq()
            >>> qreq2_ = qreq_.shallowcopy(0)
            >>> assert qreq_.get_external_daids() is qreq2_.get_external_daids()
            >>> assert len(qreq_.get_external_qaids()) != len(qreq2_.get_external_qaids())
            >>> assert qreq_.metadata is not qreq2_.metadata
        """
        qreq2_ = copy.copy(qreq_)
        if qx is not None:
            qaid_list  = qreq2_.get_external_qaids()
            quuid_list = qreq2_.get_external_quuids()
            qaid_list  = qaid_list[qx:qx + 1]
            quuid_list = quuid_list[qx:qx + 1]
            qreq2_.set_external_qaids(qaid_list, quuid_list)
        if dx is not None:
            daid_list  = qreq2_.get_external_daids()
            duuid_list = qreq2_.get_external_duuids()
            daid_list  = daid_list[dx:dx + 1]
            duuid_list = duuid_list[dx:dx + 1]
            qreq2_.set_external_daids(daid_list, duuid_list)
        # The shallow copy does not bring over output / query data
        qreq2_.indexer = None
        qreq2_.normalizer = None
        qreq2_.metadata = {}
        qreq2_.hasloaded = False
        return qreq2_

    # --- State Modification ---
    # TODO: Dont modify state

    def set_external_daids(qreq_, daid_list, duuid_list):
        assert len(daid_list) == len(duuid_list), 'unequal len external daids'
        if qreq_.qparams.vsmany:
            qreq_.set_internal_daids(daid_list, duuid_list)
        else:
            qreq_.set_internal_qaids(daid_list, duuid_list)

    def set_external_qaids(qreq_, qaid_list, quuid_list):
        # TODO make shallow copy instead
        assert len(qaid_list) == len(quuid_list), 'unequal len internal qaids'
        if qreq_.qparams.vsmany:
            qreq_.set_internal_qaids(qaid_list, quuid_list)
        else:
            qreq_.set_internal_daids(qaid_list, quuid_list)

    def set_internal_daids(qreq_, daid_list, duuid_list):
        assert len(daid_list) == len(duuid_list), 'unequal len internal daids'
        qreq_.internal_daids = np.array(daid_list)
        qreq_.internal_duuids = np.array(duuid_list)
        # Index the annotation ids for fast internal lookup
        #qreq_.internal_didx = np.arange(len(daid_list))

    def set_internal_qaids(qreq_, qaid_list, quuid_list):
        assert len(qaid_list) == len(quuid_list), 'unequal len internal qaids'
        qreq_.internal_qaids = np.array(qaid_list)
        qreq_.internal_quuids = np.array(quuid_list)
        # Index the annotation ids for fast internal lookup
        #qreq_.internal_qidx = np.arange(len(qaid_list))

    # --- INTERNAL INTERFACE ---
    # For within pipeline use only

    #def get_internal_qvecs(qreq_):
    #    return qreq_.internal_qvecs_list

    def get_internal_data_hashid(qreq_):
        aids = qreq_.get_internal_daids()
        assert len(aids) > 0, 'QRequest not populated. len(aids)=0'
        # TODO: SYSTEM : semantic should only be used if name scoring is on
        inten_data_hashid = qreq_.ibs.get_annot_hashid_semantic_uuid(aids)
        # else
        #inten_data_hashid = qreq_.ibs.get_annot_hashid_visual_uuid(aids)
        return inten_data_hashid

    def get_internal_daids(qreq_):
        return qreq_.internal_daids

    def get_internal_qaids(qreq_):
        return qreq_.internal_qaids

    def get_internal_duuids(qreq_):
        return qreq_.internal_duuids

    def get_internal_quuids(qreq_):
        return qreq_.internal_quuids

    # --- EXTERNAL INTERFACE ---

    def get_unique_species(qreq_):
        return qreq_.unique_species

    # External id-lists

    def get_external_daids(qreq_):
        """ These are the users daids in vsone mode """
        if qreq_.qparams.vsmany:
            return qreq_.get_internal_daids()
        else:
            return qreq_.get_internal_qaids()

    def get_external_qaids(qreq_):
        """ These are the users qaids in vsone mode """
        if qreq_.qparams.vsmany:
            return qreq_.get_internal_qaids()
        else:
            return qreq_.get_internal_daids()

    def get_external_quuids(qreq_):
        """ These are the users qauuids in vsone mode """
        if qreq_.qparams.vsmany:
            return qreq_.get_internal_quuids()
        else:
            return qreq_.get_internal_duuids()

    def get_external_duuids(qreq_):
        """ These are the users qauuids in vsone mode """
        if qreq_.qparams.vsmany:
            return qreq_.get_internal_duuids()
        else:
            return qreq_.get_internal_quuids()

    # External id-hashes

    def get_data_hashid(qreq_):
        daids = qreq_.get_external_daids()
        assert len(daids) > 0, 'QRequest not populated. len(daids)=0'
        # TODO: SYSTEM : semantic should only be used if name scoring is on
        data_hashid = qreq_.ibs.get_annot_hashid_semantic_uuid(daids, '_DUUIDS')
        return data_hashid

    def get_query_hashid(qreq_):
        qaids = qreq_.get_external_qaids()
        assert len(qaids) > 0, 'QRequest not populated. len(qaids)=0'
        # TODO: SYSTEM : semantic should only be used if name scoring is on
        query_hashid = qreq_.ibs.get_annot_hashid_semantic_uuid(qaids, '_QUUIDS')
        return query_hashid

    def get_cfgstr(qreq_):
        daids_hashid = qreq_.get_data_hashid()
        cfgstr = daids_hashid + qreq_.qparams.query_cfgstr
        return cfgstr

    def get_qresdir(qreq_):
        return qreq_.qresdir

    # --- IBEISControl Transition ---

    #def get_annot_name_rowids(qreq_, aids):
    #    return qreq_.ibs.get_annot_name_rowids(aids)

    #def get_annot_gids(qreq_, aids):
    #    assert qreq_.ibs is not qreq_
    #    return qreq_.ibs.get_annot_gids(aids)

    #def get_annot_kpts(qreq_, aids):
    #    return qreq_.ibs.get_annot_kpts(aids)

    #def get_annot_chipsizes(qreq_, aids):
    #    return qreq_.ibs.get_annot_chipsizes(qreq_, aids)

    # --- Lazy Loading ---

    def lazy_load(qreq_):
        """
        Performs preloading of all data needed for a batch of queries
        """
        print('[qreq] lazy loading')
        qreq_.hasloaded = True
        #qreq_.ibs = ibs  # HACK
        if qreq_.qparams.pipeline_root in ['vsone', 'vsmany']:
            qreq_.load_indexer()
            # FIXME: not sure if this is even used
            #qreq_.load_query_vectors()
            #qreq_.load_query_keypoints()
        #if qreq_.qparams.pipeline_root in ['smk']:
        #    # TODO load vocabulary indexer
        if qreq_.qparams.featweight_on is True:
            qreq_.ensure_featweights()
        if qreq_.qparams.score_normalization is True:
            qreq_.load_score_normalizer()

    # load query data structures

    def ensure_featweights(qreq_):
        """ ensure feature weights are computed """
        internal_qaids = qreq_.get_internal_qaids()
        internal_daids = qreq_.get_internal_daids()
        # TODO: pass qreq_ down so the right parameters are computed
        qreq_.ibs.get_annot_fgweights(internal_qaids, ensure=True)
        qreq_.ibs.get_annot_fgweights(internal_daids, ensure=True)

    def load_indexer(qreq_):
        if qreq_.indexer is not None:
            return False
        # TODO: SYSTEM updatable indexer
        indexer = neighbor_index.new_ibeis_nnindexer(qreq_)
        qreq_.indexer = indexer

    def load_score_normalizer(qreq_):
        if qreq_.normalizer is not None:
            return False
        # TODO: SYSTEM updatable normalizer
        normalizer = score_normalization.request_ibeis_normalizer(qreq_)
        qreq_.normalizer = normalizer

    # load data lists
    # see _broken/broken_qreq.py

    #def load_query_vectors(qreq_, ibs):
    #    if qreq_.internal_qvecs_list is not None:
    #        return False
    #    aid_list = qreq_.get_internal_qaids()
    #    vecs_list = ibs.get_annot_vecs(aid_list)
    #    qreq_.internal_qvecs_list = vecs_list

    #def load_query_keypoints(qreq_, ibs):
    #    if qreq_.internal_qkpts_list is not None:
    #        return False
    #    aid_list = qreq_.get_internal_qaids()
    #    kpts_list = ibs.get_annot_kpts(aid_list)
    #    qreq_.internal_qkpts_list = kpts_list

    #def load_data_keypoints(qreq_, ibs):
    #    if qreq_.internal_dkpts_list is not None:
    #        return False
    #    aid_list = qreq_.get_internal_daids()
    #    kpts_list = ibs.get_annot_kpts(aid_list)
    #    qreq_.internal_dkpts_list = kpts_list

    #def load_annot_nameids(qreq_, ibs):
    #    import itertools
    #    aids = list(set(itertools.chain(qreq_.qaids, qreq_.daids)))
    #    nids = ibs.get_annot_name_rowids(aids)
    #    qreq_.aid2_nid = dict(zip(aids, nids))

    def assert_self(qreq_, ibs):
        print('[qreq] ASSERT SELF')
        qaids    = qreq_.get_external_qaids()
        qauuids  = qreq_.get_external_quuids()
        daids    = qreq_.get_external_daids()
        dauuids  = qreq_.get_external_duuids()
        _qaids   = qreq_.get_internal_qaids()
        _qauuids = qreq_.get_internal_quuids()
        _daids   = qreq_.get_internal_daids()
        _dauuids = qreq_.get_internal_duuids()
        def assert_uuids(aids, uuids):
            if ut.NOT_QUIET:
                print('[qreq_] asserting %s ids' % len(aids))
            assert len(aids) == len(uuids)
            assert all([u1 == u2 for u1, u2 in
                        zip(ibs.get_annot_uuids(aids), uuids)])
        assert_uuids(qaids, qauuids)
        assert_uuids(daids, dauuids)
        assert_uuids(_qaids, _qauuids)
        assert_uuids(_daids, _dauuids)


class QueryParams(object):
    """
    Structure to store static query pipeline parameters
    parses nested config structure into this flat one

    CommandLine:
        python -m ibeis.model.hots.query_request --test-QueryParams

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import query_request
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> cfg = ibs.cfg.query_cfg
        >>> #cfg.pipeline_root = 'asmk'
        >>> cfgdict = {'pipeline_root': 'asmk', 'sv_on': False,
        ...            'fg_weight': 1.0, 'featweight_on': True}
        >>> qparams = query_request.QueryParams(cfg, cfgdict)
        >>> assert qparams.fg_weight == 1.0
        >>> assert qparams.pipeline_root == 'smk'
        >>> assert qparams.featweight_on is True
        >>> result = qparams.query_cfgstr
        >>> print(')_\n'.join(result.split(')_')))
        _smk_SMK(agg=True,t=0.0,a=3.0,idf)_
        VocabAssign(nAssign=10,a=1.2,s=None,eqw=T)_
        VocabTrain(nWords=8000,init=akmeans++,nIters=128,taids=all)_
        SV(OFF)_
        FEATWEIGHT(ON,uselabel,rf)_
        FEAT(hesaff+sift_)_
        CHIP(sz450)
    """

    def __init__(qparams, cfg, cfgdict=None):
        """
        Args:
            cfg (QueryConfig): query_config
            cfgdict (dict or None): dictionary to update cfg with
        """
        # if given custom settings update the config and ensure feasibilty
        if cfgdict is not None:
            cfg = cfg.deepcopy()
            cfg.update_query_cfg(**cfgdict)
        # Get flat item list
        param_list = Config.parse_config_items(cfg)
        # Assert that there are no config conflicts
        duplicate_keys = ut.find_duplicate_items(ut.get_list_column(param_list, 0))
        assert len(duplicate_keys) == 0, 'Configs have duplicate names: %r' % duplicate_keys
        # Set nexted config attributes as flat qparam properties
        for key, val in param_list:
            setattr(qparams, key, val)
        # Add params not implicitly represented in Config object
        pipeline_root      = cfg.pipeline_root
        active_filter_list = cfg.filt_cfg.get_active_filters()
        filt2_stw          = {filt: cfg.filt_cfg.get_stw(filt)
                               for filt in active_filter_list}
        # Correct dumb filt2_stw Pref bugs
        for key, val in six.iteritems(filt2_stw):
            if val[1] == 'None':
                val[1] = None
            if val[1] is not None and not isinstance(val[1], (float, int)):
                val[1] = float(val[1])
        qparams.active_filter_list = active_filter_list
        qparams.filt2_stw          = filt2_stw
        qparams.flann_params       = cfg.flann_cfg.get_dict_args()
        qparams.pipeline_root      = pipeline_root
        qparams.vsmany             = pipeline_root == 'vsmany'
        qparams.vsone              = pipeline_root == 'vsone'
        # Add custom strings to the mix as well
        qparams.featweight_cfgstr = cfg._featweight_cfg.get_cfgstr()
        qparams.feat_cfgstr  = cfg._featweight_cfg._feat_cfg.get_cfgstr()
        qparams.nn_cfgstr    = cfg.nn_cfg.get_cfgstr()
        qparams.filt_cfgstr  = cfg.filt_cfg.get_cfgstr()
        qparams.sv_cfgstr    = cfg.sv_cfg.get_cfgstr()
        qparams.flann_cfgstr = cfg.flann_cfg.get_cfgstr()
        qparams.query_cfgstr = cfg.get_cfgstr()
        qparams.vocabtrain_cfgstr = cfg.smk_cfg.vocabtrain_cfg.get_cfgstr()


def get_test_qreq():
    import ibeis
    qaid_list = [1, 2]
    daid_list = [1, 2, 3, 4, 5]
    ibs = ibeis.opendb(db='testdb1')
    qreq_ = new_ibeis_query_request(ibs, qaid_list, daid_list)
    return qreq_, ibs


def test_cfg_deepcopy():
    """
    TESTING FUNCTION

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.query_request import *  # NOQA
        >>> result = test_cfg_deepcopy()
        >>> print(result)
    """
    import ibeis
    ibs = ibeis.opendb('testdb1')
    cfg1 = ibs.cfg.query_cfg
    cfg2 = cfg1.deepcopy()
    cfg3 = cfg2
    assert cfg1.get_cfgstr() == cfg2.get_cfgstr()
    assert cfg2.sv_cfg is not cfg1.sv_cfg
    assert cfg3.sv_cfg is cfg2.sv_cfg
    cfg2.update_query_cfg(sv_on=False)
    assert cfg1.get_cfgstr() != cfg2.get_cfgstr()
    assert cfg2.get_cfgstr() == cfg3.get_cfgstr()


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.model.hots.query_request --test-QueryParams
        profiler.sh -m ibeis.model.hots.query_request --test-QueryParams

        python -m ibeis.model.hots.query_request
        python -m ibeis.model.hots.query_request --allexamples
        python -m ibeis.model.hots.query_request --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    ut.doctest_funcs()
