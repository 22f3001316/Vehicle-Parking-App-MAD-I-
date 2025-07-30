# Vehicle-Parking-App-MAD-I-
This project is a web dev **Vehicle Parking System**  ParkIt designed to manage and automate vehicle parking operations. It supports both **Admin** and **User** functionalities including parking lot creation, slot booking, and historical tracking.

#  Vehicle Parking App - MAD-I Project

A multi-user parking management system built using **Flask**, **SQLite**, and **Bootstrap** for **Modern Application Development I**.

This app is designed to manage vehicle parking lots, track reservations, automate spot allocation, and streamline user/admin operations. It is focused on managing **4-wheeler parking** with features for both **Users** and **Admins**.

---

## 📚 Table of Contents

- [🧩 Features](#-features)
- [🛠️ Tech Stack](#-tech-stack)
- [🏗️ Milestones](#-milestones)
- [🚀 Installation & Setup](#-installation--setup)
- [▶️ How to Run](#️-how-to-run)
- [📸 Screenshots](#-screenshots)
- [📁 Project Structure](#-project-structure)
- [📌 Notes](#-notes)
- [🧑‍💻 Contributors](#-contributors)

---

## 🧩 Features

### 👤 User Features
- User registration & login
- View available parking lots
- Auto-allocation of first available parking spot
- Occupy & Release spot with time tracking
- View personal parking history & cost summary

### 🔐 Admin Features
- Admin login (predefined)
- Create/Edit/Delete parking lots
- Automatic parking spot creation based on capacity
- View user details and current parking status
- View all reservations and summaries
- Search users, spots, lots

### 📊 Optional Enhancements
- Search functionality for admin dashboard
- REST APIs for parking lot/spot/reservation
- Data visualization with Chart.js
- Frontend + Backend validation
- Responsive UI with Bootstrap
- Flask-Login integration for security

---

## 🛠️ Tech Stack

| Layer         | Technology       |
|---------------|------------------|
| Backend       | Flask            |
| Frontend      | HTML5, CSS3, Bootstrap, Jinja2 |
| Database      | SQLite (programmatically generated) |
| Charts        | Chart.js (optional) |
| Security      | Flask-Login or Flask-Security (recommended) |

---

How to run this app in Vs code 

python -m venv venv

venv\Scripts\activate

cd  Vehicle-Parking-App-MAD-I-


pip install -r requirements.txt


flask run