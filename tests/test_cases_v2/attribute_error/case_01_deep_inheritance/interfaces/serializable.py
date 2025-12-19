class Serializable:
    """Interface for serializable objects."""

    def to_dict(self) -> dict:
        raise NotImplementedError

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        raise NotImplementedError
