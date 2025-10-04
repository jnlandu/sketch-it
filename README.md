# Sketch It 

A web-based  application for creating and generating pencil-like images from uploaded pictures. Sketch-it uses deep learnining for  generating images, and it incorporates advanced images preprocessing. 

## Overview

Sketch-It is a full-stack application that allows users to create and generate pencil-like images from their photos. The application is built with a FastAPI backend and modern frontend architecture (likely NextJs to be considred).

## Project Structure

```
sketch-it/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   │   └── v1/           # API version 1
│   │   │       ├── auth.py    # Authentication endpoints
│   │   │       ├── sketches.py # Sketch management endpoints
│   │   │       ├── users.py   # User management endpoints
│   │   │       └── subscriptions.py # Subscription endpoints
│   │   ├── config/           # Configuration files
│   │   │   ├── database.py   # Database configuration
│   │   │   └── settings.py   # Application settings
│   │   ├── core/             # Core functionality
│   │   │   ├── exceptions.py # Custom exceptions
│   │   │   ├── middleware.py # Custom middleware
│   │   │   └── security.py   # Security utilities
│   │   ├── models/           # Database models
│   │   │   ├── sketch.py     # Sketch model
│   │   │   ├── user.py       # User model
│   │   │   └── subscription.py # Subscription model
│   │   ├── schemas/          # Pydantic schemas
│   │   │   ├── auth.py       # Authentication schemas
│   │   │   ├── sketch.py     # Sketch schemas
│   │   │   └── user.py       # User schemas
│   │   ├── services/         # Business logic services
│   │   │   ├── auth_service.py # Authentication service
│   │   │   ├── sketch_service.py # Sketch management service
│   │   │   ├── storage_service.py # File storage service
│   │   │   ├── subscription_service.py # Subscription service
│   │   │   └── user_service.py # User management service
│   │   └── utils/            # Utility functions
│   │       ├── helpers.py    # General helpers
│   │       ├── image_processing.py # Image processing utilities
│   │       └── validators.py # Input validators
│   ├── docker/               # Docker configuration
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   └── Dockerfile.dev
│   ├── docs/                 # Documentation
│   │   ├── API.md
│   │   ├── ARCHITECTURE.md
│   │   ├── DEPLOYMENT.md
│   │   └── SETUP.md
│   ├── logs/                 # Application logs
│   ├── scripts/              # Utility scripts
│   │   ├── cleanup.py        # Database cleanup
│   │   ├── init_db.py        # Database initialization
│   │   └── seed_data.py      # Seed data for testing
│   ├── storage/              # File storage directories
│   │   ├── original/         # Original uploaded files
│   │   ├── sketches/         # Processed sketches
│   │   └── thumbnails/       # Generated thumbnails
│   ├── tests/                # Test files
│   └── uploads/              # Temporary upload directory
└── frontend/                 # Frontend application (to be implemented)
```

##  Features

### Authentication & User Management
- User registration and login
- JWT-based authentication
- User profile management
- Password reset functionality

### Sketch Management
- Create and edit digital sketches
- Upload and process images
- Generate thumbnails automatically
- Organize sketches in collections
- Share sketches with other users

###  Subscription System
- Multiple subscription tiers
- Usage tracking and limits
- Payment processing integration
- Subscription management

### Image Processing
- Advanced image processing capabilities
- Multiple format support
- Automatic optimization
- Thumbnail generation

### Cloud Storage
- Secure file storage with Supabase
- Automatic backup and versioning
- CDN integration for fast delivery

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- Docker and Docker Compose
- Supabase account

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sketch-it/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements.dev.txt  # For development
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   python scripts/init_db.py
   python scripts/seed_data.py  # Optional: Add sample data
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Setup

1. **Using Docker Compose**
   ```bash
   cd backend/docker
   docker-compose up -d
   ```

2. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
# Frontend setup instructions will be added when implemented
```

## Development

### Running Tests

```bash
cd backend
pytest
```
### 


### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- **Authentication**: `/api/v1/auth/`
- **Users**: `/api/v1/users/`
- **Sketches**: `/api/v1/sketches/`
- **Subscriptions**: `/api/v1/subscriptions/`

##  Database Schema

The application uses Supabase (PostgreSQL) with the following main tables:
- `users` - User accounts and profiles
- `sketches` - Sketch metadata and references
- `subscriptions` - User subscription information
- `sketch_collections` - Sketch organization

##  Configuration

### Environment Variables

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Security
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
STORAGE_BUCKET=sketch-storage
MAX_FILE_SIZE=10485760  # 10MB

# Email (Optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

## Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_sketches.py

# Run tests in watch mode
pytest-watch
```

##  Monitoring & Logging

- Application logs are stored in `logs/`
- Error tracking with structured logging
- Performance monitoring capabilities
- Health check endpoints

## Deployment

### Production Deployment

1. **Build Docker image**
   ```bash
   docker build -f docker/Dockerfile -t sketch-it-backend .
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

3. **Environment-specific configurations**
   - Development: `docker/Dockerfile.dev`
   - Production: `docker/Dockerfile`

### Cloud Deployment

The application is designed to be deployed on:
- **Railway**
- **Heroku**
- **AWS ECS**
- **Google Cloud Run**
- **Azure Container Instances**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation for new features
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](backend/LICENSE) file for details.

## Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Authentication**: JWT
- **File Storage**: Supabase Storage
- **Image Processing**: Pillow, OpenCV
- **Testing**: pytest
- **Documentation**: Swagger/OpenAPI

### Frontend (Planned)
- **Framework**: React/Next.js or Vue/Nuxt
- **State Management**: Redux/Vuex or Zustand/Pinia
- **Styling**: Tailwind CSS
- **Canvas**: Fabric.js or Konva.js

### DevOps
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with JSON

---
Built with ❤️ by the Sketch-It team
