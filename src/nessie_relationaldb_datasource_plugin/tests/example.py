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
        DROP TABLE IF EXISTS employee_skills;
        DROP TABLE IF EXISTS skills;
        DROP TABLE IF EXISTS office_locations;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS departments;
        DROP TABLE IF EXISTS clients;
        DROP TABLE IF EXISTS contracts;

        CREATE TABLE office_locations (
            id      INTEGER PRIMARY KEY,
            city    TEXT,
            country TEXT,
            floor   INTEGER
        );

        CREATE TABLE departments (
            id                 INTEGER PRIMARY KEY,
            name               TEXT,
            budget             INTEGER,
            office_location_id INTEGER,
            FOREIGN KEY (office_location_id) REFERENCES office_locations(id)
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

        CREATE TABLE skills (
            id       INTEGER PRIMARY KEY,
            name     TEXT,
            category TEXT
        );

        CREATE TABLE employee_skills (
            id          INTEGER PRIMARY KEY,
            employee_id INTEGER,
            skill_id    INTEGER,
            level       TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (skill_id)    REFERENCES skills(id)
        );

        CREATE TABLE clients (
            id       INTEGER PRIMARY KEY,
            name     TEXT,
            industry TEXT,
            country  TEXT
        );

        CREATE TABLE contracts (
            id            INTEGER PRIMARY KEY,
            title         TEXT,
            value         INTEGER,
            status        TEXT,
            client_id     INTEGER,
            department_id INTEGER,
            FOREIGN KEY (client_id)     REFERENCES clients(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        CREATE TABLE projects (
            id            INTEGER PRIMARY KEY,
            name          TEXT,
            status        TEXT,
            department_id INTEGER,
            contract_id   INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (contract_id)   REFERENCES contracts(id)
        );

        CREATE TABLE project_members (
            id          INTEGER PRIMARY KEY,
            employee_id INTEGER,
            project_id  INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (project_id)  REFERENCES projects(id)
        );

        CREATE TABLE tasks (
            id          INTEGER PRIMARY KEY,
            title       TEXT,
            priority    TEXT,
            status      TEXT,
            project_id  INTEGER,
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

    # office_locations (5)
    offices = [(i, fake.city(), fake.country(), random.randint(1, 20)) for i in range(1, 6)]
    conn.executemany("INSERT INTO office_locations VALUES (?, ?, ?, ?)", offices)

    # departments (8)
    dept_names = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Design", "DevOps", "Research"]
    departments = [(i, dept_names[i - 1], random.randint(50000, 500000), random.randint(1, 5)) for i in range(1, 9)]
    conn.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", departments)

    # employees (30) — first 8 are managers
    roles = ["Engineer", "Designer", "Analyst", "Manager", "Lead", "Consultant"]
    employees = []
    for i in range(1, 31):
        manager_id = None if i <= 8 else random.randint(1, 8)
        employees.append((i, fake.name(), fake.email(), random.choice(roles),
                          random.randint(30000, 120000), random.randint(1, 8), manager_id))
    conn.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)

    # skills (15)
    skill_data = [
        ("Python", "Programming"), ("JavaScript", "Programming"), ("SQL", "Data"),
        ("Machine Learning", "Data"), ("React", "Frontend"), ("Docker", "DevOps"),
        ("Kubernetes", "DevOps"), ("Figma", "Design"), ("Photoshop", "Design"),
        ("Project Management", "Management"), ("Communication", "Soft"),
        ("Excel", "Data"), ("Rust", "Programming"), ("Go", "Programming"), ("Leadership", "Soft"),
    ]
    skills = [(i, name, cat) for i, (name, cat) in enumerate(skill_data, 1)]
    conn.executemany("INSERT INTO skills VALUES (?, ?, ?)", skills)

    # employee_skills (40)
    levels = ["beginner", "intermediate", "advanced", "expert"]
    es_pairs = set()
    employee_skills = []
    pk = 1
    while len(employee_skills) < 40:
        emp_id = random.randint(1, 30)
        skill_id = random.randint(1, 15)
        if (emp_id, skill_id) not in es_pairs:
            es_pairs.add((emp_id, skill_id))
            employee_skills.append((pk, emp_id, skill_id, random.choice(levels)))
            pk += 1
    conn.executemany("INSERT INTO employee_skills VALUES (?, ?, ?, ?)", employee_skills)

    # clients (10)
    industries = ["Tech", "Finance", "Healthcare", "Retail", "Energy", "Education"]
    clients = [(i, fake.company(), random.choice(industries), fake.country()) for i in range(1, 11)]
    conn.executemany("INSERT INTO clients VALUES (?, ?, ?, ?)", clients)

    # contracts (12)
    contract_statuses = ["active", "completed", "negotiation", "cancelled"]
    contracts = [
        (i, fake.catch_phrase(), random.randint(10000, 500000),
         random.choice(contract_statuses), random.randint(1, 10), random.randint(1, 8))
        for i in range(1, 13)
    ]
    conn.executemany("INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?)", contracts)

    # projects (20)
    proj_statuses = ["active", "completed", "on_hold", "cancelled"]
    projects = [
        (i, fake.bs().title(), random.choice(proj_statuses),
         random.randint(1, 8), random.randint(1, 12))
        for i in range(1, 21)
    ]
    conn.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?)", projects)

    # project_members (35)
    pm_pairs = set()
    project_members = []
    pk = 1
    while len(project_members) < 35:
        emp_id = random.randint(1, 30)
        proj_id = random.randint(1, 20)
        if (emp_id, proj_id) not in pm_pairs:
            pm_pairs.add((emp_id, proj_id))
            project_members.append((pk, emp_id, proj_id))
            pk += 1
    conn.executemany("INSERT INTO project_members VALUES (?, ?, ?)", project_members)

    # tasks (25)
    priorities = ["low", "medium", "high", "critical"]
    task_statuses = ["todo", "in_progress", "review", "done"]
    tasks = [
        (i, fake.sentence(nb_words=5), random.choice(priorities),
         random.choice(task_statuses), random.randint(1, 20))
        for i in range(1, 26)
    ]
    conn.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", tasks)

    # task_assignments (30)
    ta_pairs = set()
    task_assignments = []
    pk = 1
    while len(task_assignments) < 30:
        task_id = random.randint(1, 25)
        emp_id = random.randint(1, 30)
        if (task_id, emp_id) not in ta_pairs:
            ta_pairs.add((task_id, emp_id))
            task_assignments.append((pk, task_id, emp_id))
            pk += 1
    conn.executemany("INSERT INTO task_assignments VALUES (?, ?, ?)", task_assignments)

    conn.commit()
    conn.close()

    counts = {
        "office_locations": len(offices),
        "departments":      len(departments),
        "employees":        len(employees),
        "skills":           len(skills),
        "employee_skills":  len(employee_skills),
        "clients":          len(clients),
        "contracts":        len(contracts),
        "projects":         len(projects),
        "project_members":  len(project_members),
        "tasks":            len(tasks),
        "task_assignments": len(task_assignments),
    }

    print("DB filled:")
    total = 0
    for table, count in counts.items():
        print(f"  {table:<20s} {count}")
        total += count
    print(f"  {'TOTAL NODES':<20s} {total}")
    return counts


if __name__ == "__main__":
    DB_PATH = "test.db"
    seed_database(DB_PATH)

    from nessie_api.models import Action, GraphType
    from nessie_relationaldb_datasource_plugin import relational_db_plugin

    p = relational_db_plugin()
    graph = p.handle(Action("load_graph", {
        "db_path": DB_PATH,
        "graph_type": GraphType.DIRECTED,
    }), None)

    print(f"\n{graph}")
    print(f"{'─' * 50}")

    from collections import defaultdict, Counter

    by_table = defaultdict(list)
    for node in graph.nodes:
        by_table[node["_table"]].append(node)

    for table, nodes in by_table.items():
        print(f"\n── {table.upper()} ({len(nodes)}) ──")
        for node in nodes[:3]:
            attrs = {k: v.value for k, v in node.attributes.items() if not k.startswith("_")}
            print(f"  {node.id:35s}  {attrs}")
        if len(nodes) > 3:
            print(f"  ... i jos {len(nodes) - 3} nodes")

    print(f"\n── EDGES ({len(graph.edges)}) ──")
    edge_by_relation = Counter(e["_relation"] for e in graph.edges)
    for relation, count in edge_by_relation.most_common():
        print(f"  {count:4d}x  {relation}")
