import yaml
from pydantic import ValidationError
from awa.core.spec import Spec
from pathlib import Path


def load_spec(path: str) -> Spec:
    """
    Load and validate a YAML spec file into a Spec model.
    """
    raw = Path(path).read_text()
    data = yaml.safe_load(raw)
    try:
        spec = Spec.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Spec validation error: {e}")
    return spec