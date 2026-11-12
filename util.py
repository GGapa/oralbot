import time

import requests

import api

H = dict(api.H)
H["Content-Type"] = "application/json"
O = api.cfg["origin"] + "/api/"

RETRIES = 4


def _try(method, path, body=None, raw=None, ctype=None, extra=None, timeout=120):
    h = dict(H)
    if ctype:
        h["Content-Type"] = ctype
    if extra:
        h.update(extra)
    last = None
    for i in range(RETRIES):
        try:
            if raw is not None:
                return api.s.request(method, O + path, headers=h, data=raw, timeout=timeout)
            return api.s.request(method, O + path, headers=h, json=body, timeout=timeout)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def req(method, path, body=None, raw=None, ctype=None):
    r = _try(method, path, body, raw, ctype)
    if r.status_code == 401 and api.refresh():
        r = _try(method, path, body, raw, ctype)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def post(path, body=None):
    return req("POST", path, body)


def get(path):
    return req("GET", path)


def upload(data, filename="record.m4a", ctype="audio/mp4"):
    extra = {"X-Blob-Original-File-Name": filename, "X-Blob-File-Size": str(len(data))}
    r = _try("POST", "repository-blobstore/files/upload", raw=data, ctype=ctype,
             extra=extra, timeout=180)
    if r.status_code == 401 and api.refresh():
        r = _try("POST", "repository-blobstore/files/upload", raw=data, ctype=ctype,
                 extra=extra, timeout=180)
    j = r.json()
    if "accessId" not in j:
        raise RuntimeError("upload failed: %s %s" % (r.status_code, r.text[:200]))
    return j["accessId"]
