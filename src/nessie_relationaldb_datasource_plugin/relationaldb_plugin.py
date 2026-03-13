import sqlite3
from typing import Any
from pathlib import Path

from nessie_api.models import (
    Graph,
    GraphType,
    Node,
    Edge,
    Attribute,
    Action,
    plugin,
    SetupRequirementType,
)
from nessie_api.protocols import Context


def _coerce(value: Any) -> Any:
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _validate_db_path(db_path: str) -> str:
    path = Path(db_path)

    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if path.suffix.lower() not in {".sqlite", ".db", ".sqlite3"}:
        raise ValueError("File must be a SQLite database (.sqlite, .db, .sqlite3)")

    return str(path)


def _get_tables(cursor: sqlite3.Cursor) -> list[str]:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def _get_primary_keys(cursor: sqlite3.Cursor, table: str) -> list[str]:
    cursor.execute(f'PRAGMA table_info("{table}")')
    return [row["name"] for row in cursor.fetchall() if row["pk"] > 0]


def _get_foreign_keys(cursor: sqlite3.Cursor, table: str) -> list[dict]:
    cursor.execute(f'PRAGMA foreign_key_list("{table}")')

    fks = []
    for row in cursor.fetchall():
        fks.append(
            {
                "from_col": row["from"],
                "to_table": row["table"],
                "to_col": row["to"],
            }
        )

    return fks


def _node_id(table: str, row: sqlite3.Row, pk_cols: list[str]) -> str:
    if pk_cols:
        vals = "_".join(str(row[c]) for c in pk_cols)
    else:
        vals = "_".join(str(row[c]) for c in row.keys())

    return f"{table}_{vals}"


def _parse(db_path: str, graph_type: GraphType) -> Graph:
    conn = _connect(db_path)
    cursor = conn.cursor()

    graph_name = Path(db_path).stem
    graph = Graph(graph_name, graph_type)

    tables = _get_tables(cursor)

    pk_cache: dict[str, list[str]] = {}
    fk_cache: dict[str, list[dict]] = {}

    for table in tables:
        pk_cache[table] = _get_primary_keys(cursor, table)
        fk_cache[table] = _get_foreign_keys(cursor, table)

    node_lookup = {}

    # -------- NODES --------
    for table in tables:

        cursor.execute(f'SELECT * FROM "{table}"')

        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break

            for row in rows:

                node_id = _node_id(table, row, pk_cache[table])
                node = Node(node_id)

                for col in row.keys():
                    val = row[col]
                    if val is not None:
                        node.add_attribute(Attribute(col, _coerce(val)))

                node.add_attribute(Attribute("_table", table))

                graph.add_node(node)
                node_lookup[node_id] = node

    # -------- EDGES --------
    edge_counter = 0

    for table in tables:

        fks = fk_cache[table]
        if not fks:
            continue

        cursor.execute(f'SELECT * FROM "{table}"')

        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break

            for row in rows:

                source_id = _node_id(table, row, pk_cache[table])
                source_node = node_lookup.get(source_id)

                if source_node is None:
                    continue

                for fk in fks:

                    target_table = fk["to_table"]
                    target_pk = fk_cache.get(target_table)

                    target_value = row[fk["from_col"]]

                    target_id = f"{target_table}_{target_value}"
                    target_node = node_lookup.get(target_id)

                    if target_node is None:
                        continue

                    edge_id = f"edge_{edge_counter}"
                    edge_counter += 1

                    edge = Edge(edge_id, source_node, target_node)

                    edge.add_attribute(
                        Attribute(
                            "_relation",
                            f"{table}.{fk['from_col']} -> {target_table}.{fk['to_col']}",
                        )
                    )

                    graph.add_edge(edge)

    conn.close()
    return graph


def load_graph(action: Action, context: Context) -> Graph:
    db_path = _validate_db_path(action.payload["Database Path"])
    is_directed = action.payload.get("Is Directed", False)
    graph_type = GraphType.DIRECTED if is_directed else GraphType.UNDIRECTED

    return _parse(db_path, graph_type)


@plugin(name="SQLite Relational DB")
def relational_db_plugin() -> Any:
    handlers = {
        "load_graph": load_graph,
    }

    requires = []

    setup_requires = {
        "Database Path": SetupRequirementType.FILE,
        "Is Directed": SetupRequirementType.BOOLEAN,
    }

    return {
        "handlers": handlers,
        "requires": requires,
        "setup_requires": setup_requires,
    }
