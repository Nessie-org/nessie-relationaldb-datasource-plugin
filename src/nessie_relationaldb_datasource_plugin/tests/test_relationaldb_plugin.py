import pytest
from nessie_api.models import GraphType, Action
from nessie_relationaldb_datasource_plugin.relationaldb_plugin import relational_db_plugin


@pytest.fixture
def plugin():
    return relational_db_plugin()


def parse(plugin, db_path, node_tables, edge_tables=None):
    return plugin.handle(Action("db.parse", {
        "db_path": db_path,
        "node_tables": node_tables,
        "edge_tables": edge_tables or [],
    }))


# ── Unknown action ───────────────────────────────────────────────

def test_unknown_action(plugin, test_db):
    result = plugin.handle(Action("db.invalid", {"db_path": test_db}))
    assert result is None


# ── Empty tables ──────────────────────────────────────────────────

def test_empty_node_tables(plugin, test_db):
    graph = parse(plugin, test_db, node_tables=[])
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0


def test_no_edge_tables(plugin, test_db):
    graph = parse(plugin, test_db, node_tables=["users"])
    assert len(graph.edges) == 0
    assert len(graph.nodes) == 3


# ── Nodes without FK ─────────────────────────────────────────────

def test_user_with_no_posts_has_no_edges(plugin, test_db):
    graph = parse(plugin, test_db,
                  node_tables=["users", "posts"],
                  edge_tables=[{"from_table": "posts", "from_col": "user_id",
                                "to_table": "users", "to_col": "id"}]
                  )
    solo = graph.get_node("users_3")
    assert solo is not None
    assert graph.in_neighbors(solo) == []


# ── Many edges to one node ───────────────────────────────────

def test_multiple_edges_to_same_user(plugin, test_db):
    graph = parse(plugin, test_db,
                  node_tables=["users", "posts"],
                  edge_tables=[{"from_table": "posts", "from_col": "user_id",
                                "to_table": "users", "to_col": "id"}]
                  )
    ana = graph.get_node("users_1")
    incoming = graph.in_neighbors(ana)
    assert len(incoming) == 2


# ── Missed FK target ──────────────────────────────────────────

def test_edge_skipped_if_target_table_not_in_node_tables(plugin, test_db):
    graph = parse(plugin, test_db,
                  node_tables=["posts"],
                  edge_tables=[{"from_table": "posts", "from_col": "user_id",
                                "to_table": "users", "to_col": "id"}]
                  )
    assert len(graph.edges) == 0


# ── Attributes ───────────────────────────────────────────────────────

def test_node_has_correct_attributes(plugin, test_db):
    graph = parse(plugin, test_db, node_tables=["users"])
    ana = graph.get_node("users_1")
    assert ana["name"] == "Ana"
    assert ana["age"] == 28
    assert ana["_table"] == "users"


def test_edge_has_relation_attribute(plugin, test_db):
    graph = parse(plugin, test_db,
                  node_tables=["users", "posts"],
                  edge_tables=[{"from_table": "posts", "from_col": "user_id",
                                "to_table": "users", "to_col": "id"}]
                  )
    for edge in graph.edges:
        assert edge["_relation"] == "posts.user_id -> users.id"


# ── Graph type ─────────────────────────────────────────────────────

def test_default_graph_type_is_directed(plugin, test_db):
    graph = parse(plugin, test_db, node_tables=["users"])
    assert graph.graph_type == GraphType.DIRECTED


def test_undirected_graph_type(plugin, test_db):
    graph = plugin.handle(Action("db.parse", {
        "db_path": test_db,
        "graph_type": GraphType.UNDIRECTED,
        "node_tables": ["users"],
        "edge_tables": [],
    }))
    assert graph.graph_type == GraphType.UNDIRECTED


# ── Invalid file ───────────────────────────────────────────────

def test_invalid_db_path_raises(plugin):
    with pytest.raises(Exception):
        parse(plugin, "invalid.db", node_tables=["users"])
