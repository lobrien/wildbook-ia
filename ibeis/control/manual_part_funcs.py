# -*- coding: utf-8 -*-
"""
Autogen:
    python -c "import utool as ut; ut.write_modscript_alias('Tgen.sh', 'ibeis.templates.template_generator')"  # NOQA
    sh Tgen.sh --key part --invert --Tcfg with_getters=True with_setters=True --modfname manual_part_funcs --funcname-filter=age_m  # NOQA
    sh Tgen.sh --key part --invert --Tcfg with_getters=True with_setters=True --modfname manual_part_funcs --funcname-filter=is_  # NOQA
    sh Tgen.sh --key part --invert --Tcfg with_getters=True with_setters=True --modfname manual_part_funcs --funcname-filter=is_ --diff  # NOQA
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import six
import uuid
import numpy as np
from ibeis import constants as const
from ibeis.control import accessor_decors, controller_inject
import utool as ut
from ibeis.control.controller_inject import make_ibs_register_decorator
from ibeis.web import routes_ajax
print, rrr, profile = ut.inject2(__name__)


CLASS_INJECT_KEY, register_ibs_method = make_ibs_register_decorator(__name__)


register_api   = controller_inject.get_ibeis_flask_api(__name__)


PART_NOTE               = 'part_note'
PART_NUM_VERTS          = 'part_num_verts'
PART_ROWID              = 'part_rowid'
PART_TAG_TEXT           = 'part_tag_text'
PART_THETA              = 'part_theta'
PART_VERTS              = 'part_verts'
PART_UUID               = 'part_uuid'
PART_QUALITY            = 'part_quality'


# ==========
# IDERS
# ==========


# TODO CACHE THIS AND FIND WHAT IT SHOULD INVALIDATE IT
# ADD PARTS, DELETE PARTS ANYTHING ELSE?
@register_ibs_method
@accessor_decors.ider
def _get_all_part_rowids(ibs):
    r"""
    Returns:
        list_ (list):  all unfiltered part_rowids (part rowids)
    """
    all_part_rowids = ibs.db.get_all_rowids(const.PART_TABLE)
    return all_part_rowids


@register_ibs_method
def get_num_parts(ibs, **kwargs):
    r"""
    Number of valid parts
    """
    part_rowid_list = ibs.get_valid_part_rowids(**kwargs)
    return len(part_rowid_list)


@register_ibs_method
@register_api('/api/part/<rowid>/', methods=['GET'])
def part_src_api(rowid=None):
    r"""
    Returns the base64 encoded image of part <rowid>

    RESTful:
        Method: GET
        URL:    /api/part/<rowid>/
    """
    return routes_ajax.part_src(rowid)


def filter_part_set(ibs, part_rowid_list, include_only_aid_list=None,
                          viewpoint='no-filter', minqual=None):
    # -- valid part_rowid filtering --
    if include_only_aid_list is not None:
        gid_list     = ibs.get_part_gids(part_rowid_list)
        is_valid_gid = [gid in include_only_aid_list for gid in gid_list]
        part_rowid_list     = ut.compress(part_rowid_list, is_valid_gid)
    if viewpoint != 'no-filter':
        viewpoint_list     = ibs.get_part_viewpoints(part_rowid_list)
        is_valid_viewpoint = [viewpoint == flag for flag in viewpoint_list]
        part_rowid_list     = ut.compress(part_rowid_list, is_valid_viewpoint)
    if minqual is not None:
        part_rowid_list = ibs.filter_part_rowids_to_quality(part_rowid_list, minqual, unknown_ok=True)
    part_rowid_list = sorted(part_rowid_list)
    return part_rowid_list


# ==========
# ADDERS
# ==========


@register_ibs_method
@accessor_decors.adder
@register_api('/api/part/', methods=['POST'])
def add_parts(ibs, aid_list, bbox_list=None, theta_list=None,
                detect_confidence_list=None, notes_list=None,
                vert_list=None, part_uuid_list=None, viewpoint_list=None,
                quality_list=None, type_list=None, **kwargs):
    r"""
    Adds an part to annotations

    Args:
        aid_list                 (list): annotation rowids to add part to
        bbox_list                (list): of [x, y, w, h] bounding boxes for each annotation (supply verts instead)
        theta_list               (list): orientations of parts
        vert_list                (list): alternative to bounding box

    Returns:
        list: part_rowid_list

    CommandLine:
        python -m ibeis.control.manual_part_funcs --test-add_parts
        python -m ibeis.control.manual_part_funcs --test-add_parts --verbose --print-caller

    Ignore:
       detect_confidence_list = None
       notes_list = None
       part_uuid_list = None
       viewpoint_list = None
       quality_list = None
       type_list = None

    RESTful:
        Method: POST
        URL:    /api/part/

    Example:
        >>> # Test with prevent_visual_duplicates on
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> prevalid = ibs.get_valid_part_rowids()
        >>> num_add = 1
        >>> gid_list = ibs.get_valid_gids()[0:1] * num_add
        >>> bbox_list = [(int(w * .1), int(h * .6), int(w * .5), int(h *  .3))
        ...              for (w, h) in ibs.get_image_sizes(gid_list)]
        >>> bbox_list2 = [(int(w * .2), int(h * .6), int(w * .5), int(h *  .3))
        ...              for (w, h) in ibs.get_image_sizes(gid_list)]
        >>> # Add a test part
        >>> print('Testing add_parts')
        >>> part_rowid_list1 = ibs.add_parts(gid_list, bbox_list=bbox_list, prevent_visual_duplicates=True)
        >>> part_rowid_list2 = ibs.add_parts(gid_list, bbox_list=bbox_list, prevent_visual_duplicates=True)
        >>> part_rowid_list3 = ibs.add_parts(gid_list, bbox_list=bbox_list2, prevent_visual_duplicates=True)
        >>> assert part_rowid_list1 == part_rowid_list2, 'part_rowid_list1 == part_rowid_list2'
        >>> assert part_rowid_list1 != part_rowid_list3, 'part_rowid_list1 != part_rowid_list3'
        >>> part_rowid_list_new = part_rowid_list1 + part_rowid_list3
        >>> result = part_rowid_list_new
        >>> print('Cleaning up. Removing added parts')
        >>> ibs.delete_parts(part_rowid_list_new)
        >>> print(result)
        [14, 15]
    """
    #ut.embed()
    from vtool import geometry
    if ut.VERBOSE:
        print('[ibs] adding parts')
    # Prepare the SQL input
    # For import only, we can specify both by setting import_override to True
    assert bool(bbox_list is None) != bool(vert_list is None), (
        'must specify exactly one of bbox_list or vert_list')
    ut.assert_all_not_None(aid_list, 'aid_list')

    if vert_list is None:
        vert_list = geometry.verts_list_from_bboxes_list(bbox_list)
    elif bbox_list is None:
        bbox_list = geometry.bboxes_from_vert_list(vert_list)

    if theta_list is None:
        theta_list = [0.0 for _ in range(len(aid_list))]

    len_bbox    = len(bbox_list)
    len_vert    = len(vert_list)
    len_aid     = len(aid_list)
    len_theta   = len(theta_list)
    try:
        assert len_vert  == len_bbox, 'bbox and verts are not of same size'
        assert len_aid   == len_bbox, 'bbox and aid are not of same size'
        assert len_aid   == len_theta, 'bbox and aid are not of same size'
    except AssertionError as ex:
        ut.printex(ex, key_list=['len_vert', 'len_aid', 'len_bbox'
                                    'len_theta'])
        raise

    if len(aid_list) == 0:
        # nothing is being added
        print('[ibs] WARNING: 0 parts are being added!')
        print(ut.dict_str(locals()))
        return []

    if detect_confidence_list is None:
        detect_confidence_list = [0.0 for _ in range(len(aid_list))]
    if notes_list is None:
        notes_list = ['' for _ in range(len(aid_list))]
    if viewpoint_list is None:
        viewpoint_list = [-1.0] * len(aid_list)
    if type_list is None:
        type_list = [const.UNKNOWN] * len(aid_list)

    nVert_list = [len(verts) for verts in vert_list]
    vertstr_list = [six.text_type(verts) for verts in vert_list]
    xtl_list, ytl_list, width_list, height_list = list(zip(*bbox_list))
    assert len(nVert_list) == len(vertstr_list)

    # Build ~~deterministic?~~ random and unique PART ids
    if part_uuid_list is None:
        part_uuid_list = [uuid.uuid4() for _ in range(len(aid_list))]

    # Define arguments to insert
    colnames = ('part_uuid', 'annot_rowid', 'part_xtl', 'part_ytl',
                'part_width', 'part_height', 'part_theta', 'part_num_verts',
                'part_verts', 'part_viewpoint', 'part_detect_confidence',
                'part_note', 'part_type')

    check_uuid_flags = [not isinstance(auuid, uuid.UUID) for auuid in part_uuid_list]
    if any(check_uuid_flags):
        pos = ut.list_where(check_uuid_flags)
        raise ValueError('positions %r have malformated UUIDS' % (pos,))

    params_iter = list(zip(part_uuid_list, aid_list, xtl_list, ytl_list,
                            width_list, height_list, theta_list, nVert_list,
                            vertstr_list, viewpoint_list, detect_confidence_list,
                            notes_list, type_list))

    # Execute add PARTs SQL
    superkey_paramx = (0,)
    get_rowid_from_superkey = ibs.get_part_rowids_from_uuid
    part_rowid_list = ibs.db.add_cleanly(const.PART_TABLE, colnames, params_iter,
                                         get_rowid_from_superkey, superkey_paramx)
    return part_rowid_list


@register_ibs_method
# @register_api('/api/part/rows/', methods=['GET'])
def get_part_rows(ibs, part_rowid_list):
    r"""
    Auto-docstr for 'get_part_rows'
    """
    colnames = ('part_uuid', 'annot_rowid', 'part_xtl', 'part_ytl',
                'part_width', 'part_height', 'part_theta', 'part_num_verts',
                'part_verts', 'part_viewpoint', 'part_detect_confidence',
                'part_note', 'part_quality', 'part_type')
    rows_list = ibs.db.get(const.PART_TABLE, colnames, part_rowid_list,
                           unpack_scalars=False)
    return rows_list


# ==========
# DELETERS
# ==========


@register_ibs_method
@accessor_decors.deleter
@accessor_decors.cache_invalidator(const.PART_TABLE, rowidx=0)
@register_api('/api/part/', methods=['DELETE'])
def delete_parts(ibs, part_rowid_list):
    r"""
    deletes parts from the database

    RESTful:
        Method: DELETE
        URL:    /api/part/

    Args:
        ibs (IBEISController):  ibeis controller object
        part_rowid_list (int):  list of part ids

    CommandLine:
        python -m ibeis.control.manual_part_funcs --test-delete_parts
        python -m ibeis.control.manual_part_funcs --test-delete_parts --debug-api-cache
        python -m ibeis.control.manual_part_funcs --test-delete_parts

    SeeAlso:
        back.delete_part

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.manual_part_funcs import *  # NOQA
        >>> from os.path import exists
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> ibs.delete_empty_nids()
        >>> # Add some parts to delete
        >>> num_add = 2
        >>> gid_list = ibs.get_valid_gids()[0:num_add]
        >>> nid = ibs.make_next_nids(1)[0]
        >>> nid_list = [nid] * num_add
        >>> bbox_list = [(int(w * .1), int(h * .6), int(w * .5), int(h *  .3))
        ...              for (w, h) in ibs.get_image_sizes(gid_list)]
        >>> new_part_rowid_list = ibs.add_parts(gid_list, bbox_list=bbox_list,
        >>>                               nid_list=nid_list)
        >>> ibs.get_part_nids(new_part_rowid_list)
        >>> ut.assert_lists_eq(ibs.get_part_nids(new_part_rowid_list), nid_list)
        >>> assert ibs.get_name_part_rowids(nid) == new_part_rowid_list, 'parts should all have same name'
        >>> assert new_part_rowid_list == ibs.get_name_part_rowids(nid), 'inverse name mapping should work'
        >>> #thumpaths = ibs.get_image_thumbpath(gid_list, ensure_paths=True, **{'thumbsize': 221})
        >>> #assert any(ut.lmap(exists, thumpaths)), 'thumbs should be there'
        >>> before_part_rowids = ibs.get_image_part_rowids(gid_list)
        >>> print('BEFORE gids: ' + str(before_part_rowids))
        >>> result = ibs.delete_parts(new_part_rowid_list)
        >>> assert ibs.get_name_part_rowids(nid) == [], 'parts should be removed'
        >>> after_part_rowids = ibs.get_image_part_rowids(gid_list)
        >>> #thumpaths = ibs.get_image_thumbpath(gid_list, ensure_paths=False, **{'thumbsize': 221})
        >>> #assert not any(ut.lmap(exists, thumpaths)), 'thumbs should be gone'
        >>> assert after_part_rowids != before_part_rowids, 'the invalidators must have bugs'
        >>> print('AFTER gids: ' + str(after_part_rowids))
        >>> valid_part_rowids = ibs.get_valid_part_rowids()
        >>> assert  [part_rowid not in valid_part_rowids for part_rowid in new_part_rowid_list], 'should no longer be valid part_rowids'
        >>> print(result)
        >>> ibs.delete_empty_nids()

    """
    if ut.VERBOSE:
        print('[ibs] deleting %d parts' % len(part_rowid_list))
    # delete parent rowid column if exists in part table
    return ibs.db.delete_rowids(const.PART_TABLE, part_rowid_list)


# ==========
# GETTERS
# ==========


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/rowid/uuid/', methods=['GET'])
def get_part_rowids_from_uuid(ibs, uuid_list):
    r"""
    Returns:
        list_ (list): part rowids

    RESTful:
        Method: GET
        URL:    /api/part/rowid/uuid/
    """
    # FIXME: MAKE SQL-METHOD FOR NON-ROWID GETTERS
    part_rowids_list = ibs.db.get(const.PART_TABLE, (PART_ROWID,), uuid_list,
                                  id_colname=PART_UUID)
    return part_rowids_list


@register_ibs_method
@accessor_decors.getter_1to1
# @register_api('/api/part/uuid/missing/', methods=['GET'])
def get_part_missing_uuid(ibs, uuid_list):
    r"""
    Returns:
        list_ (list): a list of missing part uuids
    """
    part_rowid_list = ibs.get_part_rowids_from_uuid(uuid_list)
    zipped = zip(part_rowid_list, uuid_list)
    missing_uuid_list = [ uuid for part_rowid, uuid in zipped if part_rowid is None ]
    return missing_uuid_list


@register_ibs_method
@ut.accepts_numpy
@accessor_decors.getter_1toM
@register_api('/api/part/bbox/', methods=['GET'])
def get_part_bboxes(ibs, part_rowid_list):
    r"""
    Returns:
        bbox_list (list):  part bounding boxes in image space

    RESTful:
        Method: GET
        URL:    /api/part/bbox/
    """
    colnames = ('part_xtl', 'part_ytl', 'part_width', 'part_height',)
    bbox_list = ibs.db.get(const.PART_TABLE, colnames, part_rowid_list)
    return bbox_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/detect/confidence/', methods=['GET'])
def get_part_detect_confidence(ibs, part_rowid_list):
    r"""
    Returns:
        list_ (list): a list confidences that the parts is a valid detection

    RESTful:
        Method: GET
        URL:    /api/part/detect/confidence/
    """
    part_detect_confidence_list = ibs.db.get(const.PART_TABLE,
                                              ('part_detect_confidence',),
                                              part_rowid_list)
    return part_detect_confidence_list


@register_ibs_method
@ut.accepts_numpy
@accessor_decors.getter_1to1
@register_api('/api/part/annot/rowid/', methods=['GET'])
def get_part_aids(ibs, part_rowid_list, assume_unique=False):
    r"""
    Get parent annotation rowids of parts

    Args:
        part_rowid_list (list):

    Returns:
        aid_list (list):  annot rowids

    RESTful:
        Method: GET
        URL:    /api/part/annot/rowid/

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.manual_part_funcs import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> part_rowid_list = ibs.get_valid_part_rowids()
        >>> result = get_part_aids(ibs, part_rowid_list)
        >>> print(result)
    """
    aid_list = ibs.db.get(const.PART_TABLE, ('annot_rowid',), part_rowid_list, assume_unique=assume_unique)
    return aid_list


@register_ibs_method
def get_part_annot_rowids(ibs, part_rowid_list):
    return ibs.get_part_aids(part_rowid_list)


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/theta/', methods=['GET'])
def get_part_thetas(ibs, part_rowid_list):
    r"""
    Returns:
        theta_list (list): a list of floats describing the angles of each part

    CommandLine:
        python -m ibeis.control.manual_part_funcs --test-get_part_thetas

    RESTful:
        Method: GET
        URL:    /api/part/theta/

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.manual_part_funcs import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('NAUT_test')
        >>> part_rowid_list = ibs.get_valid_part_rowids()
        >>> result = get_part_thetas(ibs, part_rowid_list)
        >>> print(result)
        [2.75742, 0.792917, 2.53605, 2.67795, 0.946773, 2.56729]
    """
    theta_list = ibs.db.get(const.PART_TABLE, ('part_theta',), part_rowid_list)
    return theta_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/uuid/', methods=['GET'])
def get_part_uuids(ibs, part_rowid_list):
    r"""
    Returns:
        list: part_uuid_list a list of part uuids by part_rowid

    RESTful:
        Method: GET
        URL:    /api/part/uuid/
    """
    part_uuid_list = ibs.db.get(const.PART_TABLE, ('part_uuid',), part_rowid_list)
    return part_uuid_list


@register_ibs_method
@accessor_decors.getter_1to1
# @register_api('/api/part/uuid/valid/', methods=['GET'])
def get_valid_part_uuids(ibs):
    r"""
    Returns:
        list: part_uuid_list a list of part uuids for all valid part_rowids
    """
    part_rowid_list = ibs.get_valid_part_rowids()
    part_uuid_list = ibs.get_part_uuids(part_rowid_list)
    return part_uuid_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/vert/', methods=['GET'])
def get_part_verts(ibs, part_rowid_list):
    r"""
    Returns:
        vert_list (list): the vertices that form the polygon of each part

    RESTful:
        Method: GET
        URL:    /api/part/vert/
    """
    from ibeis.algo.preproc import preproc_part
    vertstr_list = ibs.db.get(const.PART_TABLE, ('part_verts',), part_rowid_list)
    vert_list = preproc_part.postget_part_verts(vertstr_list)
    #vert_list = [eval(vertstr, {}, {}) for vertstr in vertstr_list]
    return vert_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/vert/rotated/', methods=['GET'])
def get_part_rotated_verts(ibs, part_rowid_list):
    r"""
    Returns:
        rotated_vert_list (list): verticies after rotation by theta.

    RESTful:
        Method: GET
        URL:    /api/part/vert/rotated/
    """
    import vtool as vt
    vert_list = ibs.get_part_verts(part_rowid_list)
    theta_list = ibs.get_part_thetas(part_rowid_list)
    # Convex bounding boxes for verticies
    bbox_list = vt.geometry.bboxes_from_vert_list(vert_list)
    rot_list = [vt.rotation_around_bbox_mat3x3(theta, bbox)
                for theta, bbox in zip(theta_list, bbox_list)]
    rotated_vert_list = [vt.transform_points_with_homography(rot, np.array(verts).T).T.tolist()
                         for rot, verts in zip(rot_list, vert_list)]
    #vert_list = [eval(vertstr, {}, {}) for vertstr in vertstr_list]
    return rotated_vert_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/note/', methods=['GET'])
def get_part_notes(ibs, part_rowid_list):
    r"""
    Returns:
        part_notes_list (list): a list of part notes

    RESTful:
        Method: GET
        URL:    /api/part/note/
    """
    part_notes_list = ibs.db.get(const.PART_TABLE, (PART_NOTE,), part_rowid_list)
    return part_notes_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/type/', methods=['GET'])
def get_part_types(ibs, part_rowid_list):
    r"""
    Returns:
        part_notes_list (list): a list of part notes

    RESTful:
        Method: GET
        URL:    /api/part/note/
    """
    part_type_list = ibs.db.get(const.PART_TABLE, ('part_type',), part_rowid_list)
    return part_type_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/viewpoint/', methods=['GET'])
def get_part_viewpoints(ibs, part_rowid_list):
    r"""
    Returns:
        part_notes_list (list): a list of part notes

    RESTful:
        Method: GET
        URL:    /api/part/note/
    """
    part_viewpoint_list = ibs.db.get(const.PART_TABLE, ('part_viewpoint',), part_rowid_list)
    return part_viewpoint_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/num/vert/', methods=['GET'])
def get_part_num_verts(ibs, part_rowid_list):
    r"""
    Returns:
        nVerts_list (list): the number of vertices that form the polygon of each part

    RESTful:
        Method: GET
        URL:    /api/part/num/vert/
    """
    nVerts_list = ibs.db.get(const.PART_TABLE, (PART_NUM_VERTS,), part_rowid_list)
    return nVerts_list


@register_ibs_method
@accessor_decors.getter_1to1
@accessor_decors.cache_getter(const.PART_TABLE, PART_QUALITY)
@register_api('/api/part/quality/', methods=['GET'])
def get_part_qualities(ibs, part_rowid_list, eager=True):
    r"""
    part_quality_list <- part.part_quality[part_rowid_list]

    gets data from the "native" column "part_quality" in the "part" table

    Args:
        part_rowid_list (list):

    Returns:
        list: part_quality_list

    TemplateInfo:
        Tgetter_table_column
        col = part_quality
        tbl = part

    SeeAlso:
        ibeis.const.QUALITY_INT_TO_TEXT

    RESTful:
        Method: GET
        URL:    /api/part/quality/

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.manual_part_funcs import *  # NOQA
        >>> ibs, qreq_ = testdata_ibs()
        >>> part_rowid_list = ibs._get_all_part_rowids()
        >>> eager = True
        >>> part_quality_list = ibs.get_part_qualities(part_rowid_list, eager=eager)
        >>> print('part_quality_list = %r' % (part_quality_list,))
        >>> assert len(part_rowid_list) == len(part_quality_list)
    """
    id_iter = part_rowid_list
    colnames = (PART_QUALITY,)
    part_quality_list = ibs.db.get(
        const.PART_TABLE, colnames, id_iter, id_colname='rowid', eager=eager)
    return part_quality_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/quality/text/', methods=['GET'])
def get_part_quality_texts(ibs, part_rowid_list):
    r"""
    Auto-docstr for 'get_part_quality_texts'

    RESTful:
        Method: GET
        URL:    /api/part/quality/text/
    """
    quality_list = ibs.get_part_qualities(part_rowid_list)
    quality_text_list = ut.dict_take(const.QUALITY_INT_TO_TEXT, quality_list)
    return quality_text_list


@register_ibs_method
@accessor_decors.getter_1to1
# @register_api('/api/part/isjunk/', methods=['GET'])
def get_part_isjunk(ibs, part_rowid_list):
    r"""
    Auto-docstr for 'get_part_isjunk'
    """
    qual_list = ibs.get_part_qualities(part_rowid_list)
    #isjunk_list = [qual == const.QUALITY_TEXT_TO_INT['junk'] for qual in qual_list]
    isjunk_list = [qual in const.QUALITY_TEXT_TO_INTS['junk'] for qual in qual_list]
    return isjunk_list


@register_ibs_method
@accessor_decors.getter_1to1
@register_api('/api/part/reviewed/', methods=['GET'])
def get_part_reviewed(ibs, part_rowid_list):
    r"""
    Returns:
        list_ (list): "All Instances Found" flag, true if all objects of interest
    (animals) have an PART in the part

    RESTful:
        Method: GET
        URL:    /api/part/reviewed/
    """
    reviewed_list = ibs.db.get(const.PART_TABLE, ('part_toggle_reviewed',), part_rowid_list)
    return reviewed_list


@register_ibs_method
@accessor_decors.getter_1to1
def get_part_tag_text(ibs, part_rowid_list, eager=True, nInput=None):
    r""" part_tags_list <- part.part_tags[part_rowid_list]

    gets data from the "native" column "part_tags" in the "part" table

    Args:
        part_rowid_list (list):

    Returns:
        list: part_tags_list

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.control.manual_part_funcs import *  # NOQA
        >>> ibs, config2_ = testdata_ibs()
        >>> part_rowid_list = ibs._get_all_part_rowids()
        >>> eager = True
        >>> part_tags_list = ibs.get_part_tag_text(part_rowid_list, eager=eager)
        >>> assert len(part_rowid_list) == len(part_tags_list)
    """
    id_iter = part_rowid_list
    colnames = (PART_TAG_TEXT,)
    part_tags_list = ibs.db.get(
        const.PART_TABLE, colnames, id_iter, id_colname='rowid', eager=eager, nInput=nInput)
    return part_tags_list


#### SETTERS ####  # NOQA


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/annot/rowid/', methods=['PUT'])
def _set_part_aid(ibs, part_rowid_list, aid_list):
    r"""
    Sets part notes

    RESTful:
        Method: PUT
        URL:    /api/part/annot/rowid
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_iter = ((confidence,) for confidence in aid_list)
    ibs.db.set(const.PART_TABLE, ('annot_rowid',), val_iter, id_iter)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/bbox/', methods=['PUT'])
def set_part_bboxes(ibs, part_rowid_list, bbox_list):
    r"""
    Sets bboxes of a list of parts by part_rowid,

    Args:
        part_rowid_list (list of rowids): list of part rowids
        bbox_list (list of (x, y, w, h)): new bounding boxes for each part_rowid

    Note:
        set_part_bboxes is a proxy for set_part_verts

    RESTful:
        Method: PUT
        URL:    /api/part/bbox/
    """
    from vtool import geometry
    # changing the bboxes also changes the bounding polygon
    vert_list = geometry.verts_list_from_bboxes_list(bbox_list)
    # naively overwrite the bounding polygon with a rectangle - for now trust the user!
    ibs.set_part_verts(part_rowid_list, vert_list)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/detect/confidence/', methods=['PUT'])
def set_part_detect_confidence(ibs, part_rowid_list, confidence_list):
    r"""
    Sets part notes

    RESTful:
        Method: PUT
        URL:    /api/part/detect/confidence/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_iter = ((confidence,) for confidence in confidence_list)
    ibs.db.set(const.PART_TABLE, ('part_detect_confidence',), val_iter, id_iter)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/note/', methods=['PUT'])
def set_part_notes(ibs, part_rowid_list, notes_list):
    r"""
    Sets part notes

    RESTful:
        Method: PUT
        URL:    /api/part/note/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_iter = ((notes,) for notes in notes_list)
    ibs.db.set(const.PART_TABLE, (PART_NOTE,), val_iter, id_iter)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/type/', methods=['PUT'])
def set_part_types(ibs, part_rowid_list, type_list):
    r"""
    Sets part notes

    RESTful:
        Method: PUT
        URL:    /api/part/note/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_iter = ((type_,) for type_ in type_list)
    ibs.db.set(const.PART_TABLE, ('part_type',), val_iter, id_iter)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/viewpoint/', methods=['PUT'])
def set_part_viewpoints(ibs, part_rowid_list, viewpoint_list):
    r"""
    Sets part notes

    RESTful:
        Method: PUT
        URL:    /api/part/note/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_iter = ((viewpoint_,) for viewpoint_ in viewpoint_list)
    ibs.db.set(const.PART_TABLE, ('part_viewpoint',), val_iter, id_iter)


@register_ibs_method
@accessor_decors.setter
def set_part_tag_text(ibs, part_rowid_list, part_tags_list, duplicate_behavior='error'):
    r""" part_tags_list -> part.part_tags[part_rowid_list]

    Args:
        part_rowid_list
        part_tags_list

    """
    #print('[ibs] set_part_tag_text of part_rowid_list=%r to tags=%r' % (part_rowid_list, part_tags_list))
    id_iter = part_rowid_list
    colnames = (PART_TAG_TEXT,)
    ibs.db.set(const.PART_TABLE, colnames, part_tags_list,
               id_iter, duplicate_behavior=duplicate_behavior)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/theta/', methods=['PUT'])
def set_part_thetas(ibs, part_rowid_list, theta_list):
    r"""
    Sets thetas of a list of part_rowid_list

    RESTful:
        Method: PUT
        URL:    /api/part/theta/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_list = ((theta,) for theta in theta_list)
    ibs.db.set(const.PART_TABLE, (PART_THETA,), val_list, id_iter)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/vert/', methods=['PUT'])
def set_part_verts(ibs, part_rowid_list, verts_list):
    r"""
    Sets the vertices [(x, y), ...] of a list of part_rowid_list

    RESTful:
        Method: PUT
        URL:    /api/part/vert/
    """
    from vtool import geometry
    nInput = len(part_rowid_list)
    # Compute data to set
    if isinstance(verts_list, np.ndarray):
        verts_list = verts_list.tolist()
    for index, vert_list in enumerate(verts_list):
        if isinstance(vert_list, np.ndarray):
            verts_list[index] = vert_list.tolist()
    num_verts_list   = list(map(len, verts_list))
    verts_as_strings = list(map(six.text_type, verts_list))
    id_iter1 = ((part_rowid,) for part_rowid in part_rowid_list)
    # also need to set the internal number of vertices
    val_iter1 = ((num_verts, verts) for (num_verts, verts)
                 in zip(num_verts_list, verts_as_strings))
    colnames = (PART_NUM_VERTS, PART_VERTS,)
    # SET VERTS in PART_TABLE
    ibs.db.set(const.PART_TABLE, colnames, val_iter1, id_iter1, nInput=nInput)
    # changing the vertices also changes the bounding boxes
    bbox_list = geometry.bboxes_from_vert_list(verts_list)      # new bboxes
    xtl_list, ytl_list, width_list, height_list = list(zip(*bbox_list))
    val_iter2 = zip(xtl_list, ytl_list, width_list, height_list)
    id_iter2 = ((part_rowid,) for part_rowid in part_rowid_list)
    colnames = ('part_xtl', 'part_ytl', 'part_width', 'part_height',)
    # SET BBOX in PART_TABLE
    ibs.db.set(const.PART_TABLE, colnames, val_iter2, id_iter2, nInput=nInput)


@register_ibs_method
@accessor_decors.setter
@accessor_decors.cache_invalidator(const.PART_TABLE, [PART_QUALITY], rowidx=0)
@register_api('/api/part/quality/', methods=['PUT'])
def set_part_qualities(ibs, part_rowid_list, part_quality_list):
    r"""
    part_quality_list -> part.part_quality[part_rowid_list]

    A quality is an integer representing the following types:

    Args:
        part_rowid_list
        part_quality_list

    SeeAlso:
        ibeis.const.QUALITY_INT_TO_TEXT

    RESTful:
        Method: PUT
        URL:    /api/part/quality/
    """
    id_iter = part_rowid_list
    colnames = (PART_QUALITY,)
    ibs.db.set(const.PART_TABLE, colnames, part_quality_list, id_iter)


@register_ibs_method
@register_api('/api/part/quality/text/', methods=['PUT'])
def set_part_quality_texts(ibs, part_rowid_list, quality_text_list):
    r"""
    Auto-docstr for 'set_part_quality_texts'

    RESTful:
        Method: PUT
        URL:    /api/part/quality/text/
    """
    if not ut.isiterable(part_rowid_list):
        part_rowid_list = [part_rowid_list]
    if isinstance(quality_text_list, six.string_types):
        quality_text_list = [quality_text_list]
    quality_list = ut.dict_take(const.QUALITY_TEXT_TO_INT, quality_text_list)
    ibs.set_part_qualities(part_rowid_list, quality_list)


@register_ibs_method
@accessor_decors.setter
@register_api('/api/part/reviewed/', methods=['PUT'])
def set_part_reviewed(ibs, part_rowid_list, reviewed_list):
    r"""
    Sets the part all instances found bit

    RESTful:
        Method: PUT
        URL:    /api/part/reviewed/
    """
    id_iter = ((part_rowid,) for part_rowid in part_rowid_list)
    val_list = ((reviewed,) for reviewed in reviewed_list)
    ibs.db.set(const.PART_TABLE, ('part_toggle_reviewed',), val_list, id_iter)


#==========
# Testdata
#==========


def testdata_ibs():
    r"""
    Auto-docstr for 'testdata_ibs'
    """
    import ibeis
    ibs = ibeis.opendb('testdb1')
    qreq_ = None
    return ibs, qreq_


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m ibeis.control.manual_part_funcs
        python -m ibeis.control.manual_part_funcs --allexamples
        python -m ibeis.control.manual_part_funcs --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()