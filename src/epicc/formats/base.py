from typing import Any, IO, Generic, TypeVar
from pathlib import Path
from abc import ABC, abstractmethod

T = TypeVar("T")

class BaseFormat(ABC, Generic[T]):
    """
    Abstract base class for parameter file formats.
    """

    def __init__(self, path: Path | str) -> None:
        """
        Initialize the reader.
        
        Parameters:
            path: Path to the file to read. If a string, it will be converted to a Path object.
        """
        
        self.path = Path(path) if isinstance(path, str) else path

    @abstractmethod
    def read(self, data: IO) -> tuple[dict[str, Any], T]:
        """
        Read a stream and return its contents as a format-agnostic dictionary.

        Args:
            data: some data input stream.

        Returns:
            A tuple containing:
              - Dictionary representation of the file contents.
              - Template object of type T. This can be used to preserve formatting or other metadata
                when writing back to the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed.
        """

        ...

    @abstractmethod
    def write(self, data: dict[str, Any], template: T | None = None) -> bytes:
        """
        Write a agnostic-dictionary dictionary to the appropriate format.

        Args:
            data: Dictionary to write.
            template: Optional template object to use when writing. This can be used to preserve
                formatting or other metadata.

        Returns:
            Byte array containing the data in the appropriate format. If the format is text-based,
            this is UTF-8 encoded. Otherwise, for binary formats like XLSX, the encoding is format
            specified.

        Raises:
            ValueError: If the data cannot be serialized in the appropriate format.
        """

        ...

__all__ = ["BaseFormat"]