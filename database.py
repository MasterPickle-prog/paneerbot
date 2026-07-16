import aiosqlite

DATABASE = "paneer.db"

PANEER_COLUMNS = {
    "Normal Paneer": "normal",
    "Large Paneer": "large",
    "Butter Paneer": "butter",
    "Cheese Paneer": "cheese",
    "Chili Paneer": "chili",
    "Palak Paneer": "palak"
}

async def init():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,

            normal INTEGER DEFAULT 0,
            large INTEGER DEFAULT 0,
            butter INTEGER DEFAULT 0,
            cheese INTEGER DEFAULT 0,
            chili INTEGER DEFAULT 0,
            palak INTEGER DEFAULT 0,

            last_daily TEXT,
            daily_streak INTEGER DEFAULT 0,
            last_steal TEXT,

            achievements TEXT DEFAULT ''
        )
        """)
        await db.commit()


async def ensure_user(user_id):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO users(
                id,
                normal,
                large,
                butter,
                cheese,
                chili,
                palak,
                last_daily,
                daily_streak,
                last_steal,
                achievements
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                0,
                0,
                0,
                0,
                0,
                0,
                None,
                0,
                None,
                ""
            )
        )

        await db.commit()


async def get_daily(user_id):
    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute(
            "SELECT last_daily FROM users WHERE id=?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row[0]


async def set_daily(user_id, date):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET last_daily=? WHERE id=?",
            (date,user_id)
        )
        await db.commit()


async def leaderboard():
    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute("""
        SELECT
        id,
        (
        normal * 1 +
        large * 5 +
        butter * 10 +
        cheese * 25 +
        chili * 75 +
        palak * 250
        ) AS points

        FROM users

        ORDER BY points DESC
        """)
        return await cur.fetchall()

async def get_steal(user_id):
    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute(
            "SELECT last_steal FROM users WHERE id=?",
            (user_id,)
        )

        row = await cur.fetchone()
        return row[0]


async def set_steal(user_id, time):
    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET last_steal=? WHERE id=?",
            (time, user_id)
        )
        await db.commit()

async def get_streak(user_id):

    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute(
            "SELECT daily_streak FROM users WHERE id=?",
            (user_id,)
        )

        row = await cur.fetchone()

        return row[0]



async def set_streak(user_id, streak):

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET daily_streak=? WHERE id=?",
            (streak,user_id)
        )

        await db.commit()



async def get_achievements(user_id):

    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:

        cur = await db.execute(
            "SELECT achievements FROM users WHERE id=?",
            (user_id,)
        )

        row = await cur.fetchone()

        if row[0]:
            return row[0].split(",")

        return []



async def add_achievement(user_id, achievement):

    achievements = await get_achievements(user_id)

    if achievement in achievements:
        return False


    achievements.append(achievement)


    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            "UPDATE users SET achievements=? WHERE id=?",
            (
                ",".join(achievements),
                user_id
            )
        )

        await db.commit()

    return True

async def add_paneer_type(user_id, paneer_type, amount=1):

    await ensure_user(user_id)

    columns = {
        "Normal Paneer":"normal",
        "Large Paneer":"large",
        "Butter Paneer":"butter",
        "Cheese Paneer":"cheese",
        "Chili Paneer":"chili",
        "Palak Paneer":"palak"
    }


    column = columns[paneer_type]


    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            f"""
            UPDATE users
            SET {column} = {column} + ?
            WHERE id=?
            """,
            (amount,user_id)
        )

        await db.commit()



async def get_inventory(user_id):

    await ensure_user(user_id)

    async with aiosqlite.connect(DATABASE) as db:

        cur = await db.execute(
            """
            SELECT normal,large,butter,cheese,chili,palak
            FROM users
            WHERE id=?
            """,
            (user_id,)
        )

        return await cur.fetchone()


async def get_points(user_id):

    inventory = await get_inventory(user_id)

    values = [
        1,
        5,
        10,
        25,
        75,
        250
    ]

    return sum(
        inventory[i] * values[i]
        for i in range(6)
    )

async def remove_paneer_type(user_id, paneer_type, amount):

    column = PANEER_COLUMNS[paneer_type]

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            f"""
            UPDATE users
            SET {column} = MAX({column} - ?, 0)
            WHERE id=?
            """,
            (amount,user_id)
        )

        await db.commit()



async def set_paneer_type(user_id, paneer_type, amount):

    await ensure_user(user_id)

    column = PANEER_COLUMNS[paneer_type]

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            f"""
            UPDATE users
            SET {column}=?
            WHERE id=?
            """,
            (amount,user_id)
        )

        await db.commit()