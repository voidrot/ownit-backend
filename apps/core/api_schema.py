from ninja import Schema

class AuthErrorSchema(Schema):
    message: str

class NotFoundSchema(Schema):
    message: str
