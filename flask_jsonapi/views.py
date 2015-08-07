import qstring
from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest
from werkzeug.local import LocalProxy

from . import exc
from .params import FieldsParameter, IncludeParameter
from .serializer import Serializer

blueprint = Blueprint('jsonapi', __name__)


@blueprint.after_request
def set_response_content_type(response):
    response.mimetype = 'application/vnd.api+json'
    return response


@blueprint.errorhandler(exc.RequestError)
def handle_request_error(exc):
    statuses = {e['status'] for e in exc.errors}
    status = statuses.pop() if len(statuses) == 1 else BadRequest.code
    return jsonify(errors=exc.errors), status



class Controller(object):
    def __init__(self, resource_registry, request, resource):
        self.resource_registry = resource_registry
        self.request = request
        self.resource = resource
        self.serializer = Serializer(resource_registry)

    def build_params(
        self, type, allow_fields=False, allow_include=False,
        allow_pagination=False
    ):
        return Parameters(
            self.resource_registry,
            type,
            params=qstring.nest(request.args.items(multi=True)),
            allow_fields=allow_fields,
            allow_include=allow_include,
            allow_pagination=allow_pagination
        )

    def get_model(self, id):
        params = self.build_params(allow_fields=True, allow_include=True)
        model = self.resource.repository.find_by_id(
            self.resource.model_class,
            id,
            params
        )
        data = self.serializer.dump(model, params)
        return jsonify(data)

    def get_collection(self):
        params = self.build_params(
            self.resource.type,
            allow_fields=True,
            allow_include=True,
            allow_pagination=True
        )
        models = self.resource.repository.find(
            self.resource.model_class,
            params
        )
        data = self.serializer.dump(models, params, many=True)
        return jsonify(data)

    def get_related_model(self, id, relation):
        model = self.resource.repository.find_by_id(
            self.resource.model_class,
            id
        )
        related_model_class = self.resource.repository.get_related_model_class(model.__class__, relation)
        related_resource = self.resource_registry.by_model_class[related_model_class]
        params = self.build_params(
            related_resource.type,
            allow_fields=True,
            allow_include=True
        )
        related_model = self.resource.repository.get_related_model(
            model,
            relation,
            params
        )
        data = self.serializer.dump(related_model, params)
        return jsonify(data)

    def get_related_collection(self, id, relation):
        model = self.resource.repository.find_by_id(
            self.resource.model_class,
            id
        )
        related_model_class = self.resource.repository.get_related_model_class(model.__class__, relation)
        related_resource = self.resource_registry.by_model_class[related_model_class]
        params = self.build_params(
            related_resource.type,
            allow_fields=True,
            allow_include=True,
            allow_pagination=True
        )
        related_models = self.resource.repository.get_related_collection(
            model,
            relation,
            params
        )
        data = self.serializer.dump(related_models, params, many=True)
        return jsonify(data)

jsonapi = LocalProxy(lambda: current_app.extensions['jsonapi'])


def get_resource(type):
    try:
        return jsonapi.resources.by_type[type]
    except KeyError:
        raise exc.ResourceNotFound(type)


def get_controller(resource):
    return resource.controller_class(
        resource_registry=jsonapi.resources,
        resource=resource,
        request=request
    )


@blueprint.route('/<type>', methods=['GET'])
def get_collection(type):
    return get_controller(get_resource(type)).get_collection()


@blueprint.route('/<type>/<id>', methods=['GET'])
def get(type, id):
    return get_controller(get_resource(type)).get_model(id)


@blueprint.route('/<type>/<id>/<relation>', methods=['GET'])
def get_related(type, id, relation):
    resource = get_resource(type)
    if relation not in resource.relationships:
        raise RelationshipNotFound(type, relation)
    controller = get_controller(resource)
    if resource.repository.is_many(resource.model_class, relation):
        return controller.get_related_collection(id, relation)
    else:
        return controller.get_related_model(id, relation)


@blueprint.route('/<type>/<id>/relationships/<relation>', methods=['GET'])
def get_relationship(type, id, relation):
    pass


@blueprint.route('/<type>', methods=['POST'])
def create(type):
    pass


@blueprint.route('/<type>/<id>', methods=['PATCH'])
def update(type, id):
    pass


@blueprint.route('/<type>/<id>/relationships/<relation>', methods=['PATCH'])
def update_relationship(type, id, relation):
    pass


@blueprint.route('/<type>/<id>/relationships/<relation>', methods=['POST'])
def add_to_relationship(type, id, relation):
    pass


@blueprint.route('/<type>/<id>/relationships/<relation>', methods=['DELETE'])
def delete_from_relationship(type, id, relation):
    pass
