# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut
import numpy as np
import copy
import six
(print, rrr, profile) = ut.inject2(__name__, '[depbase]')


class Config(ut.NiceRepr, ut.DictLike, ut.HashComparable):
    r"""
    Base class for heirarchical config
    need to overwrite get_param_info_list
    """
    def __init__(cfg, **kwargs):
        cfg.initialize_params(**kwargs)

    def __nice__(cfg):
        return cfg.get_cfgstr(with_name=False)

    def __hash__(cfg):
        """ Needed for comparison operators """
        return hash(cfg.get_cfgstr())

    def get_config_name(cfg, **kwargs):
        """ the user might want to overwrite this function """
        #class_str = str(cfg.__class__)
        #full_class_str = class_str.replace('<class \'', '').replace('\'>', '')
        #config_name = splitext(full_class_str)[1][1:].replace('Config', '')
        config_name = cfg.__class__.__name__.replace('Config', '')
        # VERY HACKY
        import re
        config_name = re.sub('_$', '', config_name)
        return config_name

    def get_varnames(cfg):
        return ([pi.varname for pi in cfg.get_param_info_list()] +
                cfg._subconfig_attrs)

    def update(cfg, **kwargs):
        """
        Overwrites default DictLike update for only keys that exist.

        Example:
            >>> # ENABLE_DOCTEST
            >>> from dtool.base import *  # NOQA
            >>> from dtool.example_depcache import DummyVsManyConfig
            >>> cfg = DummyVsManyConfig()
            >>> cfg.update(DummyAlgo_version=4)
            >>> print(cfg)
        """
        # FIXME: currently can't update subconfigs based on namespaces
        # and non-namespaced vars are in the context of the root level.
        self_keys = set(cfg.__dict__.keys())
        name = cfg.get_config_name()
        prefix = name + '_'
        for key, val in six.iteritems(kwargs):
            # update only existing keys or namespace prefixed keys
            if key.startswith(prefix):
                key = key[len(prefix):]
            if key in self_keys:
                setattr(cfg, key, val)

    def initialize_params(cfg, **kwargs):
        """ Initializes config class attributes based on params info list """
        for pi in cfg.get_param_info_list():
            setattr(cfg, pi.varname, pi.default)

        # SO HACKY
        # Hacks in implicit edges from nodes to the algorithm
        # using their subconfigurations
        cfg._subconfig_attrs = []
        cfg._subconfig_names = []
        _sub_config_list = cfg.get_sub_config_list()
        if _sub_config_list:
            for subclass in _sub_config_list:
                #subclass.static_config_name()
                subcfg = subclass()
                subcfg_name = subcfg.get_config_name()
                subcfg_attr = ut.to_underscore_case(subcfg_name) + '_cfg'
                setattr(cfg, subcfg_attr, subcfg)
                cfg._subconfig_names.append(subcfg_name)
                cfg._subconfig_attrs.append(subcfg_attr)
                subcfg.update(**kwargs)
        cfg.update(**kwargs)

    def get_sub_config_list(cfg):
        if hasattr(cfg, '_sub_config_list'):
            return cfg._sub_config_list
        else:
            return None

    def parse_namespace_config_items(cfg):
        """
        Recursively extracts key, val pairs from Config objects
        into a flat list. (there must not be name conflicts)
        """
        param_list = []
        seen = set([])
        for item in cfg.items():
            key, val = item
            if hasattr(val, 'parse_namespace_config_items'):
                child_cfg = val
                child_params = child_cfg.parse_namespace_config_items()
                param_list.extend(child_params)
            elif key.startswith('_'):
                pass
            else:
                if key in seen:
                    print('[Config] WARNING: key=%r appears more than once' %
                          (key,))
                seen.add(key)
                # Incorporate namespace
                name = cfg.get_config_name()
                param_list.append((name, key, val))
        return param_list

    def parse_items(cfg):
        r"""
        Returns:
            list: param_list

        CommandLine:
            python -m dtool.base --exec-parse_items

        Example:
            >>> # ENABLE_DOCTEST
            >>> from dtool.base import *  # NOQA
            >>> from dtool.example_depcache import DummyVsManyConfig
            >>> cfg = DummyVsManyConfig()
            >>> param_list = cfg.parse_items()
            >>> result = ('param_list = %s' % (ut.repr2(param_list, nl=1),))
            >>> print(result)
        """
        namespace_param_list = cfg.parse_namespace_config_items()
        param_names = ut.get_list_column(namespace_param_list, 1)
        needs_namespace_keys = ut.find_duplicate_items(param_names)
        param_list = ut.get_list_column(namespace_param_list, [1, 2])
        # prepend namespaces to variables that need it
        for idx in ut.flatten(needs_namespace_keys.values()):
            name = namespace_param_list[idx][0]
            param_list[idx][0] = name + '_' + param_list[idx][0]
        duplicate_keys = ut.find_duplicate_items(ut.get_list_column(param_list, 0))
        # hack to let version through
        import utool
        with utool.embed_on_exception_context:
            assert len(duplicate_keys) == 0, (
                'Configs have duplicate names: %r' % duplicate_keys)
        return param_list

    def get_cfgstr_list(cfg, ignore_keys=None, with_name=True, **kwargs):
        """ default get_cfgstr_list, can be overrided by a config object """
        if ignore_keys is not None:
            itemstr_list = [pi.get_itemstr(cfg)
                            for pi in cfg.get_param_info_list()
                            if pi.varname not in ignore_keys]
        else:
            itemstr_list = [pi.get_itemstr(cfg)
                            for pi in cfg.get_param_info_list()]
        filtered_itemstr_list = list(filter(len, itemstr_list))
        if with_name:
            config_name = cfg.get_config_name()
        else:
            config_name = ''
        body = ','.join(filtered_itemstr_list)
        cfgstr = ''.join([config_name, '(', body, ')'])
        return cfgstr

    def get_cfgstr(cfg, **kwargs):
        str_ = ''.join(cfg.get_cfgstr_list(**kwargs))
        return '_'.join([str_] + [cfg[subcfg_attr].get_cfgstr()
                                  for subcfg_attr in cfg._subconfig_attrs])

    def get_hashid(cfg):
        return ut.hashstr27(cfg.get_cfgstr())

    def keys(cfg):
        """ Required for DictLike interface """
        return cfg.get_varnames()

    def getitem(cfg, key):
        """ Required for DictLike interface """
        try:
            return getattr(cfg, key)
        except AttributeError as ex:
            raise KeyError(ex)

    def get(qparams, key, *d):
        """ get a paramater value by string """
        ERROR_ON_DEFAULT = True
        if ERROR_ON_DEFAULT:
            return getattr(qparams, key)
        else:
            return getattr(qparams, key, *d)

    def setitem(cfg, key, value):
        """ Required for DictLike interface """
        return getattr(cfg, key, value)

    def get_param_info_list(cfg):
        try:
            return cfg._param_info_list
        except AttributeError:
            raise NotImplementedError(
                'Need to define _param_info_list or get_param_info_list')

    @classmethod
    def from_argv_dict(cls, **kwargs):
        """
        handy command line tool
        ut.parse_argv_cfg
        """
        cfg = cls(**kwargs)
        new_vals = ut.parse_dict_from_argv(cfg)
        cfg.update(**new_vals)
        return cfg

    @classmethod
    def from_argv_cfgs(cls):
        """
        handy command line tool
        """
        cfg = cls()
        name = cfg.get_config_name()
        #name = cls.static_config_name()
        argname = '--' + name
        if hasattr(cfg, '_alias'):
            argname = (argname, '--' + cfg._alias)
        #if hasattr(cls, '_alias'):
        #    argname = (argname, '--' + cls._alias)
        new_vals_list = ut.parse_argv_cfg(argname)
        self_list = [cls(**new_vals) for new_vals in new_vals_list]
        return self_list

    def __getstate__(cfg):
        return cfg.asdict()

    def __setstate__(cfg, state):
        cfg.update(**state)

    #@classmethod
    #def static_config_name(cls):
    #    class_str = str(cls)
    #    full_class_str = class_str.replace('<class \'', '').replace('\'>', '')
    #    config_name = splitext(full_class_str)[1][1:].replace('Config', '')
    #    return config_name


def dict_as_config(default_cfgdict, tablename):
    import dtool
    class UnnamedConfig(dtool.Config):
        def get_param_info_list(cfg):
            #print('default_cfgdict = %r' % (default_cfgdict,))
            return [ut.ParamInfo(key, val)
                    for key, val in default_cfgdict.items()]
    UnnamedConfig.__name__ = str(tablename + 'Config')
    return UnnamedConfig


class IBEISRequestHacks(object):
    _isnewreq = True

    @property
    def ibs(request):
        """ HACK specific to ibeis """
        if request.depc is None:
            return None
        return request.depc.controller

    def get_external_data_config2(request):
        # HACK
        #return None
        #print('[d] request.params = %r' % (request.params,))
        return request.params

    def get_external_query_config2(request):
        # HACK
        #return None
        #print('[q] request.params = %r' % (request.params,))
        return request.params


@ut.reloadable_class
class BaseRequest(IBEISRequestHacks, ut.NiceRepr):
    """
    Class that maintains both an algorithm, inputs, and a config.
    """
    @staticmethod
    def static_new(cls, depc, parent_rowids, cfgdict=None, tablename=None):
        """ hack for autoreload """
        request = cls()
        if tablename is None:
            try:
                if hasattr(cls, '_tablename'):
                    tablename = cls._tablename
                else:
                    tablename = ut.invert_dict(depc.requestclass_dict)[cls]
            except Exception as ex:
                ut.printex(ex, 'tablename must be given')
                raise
        request.tablename = tablename
        request.parent_rowids = parent_rowids
        request.depc = depc
        if cfgdict is None:
            cfgdict = {}
        configclass = depc.configclass_dict[tablename]
        config = configclass(**cfgdict)
        request.config = config
        # hack
        request.params = dict(config.parse_items())
        return request

    @classmethod
    def new(cls, depc, parent_rowids, cfgdict=None, tablename=None):
        return cls.static_new(cls, depc, parent_rowids, cfgdict, tablename)

    def _get_rootset_hashid(request, root_rowids, prefix):
        uuid_type = 'V'
        label = ''.join((prefix, uuid_type, 'UUIDS'))
        # Hack: allow general specification of uuid types
        uuid_list = request.depc.get_root_uuid(root_rowids)
        #uuid_hashid = ut.hashstr_arr27(uuid_list, label, pathsafe=True)
        uuid_hashid = ut.hashstr_arr27(uuid_list, label, pathsafe=False)
        return uuid_hashid

    def get_cfgstr(request, with_input=False, with_pipe=True, **kwargs):
        r"""
        main cfgstring used to identify the 'querytype'
        """
        cfgstr_list = []
        if with_input:
            cfgstr_list.append(request.get_input_hashid())
        if with_pipe:
            cfgstr_list.append(request.get_pipe_cfgstr())
        cfgstr = '_'.join(cfgstr_list)
        return cfgstr

    def get_input_hashid(request):
        raise NotImplementedError('abstract class method')

    def get_pipe_cfgstr(request):
        return request.config.get_cfgstr()

    def get_pipe_hashid(request):
        return ut.hashstr27(request.get_pipe_cfgstr())

    def ensure_dependencies(request):
        """
        CommandLine:
            python -m dtool.base --exec-BaseRequest.ensure_dependencies

        Example:
            >>> # ENABLE_DOCTEST
            >>> from dtool.base import *  # NOQA
            >>> from dtool.example_depcache import testdata_depc
            >>> depc = testdata_depc()
            >>> request = depc.new_request('vsmany', [1, 2], [2, 3, 4])
            >>> request.ensure_dependencies()
        """
        import networkx as nx
        depc = request.depc
        if False:
            dependencies = nx.ancestors(depc.graph, request.tablename)
            subgraph = depc.graph.subgraph(set.union(dependencies, {request.tablename}))
            dependency_order = nx.topological_sort(subgraph)
            root = dependency_order[0]
            [nx.algorithms.dijkstra_path(subgraph, root, start)[:-1] +
             nx.algorithms.dijkstra_path(subgraph, start, request.tablename)
             for start in dependency_order]
        graph = depc.graph
        root = nx.topological_sort(graph)[0]
        edges = graph.edges()
        #parent_to_children = ut.edges_to_adjacency_list(edges)
        child_to_parents = ut.edges_to_adjacency_list([t[::-1] for t in edges])
        to_root = {request.tablename:
                   ut.paths_to_root(request.tablename, root, child_to_parents)}
        from_root = ut.reverse_path(to_root, root, child_to_parents)
        dependency_levels_ = ut.get_levels(from_root)
        dependency_levels = ut.longest_levels(dependency_levels_)

        true_order = ut.flatten(dependency_levels)[1:-1]
        #print('[req] Ensuring %s request dependencies: %r' % (request, true_order,))
        ut.colorprint(
            '[req] Ensuring request %s dependencies: %r' % (request, true_order,), 'yellow')
        for tablename in true_order:
            table = depc[tablename]
            if table.ismulti:
                pass
            else:
                # HACK FOR IBEIS
                all_aids = ut.flat_unique(request.qaids, request.daids)
                depc.get_rowids(tablename, all_aids)
                pass
            pass

        #zip(depc.get_implicit_edges())
        #zip(depc.get_implicit_edges())

        #raise NotImplementedError('todo')
        #depc = request.depc
        #parent_rowids = request.parent_rowids
        #config = request.config
        #rowid_dict = depc.get_all_descendant_rowids(
        #    request.tablename, root_rowids, config=config)
        pass

    def execute(request, parent_rowids=None, use_cache=None, postprocess=True):
        ut.colorprint('[req] Executing request %s' % (request,), 'yellow')
        table = request.depc[request.tablename]
        if use_cache is None:
            use_cache = not ut.get_argflag('--nocache')
        if parent_rowids is None:
            parent_rowids = request.parent_rowids
        # Compute and cache any uncomputed results
        rowids = table.get_rowid(parent_rowids, config=request,
                                 recompute=not use_cache)
        # Load all results
        result_list = table.get_row_data(rowids)
        if postprocess and hasattr(request, 'postprocess_execute'):
            print('Converting results')
            result_list = request.postprocess_execute(parent_rowids, result_list)
            pass
        return result_list

    def __getstate__(request):
        state_dict = request.__dict__.copy()
        # SUPER HACK
        state_dict['dbdir'] = request.depc.controller.get_dbdir()
        del state_dict['depc']
        del state_dict['config']
        return state_dict

    def __setstate__(request, state_dict):
        import ibeis
        dbdir = state_dict['dbdir']
        del state_dict['dbdir']
        params = state_dict['params']
        depc = ibeis.opendb(dbdir=dbdir, web=False).depc
        configclass = depc.configclass_dict[state_dict['tablename'] ]
        config = configclass(**params)
        state_dict['depc'] = depc
        state_dict['config'] = config
        request.__dict__.update(state_dict)


class AnnotSimiliarity(object):

    def get_query_hashid(request):
        return request._get_rootset_hashid(request.qaids, 'Q')

    def get_data_hashid(request):
        return request._get_rootset_hashid(request.daids, 'D')


@ut.reloadable_class
class VsOneSimilarityRequest(BaseRequest, AnnotSimiliarity):
    """
    Similarity request for pairwise scores

    References:
        https://thingspython.wordpress.com/2010/09/27/
        another-super-wrinkle-raising-typeerror/

    CommandLine:
        python -m dtool.base --exec-VsOneSimilarityRequest

    Example:
        >>> # ENABLE_DOCTEST
        >>> from dtool.base import *  # NOQA
        >>> from dtool.example_depcache import testdata_depc
        >>> qaid_list = [1, 2]
        >>> daid_list = [2, 3, 4]
        >>> depc = testdata_depc()
        >>> request = depc.new_request('vsone', qaid_list, daid_list)
        >>> results = request.execute()
        >>> # Test that adding a query / data id only recomputes necessary items
        >>> request2 = depc.new_request('vsone', qaid_list + [3], daid_list + [5])
        >>> results2 = request2.execute()
        >>> print('results = %r' % (results,))
        >>> print('results2 = %r' % (results2,))
        >>> assert len(results) == 5, 'incorrect num output'
        >>> assert len(results2) == 10, 'incorrect num output'
    """
    @classmethod
    def new(cls, depc, qaid_list, daid_list, cfgdict=None, tablename=None):
        parent_rowids = list(ut.product_nonsame(qaid_list, daid_list))
        request = cls.static_new(cls, depc, parent_rowids, cfgdict, tablename)
        request.qaids = safeop(np.array, qaid_list)
        request.daids = safeop(np.array, daid_list)
        return request

    @property
    def parent_rowids_T(request):
        return ut.list_transpose(request.parent_rowids)

    def execute_subset(request, qaids, use_cache=None):
        subparent_rowids = list(ut.product_nonsame(qaids, request.daids))
        results = request.execute(subparent_rowids, use_cache)
        return results

    def get_input_hashid(request):
        return '_'.join([request.get_query_hashid(), request.get_data_hashid()])

    def __nice__(request):
        dbname = (None if request.depc is None or request.depc.controller is None
                  else request.depc.controller.get_dbname())
        infostr_ = 'nQ=%s, nD=%s, nP=%d %s' % (len(request.qaids),
                                               len(request.daids),
                                               len(request.parent_rowids),
                                               request.get_pipe_hashid())
        return '(%s) %s' % (dbname, infostr_)


@ut.reloadable_class
class VsManySimilarityRequest(BaseRequest, AnnotSimiliarity):
    """
    Request for one-vs-many simlarity

    CommandLine:
        python -m dtool.base --exec-VsManySimilarityRequest

    Example:
        >>> # ENABLE_DOCTEST
        >>> from dtool.base import *  # NOQA
        >>> from dtool.example_depcache import testdata_depc
        >>> qaid_list = [1, 2]
        >>> daid_list = [2, 3, 4]
        >>> depc = testdata_depc()
        >>> request = depc.new_request('vsmany', qaid_list, daid_list)
        >>> request.ensure_dependencies()
        >>> results = request.execute()
        >>> # Test dependence on data
        >>> request2 = depc.new_request('vsmany', qaid_list + [3], daid_list + [5])
        >>> results2 = request2.execute()
        >>> print('results = %r' % (results,))
        >>> print('results2 = %r' % (results2,))
        >>> assert len(results) == 2, 'incorrect num output'
        >>> assert len(results2) == 3, 'incorrect num output'
    """

    @classmethod
    def new(cls, depc, qaid_list, daid_list, cfgdict=None, tablename=None):
        parent_rowids = list(zip(qaid_list))
        request = cls.static_new(cls, depc, parent_rowids, cfgdict, tablename)
        request.qaids = safeop(np.array, qaid_list)
        request.daids = safeop(np.array, daid_list)
        # HACK
        request.config.daids = request.daids
        return request

    def execute_subset(request, qaids, use_cache=None):
        subparent_rowids = qaids
        return request.execute(subparent_rowids, use_cache)

    def get_input_hashid(request):
        #return '_'.join([request.get_query_hashid(), request.get_data_hashid()])
        return '_'.join([request.get_query_hashid()])

    def get_cfgstr(request, with_input=False, with_data=True, with_pipe=True,
                   hash_pipe=False):
        r"""
        Override default get_cfgstr to show reliance on data
        """
        cfgstr_list = []
        if with_input:
            cfgstr_list.append(request.get_query_hashid())
        if with_data:
            cfgstr_list.append(request.get_data_hashid())
        if with_pipe:
            if hash_pipe:
                cfgstr_list.append(request.get_pipe_hashid())
            else:
                cfgstr_list.append(request.get_pipe_cfgstr())
        cfgstr = '_'.join(cfgstr_list)
        return cfgstr

    def __nice__(request):
        dbname = (None if request.depc is None or request.depc.controller is None
                  else request.depc.controller.get_dbname())
        infostr_ = 'nQ=%s, nD=%s %s' % (len(request.qaids), len(request.daids),
                                        request.get_pipe_hashid())
        return '(%s) %s' % (dbname, infostr_)


class ClassVsClassSimilarityRequest(BaseRequest):
    pass


class AlgoResult(object):
    """ Base class for algo result objects """

    @classmethod
    def load_from_fpath(cls, fpath, verbose=ut.VERBOSE):
        state_dict = ut.load_cPkl(fpath, verbose=verbose)
        self = cls()
        self.__setstate__(state_dict)
        return self

    def save_to_fpath(cm, fpath, verbose=ut.VERBOSE):
        ut.save_cPkl(fpath, cm.__getstate__(), verbose=verbose, n=2)

    def __getstate__(self):
        state_dict = self.__dict__
        return state_dict

    def __setstate__(self, state_dict):
        self.__dict__.update(state_dict)

    def copy(self):
        cls = self.__class__
        out = cls()
        state_dict = copy.deepcopy(self.__getstate__())
        out.__setstate__(state_dict)
        return out


def safeop(op_, xs, *args, **kwargs):
    return None if xs is None else op_(xs, *args, **kwargs)


class MatchResult(AlgoResult, ut.NiceRepr):
    def __init__(self, qaid=None, daids=None, qnid=None, dnid_list=None,
                 annot_score_list=None, unique_nids=None,
                 name_score_list=None):
        self.qaid = qaid
        self.daid_list = safeop(np.array, daids)
        self.dnid_list = safeop(np.array, dnid_list)
        self.annot_score_list = safeop(np.array, annot_score_list)
        self.name_score_list = safeop(np.array, name_score_list)

    @property
    def num_daids(cm):
        return None if cm.daid_list is None else len(cm.daid_list)

    @property
    def daids(cm):
        return cm.daid_list

    @property
    def qaids(cm):
        return cm.qaid

    def __nice__(cm):
        return ' qaid=%s nD=%s' % (cm.qaid, cm.num_daids)


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m dtool.base
        python -m dtool.base --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
