try:
    from pydantic.v1 import (
        BaseModel,
        Field,
        Extra,
        PrivateAttr,
        ValidationError,
        validator,
    )  # noqa
except ImportError:
    from pydantic import BaseModel, Field, Extra, PrivateAttr, ValidationError, validator  # noqa
