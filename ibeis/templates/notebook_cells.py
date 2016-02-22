# -*- coding: utf-8 -*-
"""
ComamndLine:
    python -m ibeis --tf autogen_ipynb --ipynb --db PZ_MTEST --ipynb

"""
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut

COMMENT_SPACE = ut.codeblock(
    r'''
    ### Comment space below:
    ''')

IGNOREAFTER = (ut.codeblock(
    '''
    ---

    # Developer Diagnostics  (Safely Ignored)
    # Safely Ignore the remainder of this document
    '''
), None)


introduction = (ut.codeblock(
    '''
    # Introduction: Testing IBEIS on a New Species

    This document is an IPython Notebook that summarizes a preliminary test
    of IBEIS on a new species. It includes steps (a) set up and configure
    the IBEIS image analysis code for a new data set, (b) run the core of
    this code, and (c) examine the results.

    To set the stage for what we are testing here, let's jump ahead to think
    about how IBEIS will work once we have built a database from initial
    training images for a species of interest. Given this database, IBEIS
    applies the following steps to each new set of images uploaded:

    1.  Gather the images taken at the same time and location (when known)
        to form what's known as an *occurrence*. Each image set is broken up
        into one or more occurrences.

    2.  Apply a *detection* process to each image to automatically find
        animals, to draw a bounding box around each, to label the species,
        and to determine the viewpoint on the animal. Together, this
        information forms an *annotation*.

    3.  Within each occurrence find all annotations that are the same
        animal, creating what IBEIS calls an *encounter.* If there are
        pictures of, say, five different animals in the occurrence then five
        encounters should be formed. Sometimes, of course, when animals are
        seen individually only one encounter will be formed.

    4.  Assign a *name* to the animal in each encounter by matching the
        annotations in the encounter against the database of animals. When
        this determines that an animal is previously unknown, a new name
        will be created and added to the database. Information about each
        encounter is also added to the database.

    Steps 3 and 4 are different applications of an underlying identification
    process whose goal is to determine which annotations show the same
    animal. The success of identification is the key to the success of
    IBEIS's image analysis. Therefore, the experiments reported in this
    IPython notebook are designed to study how well the current
    identification algorithms work by simulating Step 4 of the image
    analysis process – the hardest step. In addition to seeing how well the
    current IBEIS algorithms work, these tests can also suggest ways to
    improve the algorithms for the new species.

    Please note that the first three sections below – with (Code) in their
    title - can be safely skipped. They were generated by the IBEIS team to
    run the results here.
    '''), None)

initialize = ('# Initialization (Code)', ut.codeblock(
    r'''
    # STARTBLOCK
    {autogen_str}
    # Matplotlib stuff
    import matplotlib as mpl
    %matplotlib inline
    %load_ext autoreload
    %autoreload

    # Set global utool flags
    import utool as ut
    ut.util_io.__PRINT_WRITES__ = False
    ut.util_io.__PRINT_READS__ = False
    ut.util_parallel.__FORCE_SERIAL__ = True
    ut.util_cache.VERBOSE_CACHE = False
    ut.NOT_QUIET = False

    import plottool as pt
    fix_figsize = ut.partial(pt.set_figsize, w=30, h=10, dpi=256)
    pt.custom_figure.TITLE_SIZE = 20
    pt.custom_figure.LABEL_SIZE = 20
    pt.custom_figure.FIGTITLE_SIZE = 20

    draw_case_kw = dict(show_in_notebook=True, annot_modes=[0, 1])

    # Setup database specific parameter configurations
    db = '{dbname}'

    # Pick one of the following annotation configurations
    # to choose the query and database annotations
    a = [
        {annotconfig_list_body}
    ]
    #'ctrl:pername=None,view=left,view_ext=1,exclude_reference=False'


    # Set to override any special configs
    qaid_override = None
    daid_override = None

    # Uncomment one or more of the following pipeline configurations to choose
    # how the algorithm will run.  If multiple configurations are chosen, they
    # will be compared in the histograms, but only the first configuration will
    # be used for inspecting results.
    t = [
        {pipeline_list_body}
    ]

    # Load database for this test run
    import ibeis
    ibeis.expt.harness.USE_BIG_TEST_CACHE = True
    ibs = ibeis.opendb(db=db)

    # Make notebook cells wider
    from IPython.core.display import HTML
    HTML("<style>body .container {{ width:99% !important; }}</style>")
    # ENDBLOCK
    '''))


fluke_select = ('# Humpback Select',  ut.codeblock(
    r'''
    # STARTBLOCK
    # Tag annotations which have been given manual notch points
    from ibeis_flukematch.plugin import *  # NOQA
    ibs = ibeis.opendb(defaultdb='humpbacks')
    all_aids = ibs.get_valid_aids()
    isvalid = ibs.depc.get_property('Has_Notch', all_aids, 'flag')
    aid_list = ut.compress(all_aids, isvalid)
    # Tag the appropriate annots
    ibs.append_annot_case_tags(aid_list, ['hasnotch'] * len(aid_list))
    #depc = ibs.depc
    #qaid_override = aid_list[0:5]
    #daid_override = aid_list[0:7]
    #print(qaid_override)
    #print(daid_override)
    # ENDBLOCK
    '''))

annot_config_info =  ('# Annotation Config Info (Safely Ignored)', ut.codeblock(
    r'''
    # STARTBLOCK
    acfg_list, expanded_aids_list = ibeis.expt.experiment_helpers.get_annotcfg_list(
        ibs, acfg_name_list=a, qaid_override=qaid_override,
        daid_override=daid_override, verbose=0)
    ibeis.expt.annotation_configs.print_acfg_list(
        acfg_list, expanded_aids_list, ibs, per_qual=True)
    # ENDBLOCK
    ''')
)


pipe_config_info =  ('# Pipeline Config Info (Safely Ignored)', ut.codeblock(
    r'''
    # STARTBLOCK
    cfgdict_list, pipecfg_list = ibeis.expt.experiment_helpers.get_pipecfg_list(
        test_cfg_name_list=t, ibs=ibs)
    ibeis.expt.experiment_helpers.print_pipe_configs(cfgdict_list, pipecfg_list)
    # ENDBLOCK
    ''')
)


dbsize_expt = ('# Database Size Experiment ', ut.codeblock(
    r'''
    # STARTBLOCK
    if True:
        test_result = ibeis.run_experiment(
            e='rank_surface',
            db=db,
            a=['varysize_td'],
            t=['candk'])
        #test_result.print_unique_annot_config_stats()
        #test_result.print_acfg_info()
        test_result.draw_func()

    if True:
        # This test requires a little bit of relaxation to get enough data
        test_result = ibeis.run_experiment(
            e='rank_surface',
            db=db,
            a=['varysize_tdqual:qmin_pername=3,dpername=[1,2]'],
            t=['candk'])
        #test_result.print_unique_annot_config_stats()
        #test_result.print_acfg_info()
        test_result.draw_func()
    # ENDBLOCK
    ''')
)


timedelta_distribution = ('# Result Timedelta Distribution (Safely Ignore)', ut.codeblock(
    r'''
    # STARTBLOCK
    test_result = ibeis.run_experiment(
        e='timedelta_hist',
        db=db,
        a=a[0:1],
        t=t[0:1],
        qaid_override=qaid_override, daid_override=daid_override,
        truepos=True)
    test_result.draw_func()
    fix_figsize()
    # ENDBLOCK
    ''')
)


#latex_stats = ibeis.other.dbinfo.latex_dbstats([ibs], table_position='[h]') + '\n%--'
##print(latex_stats)
#pdf_fpath = ut.compile_latex_text(latex_stats, dpath=None, verbose=False, quiet=True, pad_stdout=False)
#pdf_fpath = ut.tail(pdf_fpath, n=2)
#print(pdf_fpath)
#from IPython.display import HTML
#HTML('<iframe src="%s" width=700 height=350></iframe>' % pdf_fpath)
#_ = ibeis.other.dbinfo.get_dbinfo(ibs)
timestamp_distribution = (
    ut.codeblock(
        r'''
        # Timestamp Distribution

        We can be confident that IBEIS will be successful if the
          identification process works well on photos animals that were taken
          weeks, months or years apart.
        We’d like to be able to identify an animal even if we haven’t seen it
          for a few years.
        Therefore, our first analysis studies the time distribution of the
          images.
        The plot below shows the distribution of “Timestamps” for the images
          we are testing on.
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        # Get images of those used in the tests
        acfg_list, expanded_aids_list = ibeis.expt.experiment_helpers.get_annotcfg_list(
            ibs, acfg_name_list=a, qaid_override=qaid_override,
            daid_override=daid_override, verbose=0)

        aids = ut.unique(ut.flatten(ut.flatten(expanded_aids_list)))
        # aids = ut.unique_ordered(ut.flatten([qaids, daids]))
        gids = ut.unique_ordered(ibs.get_annot_gids(aids))
        # Or just get time delta of all images
        #gids = ibs.get_valid_gids()

        ibeis.other.dbinfo.show_image_time_distributions(ibs, gids)
        #ibeis.other.dbinfo.show_image_time_distributions(ibs, gids)
        # ENDBLOCK
        '''))

example_annotations = (
    ut.codeblock(
        '''
        # Example Annotations / Detections

        The detection process is not shown in this IPython notebook. This
        process – Step 2 in the description of the introduction – is something
        we usually do not apply to a new test suite of images, largely because
        it requires a fair amount of training data to adapt to a new species.
        Shown below are example annotations. Sometimes we have to draw them
        ourselves, while other times they are given to us (along with the names
        of the animals).
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        # Get a sample of images
        #gids = ibs.get_valid_gids()
        acfg_list, expanded_aids_list = ibeis.expt.experiment_helpers.get_annotcfg_list(
                    ibs, acfg_name_list=a, qaid_override=qaid_override,
                    daid_override=daid_override, verbose=0)
        aids = ut.unique(ut.flatten(ut.flatten(expanded_aids_list)))
        gids = ut.unique_ordered(ibs.get_annot_gids(aids))
        # Or just get time delta of all images
        #gids = ibs.get_valid_gids()

        aids = ibs.get_image_aids(gids)

        nAids_list = list(map(len, aids))
        gids_sorted = ut.sortedby(gids, nAids_list)[::-1]
        samplex = list(range(5))
        print(samplex)
        gids_sample = ut.take(gids_sorted, samplex)

        import ibeis.viz
        for gid in ut.ProgressIter(gids_sample, lbl='drawing image'):
            ibeis.viz.show_image(ibs, gid)
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)


example_names = (
    ut.codeblock(
        '''
        # Example Name Graph:

        In a test where the names for each animal in each photo are provided, we
        can link up the annotations for each animal into what we call a *name
        graph.* (This is done without running the IBEIS image analysis code –
        just from the information provided.) We can use the name graph to spot
        potential problems and get an idea of how difficult the identification
        problem might be. In particular, an animal whose name graph has fewer
        annotations will be harder to identify. Similarly, when the name graph
        includes only one annotation from a particular viewpoint – such as the
        left flank – the animal will hard to identify if that annotation by
        itself was the one we tried to use to identify the animal.
        '''
    ),
    ut.codeblock(
        r'''
        # STARTBLOCK
        from ibeis.viz import viz_graph
        acfg_list, expanded_aids_list = ibeis.expt.experiment_helpers.get_annotcfg_list(
                    ibs, acfg_name_list=a, qaid_override=qaid_override,
                    daid_override=daid_override, verbose=0)
        aids = ut.unique(ut.flatten(ut.flatten(expanded_aids_list)))

        # Sample some annotations
        aids = ibs.sample_annots_general(aids, filter_kw=dict(sample_size=20, min_pername=2), verbose=False)
        # Visualize name graph
        namegraph = viz_graph.make_name_graph_interaction(ibs, aids=aids, zoom=.4)
        fix_figsize()
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)


#######
# CONFIG COMPARISONS
#######


per_annotation_accuracy = (
    ut.codeblock(
        '''
        # Annotation Identification Accuracy: (% correct annotations)

        The first and toughest test of the IBEIS identification algorithm is to
        take each annotation by itself and attempt to identify it. This is done
        by forming a database from other the annotations in the test suite and
        running the identification algorithm against this database. Other
        annotations from the same encounter as this “query annotation” are
        excluded. This is repeated for each annotation. This is the toughest
        test of image analysis because each annotation must be matched on its
        own, without any help from other annotations in the encounter. So, for
        example, if the encounter includes annotations showing both the left and
        right flank of the animal, but no other annotations in the test suite
        show this animal’s right flank, there is no hope for success in
        identifying the animal from just the right flank annotation.

        Results are shown below in both textual form and in a bar graph. It is
        probably best to skip to the bar graph. At this point, we should make
        something clear: the identification algorithm is really a ranking
        algorithm. In other words, when matching the annotation, a score is
        generated for each named animal in the database and names (and scores)
        are returned ordered by the scores. The goal is for the correct name to
        always be ranked first, but if it is ranked near the top it is usually
        ok too because the users of IBEIS make the final decisions about the
        identifying (and therefore naming) the animals.
        '''
    ),
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='rank_cdf',
            db=db, a=a, t=t, qaid_override=qaid_override, daid_override=daid_override)
        #testres.print_unique_annot_config_stats()
        _ = testres.draw_func()
        fix_figsize()
        # ENDBLOCK
        '''
    ),
    COMMENT_SPACE
)

per_name_accuracy = (

    ut.codeblock(
        r'''
        # Encounter Identification Accuracy (% correct names)

        The second test of the IBEIS identification algorithm – the most
        important test from the user’s perspective – is to take all the
        annotations in each encounter and together use them to determine the
        identity of the animal shown in the encounter. Once again, this is done
        by forming a database from the other annotations in the test suite. We
        perform this test because IBEIS algorithms combine information from
        matching for each annotation in an encounter to determine the final
        score for each possible name and thereby the final name ranking.

        Identifying an animal using all the annotations in an encounter almost
        always improves the scoring and ranking results. This is one reason why
        we strongly encourage users of the system to take and contribute several
        different images of each animal they encounter and not try to choose the
        “best” to contribute! This simplifies the user’s job and makes the IBEIS
        software as effective as possible.
        '''),

    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='rank_cdf',
            db=db, a=a, t=t, do_per_annot=False, qaid_override=qaid_override, daid_override=daid_override)
        #testres.print_unique_annot_config_stats()
        _ = testres.draw_func()
        fix_figsize()
        # ENDBLOCK
        '''
    ),
    COMMENT_SPACE
)


config_overlap = ('# Configuration Overlap (Safely Ignored)', ut.codeblock(
    r'''
    # STARTBLOCK
    # How well do different configurations compliment each other?
    testres.print_config_overlap()
    # ENDBLOCK
    '''
))


config_disagree_cases = ('# Configuration Disagreements (Safely Ignored)', ut.codeblock(
    r'''
    # STARTBLOCK
    # This shows individual examples where the tested configurations disagree.
    # This only works if more than one configuration was specified.
    # STARTBLOCK
    testres = ibeis.run_experiment(
        e='draw_cases',
        db=db, a=a, t=t,
        f=[':disagree=True,index=0:3'],
        figsize=(30, 8),
        **draw_case_kw)

    _ = testres.draw_func()
    # ENDBLOCK
    # ENDBLOCK
    '''
))


feat_score_sep = ('# Feature Correspondence Score Separation (Safely Ignored)', ut.codeblock(
    r'''
    # STARTBLOCK
    test_result = ibeis.run_experiment(
        e='TestResult.draw_feat_scoresep',
        db=db,
        a=a,
        t=t,
        #disttype=['L2_sift']
    )
    #test_result.draw_feat_scoresep(f='', disttype=['L2_sift'])
    test_result.draw_feat_scoresep(f='', disttype=None)
    fix_figsize()
    # ENDBLOCK
    '''))


success_annot_scoresep = (
    '# Scores of Success Cases (Safely Ignored)',
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='draw_annot_scoresep',
            db=db, a=a, t=t,
            f=[':fail=False,min_gf_timedelta=None'],
        )
        _ = testres.draw_func()
        fix_figsize()
        # ENDBLOCK
        '''))

all_annot_scoresep = (
    '# All Score Distribution (Safely Ignored)',
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='scores',
            db=db, a=a, t=t,
            qaid_override=qaid_override, daid_override=daid_override,
            f=[':fail=None,min_gf_timedelta=None']
        )
        _ = testres.draw_func()
        fix_figsize()
        #testres.draw_taghist()()
        #fix_figsize()
        # ENDBLOCK
        '''))


view_intereseting_tags = (
    '# Interesting Tags',
    ut.codeblock(
        r'''
        # STARTBLOCK
        test_result = ibeis.run_experiment(
            e='draw_cases',
            db=db,
            a=a,
            t=t,
            f=[':index=0:5,with_tag=interesting'],
            **draw_case_kw)
        _ = test_result.draw_func()
        # ENDBLOCK
        '''))

easy_success_cases = (
    ut.codeblock(
        '''
        # Examples of Top Scoring Successes:

        The next four sections including this one show examples of Annotation
        Identifications that are successes (top ranked) and failures (not top
        ranked). In each case results are shown in rows of two side-by-side
        blocks of annotations. Each block includes two, three or four
        annotations. In a block the left or upper left is the “query
        annotation”, i.e. the one IBEIS is trying to identify. This annotation
        has a purple border around it. Next to it and (when there are four
        annotations) below it are shown a set of “other” database annotations.
        When the identification is correct, these other annotations are all from
        the same name as the query annotation. These are framed in green. When
        the identified name is incorrect these other database annotations – all
        from the incorrect name - are framed in red.

        For the top scoring successes, we show strong true positives in the
        block on the left and the next best scoring true negative in the block
        on the right. Two rows of blocks are shown for each result, with the top
        row showing just the two blocks of annotations, and the blocks in the
        bottom row show the annotations together with matching regions linked by
        a line segment between annotations. The links go from the query
        annotation to the database annotations. Usually the links are to
        multiple database annotations (for the same animal) since information
        from more than one annotation is used to make decisions. Showing these
        matches allows us to understand what the image analysis algorithm used
        to score the match.

        (Notice that sometimes you will see matches between the background
        regions of the annotations. These will be eliminated in the production
        version of IBEIS for because IBEIS learns to figure out and ignore the
        background through training examples.)
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='draw_cases',
            db=db, a=a, t=t,
            f=[':fail=False,index=0:3,sortdsc=gtscore,max_pername=1'],
            # REM f=[':fail=False,index=0:3,sortdsc=gtscore,without_gf_tag=Photobomb,max_pername=1'],
            # REM f=[':fail=False,sortdsc=gtscore,without_gf_tag=Photobomb,max_pername=1'],
            figsize=(30, 8),
            **draw_case_kw)

        _ = testres.draw_func()
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)

hard_success_cases = (
    ut.codeblock(
        '''
        # Examples of Challenging Successes:

        This section shows Annotation Identification test cases where the top
        scoring name is correct, but the score is low and close to the score of
        the next best matching name.
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='draw_cases',
            db=db, a=a, t=t,
            f=[':fail=False,index=0:3,sortasc=gtscore,max_pername=1,min_gtscore=.00001'],  # hack min_gtscore for 0 scores marked as success
            # REM f=[':fail=False,index=0:3,sortdsc=gtscore,without_gf_tag=Photobomb,max_pername=1'],
            # REM f=[':fail=False,sortdsc=gtscore,without_gf_tag=Photobomb,max_pername=1'],
            figsize=(30, 8),
            **draw_case_kw)

        _ = testres.draw_func()
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)


# ================
# Individual Cases
# ================


#'# Cases: Failure (false neg)',
failure_type2_cases =  (
    ut.codeblock(
        '''
        # Examples of High-Scoring Failures:

        This section shows Annotation Identification test examples where the
        correct name is not the top scoring matching, but it scored reasonably
        high. In each case, the annotations from the incorrect matching name are
        shown in the block on the left (along with the query annotation), while
        annotations from the correct matching name are shown in the block on the
        right.
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='draw_cases',
            db=db, a=a, t=t,
            f=[':fail=True,index=0:3,sortdsc=gtscore,max_pername=1'],
            figsize=(30, 8),
            **draw_case_kw)
        _ = testres.draw_func()
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)

failure_type1_cases = (
    ut.codeblock(
        r'''
        # Examples of Low-Scoring Failures:

        This section shows Annotation Identification test examples where the
        correct name is not the top scoring match, and the correct name scored
        quite poorly. In each case, the annotations from the incorrect matching
        name are shown in the block on the left (along with the query
        annotation), while annotations from the failed but correct matching name
        are shown in the block on the right. Such failures are most often due to
        low quality annotations, occlusions, or the query annotation showing a
        view of the animal that is not in any annotation in the database.
        '''),
    ut.codeblock(
        r'''
        # STARTBLOCK
        testres = ibeis.run_experiment(
            e='draw_cases',
            db=db, a=a, t=t,
            f=[':fail=True,index=0:3,sortdsc=gfscore,max_pername=1'],
            figsize=(30, 8),
            **draw_case_kw)
        _ = testres.draw_func()
        # ENDBLOCK
        '''),
    COMMENT_SPACE
)


investigate_specific_case = (
    '# Cases: Custom Investigation',
    ut.codeblock(
        r'''
        # STARTBLOCK
        test_result = ibeis.run_experiment(
            e='draw_cases',
            db=db,
            a=a,
            #t=t,
            t=[t[0], t[0] + 'SV=False'],
            qaid_override=[2604],  # CHOOSE A SPECIFIC ANNOTATION
            figsize=(30, 8),
            **draw_case_kw)
        _ = test_result.draw_func()
        # ENDBLOCK
        '''))
