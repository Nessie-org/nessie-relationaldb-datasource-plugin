import sqlite3
from typing import Any
from pathlib import Path
from nessie_api.models import Graph, GraphType, Node, Edge, Attribute, Action, plugin, SetupRequirementType
from nessie_api.protocols import Context


def _coerce(value: Any) -> Any:
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_tables(cursor: sqlite3.Cursor) -> list[str]:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]


def _get_foreign_keys(cursor: sqlite3.Cursor, table: str) -> list[dict]:
    """
    Returns list of FK dicts:
    { from_col, to_table, to_col }
    """
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    fks = []
    for row in cursor.fetchall():
        fks.append({
            "from_col": row["from"],
            "to_table": row["table"],
            "to_col":   row["to"],
        })
    return fks


def _parse(db_path: str, graph_type: GraphType = GraphType.DIRECTED) -> Graph:
    conn = _connect(db_path)
    cursor = conn.cursor()
    graph_name = Path(db_path).stem
    graph = Graph(graph_name, graph_type)

    tables = _get_tables(cursor)

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]

        for row in rows:
            pk_val = row[cols[0]]
            node_id = f"{table}_{pk_val}"
            node = Node(node_id)

            for col in cols:
                val = row[col]
                if val is not None:
                    node.add_attribute(Attribute(col, _coerce(val)))

            node.add_attribute(Attribute("_table", table))
            graph.add_node(node)

    edge_counter = 0
    for table in tables:
        fks = _get_foreign_keys(cursor, table)

        if not fks:
            continue

        cursor.execute(f"SELECT * FROM {table} LIMIT 0")
        from_cols = [desc[0] for desc in cursor.description]
        select_cols = ", ".join(f'"{table}"."{c}" AS "{c}"' for c in from_cols)

        for fk in fks:
            from_col = fk["from_col"]
            to_table = fk["to_table"]
            to_col = fk["to_col"]
            to_alias = f"__{to_table}"

            cursor.execute(f"""
                SELECT {select_cols}, "{to_alias}"."{to_col}" AS _target_pk
                FROM "{table}"
                JOIN "{to_table}" AS "{to_alias}"
                  ON "{table}"."{from_col}" = "{to_alias}"."{to_col}"
            """)

            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]

            for row in rows:
                source_node = graph.get_node(f"{table}_{row[cols[0]]}")
                target_node = graph.get_node(f"{to_table}_{row['_target_pk']}")

                if source_node is None or target_node is None:
                    continue

                edge_id = f"edge_{table}_{to_table}_{edge_counter}"
                edge_counter += 1

                edge = Edge(edge_id, source_node, target_node)
                edge.add_attribute(Attribute("_relation", f"{table}.{from_col} -> {to_table}.{to_col}"))
                graph.add_edge(edge)

    conn.close()
    return graph


def load_graph(action: Action, context: Context) -> Graph:
    db_path: str = action.payload["Database Path"]
    graph_type: GraphType = action.payload.get("graph_type", GraphType.DIRECTED)
    return _parse(db_path, graph_type)


@plugin(name="SQLite Relational DB")
def relational_db_plugin() -> Any:
    handlers = {
        "load_graph": load_graph,
    }
    requires = []
    setup_requires = {
        "Database Path": SetupRequirementType.FILE,
    }
    ret_dict = {
        "handlers":      handlers,
        "requires":      requires,
        "setup_requires": setup_requires,
    }
    return ret_dict
