"""
Cliente Postgres com API compatível com o subconjunto do supabase-py usado no projeto

Permite que os repositories continuem escrevendo
`client.table("leads").select("*").eq("id", x).execute()`
enquanto as queries rodam direto no Postgres (Railway), sem PostgREST.

As linhas retornadas imitam o JSON do PostgREST: datas viram strings ISO,
UUID vira str e NUMERIC vira float — os repositories e models dependem disso.
"""
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, Dict, List, Optional
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_COMPARISON_OPS = {
    "eq": "=",
    "neq": "<>",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "ilike": "ILIKE",
}

_IS_VALUES = {"null": "NULL", "true": "TRUE", "false": "FALSE"}

_json_dumps = partial(json.dumps, default=str)


def _quote_ident(name: str) -> str:
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Identificador SQL inválido: {name!r}")
    return f'"{name}"'


def _to_db_value(value: Any) -> Any:
    """Normaliza valores Python para algo que o psycopg2 sabe adaptar"""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "model_dump"):
        return Json(value.model_dump(mode="json"), dumps=_json_dumps)
    return value


def _to_api_value(value: Any) -> Any:
    """Converte valores lidos do banco para o formato que o PostgREST devolvia"""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, list):
        return [_to_api_value(v) for v in value]
    return value


@dataclass
class QueryResponse:
    data: Any
    count: Optional[int] = None


class QueryBuilder:
    """Builder de query para uma tabela (select/insert/update/delete + filtros)"""

    def __init__(self, client: "PostgresClient", table: str):
        self._client = client
        self._table = table
        self._action = "select"
        self._columns = "*"
        self._count = False
        self._payload: Any = None
        self._where: List[str] = []
        self._params: Dict[str, Any] = {}
        self._order: List[str] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._single = False

    # ---------- ações ----------

    def select(self, columns: str = "*", count: Optional[str] = None) -> "QueryBuilder":
        self._action = "select"
        self._columns = self._parse_columns(columns)
        self._count = count == "exact"
        return self

    def insert(self, payload: Any) -> "QueryBuilder":
        self._action = "insert"
        self._payload = payload
        return self

    def update(self, payload: Dict[str, Any]) -> "QueryBuilder":
        self._action = "update"
        self._payload = payload
        return self

    def delete(self) -> "QueryBuilder":
        self._action = "delete"
        return self

    # ---------- filtros ----------

    def eq(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "eq", value)

    def neq(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "neq", value)

    def gt(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "gt", value)

    def gte(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "gte", value)

    def lt(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "lt", value)

    def lte(self, column: str, value: Any) -> "QueryBuilder":
        return self._compare(column, "lte", value)

    def like(self, column: str, pattern: str) -> "QueryBuilder":
        return self._compare(column, "like", pattern)

    def ilike(self, column: str, pattern: str) -> "QueryBuilder":
        return self._compare(column, "ilike", pattern)

    def is_(self, column: str, value: Any) -> "QueryBuilder":
        self._where.append(self._is_condition(column, value))
        return self

    def in_(self, column: str, values: List[Any]) -> "QueryBuilder":
        if not values:
            self._where.append("FALSE")
            return self
        placeholders = ", ".join(self._bind(v) for v in values)
        self._where.append(f"{_quote_ident(column)} IN ({placeholders})")
        return self

    def or_(self, filters: str) -> "QueryBuilder":
        """Filtro OR no formato PostgREST: 'col.op.valor,col.op.valor'"""
        conditions = []
        for part in filters.split(","):
            column, op, value = part.strip().split(".", 2)
            if op == "is":
                conditions.append(self._is_condition(column, value))
            elif op in _COMPARISON_OPS:
                if op in ("like", "ilike"):
                    value = value.replace("*", "%")
                conditions.append(self._condition(column, op, value))
            else:
                raise ValueError(f"Operador não suportado em or_: {op}")
        self._where.append("(" + " OR ".join(conditions) + ")")
        return self

    # ---------- modificadores ----------

    def order(self, column: str, desc: bool = False) -> "QueryBuilder":
        self._order.append(f"{_quote_ident(column)} {'DESC' if desc else 'ASC'}")
        return self

    def limit(self, size: int) -> "QueryBuilder":
        self._limit = int(size)
        return self

    def offset(self, start: int) -> "QueryBuilder":
        self._offset = int(start)
        return self

    def range(self, start: int, end: int) -> "QueryBuilder":
        self._offset = int(start)
        self._limit = int(end) - int(start) + 1
        return self

    def single(self) -> "QueryBuilder":
        self._single = True
        return self

    # ---------- execução ----------

    def execute(self) -> QueryResponse:
        if self._action == "select":
            rows, count = self._run_select()
        elif self._action == "insert":
            rows, count = self._run_insert(), None
        elif self._action == "update":
            rows, count = self._run_update(), None
        else:
            rows, count = self._run_delete(), None

        if self._single:
            if len(rows) > 1:
                raise ValueError(f"single() retornou {len(rows)} linhas em {self._table}")
            return QueryResponse(data=rows[0] if rows else None, count=count)

        return QueryResponse(data=rows, count=count)

    # ---------- internos ----------

    def _parse_columns(self, columns: str) -> str:
        columns = columns.strip()
        if columns == "*":
            return "*"
        if "(" in columns:
            raise NotImplementedError("Selects com relacionamentos embutidos não são suportados")
        return ", ".join(_quote_ident(c.strip()) for c in columns.split(","))

    def _bind(self, value: Any) -> str:
        name = f"p{len(self._params)}"
        self._params[name] = _to_db_value(value)
        return f"%({name})s"

    def _condition(self, column: str, op: str, value: Any) -> str:
        return f"{_quote_ident(column)} {_COMPARISON_OPS[op]} {self._bind(value)}"

    def _compare(self, column: str, op: str, value: Any) -> "QueryBuilder":
        self._where.append(self._condition(column, op, value))
        return self

    def _is_condition(self, column: str, value: Any) -> str:
        key = str(value).lower() if value is not None else "null"
        if key not in _IS_VALUES:
            raise ValueError(f"Valor inválido para IS: {value!r}")
        return f"{_quote_ident(column)} IS {_IS_VALUES[key]}"

    def _where_sql(self) -> str:
        return f" WHERE {' AND '.join(self._where)}" if self._where else ""

    def _require_filters(self):
        if not self._where:
            raise ValueError(f"{self._action} em {self._table} sem filtro não é permitido")

    def _bind_column_value(self, column: str, value: Any) -> str:
        """Faz bind respeitando o tipo da coluna (JSONB recebe Json, arrays recebem list)"""
        column_type = self._client.column_types(self._table).get(column)
        if value is not None and (column_type in ("json", "jsonb") or
                                  (isinstance(value, (dict, list)) and column_type != "ARRAY")):
            name = f"p{len(self._params)}"
            self._params[name] = Json(value, dumps=_json_dumps)
            return f"%({name})s"
        return self._bind(value)

    def _run_select(self):
        table = _quote_ident(self._table)
        sql = f"SELECT {self._columns} FROM {table}{self._where_sql()}"
        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"

        rows = self._client.fetch(sql, self._params)

        count = None
        if self._count:
            count_sql = f"SELECT COUNT(*) AS total FROM {table}{self._where_sql()}"
            count = self._client.fetch(count_sql, self._params)[0]["total"]

        return rows, count

    def _run_insert(self):
        records = self._payload if isinstance(self._payload, list) else [self._payload]
        if not records:
            return []

        columns = list(records[0].keys())
        values_sql = []
        for record in records:
            values_sql.append(
                "(" + ", ".join(self._bind_column_value(c, record.get(c)) for c in columns) + ")"
            )

        sql = (
            f"INSERT INTO {_quote_ident(self._table)} "
            f"({', '.join(_quote_ident(c) for c in columns)}) "
            f"VALUES {', '.join(values_sql)} RETURNING *"
        )
        return self._client.fetch(sql, self._params)

    def _run_update(self):
        self._require_filters()
        if not self._payload:
            return []

        assignments = ", ".join(
            f"{_quote_ident(c)} = {self._bind_column_value(c, v)}"
            for c, v in self._payload.items()
        )
        sql = f"UPDATE {_quote_ident(self._table)} SET {assignments}{self._where_sql()} RETURNING *"
        return self._client.fetch(sql, self._params)

    def _run_delete(self):
        self._require_filters()
        sql = f"DELETE FROM {_quote_ident(self._table)}{self._where_sql()} RETURNING *"
        return self._client.fetch(sql, self._params)


class RpcBuilder:
    """Chamada de função SQL (equivalente ao supabase.rpc)"""

    def __init__(self, client: "PostgresClient", function: str, params: Optional[Dict[str, Any]]):
        self._client = client
        self._function = function
        self._params = params or {}

    def execute(self) -> QueryResponse:
        args = ", ".join(
            f"{_quote_ident(name)} => %({name})s" for name in self._params
        )
        sql = f"SELECT * FROM {_quote_ident(self._function)}({args})"
        rows = self._client.fetch(
            sql, {k: _to_db_value(v) for k, v in self._params.items()}
        )

        # Funções escalares (ex: RETURNS JSON) voltam como o próprio valor
        if len(rows) == 1 and len(rows[0]) == 1:
            return QueryResponse(data=next(iter(rows[0].values())))
        return QueryResponse(data=rows)


class PostgresClient:
    """Ponto de entrada compatível com o client do supabase-py"""

    def __init__(self, engine):
        self._engine = engine
        self._column_types: Dict[str, Dict[str, str]] = {}

    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(self, name)

    def rpc(self, function: str, params: Optional[Dict[str, Any]] = None) -> RpcBuilder:
        return RpcBuilder(self, function, params)

    @property
    def storage(self):
        raise RuntimeError("Storage de arquivos ainda não configurado (Supabase Storage foi desativado)")

    def column_types(self, table: str) -> Dict[str, str]:
        if table not in self._column_types:
            rows = self.fetch(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %(table)s",
                {"table": table},
            )
            self._column_types[table] = {r["column_name"]: r["data_type"] for r in rows}
        return self._column_types[table]

    def fetch(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Executa a query numa transação própria e devolve as linhas no formato do PostgREST"""
        connection = self._engine.raw_connection()
        try:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql, params)
            rows = cursor.fetchall() if cursor.description else []
            connection.commit()
            return [{k: _to_api_value(v) for k, v in row.items()} for row in rows]
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
