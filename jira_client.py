import requests
from requests.auth import HTTPBasicAuth
from typing import List, Tuple, Any
import json
import rich


DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

DEFAULT_MAX_RESULTS = 50

class JiraError(Exception):
    def __init__(self, msgs: List[str]):
        self.msgs = msgs

    def __str__(self):
        return str(self.msgs)


def _check_result(r):
    try:
        r.raise_for_status()
    except requests.HTTPError:
        if r.status_code == 402:
            raise JiraError("Jira authentication failed")
        t = r.json()
        if "errorMessages" in t:
            raise JiraError(f"Jira error: {t['errorMessages']}")
        else:
            raise
        
    return r.json()


def _for_each_page(request_callback, response_callback):
    offset = 0

    while True:
        r = request_callback(offset)
        result_count = len(r["issues"])
        total = r["total"]
        response_callback(r)

        offset += result_count
        if offset >= total:
            break


class JiraClient():
    def __init__(self, url: str, email: str, token: str):
        if not url.endswith("/"):
            url += "/"
        self.api = f"{url}rest/api/3"
        self.auth = HTTPBasicAuth(email, token)


    def get_project(self, key: str):
        r = requests.get(f"{self.api}/project/{key}", auth=self.auth, headers=DEFAULT_HEADERS)
        return _check_result(r)


    def get_statuses(self):
        r = requests.get(f"{self.api}/status", auth=self.auth, headers=DEFAULT_HEADERS)
        return _check_result(r)


    def search_issues(self, jql: str, fields: List[str]):
        results = []

        def _do_request(offset: int):
            data = json.dumps({
                "jql": jql,
                "maxResults": DEFAULT_MAX_RESULTS,
                "fieldsByKeys": False,
                "fields": fields,
                "startAt": offset
            })

            r = requests.post(f"{self.api}/search", auth=self.auth, headers=DEFAULT_HEADERS, data=data)
            return _check_result(r)

        _for_each_page(_do_request, lambda r : results.extend(r["issues"]))

        return results
