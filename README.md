# nessie-relationaldb-datasource-plugin

A [Nessie](https://github.com/Nessie-org) datasource plugin that loads a **SQLite relational database into a graph** by converting tables into nodes and foreign-key relationships into edges.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://pypi.org/project/nessie-relationaldb-datasource-plugin/)

---

## Overview

This plugin bridges the gap between relational databases and graph-based analysis. Given a `.db`, `.sqlite`, or `.sqlite3` file, it:

- Creates one **node per row** across all tables, with all column values stored as node attributes
- Creates one **edge per foreign-key reference**, labelled with the relationship (e.g. `employees.department_id -> departments.id`)
- Supports both **directed** and **undirected** graphs
- Registers automatically with the Nessie plugin system via a Python entry point

---

## Requirements

- Python 3.9 or higher
- [`nessie-api`](https://github.com/Nessie-org) >= 0.1.0

---

## Installation

```bash
pip install nessie-relationaldb-datasource-plugin
```

Or install from source:

```bash
git clone https://github.com/Nessie-org/nessie-relationaldb-datasource-plugin.git
cd nessie-relationaldb-datasource-plugin
pip install -e .
```

---

## Usage

### Via the Nessie plugin system

The plugin registers itself under the name `"SQLite Relational DB"` and is automatically discovered by Nessie through the `nessie_plugins` entry point.

```python
from nessie_relationaldb_datasource_plugin import relational_db_plugin
from nessie_api.models import Action

# Instantiate the plugin
plugin = relational_db_plugin()

# Load a graph from a SQLite database
graph = plugin.handle(
    Action("load_graph", {
        "Database Path": "path/to/your/database.db",
        "Is Directed": True,   # or False for an undirected graph
    }),
    context=None,
)

print(graph)
```

### Setup parameters

| Parameter       | Type    | Required | Description                                              |
|-----------------|---------|----------|----------------------------------------------------------|
| `Database Path` | string  | Yes      | Absolute or relative path to the SQLite database file   |
| `Is Directed`   | boolean | No       | Whether to build a directed graph (default: `False`)    |

### Accepted file extensions

`.db` · `.sqlite` · `.sqlite3`

---

## How It Works

### Nodes

Every row in every table becomes a node. The node ID is built from the table name and primary key value(s):

```
{table_name}_{pk_value}                  # e.g. employees_42
{table_name}_{pk1_value}_{pk2_value}     # composite keys
```

Each node carries all column values as attributes, plus a special `_table` attribute recording which table the row came from.

### Edges

Edges are derived from `FOREIGN KEY` constraints declared in the schema. For each row that has a non-null foreign key value, an edge is created between the source row's node and the referenced row's node. Each edge includes a `_relation` attribute describing the relationship:

```
employees.department_id -> departments.id
```

### Graph type

Pass `"Is Directed": True` to get a `GraphType.DIRECTED` graph, or `False` (the default) for `GraphType.UNDIRECTED`.

---

## Example

The repository includes an example script that seeds a company database and loads it as a graph:

```python
# tests/example.py
from nessie_relationaldb_datasource_plugin import relational_db_plugin
from nessie_api.models import Action

plugin = relational_db_plugin()
graph = plugin.handle(
    Action("load_graph", {
        "Database Path": "test.db",
        "Is Directed": True,
    }),
    context=None,
)

# Inspect nodes by table
from collections import defaultdict
by_table = defaultdict(list)
for node in graph.nodes:
    by_table[node["_table"]].append(node)

for table, nodes in by_table.items():
    print(f"{table}: {len(nodes)} nodes")

# Inspect edges by relation type
from collections import Counter
edge_relations = Counter(e["_relation"] for e in graph.edges)
for relation, count in edge_relations.most_common():
    print(f"{count}x  {relation}")
```

### Test databases

The `tests/data/` directory contains ten pre-built SQLite databases for development and testing:

| Database            | Domain                                    |
|---------------------|-------------------------------------------|
| `company.db`        | Corporate org chart, employees, projects  |
| `ecommerce.db`      | Products, orders, customers               |
| `hospital.db`       | Patients, doctors, appointments           |
| `library.db`        | Books, members, loans                     |
| `university.db`     | Students, courses, enrolments             |
| `music.db`          | Artists, albums, tracks                   |
| `game.db`           | Players, items, achievements              |
| `social_network.db` | Users, posts, follows                     |
| `logistics.db`      | Shipments, carriers, warehouses           |
| `real_estate.db`    | Properties, agents, transactions          |

---

## Development

### Setting up a local environment

```bash
git clone https://github.com/Nessie-org/nessie-relationaldb-datasource-plugin.git
cd nessie-relationaldb-datasource-plugin
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Linting and type checking

```bash
ruff check src/
mypy src/
black src/
```

### Seeding the test databases

```bash
python src/nessie_relationaldb_datasource_plugin/tests/seed_all.py
```

---

## Project structure

```
nessie-relationaldb-datasource-plugin/
├── src/
│   └── nessie_relationaldb_datasource_plugin/
│       ├── __init__.py               # Exports relational_db_plugin
│       ├── relationaldb_plugin.py    # Core plugin logic
│       └── tests/
│           ├── data/                 # Pre-built SQLite test databases
│           ├── example.py            # End-to-end usage example
│           ├── seed_all.py           # Scripts to regenerate test databases
│           └── test_relationaldb_plugin.py
├── pyproject.toml
└── README.md
```

---

## Author

**Stefan Ilić** — [stefanilic3001@gmail.com](mailto:stefanilic3001@gmail.com)

Issues and contributions welcome at the [GitHub repository](https://github.com/Nessie-org/nessie-relationaldb-datasource-plugin/issues).