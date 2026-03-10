import sqlite3
import random
from faker import Faker

fake = Faker()


def seed_database(db_path: str = "main.db"):
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        DROP TABLE IF EXISTS task_assignments;
        DROP TABLE IF EXISTS tasks;
        DROP TABLE IF EXISTS project_members;
        DROP TABLE IF EXISTS projects;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS departments;

        CREATE TABLE departments (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            budget  INTEGER,
            city    TEXT
        );

        CREATE TABLE employees (
            id            INTEGER PRIMARY KEY,
            name          TEXT,
            email         TEXT,
            role          TEXT,
            salary        INTEGER,
            department_id INTEGER,
            manager_id    INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (manager_id)    REFERENCES employees(id)
        );

        CREATE TABLE projects (
            id            INTEGER PRIMARY KEY,
            name          TEXT,
            status        TEXT,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        CREATE TABLE project_members (
            id          INTEGER PRIMARY KEY,
            employee_id INTEGER,
            project_id  INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (project_id)  REFERENCES projects(id)
        );

        CREATE TABLE tasks (
            id         INTEGER PRIMARY KEY,
            title      TEXT,
            priority   TEXT,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );

        CREATE TABLE task_assignments (
            id          INTEGER PRIMARY KEY,
            task_id     INTEGER,
            employee_id INTEGER,
            FOREIGN KEY (task_id)     REFERENCES tasks(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
    """)

    # Departments (10)
    dept_names = ["Engineering", "Marketing", "Sales", "HR", "Finance",
                  "Legal", "Design", "DevOps", "Research", "Support"]
    departments = [
        (i, dept_names[i - 1], random.randint(50000, 500000), fake.city())
        for i in range(1, 11)
    ]
    conn.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", departments)

    # Employees (60) — first 10 are managers (manager_id = NULL)
    roles = ["Engineer", "Designer", "Analyst", "Manager", "Lead", "Intern", "Consultant"]
    employees = []
    for i in range(1, 61):
        manager_id = None if i <= 10 else random.randint(1, 10)
        employees.append((
            i,
            fake.name(),
            fake.email(),
            random.choice(roles),
            random.randint(30000, 120000),
            random.randint(1, 10),
            manager_id,
        ))
    conn.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)

    # Projects (30)
    statuses = ["active", "completed", "on_hold", "cancelled"]
    projects = [
        (i, fake.bs().title(), random.choice(statuses), random.randint(1, 10))
        for i in range(1, 31)
    ]
    conn.executemany("INSERT INTO projects VALUES (?, ?, ?, ?)", projects)

    # Project members (80) — employee <-> project
    pm_pairs = set()
    project_members = []
    pk = 1
    while len(project_members) < 80:
        emp_id = random.randint(1, 60)
        proj_id = random.randint(1, 30)
        if (emp_id, proj_id) not in pm_pairs:
            pm_pairs.add((emp_id, proj_id))
            project_members.append((pk, emp_id, proj_id))
            pk += 1
    conn.executemany("INSERT INTO project_members VALUES (?, ?, ?)", project_members)

    # Tasks (50)
    priorities = ["low", "medium", "high", "critical"]
    tasks = [
        (i, fake.sentence(nb_words=5), random.choice(priorities), random.randint(1, 30))
        for i in range(1, 51)
    ]
    conn.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?)", tasks)

    # Task assignments (60) — employee <-> task
    ta_pairs = set()
    task_assignments = []
    pk = 1
    while len(task_assignments) < 60:
        task_id = random.randint(1, 50)
        emp_id = random.randint(1, 60)
        if (task_id, emp_id) not in ta_pairs:
            ta_pairs.add((task_id, emp_id))
            task_assignments.append((pk, task_id, emp_id))
            pk += 1
    conn.executemany("INSERT INTO task_assignments VALUES (?, ?, ?)", task_assignments)

    conn.commit()
    conn.close()
    print("DB filled:")
    print(f"  departments:      {len(departments)}")
    print(f"  employees:        {len(employees)}")
    print(f"  projects:         {len(projects)}")
    print(f"  project_members:  {len(project_members)}")
    print(f"  tasks:            {len(tasks)}")
    print(f"  task_assignments: {len(task_assignments)}")
    total = (
            len(departments) +
            len(employees) +
            len(projects) +
            len(project_members) +
            len(tasks) +
            len(task_assignments)
    )
    print(f"  TOTAL NODES:    {total}")


if __name__ == "__main__":
    DB_PATH = "main.db"

    seed_database(DB_PATH)

    from nessie_api.models import Action, GraphType
    from nessie_relationaldb_datasource_plugin import relational_db_plugin

    p = relational_db_plugin()
    graph = p.handle(Action("db.parse", {
        "db_path": DB_PATH,
        "graph_type": GraphType.DIRECTED,
        "node_tables": ["departments", "employees", "projects", "project_members", "tasks", "task_assignments"],
        "edge_tables": [
            # Employee -> Department
            {"from_table": "employees", "from_col": "department_id",
             "to_table": "departments", "to_col": "id"},
            # Employee -> Manager
            {"from_table": "employees", "from_col": "manager_id",
             "to_table": "employees", "to_col": "id"},
            # Project -> Department
            {"from_table": "projects", "from_col": "department_id",
             "to_table": "departments", "to_col": "id"},
            # ProjectMember -> Employee
            {"from_table": "project_members", "from_col": "employee_id",
             "to_table": "employees", "to_col": "id"},
            # ProjectMember -> Project
            {"from_table": "project_members", "from_col": "project_id",
             "to_table": "projects", "to_col": "id"},
            # Task -> Project
            {"from_table": "tasks", "from_col": "project_id",
             "to_table": "projects", "to_col": "id"},
            # TaskAssignment -> Task
            {"from_table": "task_assignments", "from_col": "task_id",
             "to_table": "tasks", "to_col": "id"},
            # TaskAssignment -> Employee
            {"from_table": "task_assignments", "from_col": "employee_id",
             "to_table": "employees", "to_col": "id"},
        ]
    }))

    print(f"\n{graph}")
    print(f"{'─' * 50}")

    # Group nodes by table
    from collections import defaultdict, Counter
    by_table = defaultdict(list)
    for node in graph.nodes:
        by_table[node["_table"]].append(node)

    for table, nodes in by_table.items():
        print(f"\n── {table.upper()} ({len(nodes)}) ──")
        for node in nodes[:5]:  # first 5 for each table
            attrs = {k: v.value for k, v in node.attributes.items() if not k.startswith("_")}
            print(f"  {node.id:30s}  {attrs}")
        if len(nodes) > 5:
            print(f"  ... i jos {len(nodes) - 5} nodes")

    print(f"\n── EDGES ({len(graph.edges)}) ──")
    edge_by_relation = Counter(e["_relation"] for e in graph.edges)
    for relation, count in edge_by_relation.most_common():
        print(f"  {count:4d}x  {relation}")

    print(f"\n── Top 5 employees (tasks + projects) ──")
    emp_connections = Counter()
    for edge in graph.edges:
        if edge.target.id.startswith("employees_"):
            emp_connections[edge.target.id] += 1
    for emp_id, count in emp_connections.most_common(5):
        emp = graph.get_node(emp_id)
        print(f"  {emp['name']:30s}  role={emp['role']:15s}  edge={count}")
