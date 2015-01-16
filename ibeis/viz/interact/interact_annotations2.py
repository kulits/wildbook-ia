from __future__ import absolute_import, division, print_function
from plottool import interact_annotations
from plottool import draw_func2 as df2
#from six.moves import zip
import utool
from ibeis.constants import VALID_SPECIES
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[interact_annot2]')


#DESTROY_OLD_WINDOW = True
DESTROY_OLD_WINDOW = False


class ANNOTATION_Interaction2(object):
    def __init__(self, ibs, gid, next_callback=None, prev_callback=None,
                 rows_updated_callback=lambda: None, reset_window=True):
        self.ibs = ibs
        self.gid = gid
        self.rows_updated_callback = rows_updated_callback
        img = ibs.get_images(self.gid)
        self.aid_list = ibs.get_image_aids(self.gid)
        bbox_list     = ibs.get_annot_bboxes(self.aid_list)
        theta_list    = ibs.get_annot_thetas(self.aid_list)
        species_list  = ibs.get_annot_species_texts(self.aid_list)
        valid_species = VALID_SPECIES
        self.interact_ANNOTATIONS = interact_annotations.ANNOTATIONInteraction(
            img,
            bbox_list=bbox_list,
            theta_list=theta_list,
            species_list=species_list,
            commit_callback=self.commit_callback,
            default_species=self.ibs.cfg.detect_cfg.species,
            next_callback=next_callback,
            prev_callback=prev_callback,
            fnum=12,
            valid_species=valid_species,
            #figure_to_use=None if reset_window else self.interact_ANNOTATIONS.fig,
        )
        df2.update()

    def commit_callback(self, unchanged_indicies, deleted_indicies, changed_indicies, changed_annottups, new_annottups):
        """
        TODO: Rename to commit_callback
        Callback from interact_annotations to ibs for when data is modified
        """
        print('[interact_annot2] enter commit_callback')
        print('[interact_annot2] nUnchanged=%d, nDelete=%d, nChanged=%d, nNew=%d' %
              (len(unchanged_indicies), len(deleted_indicies), len(changed_indicies), len(new_annottups)))
        rows_updated = False
        # Delete annotations
        if len(deleted_indicies) > 0:
            rows_updated = True
            deleted_aids = [self.aid_list[del_index] for del_index in deleted_indicies]
            print('[interact_annot2] deleted_indexes: %r' % (deleted_indicies,))
            print('[interact_annot2] deleted_aids: %r' % (deleted_aids,))
            self.ibs.delete_annots(deleted_aids)
        # Set/Change annotations
        if len(changed_annottups) > 0:
            changed_aid  = [self.aid_list[index] for index in changed_indicies]
            bbox_list1    = [bbox for (bbox, t, s) in changed_annottups]
            theta_list1   = [t    for (bbox, t, s) in changed_annottups]
            species_list1 = [s    for (bbox, t, s) in changed_annottups]
            print('[interact_annot2] changed_indexes: %r' % (changed_indicies,))
            print('[interact_annot2] changed_aid: %r' % (changed_aid,))
            self.ibs.set_annot_species(changed_aid, species_list1)
            self.ibs.set_annot_thetas(changed_aid, theta_list1, delete_thumbs=False)
            self.ibs.set_annot_bboxes(changed_aid, bbox_list1, delete_thumbs=True)
        # Add annotations
        if len(new_annottups) > 0:
            #print("species_list in annotation_interaction2: %r" % list(species_list))
            #btslist_tup = list(zip(*[((x, y, w, h), t, s) for (x, y, w, h, t, s) in new_annottups]))
            #bbox_list, theta_list, species_list = btslist_tup
            # New list returns a list of tuples [(x, y, w, h, theta, species) ...]
            rows_updated = True
            bbox_list2    = [bbox for (bbox, t, s) in new_annottups]
            theta_list2   = [t    for (bbox, t, s) in new_annottups]
            species_list2 = [s    for (bbox, t, s) in new_annottups]
            gid_list = [self.gid] * len(new_annottups)
            new_aids = self.ibs.add_annots(gid_list, bbox_list=bbox_list2,
                                           theta_list=theta_list2,
                                           species_list=species_list2)
            print('[interact_annot2] new_indexes: %r' % (new_annottups,))
            print('[interact_annot2] new_aids: %r' % (new_aids,))

        print('[interact_annot2] about to exit callback')
        if rows_updated:
            self.rows_updated_callback()
        print('[interact_annot2] exit callback')

    def update_image_and_callbacks(self, gid, nextcb, prevcb, do_save=True):
        if do_save:
            # save the current changes when pressing next or previous
            self.interact_ANNOTATIONS.accept_new_annotations(None, do_close=False)
        if DESTROY_OLD_WINDOW:
            ANNOTATION_Interaction2.__init__(self, self.ibs, gid,
                                             next_callback=nextcb,
                                             prev_callback=prevcb,
                                             rows_updated_callback=self.rows_updated_callback,
                                             reset_window=False)
        else:
            ibs = self.ibs
            self.gid = gid
            img = ibs.get_images(self.gid)
            self.aid_list = ibs.get_image_aids(self.gid)
            bbox_list = ibs.get_annot_bboxes(self.aid_list)
            theta_list = ibs.get_annot_thetas(self.aid_list)
            species_list = ibs.get_annot_species_texts(self.aid_list)
            self.interact_ANNOTATIONS.update_image_and_callbacks(
                img,
                bbox_list=bbox_list,
                theta_list=theta_list,
                species_list=species_list,
                next_callback=nextcb,
                prev_callback=prevcb,
            )


# Removed for pyinstaller?
#if __name__ == '__main__':
#    import ibeis
#    main_locals = ibeis.main(gui=False)
#    ibs = main_locals['ibs']
#    gid_list = ibs.get_valid_gids()
#    gid = gid_list[len(gid_list) - 1]
#    annotation = ANNOTATION_Interaction2(ibs, gid)
#    exec(df2.present())
