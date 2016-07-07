# -*- coding: utf-8 -*-
"""
Dependencies: flask, tornado
"""
from __future__ import absolute_import, division, print_function
from os.path import splitext, basename
import uuid
import six
from ibeis.control import controller_inject
import utool as ut


register_api   = controller_inject.get_ibeis_flask_api(__name__)


@register_api('/api/image/json/', methods=['POST'])
def add_images_json(ibs, image_uri_list, image_uuid_list, image_width_list,
                    image_height_list, image_orig_name_list=None, image_ext_list=None,
                    image_time_posix_list=None, image_gps_lat_list=None,
                    image_gps_lon_list=None, image_orientation_list=None,
                    image_notes_list=None, **kwargs):
    """
    REST:
        Method: POST
        URL: /api/image/json/

    Ignore:
        sudo pip install boto

    Args:
        image_uri_list (list) : list of string image uris, most likely HTTP(S) or S3
            encoded URLs.  Alternatively, this can be a list of dictionaries (JSON
            objects) that specify AWS S3 stored assets.  An example below:

                image_uri_list = [
                    'http://domain.com/example/asset1.png',
                    '/home/example/Desktop/example/asset2.jpg',
                    's3://s3.amazon.com/example-bucket-2/asset1-in-bucket-2.tif',
                    {
                        'bucket'          : 'example-bucket-1',
                        'key'             : 'example/asset1.png',
                        'auth_domain'     : None,  # Uses localhost
                        'auth_access_id'  : None,  # Uses system default
                        'auth_secret_key' : None,  # Uses system default
                    },
                    {
                        'bucket' : 'example-bucket-1',
                        'key'    : 'example/asset2.jpg',
                        # if unspecified, auth uses localhost and system defaults
                    },
                    {
                        'bucket'          : 'example-bucket-2',
                        'key'             : 'example/asset1-in-bucket-2.tif',
                        'auth_domain'     : 's3.amazon.com',
                        'auth_access_id'  : '____________________',
                        'auth_secret_key' : '________________________________________',
                    },
                ]

            Note that you cannot specify AWS authentication access ids or secret keys
            using string uri's.  For specific authentication methods, please use the
            latter list of dictionaries.

        image_uuid_list (list of str) : list of image UUIDs to be used in IBEIS IA
        image_width_list (list of int) : list of image widths
        image_height_list (list of int) : list of image heights
        image_orig_name_list (list of str): list of original image names
        image_ext_list (list of str): list of original image names
        image_time_posix_list (list of int): list of image's POSIX timestamps
        image_gps_lat_list (list of float): list of image's GPS latitude values
        image_gps_lon_list (list of float): list of image's GPS longitude values
        image_orientation_list (list of int): list of image's orientation flags
        image_notes_list (list of str) : optional list of any related notes with
            the images
        **kwargs : key-value pairs passed to the ibs.add_images() function.

    CommandLine:
        python -m ibeis.web.app --test-add_images_json

    Example:
        >>> # WEB_DOCTEST
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> import ibeis
        >>> web_instance = ibeis.opendb(db='testdb1')
        >>> _payload = {
        >>>     'image_uri_list': [
        >>>         'https://upload.wikimedia.org/wikipedia/commons/4/49/Zebra_running_Ngorongoro.jpg',
        >>>         {
        >>>             'bucket'          : 'test-asset-store',
        >>>             'key'             : 'caribwhale/20130903-JAC-0002.JPG',
        >>>         },
        >>>     ],
        >>>     'image_uuid_list': [
        >>>         uuid.UUID('7fea8101-7dec-44e3-bf5d-b8287fd231e2'),
        >>>         uuid.UUID('c081119a-e08e-4863-a710-3210171d27d6'),
        >>>     ],
        >>>     'image_width_list': [
        >>>         1992,
        >>>         1194,
        >>>     ],
        >>>     'image_height_list': [
        >>>         1328,
        >>>         401,
        >>>     ],
        >>> }
        >>> gid_list = ibeis.web.app.add_images_json(web_instance, **_payload)
        >>> print(gid_list)
        >>> print(web_instance.get_image_uuids(gid_list))
        >>> print(web_instance.get_image_uris(gid_list))
        >>> print(web_instance.get_image_paths(gid_list))
        >>> print(web_instance.get_image_uris_original(gid_list))
    """
    def _get_standard_ext(gpath):
        ext = splitext(gpath)[1].lower()
        return '.jpg' if ext == '.jpeg' else ext

    def _parse_imageinfo(index):
        def _resolve_uri():
            list_ = image_uri_list
            if list_ is None or index >= len(list_) or list_[index] is None:
                raise ValueError('Must specify all required fields')
            value = list_[index]
            if isinstance(value, dict):
                value = ut.s3_dict_encode_to_str(value)
            return value

        def _resolve(list_, default='', assert_=False):
            if list_ is None or index >= len(list_) or list_[index] is None:
                if assert_:
                    raise ValueError('Must specify all required fields')
                return default
            return list_[index]

        uri = _resolve_uri()
        orig_gname = basename(uri)
        ext = _get_standard_ext(uri)

        uuid_ = _resolve(image_uuid_list, assert_=True)
        if isinstance(uuid_, six.string_types):
            uuid_ = uuid.UUID(uuid_)

        param_tup = (
            uuid_,
            uri,
            uri,
            _resolve(image_orig_name_list, default=orig_gname),
            _resolve(image_ext_list, default=ext),
            int(_resolve(image_width_list, assert_=True)),
            int(_resolve(image_height_list, assert_=True)),
            int(_resolve(image_time_posix_list, default=-1)),
            float(_resolve(image_gps_lat_list, default=-1.0)),
            float(_resolve(image_gps_lon_list, default=-1.0)),
            int(_resolve(image_orientation_list, default=0)),
            _resolve(image_notes_list),
        )
        return param_tup

    # TODO: FIX ME SO THAT WE DON'T HAVE TO LOCALIZE EVERYTHING
    kwargs['auto_localize'] = kwargs.get('auto_localize', True)
    kwargs['sanitize'] = kwargs.get('sanitize', False)

    index_list = range(len(image_uri_list))
    params_gen = ut.generate(_parse_imageinfo, index_list, adjust=True,
                             force_serial=True, **kwargs)
    params_gen = list(params_gen)
    gpath_list = [ _[0] for _ in params_gen ]
    gid_list = ibs.add_images(gpath_list, params_list=params_gen, **kwargs)  # NOQA
    # return gid_list
    image_uuid_list = ibs.get_image_uuids(gid_list)
    return image_uuid_list


@register_api('/api/annot/json/', methods=['POST'])
def add_annots_json(ibs, image_uuid_list, annot_uuid_list, annot_bbox_list,
                    annot_theta_list=None, annot_species_list=None,
                    annot_name_list=None, annot_notes_list=None, **kwargs):
    """
    REST:
        Method: POST
        URL: /api/annot/json/

    Ignore:
        sudo pip install boto

    Args:
        image_uuid_list (list of str) : list of image UUIDs to be used in IBEIS IA
        annot_uuid_list (list of str) : list of annotations UUIDs to be used in IBEIS IA
        annot_bbox_list (list of 4-tuple) : list of bounding box coordinates encoded as
            a 4-tuple of the values (xtl, ytl, width, height) where xtl is the
            'top left corner, x value' and ytl is the 'top left corner, y value'.
        annot_theta_list (list of float) : list of radian rotation around center.
            Defaults to 0.0 (no rotation).
        annot_species_list (list of str) : list of species for the annotation, if known.
            If the list is partially known, use None (null in JSON) for unknown entries.
        annot_name_list (list of str) : list of names for the annotation, if known.
            If the list is partially known, use None (null in JSON) for unknown entries.
        annot_notes_list (list of str) : list of notes to be added to the annotation.
        **kwargs : key-value pairs passed to the ibs.add_annots() function.

    CommandLine:
        python -m ibeis.web.app --test-add_annots_json

    Example:
        >>> import ibeis
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> web_instance = ibeis.opendb(db='testdb1')
        >>> _payload = {
        >>>     'image_uuid_list': [
        >>>         uuid.UUID('7fea8101-7dec-44e3-bf5d-b8287fd231e2'),
        >>>         uuid.UUID('c081119a-e08e-4863-a710-3210171d27d6'),
        >>>     ],
        >>>     'annot_uuid_list': [
        >>>         uuid.UUID('fe1547c5-1425-4757-9b8f-b2b4a47f552d'),
        >>>         uuid.UUID('86d3959f-7167-4822-b99f-42d453a50745'),
        >>>     ],
        >>>     'annot_bbox_list': [
        >>>         [0, 0, 1992, 1328],
        >>>         [0, 0, 1194, 401],
        >>>     ],
        >>> }
        >>> aid_list = ibeis.web.app.add_annots_json(web_instance, **_payload)
        >>> print(aid_list)
        >>> print(web_instance.get_annot_image_uuids(aid_list))
        >>> print(web_instance.get_annot_uuids(aid_list))
        >>> print(web_instance.get_annot_bboxes(aid_list))
    """

    image_uuid_list = [
        uuid.UUID(uuid_) if isinstance(uuid_, six.string_types) else uuid_
        for uuid_ in image_uuid_list
    ]
    annot_uuid_list = [
        uuid.UUID(uuid_) if isinstance(uuid_, six.string_types) else uuid_
        for uuid_ in annot_uuid_list
    ]
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    aid_list = ibs.add_annots(gid_list, annot_uuid_list=annot_uuid_list,  # NOQA
                              bbox_list=annot_bbox_list, theta_list=annot_theta_list,
                              species_list=annot_species_list, name_list=annot_name_list,
                              notes_list=annot_notes_list, **kwargs)
    # return aid_list
    annot_uuid_list = ibs.get_annot_uuids(aid_list)
    return annot_uuid_list


@register_api('/api/image/annot/uuids/json/', methods=['GET'])
def get_image_annot_uuids_json(ibs, image_uuid_list):
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    aids_list = ibs.get_image_aids(gid_list)
    annot_uuid_list = [
        ibs.get_annot_uuids(aid_list)
        for aid_list in aids_list
    ]
    return annot_uuid_list


@register_api('/api/annot/exemplar/flags/json/', methods=['POST'])
def set_exemplars_from_quality_and_viewpoint_json(ibs, annot_uuid_list,
                                                  annot_name_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    if annot_name_list is not None:
        # Set names for query annotations
        nid_list = ibs.add_names(annot_name_list)
        ibs.set_annot_name_rowids(aid_list, nid_list)
    new_aid_list, new_flag_list = ibs.set_exemplars_from_quality_and_viewpoint(aid_list, **kwargs)
    new_annot_uuid_list = ibs.get_annot_uuids(new_aid_list)
    return new_annot_uuid_list, new_flag_list


@register_api('/api/image/unixtimes/json/', methods=['GET'])
def get_image_unixtimes_json(ibs, image_uuid_list):
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    return ibs.get_image_unixtime(gid_list)


@register_api('/api/image/uris_original/json/', methods=['GET'])
def get_image_uris_original_json(ibs, image_uuid_list):
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    return ibs.get_image_uris_original(gid_list)


@register_api('/api/image/json/', methods=['GET'])
def get_valid_image_uuids_json(ibs, **kwargs):
    gid_list = ibs.get_valid_gids(**kwargs)
    return ibs.get_image_uuids(gid_list)


@register_api('/api/name/json/', methods=['GET'])
def get_valid_name_uuids_json(ibs, **kwargs):
    nid_list = ibs.get_valid_nids(**kwargs)
    return ibs.get_name_uuids(nid_list)


@register_api('/api/annot/json/', methods=['GET'])
def get_valid_annot_uuids_json(ibs, **kwargs):
    aid_list = ibs.get_valid_aids(**kwargs)
    return ibs.get_annot_uuids(aid_list)


@register_api('/api/imageset/json/', methods=['GET'])
def get_valid_imageset_uuids_json(ibs, **kwargs):
    imgsetid_list = ibs.get_valid_imgsetids(**kwargs)
    return ibs.get_imageset_uuid(imgsetid_list)


@register_api('/api/annot/bboxes/json/', methods=['GET'])
def get_annot_bboxes_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_bboxes(aid_list, **kwargs)


@register_api('/api/annot/detect/confidence/json/', methods=['GET'])
def get_annot_detect_confidence_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_detect_confidence(aid_list, **kwargs)


@register_api('/api/annot/exemplar/flags/json/', methods=['GET'])
def get_annot_exemplar_flags_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_exemplar_flags(aid_list, **kwargs)


@register_api('/api/annot/thetas/json/', methods=['GET'])
def get_annot_thetas_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_thetas(aid_list, **kwargs)


@register_api('/api/annot/verts/json/', methods=['GET'])
def get_annot_verts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_verts(aid_list, **kwargs)


@register_api('/api/annot/verts/rotated/json/', methods=['GET'])
def get_annot_rotated_verts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_rotated_verts(aid_list, **kwargs)


@register_api('/api/annot/yaws/json/', methods=['GET'])
def get_annot_yaws_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_yaws(aid_list, **kwargs)


@register_api('/api/annot/notes/json/', methods=['GET'])
def get_annot_notes_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_notes(aid_list, **kwargs)


@register_api('/api/annot/num_verts/json/', methods=['GET'])
def get_annot_num_verts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_num_verts(aid_list, **kwargs)


@register_api('/api/annot/name/uuids/json/', methods=['GET'])
def get_annot_name_rowids_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    nid_list = ibs.get_annot_name_rowids(aid_list, **kwargs)
    return ibs.get_name_uuids(nid_list)


@register_api('/api/annot/name/texts/json/', methods=['GET'])
def get_annot_name_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_name_texts(aid_list, **kwargs)


@register_api('/api/annot/species/json/', methods=['GET'])
def get_annot_species_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_species(aid_list, **kwargs)


@register_api('/api/annot/species/texts/json/', methods=['GET'])
def get_annot_species_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_species_texts(aid_list, **kwargs)


@register_api('/api/annot/image/names/json/', methods=['GET'])
def get_annot_image_names_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_image_names(aid_list, **kwargs)


@register_api('/api/annot/image/unixtimes/json/', methods=['GET'])
def get_annot_image_unixtimes_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_image_unixtimes(aid_list, **kwargs)


@register_api('/api/annot/image/gps/json/', methods=['GET'])
def get_annot_image_gps_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_image_gps(aid_list, **kwargs)


@register_api('/api/annot/image/paths/json/', methods=['GET'])
def get_annot_image_paths_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_image_paths(aid_list, **kwargs)


@register_api('/api/annot/image/uuids/json/', methods=['GET'])
def get_annot_image_uuids_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    image_uuid_list = [
        None if aid is None else ibs.get_annot_image_uuids(aid, **kwargs)
        for aid in aid_list
    ]
    return image_uuid_list


@register_api('/api/imageset/annot/uuids/json/', methods=['GET'])
def get_imageset_annot_uuids_json(ibs, imageset_uuid_list):
    imgsetid_list = ibs.get_imageset_imgsetids_from_uuid(imageset_uuid_list)
    aids_list = ibs.get_imageset_aids(imgsetid_list)
    annot_uuids_list = [
        ibs.get_annot_uuids(aid_list)
        for aid_list in aids_list
    ]
    return annot_uuids_list


@register_api('/api/imageset/annot/aids/json/', methods=['GET'])
def get_imageset_annot_aids_json(ibs, imageset_uuid_list):
    imgsetid_list = ibs.get_imageset_imgsetids_from_uuid(imageset_uuid_list)
    aids_list = ibs.get_imageset_aids(imgsetid_list)
    return aids_list


@register_api('/api/annot/qualities/json/', methods=['GET'])
def get_annot_qualities_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_qualities(aid_list, **kwargs)


@register_api('/api/annot/quality/texts/json/', methods=['GET'])
def get_annot_quality_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_quality_texts(aid_list, **kwargs)


@register_api('/api/annot/yaw_texts/json/', methods=['GET'])
def get_annot_yaw_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_yaw_texts(aid_list, **kwargs)


@register_api('/api/annot/sex/json/', methods=['GET'])
def get_annot_sex_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_sex(aid_list, **kwargs)


@register_api('/api/annot/sex/texts/json/', methods=['GET'])
def get_annot_sex_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_sex_texts(aid_list, **kwargs)


@register_api('/api/annot/age/min/json/', methods=['GET'])
def get_annot_age_months_est_min_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_age_months_est_min(aid_list, **kwargs)


@register_api('/api/annot/age/max/json/', methods=['GET'])
def get_annot_age_months_est_max_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_age_months_est_max(aid_list, **kwargs)


@register_api('/api/annot/age/min/texts/json/', methods=['GET'])
def get_annot_age_months_est_min_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_age_months_est_min_texts(aid_list, **kwargs)


@register_api('/api/annot/age/max/texts/json/', methods=['GET'])
def get_annot_age_months_est_max_texts_json(ibs, annot_uuid_list, **kwargs):
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    return ibs.get_annot_age_months_est_max_texts(aid_list, **kwargs)


@register_api('/chaos/imageset/', methods=['GET', 'POST'])
def chaos_imageset(ibs):
    """
    REST:
        Method: POST
        URL: /api/image/json/

    Args:
        image_uuid_list (list of str) : list of image UUIDs to be delete from IBEIS
    """
    from random import shuffle, randint
    gid_list = ibs.get_valid_gids()
    shuffle(gid_list)
    sample = min(len(gid_list) // 2, 50)
    assert sample > 0, 'Cannot create a chaos imageset using an empty database'
    gid_list_ = gid_list[:sample]
    imagetset_name = 'RANDOM_CHAOS_TEST_IMAGESET_%08d' % (randint(0, 99999999))
    imagetset_rowid = ibs.add_imagesets(imagetset_name)
    imagetset_uuid = ibs.get_imageset_uuid(imagetset_rowid)
    ibs.add_image_relationship(gid_list_, [imagetset_rowid] * len(gid_list_))
    return imagetset_name, imagetset_uuid


@register_api('/api/imageset/json/', methods=['DELETE'])
def delete_imageset_json(ibs, imageset_uuid_list):
    """
    REST:
        Method: POST
        URL: /api/image/json/

    Args:
        image_uuid_list (list of str) : list of image UUIDs to be delete from IBEIS
    """
    imgsetid_list = ibs.get_imageset_imgsetids_from_uuid(imageset_uuid_list)
    ibs.delete_imagesets(imgsetid_list)
    return True


@register_api('/api/image/json/', methods=['DELETE'])
def delete_images_json(ibs, image_uuid_list):
    """
    REST:
        Method: POST
        URL: /api/image/json/

    Args:
        image_uuid_list (list of str) : list of image UUIDs to be delete from IBEIS
    """
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    ibs.delete_images(gid_list)
    return True


@register_api('/api/annot/json/', methods=['DELETE'])
def delete_annots_json(ibs, annot_uuid_list):
    """
    REST:
        Method: POST
        URL: /api/annot/json/

    Args:
        annot_uuid_list (list of str) : list of annot UUIDs to be delete from IBEIS
    """
    aid_list = ibs.get_annot_aids_from_uuid(annot_uuid_list)
    ibs.delete_annots(aid_list)
    return True


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.web.app
        python -m ibeis.web.app --allexamples
        python -m ibeis.web.app --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
