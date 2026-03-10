import sqlite3
from typing import Any
from nessie_api.models import Graph, GraphType, Node, Edge, Attribute, Action, plugin


def _coerce(value: Any) -> Any:
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse(action: Action) -> Graph:
    """
    payload: {
        "db_path": str,
        "graph_type": GraphType (optional, default DIRECTED),
        "node_tables": list[str],
        "edge_tables": list[
            {
                "from_table": str,
                "from_col": str,
                "to_table": str,
                "to_col": str,
                "edge_id_col": str (optional)
            }
        ]
    }
    """
    conn = _connect(action.payload["db_path"])
    graph_type: GraphType = action.payload.get("graph_type", GraphType.DIRECTED)
    node_tables: list[str] = action.payload["node_tables"]
    edge_definitions: list[dict] = action.payload.get("edge_tables", [])

    graph = Graph(graph_type)
    cursor = conn.cursor()

    for table in node_tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]

        for row in rows:
            node_id = f"{table}_{row[cols[0]]}"
            node = Node(node_id)

            for col in cols:
                val = row[col]
                if val is not None:
                    node.add_attribute(Attribute(col, _coerce(val)))

            node.add_attribute(Attribute("_table", table))
            graph.add_node(node)

    for i, edge_def in enumerate(edge_definitions):
        from_table = edge_def["from_table"]
        from_col = edge_def["from_col"]
        to_table = edge_def["to_table"]
        to_col = edge_def["to_col"]
        edge_id_col = edge_def.get("edge_id_col")

        # without data, just for col names
        cursor.execute(f"SELECT * FROM {from_table} LIMIT 0")
        from_cols = [desc[0] for desc in cursor.description]

        select_cols = ", ".join(f"{from_table}.{c} AS {c}" for c in from_cols)

        # for disambiguating PK col of target table in case it's also present in source table
        to_alias = f"__{to_table}"

        cursor.execute(f"""
            SELECT {select_cols}, {to_alias}.{to_col} AS _target_pk
            FROM {from_table}
            JOIN {to_table} AS {to_alias} ON {from_table}.{from_col} = {to_alias}.{to_col}
        """)

        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]

        for j, row in enumerate(rows):
            source_node = graph.get_node(f"{from_table}_{row[cols[0]]}")
            target_node = graph.get_node(f"{to_table}_{row['_target_pk']}")

            if source_node is None or target_node is None:
                continue

            edge_id = (
                f"{from_table}_{row[edge_id_col]}"
                if edge_id_col
                else f"edge_{from_table}_{to_table}_{i}_{j}"
            )

            edge = Edge(edge_id, source_node, target_node)
            edge.add_attribute(Attribute("_relation", f"{from_table}.{from_col} -> {to_table}.{to_col}"))
            graph.add_edge(edge)

    conn.close()
    return graph


@plugin(name="relational_db_parser")
def relational_db_plugin() -> Any:
    handlers = {
        "db.parse": _parse,
    }
    requires = []
    return handlers, requires
