class ErrorTemplate:
    class UploadError:
        @staticmethod
        def invalid_file_extension(allow_extension: list[str]) -> dict[str, str]:
            return {
                "code": "UPLOAD_0",
                "message": "Invalid file extensions, only allow: " + ", ".join(allow_extension),
            }
