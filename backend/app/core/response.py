from typing import Any


def ok_response(data: Any) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(message: str, details: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {
            "message": message,
            "details": details,
        },
    }
