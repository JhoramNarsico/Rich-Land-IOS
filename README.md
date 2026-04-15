# Richland Inventory System

A comprehensive inventory management application built with Django and MySQL, designed for robust tracking and audit logging.

## Core Features

*   **Product Tracking:** Manage product stock, details, and history.
*   **Audit Logging:** Automatic tracking of all product edits via `django-simple-history`.
*   **Strictly Offline & Local:** The system is hardcoded to run on `127.0.0.1`, ensuring student data privacy by preventing any network or internet access.
*   **Relational Data Management:** Full CRUD (Create, Read, Update, Delete) functionality for managing students, teachers, sections, subjects, and their relationships.

## Tech Stack

*   **Backend:** Python 3.10+, Django
-   **Language:** Python 3.12 (Required)
*   **Database:** MySQL 8.0
*   **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript

---

## Getting Started

Follow these instructions to set up and run the project on your local machine for development and testing purposes.

### Prerequisites

You must have the following software installed on your machine:
*   [Python 3.12+](https://www.python.org/downloads/)
*   [Git](https://git-scm.com/downloads/)
*   [XAMPP](https://www.apachefriends.org/index.html) (or another local MySQL server environment)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/Rich-Land-IOS.git
    cd your-repo-name
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # Create the virtual environment folder
    python -m venv venv

    # Activate it:
    # Windows:
    venv\Scripts\activate
    # Unix/macOS:
    source venv/bin/activate
    ```

3.  **Install Project Dependencies**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Set Up the Local MySQL Database**
    > **Important:** This application requires a local MySQL database to run.

    a. Open your XAMPP Control Panel and start the **MySQL** module.
    b. Open your web browser and navigate to `http://localhost/phpmyadmin/`.
    c. Create a new, empty database with the exact name: `richland_db`

5.  **Configure Database Connection**
    a. Open the `richland_inventory/settings.py` file.
    b. Scroll down to the `DATABASES` section.
    c. Update the `USER`, `PASSWORD`, and `NAME` to match your local setup.

6.  **Build the Database Tables**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Create Your Admin Account**
    ```bash
    python manage.py createsuperuser
    ```

---

## Running the Application

You can run the system in two ways:

#### 1. Running the Local Server
```bash
python manage.py runserver
```

---
## Running with Docker

Utilizing Docker simplifies the setup of the MySQL database and Python dependencies.

1.  **Build and Start the Containers**  
    This command builds the Django image and starts both the web and database services.
    ```bash
    docker-compose up --build
    ```

2.  **Create Your Admin Account**  
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

3.  **Seeding Data**  
    ```bash
    docker-compose exec web python manage.py seed_data
    ```

4.  **Access the System**  
    Open your browser and navigate to `http://localhost:8000`.

---

## Maintenance

### Audit Log Rotation
To prevent the history tables from growing too large, use the built-in rotation command. This deletes product edit history older than a specific number of days (default is 365).

```bash
# Keep the last 90 days of history
python manage.py rotate_audit_log --days 90

# Running via Docker
docker-compose exec web python manage.py rotate_audit_log --days 90
```