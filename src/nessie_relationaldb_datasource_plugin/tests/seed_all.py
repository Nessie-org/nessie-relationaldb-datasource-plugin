"""
Generates 10 SQLite databases with different schemas into the data/ folder.
Run this once to populate all databases, then pass any db path to the plugin.

Usage:
    python seed_all.py
"""

import sqlite3
import random
import os
from faker import Faker

fake = Faker()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def db_path(name: str) -> str:
    return os.path.join(DATA_DIR, name)


# ─────────────────────────────────────────────
# 1. company.db — departments, employees, projects, tasks
# ─────────────────────────────────────────────
def seed_company():
    conn = sqlite3.connect(db_path("company.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS tasks;
        DROP TABLE IF EXISTS project_members;
        DROP TABLE IF EXISTS projects;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS departments;

        CREATE TABLE departments (
            id     INTEGER PRIMARY KEY,
            name   TEXT,
            budget INTEGER,
            city   TEXT
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
    """)
    depts = [(i, n, random.randint(50000,500000), fake.city())
             for i, n in enumerate(["Engineering","Marketing","Sales","HR","Finance","Design","DevOps","Research"], 1)]
    conn.executemany("INSERT INTO departments VALUES (?,?,?,?)", depts)

    emps = []
    for i in range(1, 41):
        emps.append((i, fake.name(), fake.email(), random.choice(["Engineer","Manager","Lead","Analyst"]),
                     random.randint(30000,120000), random.randint(1,8), None if i<=8 else random.randint(1,8)))
    conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?)", emps)

    projs = [(i, fake.bs().title(), random.choice(["active","completed","on_hold"]), random.randint(1,8))
             for i in range(1, 21)]
    conn.executemany("INSERT INTO projects VALUES (?,?,?,?)", projs)

    pms, seen = [], set()
    pk = 1
    while len(pms) < 40:
        e, p = random.randint(1,40), random.randint(1,20)
        if (e,p) not in seen:
            seen.add((e,p)); pms.append((pk,e,p)); pk+=1
    conn.executemany("INSERT INTO project_members VALUES (?,?,?)", pms)

    tasks = [(i, fake.sentence(4), random.choice(["low","medium","high","critical"]), random.randint(1,20))
             for i in range(1, 51)]
    conn.executemany("INSERT INTO tasks VALUES (?,?,?,?)", tasks)

    conn.commit(); conn.close()
    print(f"  company.db        depts={len(depts)} emps={len(emps)} projs={len(projs)} tasks={len(tasks)}")


# ─────────────────────────────────────────────
# 2. ecommerce.db — customers, products, orders, order_items, reviews
# ─────────────────────────────────────────────
def seed_ecommerce():
    conn = sqlite3.connect(db_path("ecommerce.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS reviews;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            email   TEXT,
            country TEXT,
            tier    TEXT
        );
        CREATE TABLE categories (
            id     INTEGER PRIMARY KEY,
            name   TEXT,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        );
        CREATE TABLE products (
            id          INTEGER PRIMARY KEY,
            name        TEXT,
            price       REAL,
            stock       INTEGER,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY,
            status      TEXT,
            total       REAL,
            customer_id INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        CREATE TABLE order_items (
            id         INTEGER PRIMARY KEY,
            quantity   INTEGER,
            unit_price REAL,
            order_id   INTEGER,
            product_id INTEGER,
            FOREIGN KEY (order_id)   REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE reviews (
            id          INTEGER PRIMARY KEY,
            rating      INTEGER,
            comment     TEXT,
            customer_id INTEGER,
            product_id  INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id)  REFERENCES products(id)
        );
    """)
    customers = [(i, fake.name(), fake.email(), fake.country(), random.choice(["bronze","silver","gold","platinum"]))
                 for i in range(1, 31)]
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    cats = [(1,"Electronics",None),(2,"Clothing",None),(3,"Books",None),(4,"Phones",1),
            (5,"Laptops",1),(6,"T-Shirts",2),(7,"Jackets",2),(8,"Fiction",3),(9,"Non-Fiction",3)]
    conn.executemany("INSERT INTO categories VALUES (?,?,?)", cats)

    products = [(i, fake.catch_phrase(), round(random.uniform(5,500),2), random.randint(0,200), random.randint(1,9))
                for i in range(1, 31)]
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

    orders = [(i, random.choice(["pending","shipped","delivered","cancelled"]),
               round(random.uniform(20,1000),2), random.randint(1,30)) for i in range(1, 41)]
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)

    items = [(i, random.randint(1,5), round(random.uniform(5,200),2), random.randint(1,40), random.randint(1,30))
             for i in range(1, 61)]
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

    reviews, seen = [], set()
    pk = 1
    while len(reviews) < 40:
        c, p = random.randint(1,30), random.randint(1,30)
        if (c,p) not in seen:
            seen.add((c,p)); reviews.append((pk, random.randint(1,5), fake.sentence(), c, p)); pk+=1
    conn.executemany("INSERT INTO reviews VALUES (?,?,?,?,?)", reviews)

    conn.commit(); conn.close()
    print(f"  ecommerce.db      customers={len(customers)} products={len(products)} orders={len(orders)} reviews={len(reviews)}")


# ─────────────────────────────────────────────
# 3. hospital.db — doctors, patients, wards, appointments, prescriptions
# ─────────────────────────────────────────────
def seed_hospital():
    conn = sqlite3.connect(db_path("hospital.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS prescriptions;
        DROP TABLE IF EXISTS appointments;
        DROP TABLE IF EXISTS patients;
        DROP TABLE IF EXISTS doctors;
        DROP TABLE IF EXISTS wards;

        CREATE TABLE wards (
            id       INTEGER PRIMARY KEY,
            name     TEXT,
            floor    INTEGER,
            capacity INTEGER
        );
        CREATE TABLE doctors (
            id          INTEGER PRIMARY KEY,
            name        TEXT,
            specialty   TEXT,
            ward_id     INTEGER,
            FOREIGN KEY (ward_id) REFERENCES wards(id)
        );
        CREATE TABLE patients (
            id         INTEGER PRIMARY KEY,
            name       TEXT,
            age        INTEGER,
            diagnosis  TEXT,
            ward_id    INTEGER,
            FOREIGN KEY (ward_id) REFERENCES wards(id)
        );
        CREATE TABLE appointments (
            id         INTEGER PRIMARY KEY,
            date       TEXT,
            status     TEXT,
            doctor_id  INTEGER,
            patient_id INTEGER,
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE prescriptions (
            id          INTEGER PRIMARY KEY,
            medication  TEXT,
            dosage      TEXT,
            patient_id  INTEGER,
            doctor_id   INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
        );
    """)
    wards = [(i, n, random.randint(1,6), random.randint(10,40))
             for i, n in enumerate(["Cardiology","Neurology","Oncology","Pediatrics","Emergency","Surgery"], 1)]
    conn.executemany("INSERT INTO wards VALUES (?,?,?,?)", wards)

    doctors = [(i, fake.name(), random.choice(["Cardiologist","Neurologist","Surgeon","Pediatrician","Oncologist"]),
                random.randint(1,6)) for i in range(1, 21)]
    conn.executemany("INSERT INTO doctors VALUES (?,?,?,?)", doctors)

    patients = [(i, fake.name(), random.randint(1,90),
                 random.choice(["Hypertension","Diabetes","Fracture","Fever","Cancer","Migraine"]),
                 random.randint(1,6)) for i in range(1, 41)]
    conn.executemany("INSERT INTO patients VALUES (?,?,?,?,?)", patients)

    appts = [(i, str(fake.date_between("-1y","today")), random.choice(["scheduled","completed","cancelled"]),
              random.randint(1,20), random.randint(1,40)) for i in range(1, 51)]
    conn.executemany("INSERT INTO appointments VALUES (?,?,?,?,?)", appts)

    prescriptions = [(i, fake.word().capitalize(), f"{random.randint(1,3)}x{random.randint(100,500)}mg",
                      random.randint(1,40), random.randint(1,20)) for i in range(1, 41)]
    conn.executemany("INSERT INTO prescriptions VALUES (?,?,?,?,?)", prescriptions)

    conn.commit(); conn.close()
    print(f"  hospital.db       wards={len(wards)} doctors={len(doctors)} patients={len(patients)} appts={len(appts)}")


# ─────────────────────────────────────────────
# 4. university.db — faculties, professors, students, courses, enrollments
# ─────────────────────────────────────────────
def seed_university():
    conn = sqlite3.connect(db_path("university.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS professors;
        DROP TABLE IF EXISTS faculties;

        CREATE TABLE faculties (
            id   INTEGER PRIMARY KEY,
            name TEXT,
            dean TEXT
        );
        CREATE TABLE professors (
            id         INTEGER PRIMARY KEY,
            name       TEXT,
            title      TEXT,
            faculty_id INTEGER,
            FOREIGN KEY (faculty_id) REFERENCES faculties(id)
        );
        CREATE TABLE students (
            id         INTEGER PRIMARY KEY,
            name       TEXT,
            email      TEXT,
            year       INTEGER,
            faculty_id INTEGER,
            FOREIGN KEY (faculty_id) REFERENCES faculties(id)
        );
        CREATE TABLE courses (
            id           INTEGER PRIMARY KEY,
            name         TEXT,
            credits      INTEGER,
            professor_id INTEGER,
            FOREIGN KEY (professor_id) REFERENCES professors(id)
        );
        CREATE TABLE enrollments (
            id         INTEGER PRIMARY KEY,
            grade      REAL,
            student_id INTEGER,
            course_id  INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_id)  REFERENCES courses(id)
        );
    """)
    faculties = [(i, n, fake.name()) for i, n in enumerate(
        ["Computer Science","Medicine","Law","Economics","Engineering","Arts"], 1)]
    conn.executemany("INSERT INTO faculties VALUES (?,?,?)", faculties)

    profs = [(i, fake.name(), random.choice(["PhD","MSc","Prof","Assoc.Prof"]), random.randint(1,6))
             for i in range(1, 21)]
    conn.executemany("INSERT INTO professors VALUES (?,?,?,?)", profs)

    students = [(i, fake.name(), fake.email(), random.randint(1,5), random.randint(1,6))
                for i in range(1, 41)]
    conn.executemany("INSERT INTO students VALUES (?,?,?,?,?)", students)

    courses = [(i, fake.catch_phrase(), random.randint(3,6), random.randint(1,20))
               for i in range(1, 26)]
    conn.executemany("INSERT INTO courses VALUES (?,?,?,?)", courses)

    enrollments, seen = [], set()
    pk = 1
    while len(enrollments) < 60:
        s, c = random.randint(1,40), random.randint(1,25)
        if (s,c) not in seen:
            seen.add((s,c)); enrollments.append((pk, round(random.uniform(5,10),1), s, c)); pk+=1
    conn.executemany("INSERT INTO enrollments VALUES (?,?,?,?)", enrollments)

    conn.commit(); conn.close()
    print(f"  university.db     faculties={len(faculties)} profs={len(profs)} students={len(students)} enrollments={len(enrollments)}")


# ─────────────────────────────────────────────
# 5. social_network.db — users, posts, comments, follows, likes
# ─────────────────────────────────────────────
def seed_social_network():
    conn = sqlite3.connect(db_path("social_network.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS likes;
        DROP TABLE IF EXISTS comments;
        DROP TABLE IF EXISTS follows;
        DROP TABLE IF EXISTS posts;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id       INTEGER PRIMARY KEY,
            username TEXT,
            email    TEXT,
            country  TEXT,
            verified INTEGER
        );
        CREATE TABLE posts (
            id      INTEGER PRIMARY KEY,
            content TEXT,
            topic   TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE follows (
            id          INTEGER PRIMARY KEY,
            follower_id INTEGER,
            followee_id INTEGER,
            FOREIGN KEY (follower_id) REFERENCES users(id),
            FOREIGN KEY (followee_id) REFERENCES users(id)
        );
        CREATE TABLE comments (
            id      INTEGER PRIMARY KEY,
            content TEXT,
            user_id INTEGER,
            post_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
        CREATE TABLE likes (
            id      INTEGER PRIMARY KEY,
            user_id INTEGER,
            post_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
    """)
    users = [(i, fake.user_name(), fake.email(), fake.country(), random.randint(0,1))
             for i in range(1, 31)]
    conn.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)

    posts = [(i, fake.sentence(), random.choice(["tech","sports","politics","music","travel"]), random.randint(1,30))
             for i in range(1, 41)]
    conn.executemany("INSERT INTO posts VALUES (?,?,?,?)", posts)

    follows, seen = [], set()
    pk = 1
    while len(follows) < 50:
        a, b = random.randint(1,30), random.randint(1,30)
        if a != b and (a,b) not in seen:
            seen.add((a,b)); follows.append((pk,a,b)); pk+=1
    conn.executemany("INSERT INTO follows VALUES (?,?,?)", follows)

    comments = [(i, fake.sentence(), random.randint(1,30), random.randint(1,40))
                for i in range(1, 41)]
    conn.executemany("INSERT INTO comments VALUES (?,?,?,?)", comments)

    likes, seen = [], set()
    pk = 1
    while len(likes) < 50:
        u, p = random.randint(1,30), random.randint(1,40)
        if (u,p) not in seen:
            seen.add((u,p)); likes.append((pk,u,p)); pk+=1
    conn.executemany("INSERT INTO likes VALUES (?,?,?)", likes)

    conn.commit(); conn.close()
    print(f"  social_network.db users={len(users)} posts={len(posts)} follows={len(follows)} comments={len(comments)}")


# ─────────────────────────────────────────────
# 6. library.db — authors, books, members, loans, genres
# ─────────────────────────────────────────────
def seed_library():
    conn = sqlite3.connect(db_path("library.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS loans;
        DROP TABLE IF EXISTS book_genres;
        DROP TABLE IF EXISTS genres;
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS authors;

        CREATE TABLE authors (
            id          INTEGER PRIMARY KEY,
            name        TEXT,
            nationality TEXT
        );
        CREATE TABLE genres (
            id   INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE books (
            id        INTEGER PRIMARY KEY,
            title     TEXT,
            year      INTEGER,
            copies    INTEGER,
            author_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors(id)
        );
        CREATE TABLE book_genres (
            id       INTEGER PRIMARY KEY,
            book_id  INTEGER,
            genre_id INTEGER,
            FOREIGN KEY (book_id)  REFERENCES books(id),
            FOREIGN KEY (genre_id) REFERENCES genres(id)
        );
        CREATE TABLE members (
            id    INTEGER PRIMARY KEY,
            name  TEXT,
            email TEXT,
            plan  TEXT
        );
        CREATE TABLE loans (
            id          INTEGER PRIMARY KEY,
            loaned_on   TEXT,
            returned_on TEXT,
            member_id   INTEGER,
            book_id     INTEGER,
            FOREIGN KEY (member_id) REFERENCES members(id),
            FOREIGN KEY (book_id)   REFERENCES books(id)
        );
    """)
    authors = [(i, fake.name(), fake.country()) for i in range(1, 21)]
    conn.executemany("INSERT INTO authors VALUES (?,?,?)", authors)

    genres = [(i, g) for i, g in enumerate(
        ["Fiction","Non-Fiction","Sci-Fi","Mystery","Biography","History","Fantasy","Romance"], 1)]
    conn.executemany("INSERT INTO genres VALUES (?,?)", genres)

    books = [(i, fake.sentence(4).rstrip("."), random.randint(1900,2024),
              random.randint(1,10), random.randint(1,20)) for i in range(1, 31)]
    conn.executemany("INSERT INTO books VALUES (?,?,?,?,?)", books)

    bg, seen = [], set()
    pk = 1
    while len(bg) < 40:
        b, g = random.randint(1,30), random.randint(1,8)
        if (b,g) not in seen:
            seen.add((b,g)); bg.append((pk,b,g)); pk+=1
    conn.executemany("INSERT INTO book_genres VALUES (?,?,?)", bg)

    members = [(i, fake.name(), fake.email(), random.choice(["basic","premium","student"]))
               for i in range(1, 26)]
    conn.executemany("INSERT INTO members VALUES (?,?,?,?)", members)

    loans = [(i, str(fake.date_between("-2y","-1d")), str(fake.date_between("-6m","today")) if random.random()>0.3 else None,
              random.randint(1,25), random.randint(1,30)) for i in range(1, 51)]
    conn.executemany("INSERT INTO loans VALUES (?,?,?,?,?)", loans)

    conn.commit(); conn.close()
    print(f"  library.db        authors={len(authors)} books={len(books)} members={len(members)} loans={len(loans)}")


# ─────────────────────────────────────────────
# 7. game.db — players, characters, guilds, quests, quest_completions
# ─────────────────────────────────────────────
def seed_game():
    conn = sqlite3.connect(db_path("game.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS quest_completions;
        DROP TABLE IF EXISTS quests;
        DROP TABLE IF EXISTS characters;
        DROP TABLE IF EXISTS players;
        DROP TABLE IF EXISTS guilds;

        CREATE TABLE guilds (
            id     INTEGER PRIMARY KEY,
            name   TEXT,
            level  INTEGER,
            server TEXT
        );
        CREATE TABLE players (
            id       INTEGER PRIMARY KEY,
            username TEXT,
            country  TEXT,
            guild_id INTEGER,
            FOREIGN KEY (guild_id) REFERENCES guilds(id)
        );
        CREATE TABLE characters (
            id        INTEGER PRIMARY KEY,
            name      TEXT,
            class     TEXT,
            level     INTEGER,
            player_id INTEGER,
            FOREIGN KEY (player_id) REFERENCES players(id)
        );
        CREATE TABLE quests (
            id         INTEGER PRIMARY KEY,
            name       TEXT,
            difficulty TEXT,
            reward_xp  INTEGER
        );
        CREATE TABLE quest_completions (
            id           INTEGER PRIMARY KEY,
            completed_at TEXT,
            character_id INTEGER,
            quest_id     INTEGER,
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (quest_id)     REFERENCES quests(id)
        );
    """)
    guilds = [(i, fake.company(), random.randint(1,50), random.choice(["EU","US","ASIA"]))
              for i in range(1, 11)]
    conn.executemany("INSERT INTO guilds VALUES (?,?,?,?)", guilds)

    players = [(i, fake.user_name(), fake.country(), random.randint(1,10))
               for i in range(1, 26)]
    conn.executemany("INSERT INTO players VALUES (?,?,?,?)", players)

    chars = [(i, fake.first_name(), random.choice(["Warrior","Mage","Rogue","Paladin","Archer"]),
              random.randint(1,60), random.randint(1,25)) for i in range(1, 36)]
    conn.executemany("INSERT INTO characters VALUES (?,?,?,?,?)", chars)

    quests = [(i, fake.bs().title(), random.choice(["easy","medium","hard","epic"]),
               random.randint(100,5000)) for i in range(1, 26)]
    conn.executemany("INSERT INTO quests VALUES (?,?,?,?)", quests)

    completions, seen = [], set()
    pk = 1
    while len(completions) < 60:
        c, q = random.randint(1,35), random.randint(1,25)
        if (c,q) not in seen:
            seen.add((c,q)); completions.append((pk, str(fake.date_between("-1y","today")), c, q)); pk+=1
    conn.executemany("INSERT INTO quest_completions VALUES (?,?,?,?)", completions)

    conn.commit(); conn.close()
    print(f"  game.db           guilds={len(guilds)} players={len(players)} chars={len(chars)} completions={len(completions)}")


# ─────────────────────────────────────────────
# 8. logistics.db — warehouses, vehicles, drivers, shipments, shipment_items
# ─────────────────────────────────────────────
def seed_logistics():
    conn = sqlite3.connect(db_path("logistics.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS shipment_items;
        DROP TABLE IF EXISTS shipments;
        DROP TABLE IF EXISTS drivers;
        DROP TABLE IF EXISTS vehicles;
        DROP TABLE IF EXISTS warehouses;

        CREATE TABLE warehouses (
            id       INTEGER PRIMARY KEY,
            city     TEXT,
            country  TEXT,
            capacity INTEGER
        );
        CREATE TABLE vehicles (
            id           INTEGER PRIMARY KEY,
            plate        TEXT,
            type         TEXT,
            max_load_kg  INTEGER
        );
        CREATE TABLE drivers (
            id         INTEGER PRIMARY KEY,
            name       TEXT,
            license    TEXT,
            vehicle_id INTEGER,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
        CREATE TABLE shipments (
            id               INTEGER PRIMARY KEY,
            status           TEXT,
            origin_id        INTEGER,
            destination_id   INTEGER,
            driver_id        INTEGER,
            FOREIGN KEY (origin_id)      REFERENCES warehouses(id),
            FOREIGN KEY (destination_id) REFERENCES warehouses(id),
            FOREIGN KEY (driver_id)      REFERENCES drivers(id)
        );
        CREATE TABLE shipment_items (
            id          INTEGER PRIMARY KEY,
            description TEXT,
            weight_kg   REAL,
            shipment_id INTEGER,
            FOREIGN KEY (shipment_id) REFERENCES shipments(id)
        );
    """)
    warehouses = [(i, fake.city(), fake.country(), random.randint(500,5000))
                  for i in range(1, 11)]
    conn.executemany("INSERT INTO warehouses VALUES (?,?,?,?)", warehouses)

    vehicles = [(i, fake.license_plate(), random.choice(["truck","van","motorcycle"]), random.randint(500,20000))
                for i in range(1, 16)]
    conn.executemany("INSERT INTO vehicles VALUES (?,?,?,?)", vehicles)

    drivers = [(i, fake.name(), fake.bothify("??-###-??"), random.randint(1,15))
               for i in range(1, 21)]
    conn.executemany("INSERT INTO drivers VALUES (?,?,?,?)", drivers)

    shipments = []
    for i in range(1, 36):
        o, d = random.sample(range(1,11), 2)
        shipments.append((i, random.choice(["pending","in_transit","delivered","failed"]), o, d, random.randint(1,20)))
    conn.executemany("INSERT INTO shipments VALUES (?,?,?,?,?)", shipments)

    items = [(i, fake.word(), round(random.uniform(1,500),1), random.randint(1,35))
             for i in range(1, 61)]
    conn.executemany("INSERT INTO shipment_items VALUES (?,?,?,?)", items)

    conn.commit(); conn.close()
    print(f"  logistics.db      warehouses={len(warehouses)} vehicles={len(vehicles)} drivers={len(drivers)} shipments={len(shipments)}")


# ─────────────────────────────────────────────
# 9. music.db — artists, albums, tracks, playlists, playlist_tracks
# ─────────────────────────────────────────────
def seed_music():
    conn = sqlite3.connect(db_path("music.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS playlist_tracks;
        DROP TABLE IF EXISTS playlists;
        DROP TABLE IF EXISTS tracks;
        DROP TABLE IF EXISTS albums;
        DROP TABLE IF EXISTS artists;

        CREATE TABLE artists (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            genre   TEXT,
            country TEXT
        );
        CREATE TABLE albums (
            id        INTEGER PRIMARY KEY,
            title     TEXT,
            year      INTEGER,
            artist_id INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        );
        CREATE TABLE tracks (
            id         INTEGER PRIMARY KEY,
            title      TEXT,
            duration_s INTEGER,
            album_id   INTEGER,
            FOREIGN KEY (album_id) REFERENCES albums(id)
        );
        CREATE TABLE playlists (
            id    INTEGER PRIMARY KEY,
            name  TEXT,
            owner TEXT
        );
        CREATE TABLE playlist_tracks (
            id          INTEGER PRIMARY KEY,
            position    INTEGER,
            playlist_id INTEGER,
            track_id    INTEGER,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id),
            FOREIGN KEY (track_id)    REFERENCES tracks(id)
        );
    """)
    artists = [(i, fake.name(), random.choice(["Rock","Pop","Jazz","Hip-Hop","Classical","Electronic"]),
                fake.country()) for i in range(1, 16)]
    conn.executemany("INSERT INTO artists VALUES (?,?,?,?)", artists)

    albums = [(i, fake.sentence(3).rstrip("."), random.randint(1970,2024), random.randint(1,15))
              for i in range(1, 26)]
    conn.executemany("INSERT INTO albums VALUES (?,?,?,?)", albums)

    tracks = [(i, fake.sentence(3).rstrip("."), random.randint(120,420), random.randint(1,25))
              for i in range(1, 51)]
    conn.executemany("INSERT INTO tracks VALUES (?,?,?,?)", tracks)

    playlists = [(i, fake.catch_phrase(), fake.user_name()) for i in range(1, 11)]
    conn.executemany("INSERT INTO playlists VALUES (?,?,?)", playlists)

    pt, seen = [], set()
    pk = 1
    while len(pt) < 60:
        pl, t = random.randint(1,10), random.randint(1,50)
        if (pl,t) not in seen:
            seen.add((pl,t)); pt.append((pk, len([x for x in pt if x[2]==pl])+1, pl, t)); pk+=1
    conn.executemany("INSERT INTO playlist_tracks VALUES (?,?,?,?)", pt)

    conn.commit(); conn.close()
    print(f"  music.db          artists={len(artists)} albums={len(albums)} tracks={len(tracks)} playlist_tracks={len(pt)}")


# ─────────────────────────────────────────────
# 10. real_estate.db — agents, properties, buyers, listings, offers
# ─────────────────────────────────────────────
def seed_real_estate():
    conn = sqlite3.connect(db_path("real_estate.db"))
    conn.executescript("""
        DROP TABLE IF EXISTS offers;
        DROP TABLE IF EXISTS listings;
        DROP TABLE IF EXISTS properties;
        DROP TABLE IF EXISTS buyers;
        DROP TABLE IF EXISTS agents;

        CREATE TABLE agents (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            email   TEXT,
            agency  TEXT,
            city    TEXT
        );
        CREATE TABLE buyers (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            email   TEXT,
            budget  INTEGER
        );
        CREATE TABLE properties (
            id        INTEGER PRIMARY KEY,
            address   TEXT,
            city      TEXT,
            type      TEXT,
            area_sqm  INTEGER,
            agent_id  INTEGER,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        );
        CREATE TABLE listings (
            id          INTEGER PRIMARY KEY,
            price       INTEGER,
            status      TEXT,
            property_id INTEGER,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        );
        CREATE TABLE offers (
            id         INTEGER PRIMARY KEY,
            amount     INTEGER,
            status     TEXT,
            buyer_id   INTEGER,
            listing_id INTEGER,
            FOREIGN KEY (buyer_id)   REFERENCES buyers(id),
            FOREIGN KEY (listing_id) REFERENCES listings(id)
        );
    """)
    agents = [(i, fake.name(), fake.email(), fake.company(), fake.city()) for i in range(1, 16)]
    conn.executemany("INSERT INTO agents VALUES (?,?,?,?,?)", agents)

    buyers = [(i, fake.name(), fake.email(), random.randint(50000,2000000)) for i in range(1, 26)]
    conn.executemany("INSERT INTO buyers VALUES (?,?,?,?)", buyers)

    properties = [(i, fake.street_address(), fake.city(),
                   random.choice(["apartment","house","office","land"]),
                   random.randint(30,500), random.randint(1,15)) for i in range(1, 36)]
    conn.executemany("INSERT INTO properties VALUES (?,?,?,?,?,?)", properties)

    listings = [(i, random.randint(50000,1500000),
                 random.choice(["active","sold","withdrawn"]), random.randint(1,35))
                for i in range(1, 36)]
    conn.executemany("INSERT INTO listings VALUES (?,?,?,?)", listings)

    offers = [(i, random.randint(40000,1500000),
               random.choice(["pending","accepted","rejected"]),
               random.randint(1,25), random.randint(1,35)) for i in range(1, 41)]
    conn.executemany("INSERT INTO offers VALUES (?,?,?,?,?)", offers)

    conn.commit(); conn.close()
    print(f"  real_estate.db    agents={len(agents)} properties={len(properties)} listings={len(listings)} offers={len(offers)}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generating databases in: {DATA_DIR}\n")
    seed_company()
    seed_ecommerce()
    seed_hospital()
    seed_university()
    seed_social_network()
    seed_library()
    seed_game()
    seed_logistics()
    seed_music()
    seed_real_estate()
    print(f"\nDone. Files in {DATA_DIR}:")
    for f in sorted(os.listdir(DATA_DIR)):
        size = os.path.getsize(os.path.join(DATA_DIR, f))
        print(f"  {f:<25s}  {size/1024:.1f} KB")
