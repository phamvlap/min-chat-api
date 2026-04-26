import os
from pathlib import Path
from typing import TypeVar, cast, overload


def load_env(file_path: str | Path) -> None:
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check if the file exists
    if not file_path.exists():
        return

    # Check if the file is a regular file (not a directory)
    if not file_path.is_file():
        return

    with file_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            # Ignore empty lines, comments, and lines without an '=' character
            if not line or line.startswith("#") or "=" not in line:
                continue

            # Split the line into key and value at the first '=' character
            key, _, value = line.partition("=")

            key = key.strip()
            value = value.strip()

            if not key:
                continue

            # Handle multi-line values enclosed in quotes
            if (value.startswith('"') and not value.endswith('"')) or (
                value.startswith("'") and not value.endswith("'")
            ):
                quote_char: str = value[0]
                multi_line_value_buffer: list[str] = [value[1:]]

                while True:
                    next_line: str = file.readline()
                    if not next_line:
                        break  # End of file reached without closing quote

                    next_line = next_line.rstrip()

                    # If the next line ends with the closing quote, we can stop reading further
                    if next_line.endswith(quote_char):
                        multi_line_value_buffer.append(next_line[:-1])  # Remove the closing quote
                        break

                    multi_line_value_buffer.append(next_line)

                value = "\n".join(multi_line_value_buffer)

            # Remove surrounding quotes from the value if present for single-line values
            elif len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]

            os.environ[key] = value


T = TypeVar("T", str, bool, int, float)


@overload
def cast_value(value: str, target_type: type[str]) -> str: ...


@overload
def cast_value(value: str, target_type: type[bool]) -> bool: ...


@overload
def cast_value(value: str, target_type: type[int]) -> int: ...


@overload
def cast_value(value: str, target_type: type[float]) -> float: ...


def cast_value[T](value: str, target_type: type[T]) -> T:
    value = value.strip()

    if target_type is str:
        return cast(T, value)

    if target_type is bool:
        return cast(T, value.lower() in ("true", "1", "yes", "on"))

    if target_type is int:
        return cast(T, int(value))

    if target_type is float:
        return cast(T, float(value))

    raise ValueError(f"Unsupported target type: {target_type}")


@overload
def cast_list_value(value: str, item_type: type[str]) -> list[str]: ...


@overload
def cast_list_value(value: str, item_type: type[bool]) -> list[bool]: ...


@overload
def cast_list_value(value: str, item_type: type[int]) -> list[int]: ...


@overload
def cast_list_value(value: str, item_type: type[float]) -> list[float]: ...


def cast_list_value[T](value: str, item_type: type[T]) -> list[T]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return [cast_value(item, item_type) for item in items]


@overload
def get_env(key: str, target_type: type[str] = str, *, default: str | None = None) -> str: ...


@overload
def get_env(key: str, target_type: type[bool], *, default: bool | None = None) -> bool: ...


@overload
def get_env(key: str, target_type: type[int], *, default: int | None = None) -> int: ...


@overload
def get_env(key: str, target_type: type[float], *, default: float | None = None) -> float: ...


def get_env[T](key: str, target_type: type[T] = str, *, default: T | None = None) -> T:
    value = os.getenv(key)

    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{key}' is not set and no default value provided.")

    return cast_value(value, target_type)


@overload
def get_env_list(
    key: str,
    item_type: type[str] = str,
    *,
    default: list[str] | None = None,
) -> list[str]: ...


@overload
def get_env_list(
    key: str,
    item_type: type[bool],
    *,
    default: list[bool] | None = None,
) -> list[bool]: ...


@overload
def get_env_list(
    key: str,
    item_type: type[int],
    *,
    default: list[int] | None = None,
) -> list[int]: ...


@overload
def get_env_list(
    key: str,
    item_type: type[float],
    *,
    default: list[float] | None = None,
) -> list[float]: ...


def get_env_list[T](
    key: str,
    item_type: type[T] = str,
    *,
    default: list[T] | None = None,
) -> list[T]:
    value = os.getenv(key)

    if value is None:
        return default if default is not None else []

    return cast_list_value(value, item_type)
