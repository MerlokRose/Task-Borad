# Task Board (Full-Stack Kanban)

My first complete Full-Stack project — an interactive Kanban board for task management. Built from scratch to master the entire web development cycle: from frontend logic to REST API, database design, and cloud deployment.

## 🔗 Live Links
* **Live Demo (Frontend):** [https://merloktask-board.netlify.app/](https://merloktask-board.netlify.app/)
* **API Endpoint (Backend):** [https://task-borad.onrender.com](https://task-borad.onrender.com)

*(Note: The backend is hosted on Render's free tier. The first request after a period of inactivity may take 30–50 seconds to "wake up" the server).*

## ✨ Features
* **Authentication:** User registration and login. Passwords are securely hashed before being saved to the database.
* **Data Privacy:** Each user has their own isolated board (session-based authentication via HTTP-only cookies).
* **CRUD Operations:** Create, read, update (saves on blur), and delete tasks.
* **Drag & Drop:** Move tasks between columns with instant database synchronization and a visual drop indicator.
* **Design:** Dark Cyberpunk theme, custom scrollbars, modal windows, and a responsive layout for mobile devices.

## 🛠️ Tech Stack
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API, Drag & Drop API).
* **Backend:** Python 3, Flask, Flask-CORS, Werkzeug.
* **Database:** PostgreSQL (Cloud hosted on Neon).
* **Security:** Password hashing, Session management, CORS configuration, SQL Injection protection (parameterized queries).
* **Deployment:** Netlify (Frontend) + Render (Backend).

## 🚀 How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Task-Borad.git

2. Navigate to the project directory and install dependencies:
   pip install -r requirements.txt

3. Create a .env file in the root directory and add your environment variables:
   SECRET_KEY='your_super_secret_key_here'
  DATABASE_URL='your_postgresql_connection_string'

4. Start the Flask server:
   python server.py

5. Open index.html in your browser.
  (Note: For local development, you might need to change the API URLs in script.js back to http://127.0.0.1:5000).
