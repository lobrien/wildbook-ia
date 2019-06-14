# -*- coding: utf-8 -*-
"""Dependencies: flask, tornado."""
from __future__ import absolute_import, division, print_function
from ibeis.control import controller_inject
from flask_swagger import swagger
from flask import current_app
from flask import jsonify
import traceback
import utool as ut
import uuid


CLASS_INJECT_KEY, register_ibs_method = (
    controller_inject.make_ibs_register_decorator(__name__))

PREFIX         = controller_inject.VULCAN_API_PREFIX
register_api   = controller_inject.get_ibeis_flask_api(__name__)
register_route = controller_inject.get_ibeis_flask_route(__name__)


def _prefix(route=''):
    rule = '/%s/%s/' % (PREFIX, route, )
    while '//' in rule:
        rule = rule.replace('//', '/')
    return rule


def _image(ibs, gid):
    return {
        'uuid': str(ibs.get_image_uuids(gid)),
    }


def _sequence(ibs, sequence_rowid):
    return {
        'uuid': str(ibs.get_imageset_uuid(sequence_rowid)),
    }


def _task(ibs, taskid):
    return {
        'uuid': taskid,
    }


def _ensure_images_exist(ibs, images, allow_none=False):
    for index, image in enumerate(images):
        try:
            if allow_none and image is None:
                continue
            parameter = 'images:%d' % (index, )
            assert 'uuid' in image, 'Image Model provided is invalid, missing UUID key'
        except AssertionError as ex:
            raise controller_inject.WebInvalidInput(str(ex), parameter)

    uuid_list = [
        None if image is None else uuid.UUID(image['uuid'])
        for image in images
    ]
    gid_list = ibs.get_image_gids_from_uuid(uuid_list)

    bad_index_list = []
    for index, (uuid_, gid) in enumerate(zip(uuid_list, gid_list)):
        if allow_none and gid is None:
            continue
        if gid is None:
            bad_index_list.append((index, uuid_))

    if len(bad_index_list) > 0:
        message = 'Uploaded list contains unrecognized %d records (index, UUID): %s' % (len(bad_index_list), bad_index_list, )
        raise controller_inject.WebInvalidInput(message, 'images')

    if not allow_none:
        assert None not in gid_list

    return gid_list


def _ensure_sequence_exist(ibs, sequence):
    try:
        parameter = 'sequence'
        assert 'uuid' in sequence, 'Sequence Model provided is invalid, missing UUID key'
    except AssertionError as ex:
        raise controller_inject.WebInvalidInput(str(ex), parameter)

    sequence_uuid = uuid.UUID(sequence['uuid'])
    sequence_rowid = ibs.get_imageset_imgsetids_from_uuid(sequence_uuid)

    if sequence_uuid is None or sequence_rowid is None:
        message = 'Sequence is unrecognized'
        raise controller_inject.WebInvalidInput(message, 'sequence')

    return sequence_rowid


@register_route(_prefix('swagger'), methods=['GET'])
def vulcan_core_specification_swagger(*args, **kwargs):
    r"""
    Returns the API specification in the Swagger 2.0 (OpenAPI) JSON format.

    The Swagger API specification (https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md) provides a standardized method to export REST API documentation and examples.  Our documentation is built on-demand with the help of the Python package flask-swagger (https://github.com/gangverk/flask-swagger).

    The API specification includes GET, POST, PUT, and DELETE methods and Model definitions.
    ---
    definitions:
    - schema:
        id: Image
        description: An Image is a semantic construct that represents an uploaded image.  Images can be uploaded for later processing or be used immediately for inference with the pipeline.
        required:
          - uuid
        properties:
          uuid:
            description: a deterministically-derived UUID based on the image pixels, which can be used to identify duplicate Images.
            type: string
            format: uuid
    - schema:
        id: Sequence
        description: A Sequence is a semantic construct that represents an ordered list of images, where the images are assumed to be in order spatially and temporally
        required:
          - name
          - uuid
        properties:
          name:
            description: a text name to easily refer to the sequence of images (e.g. "Location Samburu, Survey 3, Sequence 10, Camera Left")
            type: string
          uuid:
            description: a random UUID to identify the sequence
            type: string
            format: uuid
    - schema:
        id: Task
        description: A Task is a semantic construct that represents a background task in an asynchronous call.  A Task has an optional callback on completion or the status (and result) can be checked via the API
        required:
          - uuid
        properties:
          uuid:
            description: a random UUID to identify a given asynchronous call, used to check status and results of a background task
            type: string
            format: uuid
    produces:
    - application/json
    responses:
        200:
          description: Returns the Swagger 2.0 JSON format
    """
    swag = swagger(current_app)
    swag['info']['title'] = 'Wild Me - Vulcan MWS Project, Phase 1'
    swag['info']['description'] = 'Documentation for all REST API endpoints provided by Wild Me for the Vulcan collaboration'
    swag['info']['version'] = 'v0.1'
    swag['info']['contact'] = {
        'name':  'Wild Me',
        'url':   'http://wildme.org',
        'email': 'dev@wildme.org',
    }
    swag['info']['license'] = {
        'name': 'Apache 2.0',
        'url':  'http://www.apache.org/licenses/LICENSE-2.0.html'
    }
    swag['host'] = 'kaiju.dyn.wildme.io:5000'
    swag['schemes'] = [
        'http',
    ]

    response = jsonify(swag)
    return response


@register_api(_prefix('status'), methods=['GET'], __api_plural_check__=False)
def vulcan_core_status(*args, **kwargs):
    r"""
    Returns the health status of the API back-end; optionally can be used as a service heatbeat.
    ---
    produces:
    - application/json
    responses:
      200:
        description: Returns the status of the server
        schema:
          type: object
          properties:
            status:
              type: string
              enum:
              - healthy
              - warning
              - critical
        examples:
        - application/json:
            status: healthy
    """
    status = 'healthy'
    return {'status': status}


@register_api(_prefix('image'), methods=['POST'])
def vulcan_image_upload(ibs, precompute=True, return_times=False, *args, **kwargs):
    r"""
    Upload an image for future processing.

    ---
    parameters:
    - name: image
      in: formData
      description: The image to upload.
      required: true
      type: file
      enum:
      - image/png
      - image/jpg
      - image/tiff
    - name: precompute
      in: body
      description: A boolean flag to precompute the tiles for this image
      required: false
      type: boolean
      default: true
    produces:
    - application/json
    responses:
      200:
        description: Returns an Image model with an ID
        schema:
          $ref: '#/definitions/Image'
      400:
        description: Invalid input parameter
      415:
        description: Unsupported media type in the request body. Currently only image/png, image/jpeg, image/tiff are supported.
    """
    with ut.Timer('Uploading') as time_upload:
        from ibeis.web.apis import image_upload
        try:
            gid = image_upload(cleanup=True, **kwargs)
            assert gid is not None
        except controller_inject.WebException:
            raise
        except:
            raise controller_inject.WebInvalidInput('Uploaded image is corrupted or is an unsupported file format (supported: image/png, image/jpeg, image/tiff)', 'image', image=True)
        image = _image(ibs, gid)

    with ut.Timer('Tiling') as time_tile:
        # Pre-compute tiles
        ibs.vulcan_get_valid_tile_rowids(gid_list=[gid], include_grid2=True)

    if return_times:
        return image, time_upload, time_tile
    else:
        return image


@register_api(_prefix('image'), methods=['GET'])
def vulcan_image(ibs, image, *args, **kwargs):
    r"""
    Check if an Image is available in the database.

    ---
    parameters:
    - name: sequence
      in: body
      description: An Image model
      required: true
      schema:
        $ref: "#/definitions/Image"
    produces:
    - application/json
    responses:
      200:
        description: The Image is registered and available
      400:
        description: Invalid input parameter
    """
    # Input argument validation
    try:
        status = 'available'
        _ensure_images_exist(ibs, [image])
    except:
        status = 'unavailable'
    return {'status': status}


@register_api(_prefix('sequence'), methods=['POST'])
def vulcan_sequence_add(ibs, name, images, overwrite=False, *args, **kwargs):
    r"""
    Add an image sequence for future processing using a list of previously-uploaded images

    ---
    parameters:
    - name: name
      in: body
      description: A name for the sequence
      required: true
      type: string
    - name: images
      in: body
      description: A JSON ordered list of Image models to process with the pipeline.  Use None (null) values to indicate missing images in the sequence.  The index of the images list always begin with 0 and is sequential.
      required: true
      type: array
      items:
        $ref: '#/definitions/Image'
    - name: overwrite
      in: body
      description: A boolean flag to overwrite the existing sequence, if present
      required: false
      type: boolean
      default: false
    produces:
    - application/json
    responses:
      200:
        description: Returns a Sequence model with an ID
        schema:
          $ref: '#/definitions/Sequence'
      400:
        description: Invalid input parameter
    """
    # Input argument validation
    if isinstance(name, (list, tuple)):
        try:
            assert len(name) == 1
            name = name[0]
        except AssertionError as ex:
            parameter = 'name'
            raise controller_inject.WebInvalidInput(str(ex), parameter)

    gid_list = _ensure_images_exist(ibs, images, allow_none=True)
    sequence_rowid = ibs.get_imageset_imgsetids_from_text(name)

    metadata_dict = ibs.get_imageset_metadata(sequence_rowid)
    sequence = metadata_dict.get('sequence', None)
    if sequence is not None:
        assert overwrite, 'This sequence has already been defined and overwriting is OFF (use overwrite = True to force)'

    sequence = []
    for index, gid in enumerate(gid_list):
        sequence.append({
            'index' : index,
            'gid'   : gid,
        })

    metadata_dict['sequence'] = sequence
    ibs.set_imageset_metadata([sequence_rowid], [metadata_dict])

    current_sequence_gid_list = ibs.get_imageset_gids(sequence_rowid)
    ibs.unrelate_images_and_imagesets(current_sequence_gid_list, [sequence_rowid] * len(current_sequence_gid_list))
    new_sequence_gid_list = list(set(gid_list) - set([None]))
    ibs.set_image_imgsetids(new_sequence_gid_list, [sequence_rowid] * len(new_sequence_gid_list))

    sequence = _sequence(ibs, sequence_rowid)
    return sequence


@register_api(_prefix('sequence'), methods=['GET'])
def vulcan_sequence_images(ibs, sequence, *args, **kwargs):
    r"""
    Return the sequence's images

    ---
    parameters:
    - name: sequence
      in: body
      description: A Sequence model
      required: true
      schema:
        $ref: "#/definitions/Sequence"
    produces:
    - application/json
    responses:
      200:
        description: Returns a JSON object with the list of Image models and their index in the sequence
      400:
        description: Invalid input parameter
    """
    # Input argument validation
    sequence_rowid = _ensure_sequence_exist(ibs, sequence)
    metadata_dict = ibs.get_imageset_metadata(sequence_rowid)
    sequence_dict = metadata_dict.get('sequence', None)

    for value in sequence_dict:
        gid = value.pop('gid')
        value['image'] = _image(ibs, gid)

    return {'sequence': sequence_dict}


@register_ibs_method
def vulcan_pipeline(ibs, images,
                    testing=False,
                    quick=True,
                    _run_all_loc=False,
                    __jobid__=None,
                    time_upload=None,
                    *args, **kwargs):

    def _timer(*args):
        time = 0.0
        for timer in args:
            if timer is not None:
                time += timer.ellapsed
        return time

    try:
        with ut.Timer('Config') as time_config:
            include_grid2 = not quick

            detection_config = ibs.vulcan_detect_config(quick=quick)
            detection_agg_weight = detection_config['weight_filepath']
            detection_weight_algo, detection_weight_config = detection_agg_weight.strip().split(';')
            detection_weight_algo_wic, detection_weight_algo_loc = detection_weight_algo.strip().split('+')

            values = detection_weight_config.strip().split(',')
            assert len(values) == 4
            detection_weight_config_wic_model_tag   = values[0]
            detection_weight_config_wic_sensitivity = float(values[1])
            detection_weight_config_loc_model_tag   = values[2]
            detection_weight_config_loc_tile_nms    = float(values[3])

        with ut.Timer('UUIDs') as time_uuid:
            gid_list = _ensure_images_exist(ibs, images)

        with ut.Timer('Test Deleting') as time_test:
            if testing:
                print('TESTING')
                tile_list = ibs.vulcan_get_valid_tile_rowids(gid_list=gid_list)
                flag_list = [tile for tile in tile_list if tile is not None]
                tile_list = ut.compress(tile_list, flag_list)
                ibs.depc_image.delete_property_all('tiles', gid_list)
                ibs.depc_image.delete_root(gid_list)
                ibs.delete_images(tile_list, trash_images=False)
            else:
                print('NOT TESTING')

        with ut.Timer('Tiling') as time_tile:
            # Pre-compute tiles
            tile_list = ibs.vulcan_get_valid_tile_rowids(gid_list=gid_list, include_grid2=include_grid2)
            num_tiles_wic = len(tile_list)
            # ancestor_gid_list = ibs.get_vulcan_image_tile_ancestor_gids(tile_list)

        with ut.Timer('WIC') as time_wic:
            wic_confidence_list = ibs.vulcan_wic_test(
                tile_list,
                classifier_algo=detection_weight_algo_wic,
                model_tag=detection_weight_config_wic_model_tag
            )
            wic_flag_list = [wic_confidence >= detection_weight_config_wic_sensitivity for wic_confidence in wic_confidence_list]  # NOQA
            tile_list_filtered = ut.compress(tile_list, wic_flag_list)
            num_tiles_loc = len(tile_list_filtered)

        # with ut.Timer('LOC All') as time_loc_all:
        #     if _run_all_loc:
        #         model_tag               = '%s,%0.03f,%s,%0.02f' % (wic_model_tag, wic_sensitivity, loc_model_tag, loc_nms, )
        #         all_loc_confidence_list = ibs.vulcan_wic_test(tile_list, classifier_algo=loc_all_classifier_algo, model_tag=model_tag)
        #         all_loc_flag_list       = [all_loc_confidence >= loc_sensitivity for all_loc_confidence in all_loc_confidence_list]  # NOQA

        with ut.Timer('LOC') as time_loc:
            # detections_list =
            ibs.vulcan_localizer_test(
                tile_list_filtered,
                algo=detection_weight_algo_loc,
                model_tag=detection_weight_config_loc_model_tag,
                sensitivity=0.0,
                nms_thresh=detection_weight_config_loc_tile_nms
            )
            # filtered_loc_flag_list       = [filtered_loc_confidence >= loc_sensitivity for filtered_loc_confidence in filtered_loc_confidence_list]  # NOQA

        with ut.Timer('Cluster + Aggregate') as time_agg:
            result_list, time_cluster = ibs.vulcan_detect(
                gid_list,
                detection_config=detection_config,
                return_times=True
            )

            results = []
            for result in result_list:
                bboxes, classes, confs, clusters = result
                zipped = zip(bboxes, classes, confs, clusters)
                result_ = []
                for bbox, class_, conf, cluster in zipped:
                    result_.append({
                        'bbox': bbox,
                        'class': class_,
                        'confidence': conf,
                        'cluster': cluster,
                    })
                results.append(result_)
    except:
        traceback.print_exc()
        raise controller_inject.WebException('The Vulcan pipeline process has failed for an unknown reason')

    response = {
        'results': results,
        'times': {
            '_test'            : _timer(time_test),
            '_num_tiles_wic'   : num_tiles_wic,
            '_num_tiles_loc'   : num_tiles_loc,
            # '_loc_all'         : _timer(time_loc_all),
            'step_0_upload'    : _timer(time_upload),
            'step_1_uuid'      : _timer(time_config, time_uuid),
            'step_2_tile'      : _timer(time_tile),
            'step_3_wic'       : _timer(time_wic),
            'step_4_loc'       : _timer(time_loc),
            'step_5_aggregate' : _timer(time_agg) - _timer(time_cluster),
            'step_6_cluster'   : _timer(time_cluster),
            'gpu_inference'    : _timer(time_wic, time_loc),
            'overhead'         : _timer(time_upload, time_config, time_uuid, time_tile, time_agg),
            'total'            : _timer(time_upload, time_config, time_uuid, time_tile, time_wic, time_loc, time_agg),
        },
    }

    return response


@register_api(_prefix('pipeline'), methods=['POST'])
def vulcan_pipeline_upload(ibs, *_args, **kwargs):
    r"""
    Returns the results for an uploaded image and a provided model configuration.
    ---
    parameters:
    - name: image
      in: formData
      description: The image to process with the pipeline.
      required: true
      type: file
      enum:
      - image/png
      - image/jpg
      - image/tiff
    responses:
      200:
        description: Returns an array of results on the uploaded image
      400:
        description: Invalid input parameter
      415:
        description: Unsupported media type in the request body. Currently only image/png, image/jpeg, image/tiff are supported.
    """
    ibs = current_app.ibs

    # Input argument validation
    image, time_upload, time_tile = vulcan_image_upload(ibs, return_times=True)
    images = [image]
    args = (images, )
    response = vulcan_pipeline(ibs, *args, time_upload=time_upload, **kwargs)
    return response


@register_api(_prefix('pipeline/batch'), methods=['POST'])
def vulcan_pipeline_batch(ibs, images, async=True,
                           callback_url=None, callback_method=None,
                           *_args, **kwargs):
    r"""
    The asynchronous variant of POST 'pipeline' that takes in a list of Image models and returns a task ID.

    It may be more ideal for a particular application to upload many images at one time and perform processing later in a large batch.  This type of batch API call is more efficient because the pipeline on GPU can process more images in parallel.  However, if you intend to run the pipeline on an upload as quickly as possible, please use the on-demand, non-batched API.
    ---
    parameters:
    - name: images
      in: body
      description: A JSON list of Image models to process with the pipeline.
      required: true
      type: array
      items:
        $ref: '#/definitions/Image'
    - name: callback_url
      in: body
      description: The URL of where to callback when the task is completed, must be a fully resolvable address and accessible.  The callback will include a 'body' parameter called `task` which will provide a Task model
      required: false
      type: string
      format: url
    - name: callback_method
      in: body
      description: The HTTP method for which to make the callback
      required: false
      default: post
      type: string
      enum:
      - get
      - post
      - put
      - delete
    responses:
      200:
        description: Returns a Task model
        schema:
          $ref: "#/definitions/Task"
      400:
        description: Invalid input parameter
      x-task-response:
        description: The task returns an array of arrays of results, in parallel lists with the provided Image models
    """
    ibs = current_app.ibs

    # Input argument validation
    for index, image in enumerate(images):
        try:
            parameter = 'images:%d' % (index, )
            assert 'uuid' in image, 'Image Model provided is invalid, missing UUID key'
        except AssertionError as ex:
            raise controller_inject.WebInvalidInput(str(ex), parameter)

    try:
        parameter = 'async'
        assert isinstance(async, bool), 'Asynchronous flag must be a boolean'

        parameter = 'callback_url'
        assert callback_url is None or isinstance(callback_url, str), 'Callback URL must be a string'
        if callback_url is not None:
            assert callback_url.startswith('http://') or callback_url.startswith('https://'), 'Callback URL must start with http:// or https://'

        parameter = 'callback_method'
        assert callback_method is None or isinstance(callback_method, str), 'Callback URL must be a string'
        if callback_method is not None:
            callback_method = callback_method.lower()
            assert callback_method in ['get', 'post', 'put', 'delete'], 'Unsupported callback method, must be one of ("get", "post", "put", "delete")'
    except AssertionError as ex:
        raise controller_inject.WebInvalidInput(str(ex), parameter)

    args = (images, )
    if async:
        taskid = ibs.job_manager.jobiface.queue_job('vulcan_pipeline',
                                                    callback_url, callback_method,
                                                    *args, **kwargs)
        response = _task(ibs, taskid)
    else:
        response = ibs.vulcan_pipeline(*args, **kwargs)

    return response


@register_api(_prefix('pipeline/sequence'), methods=['POST'])
def vulcan_pipeline_sequence(ibs, sequence, *_args, **kwargs):
    r"""
    A wrapper around $prefix/batch to send an entire sequence to the detection pipeline.  Takes in the same configuration parameters as that call.
    ---
    parameters:
    - name: sequence
      in: body
      description: A Sequence model to process with the pipeline.
      required: true
      schema:
        $ref: "#/definitions/Sequence"
    responses:
      200:
        description: Returns a Task model
        schema:
          $ref: "#/definitions/Task"
      400:
        description: Invalid input parameter
      x-task-response:
        description: The task returns an array of arrays of results, in parallel lists with the provided Image models
    """
    ibs = current_app.ibs
    ut.embed()

    sequence_dict = vulcan_sequence_images(ibs, sequence)
    return


@register_api(_prefix('task'), methods=['GET'])
def vulcan_task_status(ibs, task):
    r"""
    Check the status of an asynchronous Task.

    A Task is an asynchronous task that was launched as a background process with an optional callback.  The status of a given Task with a UUID can be checked with this call.  The status of the call depends on where in the execution queue the Task is currently, which will be processed in a first-come-first-serve list and only one Task at a time to present atomicity of the API.

    The status can be one of the following:
    - received   -> The Task request was received but has not passed any input validation.
    - accepted   -> The Task request has passed basic input validation and will be queued soon for execution.
    - queued     -> The Task is queued in the execution list and will be processed in order and one at a time.
    - working    -> The Task is being processed, awaiting completed results or an error exception
    - publishing -> The Task is publishing the results of the background API call.
    - completed  -> One of two end states: the Task is complete, completed results available for downloading with the REST API.
    - exception  -> One of two end states: the Task has encountered an error, an error message can be received using the results REST API.
    - unknown    -> The Task you asked for is not known, indicating that the either UUID is not recognized (i.e. a Task with that ID was never currently created) or the server has been restarted.

    **Important: when the API server is restarted, all queued and running background Tasks are killed and all Task requests and cached results are deleted.**
    ---
    parameters:
    - name: task
      in: body
      description: A Task model
      required: true
      schema:
        $ref: "#/definitions/Task"
    responses:
      200:
        description: Returns the status of the provided Task
        schema:
          type: object
          properties:
            status:
              type: string
              enum:
              - received
              - accepted
              - queued
              - working
              - publishing
              - completed
              - exception
              - unknown
      400:
        description: Invalid input parameter
    """
    ibs = current_app.ibs

    # Input argument validation
    try:
        parameter = 'task'
        assert 'uuid' in task, 'Task Model provided is invalid, missing UUID key'
    except AssertionError as ex:
        raise controller_inject.WebInvalidInput(str(ex), parameter)

    uuid_ = task.get('uuid', None)
    assert uuid_ is not None
    status = ibs.get_job_status(uuid_)
    status = status.get('jobstatus', None)
    return {'status': status}


@register_api(_prefix('task'), methods=['POST'])
def vulcan_task_result(ibs, task):
    r"""
    Retrieve the result of a completed asynchronous Task
    ---
    parameters:
    - name: task
      in: body
      description: A Task model
      required: true
      schema:
        $ref: "#/definitions/Task"
    responses:
      200:
        description: Returns the result of the provided Task
      400:
        description: Invalid input parameter
    """
    ibs = current_app.ibs

    # Input argument validation
    try:
        parameter = 'task'
        assert 'uuid' in task, 'Task Model provided is invalid, missing UUID key'
    except AssertionError as ex:
        raise controller_inject.WebInvalidInput(str(ex), parameter)

    uuid_ = task.get('uuid', None)
    assert uuid_ is not None
    result = ibs.get_job_result(uuid_)
    result = result.get('json_result', None)
    return result


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
