# BlogApp

A production-inspired blog backend built with **FastAPI**, following clean architecture principles and modern backend development practices. The project provides secure authentication, blog management, image uploads, password recovery, caching, and a modular storage layer designed to support multiple cloud providers.

---

## ✨ Features

- 🔐 JWT Authentication & Authorization
- 👤 User Registration & Profile Management
- 📝 CRUD Operations for Blog Posts
- 🖼️ Profile & Post Image Uploads
- 📧 Password Reset via Email
- 📄 Pagination for Posts
- ⚡ Redis Caching
- 📦 Provider-Agnostic Object Storage
- 🐳 Docker Support
- 📚 OpenAPI (Swagger) Documentation

---

## 🏗️ Architecture

The project follows a layered architecture with clear separation of concerns.

```
app/
│
├── api/
├── config.py
├── db/
├── dependencies/
├── models/
├── providers/
│   └── storage/
├── repositories/
├── schemas/
├── services/
├── uow/
└── utils/
```

### Design Patterns

- Repository Pattern
- Unit of Work Pattern
- Service Layer
- Factory Pattern
- Dependency Injection

---

## 🛠️ Tech Stack

### Backend

- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Pydantic
- Alembic

### Authentication

- OAuth2 Password Flow
- JWT Tokens
- Password Hashing (bcrypt)

### Storage

- Pluggable Storage Provider Architecture
- AWS S3
- Backblaze B2
- MinIO
- Easily extendable to Cloudinary or other providers

### Caching

- Redis

### Email

- SMTP Password Reset Emails

### Image Processing

- Pillow

### Containerization

- Docker
- Docker Compose

---

## 🚀 Key Features

### Authentication

- User Registration
- Login
- JWT Access Tokens
- Password Change
- Forgot Password
- Password Reset via Email

---

### User Management

- Update Profile
- Upload Profile Picture
- Delete Profile Picture
- User-specific Posts

---

### Blog Posts

- Create Posts
- Update Posts
- Delete Posts
- Pagination
- Author Information
- Image Upload Support

---

### Object Storage

The application uses a provider abstraction for object storage.

```
StorageProvider
        │
        ▼
S3StorageProvider
        │
        ├── AWS S3
        ├── Backblaze B2
        └── MinIO
```

Adding a new provider only requires implementing the `StorageProvider` interface and registering it in the storage factory.

---

## 📦 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/blogapp.git

cd blogapp
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Linux/macOS

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=

SECRET_KEY=

ACCESS_TOKEN_EXPIRE_MINUTES=30

STORAGE_PROVIDER=s3

S3_BUCKET_NAME=

S3_REGION=

S3_ACCESS_KEY_ID=

S3_SECRET_ACCESS_KEY=

S3_ENDPOINT_URL=

REDIS_HOST=

REDIS_PORT=
```

---

## 🐳 Running with Docker

```bash
docker compose up --build
```

---

## ▶️ Running Locally

```bash
uvicorn app.main:app --reload
```

---

## 📖 API Documentation

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

## 📂 Project Highlights

- Asynchronous FastAPI backend
- Clean layered architecture
- Async SQLAlchemy ORM
- Repository & Unit of Work patterns
- Dependency Injection
- Provider-based object storage
- JWT Authentication
- Password recovery via email
- Redis integration
- Image optimization before upload
- Dockerized development environment
- Production-ready configuration using Pydantic Settings

---

## 📈 Future Improvements

- Refresh Tokens
- Role-Based Access Control (RBAC)
- Rate Limiting
- Background Jobs with Celery
- Full-text Search
- Comment System
- Likes & Bookmarks
- Notifications
- CI/CD Pipeline
- Kubernetes Deployment

---

## 📄 License

This project is available under the MIT License.