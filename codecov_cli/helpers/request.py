import requests

from codecov_cli.types import RequestError, RequestResult


def send_post_request(
    url: str,
    data: dict = None,
    headers: dict = None,
):
    resp = requests.post(
        url=url,
        data=data,
        headers=headers,
    )
    return request_result(resp)


def send_put_request(
    url: str,
    data: dict = None,
    headers: dict = None,
):
    resp = requests.put(url=url, data=data, headers=headers)
    return request_result(resp)


def request_result(resp):
    if resp.status_code >= 400:
        return RequestResult(
            status_code=resp.status_code,
            error=RequestError(
                code=f"HTTP Error {resp.status_code}",
                description=resp.text,
                params={},
            ),
            warnings=[],
            text=resp.text,
        )

    return RequestResult(
        status_code=resp.status_code, error=None, warnings=[], text=resp.text
    )
