from flask import Flask, render_template, request, redirect, session, url_for
from PIL import Image, ImageDraw, ImageFont
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

BADGE_FOLDER = "static/badges"

# ---------- DATABASE SETUP ----------
def create_user_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

create_user_table()

# ---------- USER AUTH ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return "Username already exists!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect("/")
        else:
            return "Invalid username or password!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- BADGE HOMEPAGE ----------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")


# ---------- BADGE GENERATION ----------
# KEEP YOUR EXISTING BADGE GENERATOR CODE HERE!
# (Use the working code I gave earlier)
# ------------------------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    # Your badge-generation code (same as previous working version)
    return "Generated!"


if __name__ == "__main__":
    app.run(debug=True)


if not os.path.exists(BADGE_FOLDER):
    os.makedirs(BADGE_FOLDER)

# Clear old badges
for file in os.listdir(BADGE_FOLDER):
    os.remove(os.path.join(BADGE_FOLDER, file))

# Progress mapping
PROGRESS_MAP = {
    "beginner": 0.3,
    "intermediate": 0.6,
    "expert": 1.0
}

# Colors
COLOR_OPTIONS = {
    "blue": (30, 144, 255),
    "green": (34, 139, 34),
    "orange": (255, 140, 0),
    "purple": (138, 43, 226)
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    skills_input = request.form["skills"]
    skills = [s.strip() for s in skills_input.split(",")]

    shape = request.form.get("shape", "rectangle")
    color_choice = request.form.get("color", "blue")
    size_choice = request.form.get("size", "medium")

    # Badge size
    if size_choice == "small":
        width, height = 200, 60
    elif size_choice == "large":
        width, height = 300, 100
    else:
        width, height = 250, 80

    bg_color = COLOR_OPTIONS.get(color_choice, (30, 144, 255))
    badge_paths = []
    font = ImageFont.load_default()

    for idx, entry in enumerate(skills):

        # Skill:Level
        if ":" in entry:
            skill, level = entry.split(":")
            level = level.strip().lower()
        else:
            skill = entry
            level = ""
        skill = skill.strip()

        # SHAPES
        if shape == "circle":
            # Circle must be square
            size = max(width, height)
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # transparent
            draw = ImageDraw.Draw(img)
            draw.ellipse([0, 0, size - 1, size - 1], fill=bg_color + (255,))

        else:
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            if shape == "rounded":
                radius = int(min(width, height) * 0.25)
                draw.rounded_rectangle(
                    [0, 0, width - 1, height - 1],
                    radius=radius,
                    fill=bg_color + (255,)
                )
            else:
                # rectangle
                draw.rectangle(
                    [0, 0, width - 1, height - 1],
                    fill=bg_color + (255,)
                )

        # TEXT POSITION
        bbox = draw.textbbox((0, 0), skill, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if shape == "circle":
            offset_x = (size - text_width) / 2
            offset_y = (size - text_height) / 2
            draw.text((offset_x, offset_y), skill.upper(), fill=(255, 255, 255), font=font)

        else:
            offset_x = (width - text_width) / 2
            offset_y = (height - text_height) / 2 - 5
            draw.text((offset_x, offset_y), skill.upper(), fill=(255, 255, 255), font=font)

            # PROGRESS BAR (rectangular only)
            if level in PROGRESS_MAP:
                progress_ratio = PROGRESS_MAP[level]
                bar_width = int((width - 20) * progress_ratio)
                bar_height = int(height * 0.12)

                bar_x = 10
                bar_y = height - bar_height - 5

                # background bar
                draw.rectangle([bar_x, bar_y, width - 10, bar_y + bar_height], fill=(169, 169, 169, 255))
                # progress
                draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(255, 255, 255, 255))

        # Save badge
        path = f"{BADGE_FOLDER}/{skill}_{idx}.png"
        img.save(path)
        badge_paths.append(path)

    return render_template("index.html", badges=badge_paths)

if __name__ == "__main__":
    app.run(debug=True)
