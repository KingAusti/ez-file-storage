# Data Storage Application

A secure, production-ready web application for storing and managing personal data with enterprise-grade features including authentication, audit logging, and dark mode.

## ✨ Features

- **🔐 Secure Authentication**: JWT with refresh tokens, password reset, rate limiting
- **📝 Data Management**: Create, read, update, and delete data entries
- **🌙 Dark Mode**: Beautiful light/dark theme with smooth transitions
- **📊 Audit Logging**: Complete tracking of all user actions
- **🚀 Production Ready**: PostgreSQL, Redis, monitoring, automated backups
- **🐳 Docker Ready**: One-command setup with Docker Compose
- **📱 Responsive**: Works great on desktop and mobile devices

## 🚀 Quick Start (30 seconds)

**Prerequisites**: Docker and Docker Compose

### Option 1: Automated Setup (Recommended)
```bash
# 1. Clone the repository
git clone <repository-url>
cd data-storage-app

# 2. Run the setup script (that's it!)
./setup.sh
```

### Option 2: Manual Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd data-storage-app

# 2. Start the application
docker-compose up --build

# 3. Open your browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**That's it!** The application will automatically:
- Set up PostgreSQL database with secure passwords
- Configure Redis for caching
- Start the backend API server
- Launch the React frontend
- Run database migrations
- Generate secure environment variables
- **Make the app accessible from your local network** (same WiFi)
- **Handle port conflicts automatically** (finds alternative ports if needed)

## 🎯 What You Get

Once running, you can:
1. **Register** a new account at http://localhost:3000/register
2. **Login** and start creating data entries
3. **Toggle dark mode** using the 🌙/☀️ button in the navbar
4. **View API documentation** at http://localhost:8000/docs
5. **Monitor health** at http://localhost:8000/health
6. **Access from other devices** on your WiFi network using your computer's IP address

## 🌍 Network Access

The application is configured to be accessible from:
- **Local machine**: http://localhost:3000
- **Same WiFi network**: http://YOUR_IP:3000 (setup script will show your IP)
- **Other devices**: Phones, tablets, other computers on your network

**Note**: For internet access, see the [Production Deployment](#-production-deployment) section.

### Finding Your IP Address

The setup script will automatically show your IP address, but you can also find it manually:

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig | findstr "IPv4"
```

### Testing External Access

1. **Start the application**: `./setup.sh` or `docker-compose up --build`
2. **Note your IP address and ports** from the setup output
3. **Test from another device** on the same WiFi:
   - Open browser on phone/tablet/other computer
   - Navigate to `http://YOUR_IP:FRONTEND_PORT` (setup script will show the actual port)
   - You should see the login page

### Port Conflict Handling

The setup script automatically handles port conflicts:

```bash
# Check for port conflicts before setup
./scripts/check-ports.sh

# Or just run setup (it handles conflicts automatically)
./setup.sh
```

**What happens if ports are in use:**
- ✅ **Automatic detection**: Script checks if default ports (3000, 8000, 5432, 6379) are available
- ✅ **Alternative ports**: Finds next available ports automatically
- ✅ **Clear feedback**: Shows which ports are being used
- ✅ **No manual configuration**: Everything is handled automatically
- ✅ **Cross-platform**: Works on macOS, Linux, and Windows
- ✅ **Smart detection**: Uses `lsof`, `netstat`, or `ip` commands as available

## 🛠️ Development Setup (Without Docker)

If you prefer to run without Docker, you'll need PostgreSQL and Redis running locally:

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- uv (Python package manager)

### Quick Setup
```bash
# Backend
cd backend
cp env.example .env  # Edit with your database credentials
uv sync
uv run python main.py

# Frontend (in another terminal)
cd frontend
npm install
npm start
```

## 🐳 Docker Commands

```bash
# Start the application
docker-compose up --build

# Start in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Clean up everything (removes data!)
docker-compose down -v --remove-orphans
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🌐 Production Deployment

### Simple Production Setup

1. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with production values (SECRET_KEY, database passwords, etc.)
   ```

2. **Start with Nginx**:
   ```bash
   docker-compose --profile production up --build -d
   ```

3. **Setup automated backups**:
   ```bash
   # Add to crontab for daily backups
   crontab -e
   # Add: 0 2 * * * /path/to/scripts/backup.sh
   ```

### Production Security Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use strong database passwords
- [ ] Enable HTTPS (place SSL certs in `nginx/ssl/`)
- [ ] Configure firewall (ports 80, 443, 22)
- [ ] Setup monitoring (Sentry DSN in `.env`)
- [ ] Configure email settings for password reset

## 🛠️ Development

### Backend Development
```bash
cd backend
uv sync --dev    # Install dev dependencies
uv run black .   # Format code
uv run pytest    # Run tests
```

### Frontend Development
```bash
cd frontend
npm install      # Install dependencies
npm start        # Start dev server
npm test         # Run tests
```

## 🔧 Troubleshooting

### Common Issues

**Port already in use**:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# The setup script handles this automatically, but if you need to manually check:
./scripts/check-ports.sh

# Or find what's using a specific port:
lsof -i :PORT_NUMBER
netstat -an | grep :PORT_NUMBER
```

**Docker permission errors**:
```bash
# On Linux, add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**Application won't start**:
```bash
# Check logs
docker-compose logs

# Clean restart
docker-compose down -v
docker-compose up --build
```

**Database connection issues**:
- Ensure PostgreSQL and Redis are running
- Check environment variables in `.env`
- Verify database credentials

### Reset Everything
```bash
docker-compose down -v --remove-orphans
docker system prune -f
docker-compose up --build
```

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Bootstrap
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL 15 with connection pooling
- **Cache**: Redis 7
- **Authentication**: JWT with refresh tokens
- **Security**: Rate limiting, audit logging, password strength validation
- **Monitoring**: Structured logging, health checks, Sentry integration

## 📋 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user  
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password
- `GET /auth/me` - Get current user info

### Data Entries
- `GET /data-entries/` - Get all user's data entries
- `POST /data-entries/` - Create new data entry
- `GET /data-entries/{id}` - Get specific data entry
- `PUT /data-entries/{id}` - Update data entry
- `DELETE /data-entries/{id}` - Delete data entry

### System
- `GET /health` - Health check with dependency validation
- `GET /metrics` - Prometheus metrics

## 🔒 Security Features

- **Authentication**: JWT with refresh tokens (7-day expiry)
- **Rate Limiting**: 5 login attempts/minute, 100 API calls/hour
- **Password Security**: bcrypt hashing + strength validation
- **Account Protection**: Lockout after failed attempts
- **Audit Logging**: Complete action tracking
- **Input Validation**: Pydantic schemas + sanitization
- **CORS Protection**: Configurable origins
- **SQL Injection Protection**: SQLAlchemy ORM

## 📊 Production Features

- **Database**: PostgreSQL with migrations and backups
- **Caching**: Redis for sessions and query results
- **Monitoring**: Structured logging + Sentry error tracking
- **Health Checks**: Dependency validation + metrics
- **Backups**: Automated daily backups with S3 integration
- **CI/CD**: GitHub Actions with testing and security scanning
- **Containerization**: Multi-service Docker setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `docker-compose exec backend uv run pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Need help?** Check the [troubleshooting section](#-troubleshooting) or open an issue on GitHub.
