# 🚗 Vehicle Parking App

Welcome to the Vehicle Parking App! This is a Flask-based web application for managing parking lots, spots, and reserved vehicles for 4-wheelers. The app is built around two roles—**Admin** and **User**—and supports multi-user operations, secure parking spot allocation, and real-time status tracking.

---

## 📝 Project Statement

> **Modern Application Development I - Vehicle Parking App V1**

- **Purpose:** Manage different parking lots, parking spots, and parked vehicles for 4-wheeler parking.
- **Roles:**  
  - **Admin (Superuser):** Full system control, no registration required.
  - **User:** Can register/login and reserve/vacate parking spots.
- **Design:** Responsive web app using Flask (backend), Jinja2 + HTML/CSS/Bootstrap (frontend), and SQLite (programmatic DB creation).

---

## 🌟 Core Features

### 🚦 Admin Functionalities

- Login with predefined credentials (no registration needed; admin is created with the DB)
- Create, edit, and delete parking lots (delete only if all spots are empty)
- Define the number of spots for each lot; spots are created programmatically
- View and manage all parking lots, spots, and their statuses (Occupied/Available)
- View details of parked vehicles and registered users
- Dashboard summary charts for lots/spots (e.g., using Chart.js)
- Optional: Search for a specific parking spot and its status

### 🧑‍💼 User Functionalities

- Register and login
- View available parking lots and reserve an available spot (auto-assigned)
- Vacate/release spots, updating status in real time
- View personal parking history, parking durations, and costs
- Dashboard with summary charts of parking activity

---

## 🏗️ Tech Stack

- **Backend:** Flask
- **Frontend:** Jinja2 templating, HTML, CSS, Bootstrap
- **Database:** SQLite (created programmatically, no manual DB setup)
- **Charts:** Chart.js (or similar)
- **APIs:** Optional REST endpoints (Flask or Flask-RESTful)

---

## 🗂️ Database Models

- **User:** id, username, password, role (admin/user), etc.
- **Admin:** Superuser, exists on DB creation
- **ParkingLot:** id, prime_location_name, price, address, pin code, max_number_of_spots, etc.
- **ParkingSpot:** id, lot_id (FK), status (O/A), etc.
- **Reservation:** id, spot_id (FK), user_id (FK), parking_timestamp, leaving_timestamp, parking_cost, etc.

*All tables are created programmatically; no manual database editing is permitted.*

---

## 📋 Project Report

Read the detailed project report for system architecture, database schema, features, and milestones:

👉 [Project Report (Google Drive)](https://drive.google.com/file/d/1N3VbfZd8ZmmQOvfgGVvFelIN6BmAJ6Lo/view?usp=drive_link)

---

## 🎬 Project Demo Video

Watch the app in action:

👉 [Project Demo Video (Google Drive)](https://drive.google.com/file/d/1N8HT78i6gNe-MudNOAMmSCojCUHB-by/view?usp=sharing)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip

### Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/22f3001316/Vehicle-Parking-App-MAD-I-.git
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Navigate to the project directory:**
   ```bash
   cd Vehicle-Parking-App-MAD-I-
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   flask run
   ```

6. **Access the app:**  
   Open your web browser and go to `http://127.0.0.1:5000/`

---

## 📦 Project Structure

```
Vehicle-Parking-App-MAD-I-/
│
├── static/             # CSS, JS, images
├── templates/          # Jinja2 HTML templates
├── app.py              # Flask application entry point
├── models.py           # Database models and table creation
├── requirements.txt
└── README.md
```

---

## 🖥️ Screenshots

> *(Include screenshots here for a visual overview!)*

---

## 🔑 Admin Credentials

> Admin is created automatically when the database is initialized. Change default credentials in code as needed.

---

## 👥 Contributors

- [Harsh Kumar]

---

## 📄 License

This project is for educational purposes. For usage or distribution, please contact the repository owner.

---

Thank you for checking out the Vehicle Parking App! If you have any feedback, feel free to open an issue or submit a pull request.