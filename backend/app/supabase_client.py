from __future__ import annotations

import httpx
from app.config import settings

HEADERS = {
    "apikey": settings.supabase_anon_key,
    "Authorization": f"Bearer {settings.supabase_service_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

REST_URL = f"{settings.supabase_url.rstrip('/')}/rest/v1"


class SupabaseTable:
    def __init__(self, table: str):
        self.table = table
        self._url = f"{REST_URL}/{table}"
        self._params: dict = {}
        self._data: dict | list | None = None
        self._method = "GET"
        self._single = False

    def _clone(self):
        c = SupabaseTable(self.table)
        c._params = self._params.copy()
        c._data = self._data
        c._method = self._method
        c._single = self._single
        return c

    def select(self, columns="*"):
        c = self._clone()
        c._params["select"] = columns
        c._method = "GET"
        return c

    def insert(self, data: dict | list):
        c = self._clone()
        c._data = data
        c._method = "POST"
        return c

    def update(self, data: dict):
        c = self._clone()
        c._data = data
        c._method = "PATCH"
        return c

    def delete(self):
        c = self._clone()
        c._method = "DELETE"
        return c

    def eq(self, col: str, val):
        c = self._clone()
        c._params[col] = f"eq.{val}"
        return c

    def in_(self, col: str, vals: list):
        c = self._clone()
        c._params[col] = f"in.({','.join(str(v) for v in vals)})"
        return c

    def ilike(self, col: str, pattern: str):
        c = self._clone()
        c._params[col] = f"ilike.{pattern}"
        return c

    def order(self, col: str, desc: bool = False):
        c = self._clone()
        c._params["order"] = f"{col}.desc" if desc else f"{col}.asc"
        return c

    def range(self, start: int, end: int):
        c = self._clone()
        c._params["offset"] = start
        c._params["limit"] = end - start + 1
        return c

    def limit(self, n: int):
        c = self._clone()
        c._params["limit"] = n
        return c

    def maybe_single(self):
        c = self._clone()
        c._single = True
        c._params["limit"] = 1
        return c

    def execute(self):
        headers = HEADERS.copy()

        # Para INSERT/UPDATE: pede representação completa incluindo todos os campos
        if self._method in ("POST", "PATCH"):
            params = {**self._params, "select": "*"}
        else:
            params = self._params

        with httpx.Client(timeout=20) as client:
            if self._method == "GET":
                r = client.get(self._url, headers=headers, params=params)
            elif self._method == "POST":
                r = client.post(self._url, headers=headers, params=params, json=self._data)
            elif self._method == "PATCH":
                r = client.patch(self._url, headers=headers, params=params, json=self._data)
            elif self._method == "DELETE":
                r = client.delete(self._url, headers=headers, params=self._params)

        r.raise_for_status()
        body = r.json() if r.content else []

        # maybe_single(): retorna primeiro elemento ou None (sem usar Accept header
        # que causava 406 no PostgREST quando não havia linhas)
        if self._single:
            data = body[0] if body else None
        else:
            data = body

        class Result:
            pass

        result = Result()
        result.data = data
        return result


class SupabaseClient:
    def table(self, name: str) -> SupabaseTable:
        return SupabaseTable(name)


_client: SupabaseClient | None = None


def get_supabase() -> SupabaseClient:
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
