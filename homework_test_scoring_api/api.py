# pylint: disable=C0114,C0115,C0116,C0301,C0103,R0903,W0402,W0703,E1133
import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
from requests import RequestException
from store import Store, RedisDBStorage
from scoring import get_interests, get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
VALID_ARG_PAIRS = [('email', 'phone'), ('first_name', 'last_name'), ('birthday', 'gender')]
IS_NULLABLE = ('', [], {}, (), None)


class ValidationError(Exception):
    pass


class BaseField(ABC):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    @abstractmethod
    def validate(self, value):
        if self.required and value is None:
            raise ValidationError(f"{self.__class__.__name__} is required")
        if not self.nullable and value in IS_NULLABLE:
            raise ValidationError(f"{self.__class__.__name__} can't be nullable")


class CharField(BaseField):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, str):
            raise ValidationError(f"{self.__class__.__name__} value type must be str")


class ArgumentsField(BaseField):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, dict):
            raise ValidationError(f"{self.__class__.__name__} value type must be dict")


class EmailField(CharField):
    def validate(self, value):
        super().validate(value)
        if '@' not in value:
            raise ValidationError(f"{self.__class__.__name__} must contain '@' character")


class PhoneField(BaseField):
    def validate(self, value):
        super().validate(value)
        if not value:
            return
        if not isinstance(value, (int, str)):
            raise ValidationError(f"{self.__class__.__name__} must be int or str")
        if len(str(value)) != 11:
            raise ValidationError(f"{self.__class__.__name__} length must be 11")
        if isinstance(value, str):
            if not value.startswith('7'):
                raise ValidationError(f"{self.__class__.__name__} must starts with 7")
            try:
                int(value)
            except ValueError as err:
                raise ValidationError(f"{self.__class__.__name__} must contain numbers only") from err
        if isinstance(value, int):
            if not str(value).startswith('7'):
                raise ValidationError(f"{self.__class__.__name__} must starts with 7")


class DateField(CharField):
    def validate(self, value):
        super().validate(value)
        if not value:
            return None
        try:
            return datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError as err:
            raise ValidationError(f"{self.__class__.__name__} must be in 'DD.MM.YYYY' format") from err


class BirthDayField(DateField):
    def validate(self, value):
        parsed_date = super().validate(value)
        if parsed_date and (datetime.today().date() - parsed_date > timedelta(days=365) * 70):
            raise ValidationError(f"since that date {self.__class__.__name__} have passed more than 70 years")


class GenderField(BaseField):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, int):
            raise ValidationError(f"{self.__class__.__name__} must be of type int")
        if value not in GENDERS:
            raise ValidationError(f"{self.__class__.__name__} must be 0, 1 or 2")


class ClientIDsField(BaseField):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, list):
            raise ValidationError(f"{self.__class__.__name__} must be of type list")
        if value and not all(isinstance(i, int) for i in value):
            raise ValidationError(f"{self.__class__.__name__} must contain a list of int values only")


class RequestMeta(type):
    def __new__(cls, name, bases, dct):
        renewed = dct.copy()
        renewed['_fields'] = {}
        for key, value in dct.items():
            if isinstance(value, BaseField):
                renewed['_fields'][key] = value
                # print(key)
                # print(value)
                del renewed[key]
        # print(renewed)
        return super().__new__(cls, name, bases, renewed)


class BaseRequest(metaclass=RequestMeta):
    def __init__(self, body):
        self.body = body
        self._errors = {}
        self._fields = self.fields

    def validate(self):
        self._errors = {}
        for key, value in self._fields.items():
            if key not in self.body and not value.required:
                continue
            val = self.body.get(key)
            try:
                value.validate(val)
                setattr(self, key, val)
            except ValidationError as err:
                self._errors[key] = str(err)

    @property
    def fields(self):
        return self._fields

    @property
    def errors(self):
        return self._errors


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def get_result(self, _, context, store):
        client_ids_list = getattr(self, 'client_ids', [])
        context["nclients"] = len(client_ids_list)
        result = {}
        for client_id in client_ids_list:
            result[f"client_id{client_id}"] = get_interests(store, client_id)
        return result


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super().validate()
        for pair in VALID_ARG_PAIRS:
            if getattr(self, pair[0], None) not in IS_NULLABLE and getattr(self, pair[1], None) not in IS_NULLABLE:
                return
        self._errors["arguments"] = f"{self.__class__.__name__} needs to have at least one pair" \
                                    f"with not-null values: {VALID_ARG_PAIRS}"

    def get_result(self, is_admin, context, store):
        context['has'] = list(filter(lambda obj: getattr(self, obj, None) not in IS_NULLABLE, self._fields))
        kwargs = {key: getattr(self, key, None) for key in self._fields}
        score = 42 if is_admin else get_score(store, **kwargs)
        return {'score': score}


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request) -> bool:
    if request.is_admin:
        digest = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    request_classes = {
        'online_score': OnlineScoreRequest,
        'clients_interests': ClientsInterestsRequest
    }
    method_request = MethodRequest(request['body'])
    method_request.validate()
    if method_request.errors:
        return method_request.errors, INVALID_REQUEST
    if not check_auth(method_request):
        return f"Authentication failed for user {method_request.login}", FORBIDDEN
    if method_request.method not in request_classes:
        return f"Method {method_request.method} not found", NOT_FOUND

    request_obj = request_classes[method_request.method](method_request.arguments)
    request_obj.validate()
    result = request_obj.get_result(method_request.is_admin, ctx, store)
    if request_obj.errors:
        return request_obj.errors, INVALID_REQUEST
    return result, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = Store(RedisDBStorage())
    store.storage.connect()

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except RequestException as err:
            logging.exception("Bad request error: %s", err)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s", self.path, data_string, context["request_id"])
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as err:
                    logging.exception("Unexpected error: %s", err)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            res = {"response": response, "code": code}
        else:
            res = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(res)
        logging.info(context)
        self.wfile.write(json.dumps(res).encode('utf-8'))


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s", opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
