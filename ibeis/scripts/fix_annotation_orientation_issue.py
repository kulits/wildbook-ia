# -*- coding: utf-8 -*-
import utool as ut
import vtool as vt


def fix_annotation_orientation(ibs, min_percentage=0.95):
    """
    Fixes the annotations that are outside the bounds of the image due to a
    changed image orientation flag in the database

    CommandLine:
        python -m ibeis.scripts.fix_annotation_orientation_issue fix_annotation_orientation

    Example:
        >>> # SCRIPT
        >>> import ibeis
        >>> from ibeis.scripts.fix_annotation_orientation_issue import *  # NOQA
        >>> ibs = ibeis.opendb()
        >>> result = fix_annotation_orientation(ibs)

    """
    from vtool import exif

    def bbox_overlap(bbox1, bbox2):
        ax1 = bbox1[0]
        ay1 = bbox1[1]
        ax2 = bbox1[0] + bbox1[2]
        ay2 = bbox1[1] + bbox1[3]
        bx1 = bbox2[0]
        by1 = bbox2[1]
        bx2 = bbox2[0] + bbox2[2]
        by2 = bbox2[1] + bbox2[3]
        overlap_x = max(0, min(ax2, bx2) - max(ax1, bx1))
        overlap_y = max(0, min(ay2, by2) - max(ay1, by1))
        return overlap_x * overlap_y

    orient_dict = exif.ORIENTATION_DICT_INVERSE
    good_orient_list = [
        exif.ORIENTATION_UNDEFINED,
        exif.ORIENTATION_000,
    ]
    good_orient_key_list = [
        orient_dict.get(good_orient)
        for good_orient in good_orient_list
    ]
    assert None not in good_orient_key_list

    gid_list = ibs.get_valid_gids()
    orient_list = ibs.get_image_orientation(gid_list)
    flag_list = [ orient not in good_orient_key_list for orient in orient_list ]

    # Filter based on based gids
    gid_list = ut.filter_items(gid_list, flag_list)
    if len(gid_list) > 0:
        args = (len(gid_list), )
        print('Found %d images with non-standard orientations' % args)
        aids_list = ibs.get_image_aids(gid_list)
        size_list = ibs.get_image_sizes(gid_list)
        invalid_gid_list = []
        zipped = zip(gid_list, orient_list, aids_list, size_list)
        for gid, orient, aid_list, (w_, h_) in zipped:
            image = ibs.get_images(gid)
            h, w = image.shape[:2]
            if h_ != h or w_ != w:
                ibs._set_image_sizes(gid, w, h)
            image_bbox = (0, 0, w, h)
            verts_list = ibs.get_annot_rotated_verts(aid_list)
            invalid = False
            for aid, vert_list in zip(aid_list, verts_list):
                annot_bbox = vt.bbox_from_verts(vert_list)
                overlap = bbox_overlap(image_bbox, annot_bbox)
                area = annot_bbox[2] * annot_bbox[3]
                percentage = overlap / area
                if percentage < min_percentage:
                    invalid = True
                    args = (gid, aid, overlap, area, overlap / area)
                    print('\tGID %r, AID %r: Overlap %0.2f, Area %0.2f (%0.2f %%)' % args)
                    if orient == orient_dict.get(exif.ORIENTATION_090):
                        pass
                    elif orient == orient_dict.get(exif.ORIENTATION_180):
                        pass
                    elif orient == orient_dict.get(exif.ORIENTATION_270):
                        pass
                    else:
                        raise ValueError('Unrecognized invalid orientation')
            if invalid:
                invalid_gid_list.append(gid)
        args = (len(invalid_gid_list), invalid_gid_list)
        print('Found %d images with invalid annotations = %r' % args)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    ut.doctest_funcs()