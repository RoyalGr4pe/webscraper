class InvalidResponse(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidResponseType(Exception):
    def __init__(self, response_type: str, website_name: str) -> None:
        message = f"Cannot scrape response type ({response_type}) on ({website_name})"
        super().__init__(message)