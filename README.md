# Birthday Freebies 🎂

A full-stack web application that aggregates birthday freebies from major US chain restaurants and retailers. Help birthday celebrants discover and track available birthday offers easily.

## Project Overview

**Status**: Early Development 🚧

Birthday Freebies is a platform designed to help people in the United States find and track birthday offers from their favorite restaurants and retailers. Users can search for available deals, view redemption requirements, check expiration dates, and discover what rewards they can claim on their special day.

### Core Features (Planned)

- 🎁 Browse and search birthday offers
- 🔍 Advanced filtering by restaurant, location, and offer type
- 📍 Restaurant information and locations
- ❤️ Save favorite offers
- 📱 Fully responsive design for all devices
- 🔄 Automated data updates via web scraping

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (async) with Alembic migrations
- **Authentication**: JWT (JSON Web Tokens)
- **API Design**: RESTful API
- **Testing**: pytest with httpx

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: CSS3 / Tailwind CSS
- **Responsive Design**: Mobile-first approach

### DevOps & Infrastructure
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git & GitHub
- **CI/CD**: GitHub Actions
- **Deployment**: Docker-based deployment

## Project Structure

```
Birthday_Freebies/
├── backend/                    # Python FastAPI application
│   ├── app/                    # Main application code
│   ├── config/                 # Environment configurations
│   ├── scripts/                # Database setup & utilities
│   ├── tests/                  # Test suite
│   ├── requirements.txt
│   └── run.py
│
├── frontend/                   # React TypeScript application
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client layer
│   │   ├── styles/             # Global styles
│   │   └── types/              # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
│
├── .github/
│   └── workflows/              # CI/CD automation
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11
- Node.js 16+
- npm or yarn
- Docker (optional)

### Local Development Setup

**Coming Soon** - Detailed setup instructions will be added as the project progresses.

## Documentation

Detailed documentation will be available in the `docs/` directory as the project develops.

## Testing

**Coming Soon** - Testing setup will be documented as test files are created.

## Development Roadmap

### Phase 1: Foundation
- [ ] Backend API setup with FastAPI
- [ ] PostgreSQL database schema design
- [ ] Frontend project setup with React + TypeScript
- [ ] Basic CRUD operations for offers and restaurants

### Phase 2: Core Features
- [ ] User authentication with JWT
- [ ] Web scraping service for data collection
- [ ] Advanced filtering and search
- [ ] Comprehensive test suite

### Phase 3: Polish & Deploy
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Docker containerization
- [ ] Production deployment

## Contributing

Contributions are welcome! This project is in early development phase, so please reach out before starting work on major features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**SunnyORZ030**

- GitHub: [@SunnyORZ030](https://github.com/SunnyORZ030)

---

⭐ If you find this project helpful or interesting, please give it a star!

*Built for internship applications and portfolio development*
