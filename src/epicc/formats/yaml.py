"""
Generic reader for YAML parameter files. Excepts a YAML file with a mapping at the top level, which
is parsed into a dictionary.
"""

from io import StringIO
from typing import IO, Any

from ruamel.yaml import YAML

from epicc.formats.base import BaseFormat


class YAMLFormat(BaseFormat[YAML]):
    """Reader for YAML parameter files."""

    def read(self, data: IO) -> tuple[dict[str, Any], YAML]:
        """Read a YAML file and return its contents as a dictionary.

        Args:
            data: Input stream containing the YAML data.

        Returns:
            A tuple containing:
              - Dictionary representation of the YAML contents.
              - YAML object representing the YAML file, which can be used as a template for writing.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as valid YAML,
                or if the top-level structure is not a mapping.
        """

        yaml = YAML(typ="safe")

        try:
            data = yaml.load(data)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML data at {self.path}") from e

        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a YAML mapping at the top level in {self.path}, got {type(data).__name__}"
            )

        return data, yaml

    def write(self, data: dict[str, Any], template: YAML | None = None) -> bytes:
        """Write a dictionary to a YAML file.

        Args:
            data: Dictionary to write.
            template: Optional YAML object to use as a template when writing. This can be used to preserve
                formatting or other metadata.

        Returns:
            Byte array containing the YAML data, UTF-8 encoded.
        """

        yaml = template or YAML(typ="safe")
        output = StringIO()
        yaml.dump(data, output)
        return output.getvalue().encode("utf-8")


__all__ = ["YAMLFormat"]
