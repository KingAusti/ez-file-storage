# Changelog

All notable changes to the Data Storage Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-10-03

### Added
- MIT `LICENSE` (Copyright (c) 2025 Austin Henry)
- Dependabot configuration for `/backend` (uv) and GitHub Actions, weekly, minor and patch updates grouped

### Changed
- Repository is now API-only: the orphaned `frontend` gitlink was removed (no frontend source exists)
- `POST /auth/login` returns `refresh_token` alongside `access_token`
- CI fixed; the `backend-tests`, `security-scan` and `docker-build` jobs pass
- README rewritten for the API service
- Env examples consolidated: `backend/.env.example` lists exactly the keys read by `app/core/config.py`, root `.env.example` lists the keys read by `docker-compose.yml`

### Removed
- `backend/env.example` (duplicate of `backend/.env.example` with a different key set)
- `IMPROVEMENTS_SUMMARY.md` and `data-storage-app/README.md` (stale; still available in git history)

## [1.1.0] - 2024-01-01

### Added
- **Versioning System**: Comprehensive version tracking with build information and feature flags
- **Tags System**: Full CRUD operations for organizing data entries with color-coded tags
- **Advanced Search & Filtering**: Full-text search across titles and content with date range filtering
- **Enhanced Data Entry Management**: Support for associating tags with data entries
- **New API Endpoints**:
  - `GET /version` - Detailed version information
  - `GET /tags/` - List all tags with usage counts
  - `POST /tags/` - Create new tags
  - `PUT /tags/{id}` - Update tags
  - `DELETE /tags/{id}` - Delete tags
  - Enhanced `GET /data-entries/` with search, filtering, and pagination

### Enhanced
- **Data Entry API**: Added search, filtering, sorting, and pagination capabilities
- **Database Schema**: Added tags table and many-to-many relationship with data entries
- **API Documentation**: Enhanced OpenAPI schemas with detailed descriptions
- **Audit Logging**: Extended to track tag operations and search activities

### Technical Improvements
- **Database Migration**: Added Alembic migration for tags system
- **Query Optimization**: Implemented efficient search and filtering with proper indexing
- **Response Format**: Standardized API responses with consistent tag information
- **Error Handling**: Improved validation and error messages for tag operations

## [1.0.0] - 2024-01-01

### Added
- **Core Application**: Complete data storage application with authentication
- **PostgreSQL Database**: Production-ready database with connection pooling
- **JWT Authentication**: Secure authentication with refresh tokens
- **Rate Limiting**: Protection against abuse with configurable limits
- **Audit Logging**: Complete tracking of all user actions
- **Structured Logging**: JSON-formatted logging with request ID tracking
- **Error Tracking**: Sentry integration for monitoring
- **Health Monitoring**: Enhanced health checks with dependency validation
- **Database Backups**: Automated backup system with S3 integration
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Dark Mode**: Theme system with localStorage persistence
- **Docker Support**: Complete containerization with multi-service setup
- **Port Conflict Handling**: Automatic port detection and resolution
- **Cross-Platform Support**: Works on macOS, Linux, and Windows

### Features
- User registration and authentication
- Data entry CRUD operations
- Password reset functionality
- Account lockout protection
- Comprehensive API documentation
- Production-ready deployment options
- Automated testing suite
- Security best practices implementation

---

## Version Information

- **Current Version**: 1.1.0
- **API Version**: v1
- **Database Schema**: 002 (includes tags system)
- **Minimum Requirements**: Docker, Docker Compose
- **Supported Platforms**: macOS, Linux, Windows

## Migration Notes

### From 1.0.0 to 1.1.0
- Run database migrations: `alembic upgrade head`
- New environment variables: None (backward compatible)
- Breaking changes: None
- New features: Tags system, advanced search, versioning

## Future Roadmap

### Planned for 1.2.0
- Rich text editor integration
- File upload support
- Advanced pagination with cursor-based navigation
- Redis caching layer
- Mobile app improvements

### Planned for 1.3.0
- Collaboration features (sharing entries)
- Advanced analytics and reporting
- Bulk operations
- API rate limiting per user
- Webhook support
