<div align="center">
  <img src="richland_inventory/static/images/readme_header.png" alt="Rich Land Auto Supply Logo" width="800" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</div>

<br>

> A full-featured **integrated operations system** for auto parts businesses, built with **Python**, **Django**, and **Bootstrap 5**. Track products, manage stock-in/stock-out transactions, view edit history, and generate PDF/CSV reports—all in one application.

Render Deployment Link: https://rich-land-ios.onrender.com/accounts/login/
---

##  Team Members

| Name                      | GitHub Profile                                      |
|--------------------------|-----------------------------------------------------|
| Jhoram Narsico           | [github.com/jhoramnarsico](https://github.com/jhoramnarsico) |
| Joseph Ernest Alberto    | [github.com/Jepoyskies](https://github.com/Jepoyskies) |
| Jillian Athea Boc        | [github.com/Jillian-Athea](https://github.com/Jillian-Athea) |



---

##  Key Features

-  **Full CRUD** operations for products and categories  
-  **Stock tracking** with stock-in and stock-out transactions  
-  **Audit trail** for every product change (who changed what & when)  
-  **Export reports** as **PDF** (`xhtml2pdf`) or **CSV**  
-  **Responsive UI** with **Bootstrap 5**  
-  **RESTful API** with **Django REST Framework**  
-  **Interactive API docs** via **Swagger UI** (`drf-spectacular`)  
-  **Role-based access** and secure admin panel

---

## Technology Stack

### Backend
- **Language**: Python 3.8+  
- **Framework**: Django  
- **Database**: MySQL  
- **API**: Django REST Framework (DRF)

### Libraries
- `django-simple-history` → Audit logs  
- `drf-spectacular` → OpenAPI 3.0 documentation  
- `xhtml2pdf` → PDF report generation  
- `python-decouple` → Secure `.env` management  
- `PyMySQL` → MySQL database driver

### Frontend
- **Templates**: Django HTML  
- **Styling**: Bootstrap 5  
- **Interactivity**: Vanilla JavaScript + Bootstrap JS


### 1. Clone the Repository

Open your terminal or command prompt and clone the project from its GitHub repository.

```bash
# Replace <your-repository-url> with the actual URL from GitHub
git clone <your-repository-url>

# Navigate into the project directory
cd richland_inventory

```
### 2. Create and Activate a Virtual Environment
Using a virtual environment is highly recommended to isolate project dependencies.

```bash

# Step 1: Create the virtual environment
python -m venv venv
```

```bash
# Step 2: Activate the virtual environment using PowerShell
.\venv\Scripts\activate

```
```bash
#IF there is an error activating the virtual environment, input this
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
### 3. Install Required Packages

```bash
pip install -r requirements.txt

```
### 4. Set Up the MySQL Database

```bash
# Create a new database. We recommend using utf8mb4 for full Unicode support.
CREATE DATABASE richland_inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

#Create a new user and grant it privileges on the new database. Replace 'your_password' with a secure password.
CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON richland_inventory_db.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;

```
### 5. Creating a .env file.
In the same directory as your manage.py file (the root of your project), create a new file named .env.
```bash
# .env
# SECURITY WARNING: keep the secret key used in production secret!
# SECURITY WARNING: Generate your own secret key for production
SECRET_KEY='django-insecure-your-own-secret-key'

# Set to False in production!
DEBUG=True

# In production, set this to your domain names e.g., 'www.yourdomain.com,yourdomain.com'
ALLOWED_HOSTS='127.0.0.1,localhost'

# -- Database Configuration --
DB_NAME='richland_inventory_db'
DB_USER='your_mysql_username'
DB_PASSWORD='your_mysql_password'
DB_HOST='localhost'
DB_PORT='3306'

```

### 6. Apply Database Migrations
   
 ```bash
python manage.py makemigrations

python manage.py migrate

### 7. Create an Administrator Account

 ```bash
python manage.py createsuperuser
```

### 8. Start the Django Web Server

 ```bash
python manage.py runserver

```
### Testing the Application
 ```bash
python manage.py test inventory
```

 ```bash
python manage.py flush
```

 ```bash
python manage.py seed_data
```
## Running with Docker (Milestone 2)

Utilizing Docker ensures environment parity and simplifies the setup of the MySQL database and Python dependencies.

1.  **Build and Start the Containers**
    This command builds the Django image and starts both the web and database services.
    ```bash
    docker-compose up --build
    ```

2.  **Initialize the Database**
    Once the containers are running, execute the migrations:
    ```bash
    docker-compose exec web python richland_inventory/manage.py migrate
        ```

3.  **Seed the Database (Optional)**
    Populate the system with comprehensive initial test data:
    ```bash
    docker-compose exec web python richland_inventory/manage.py seed_data
    ```

4.  **Delete Database**
    To completely remove the database and start fresh (this wipes the persistent volume):
    ```bash
    docker-compose down -v
    ```

5.  **Restart Service (If you pull latest commit)**
    Restart the services to pick up local code changes:
    ```bash
    docker-compose up
    ```
(NOTED: You only need to run migrations when your database schema is out of sync with your Django models.)
