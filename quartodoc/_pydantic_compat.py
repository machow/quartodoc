try:
    from pydantic.v1 import (
        BaseModel,
        Field,
        Extra,
        PrivateAttr,
        ValidationError,
    )  # noqa
except ImportError:
    from pydantic import BaseModel, Field, Extra, PrivateAttr, ValidationError  # noqa
