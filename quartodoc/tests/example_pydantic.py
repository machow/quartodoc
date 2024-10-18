from pydantic import BaseModel


class AModel(BaseModel):
    a: int
    """The a attribute."""
