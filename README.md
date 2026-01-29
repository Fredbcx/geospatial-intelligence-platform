# 🗺️ Geospatial Intelligence Platform

**Real-time aircraft tracking and anomaly detection system for situational awareness and defense intelligence applications.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📸 Screenshots

### 3D Visualization - European Airspace
![3D View Europe](docs/screenshots/3d_view_europe.png)
*Interactive 3D visualization with altitude-based coloring and pitch/bearing controls*

### Aircraft Details & Trajectory Tracking
![Aircraft Trajectory](docs/screenshots/aircraft_trajectory.png)
*Real-time aircraft information with historical trajectory visualization*

### Density Heatmap Analysis
![Density Heatmap](docs/screenshots/density_heatmap.png)
*Spatial density analysis showing high-traffic corridors over Europe*

### Alert Management System
![Alert Panel](docs/screenshots/alerts_panel.png)
*Real-time geofence violation detection with severity classification*

### Global Coverage - Middle East Region
![Middle East Coverage](docs/screenshots/middle_east_view.png)
*Platform tracking 600+ aircraft simultaneously across multiple regions*

---

## 🎯 Overview

This platform demonstrates **production-grade geospatial intelligence capabilities** relevant to defense AI and battlefield management systems. Built as a portfolio project to showcase ML engineering, real-time data processing, and full-stack development skills.

**Key Value Proposition:**
- **Single pane of glass** for multi-source geospatial data integration
- **Automated anomaly detection** across 5 statistical and ML-based methods
- **Real-time processing** of 1,000+ aircraft with sub-second query performance
- **3D interactive visualization** with 60 FPS rendering using Deck.gl

---

## ✨ Features

### Core Capabilities

#### 🛫 Real-time Aircraft Tracking
- **OpenSky Network integration** - 3-minute polling interval (480 requests/day)
- **Live updates** via RESTful API with spatial filtering
- **Historical trajectories** with path visualization

#### 🚨 Anomaly Detection System
Five complementary detection methods:
1. **Speed anomalies** - Z-score statistical outliers (threshold: 2.5σ)
2. **Altitude anomalies** - IQR-based detection for unusual flight levels
3. **Geofence violations** - Spatial boundary checks (5 restricted zones)
4. **Clustering anomalies** - DBSCAN isolation of spatial outliers
5. **ML-based detection** - Isolation Forest for multivariate patterns

**Current metrics:** ~100 active alerts with severity classification (HIGH/MEDIUM/LOW)

#### 🗺️ Interactive 3D Visualization
- **Deck.gl + MapBox GL** - Hardware-accelerated WebGL rendering
- **3D perspective mode** - Adjustable pitch (0-60°) and bearing (0-360°)
- **Altitude-based coloring:**
  - 🔴 Red: >10,000m (high altitude)
  - 🟡 Orange: 5,000-10,000m (cruising)
  - 🔵 Blue: <5,000m (low altitude)
  - ⚪ Gray: Ground/unknown
- **Layer controls:**
  - Aircraft points (real-time positions)
  - Trajectories (historical paths)
  - Density heatmap (H3 hexagonal aggregation)

#### 📊 Geospatial Analytics
- **H3 hexagonal indexing** (Uber H3) - Multi-resolution spatial indexing
- **PostGIS spatial queries** - Sub-100ms bounding box queries
- **Density heatmap** - Activity aggregation by geographic cells
- **Spatial filtering** - Real-time viewport-based data loading

---

## 🛠️ Tech Stack

### Backend (Python)
```
FastAPI 0.109.0       # REST API framework
PostgreSQL 15         # Primary database (via Docker)
PostGIS 3.3           # Geospatial extension
SQLAlchemy 2.0.45     # ORM
GeoAlchemy2 0.14.3    # PostGIS integration
Shapely 2.0.2         # Geometric operations
H3 4.4.1              # Hexagonal indexing (Uber H3)
GeoPandas 0.14.2      # Geospatial data analysis
scikit-learn 1.4.0    # Anomaly detection (Isolation Forest, DBSCAN)
APScheduler 3.10.4    # Job scheduling (OpenSky polling)
aiohttp 3.9.1         # Async HTTP client
psycopg 3.1.18        # PostgreSQL driver
```

### Frontend (TypeScript/React)
```
React 18.2            # UI framework
TypeScript 5.0        # Type safety
Deck.gl 8.9           # 3D geospatial visualization
MapBox GL 2.15        # Base map tiles
Material-UI 5.14      # Component library
Axios 1.6             # HTTP client
Zustand 4.4           # State management
```

### Infrastructure
```
Docker / Docker Compose
PostgreSQL 15 + PostGIS 3.3 (official postgis/postgis image)
Redis 7 Alpine (caching - optional, planned)
```

**Note:** Current Docker Compose provides database services only. Backend and frontend run locally during development. Production containerization is on the roadmap.

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (for PostgreSQL + PostGIS)
- **Python 3.12.1** (backend)
- **Node.js 18+** (frontend)
- **8GB+ RAM** recommended
- Git

### Installation

1. **Clone repository**
```bash
git clone https://github.com/Fredbcx/geospatial-intelligence-platform.git
cd geospatial-intelligence-platform
```

2. **Start database services**
```bash
# Start PostgreSQL + PostGIS and Redis
docker-compose up -d

# Verify services are running
docker ps
# Should show: geoint-postgis, geoint-redis
```

3. **Setup backend**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Edit .env with your settings:
# OPENSKY_USERNAME=your_username  (optional, for higher rate limits)
# OPENSKY_PASSWORD=your_password
# DATABASE_URL=postgresql://geoint:password@localhost:5432/geoint

# Run database migrations (creates tables, indexes)
python database.py

# Start backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Setup frontend** (in new terminal)
```bash
cd frontend

# Install dependencies
npm install

# Configure MapBox token
cp .env.local.example .env.local

# Edit .env.local and add your MapBox token:
# VITE_API_URL=http://localhost:8000
# VITE_MAPBOX_TOKEN=your_mapbox_token_here
#
# Get free token at: https://account.mapbox.com/access-tokens/

# Start development server
npm run dev
```

5. **Verify deployment**
- **Backend API:** http://localhost:8000/docs (Swagger UI)
- **Frontend:** http://localhost:5173
- **Database:** localhost:5432 (user: geoint, password: password)

### First Run

The system will automatically:
1. ✅ Initialize PostgreSQL with PostGIS extension
2. ✅ Create database schema (aircraft, positions, alerts tables)
3. ✅ Create spatial indexes (GIST on geometry columns)
4. ✅ Start OpenSky data ingestion (3-minute intervals)
5. ✅ Generate anomaly alerts

**Initial data population:** ~10-15 minutes to reach 1,000+ aircraft

### Testing Without OpenSky (Optional)

If OpenSky Network is unavailable or you want instant data:

```bash
cd backend

# Populate database with 100 realistic test aircraft (with trajectories)
python populate_test_data_with_trajectory.py

# This generates:
# - 100 aircraft with realistic positions over Europe
# - Historical trajectory data (24h simulated flight paths)
# - Anomaly alerts based on test data
```

---

## 📐 Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                   DATA SOURCES (External APIs)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  OpenSky    │  │   Future    │  │   Future    │           │
│  │  Network    │  │   Weather   │  │   Events    │           │
│  │ (Aircraft)  │  │    APIs     │  │   (GDELT)   │           │
│  └──────┬──────┘  └─────────────┘  └─────────────┘           │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI + Python)                      │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Data Ingestion Layer                                 │   │
│  │  • APScheduler (3-min intervals)                      │   │
│  │  • API polling with retry logic                       │   │
│  │  • Data validation (Pydantic)                         │   │
│  └────────────────────┬──────────────────────────────────┘   │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Geospatial Processing Engine                         │   │
│  │  • H3 hexagonal indexing                              │   │
│  │  • Shapely geometric operations                       │   │
│  │  • PostGIS spatial queries                            │   │
│  └────────────────────┬──────────────────────────────────┘   │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Anomaly Detection Engine                             │   │
│  │  • Z-score (speed)                                    │   │
│  │  • IQR (altitude)                                     │   │
│  │  • Geofence (spatial)                                 │   │
│  │  • DBSCAN clustering                                  │   │
│  │  • Isolation Forest (ML)                              │   │
│  └────────────────────┬──────────────────────────────────┘   │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  REST API Layer                                       │   │
│  │  • /api/aircraft (spatial queries)                    │   │
│  │  • /api/alerts (anomaly management)                   │   │
│  │  • /api/trajectories (historical paths)               │   │
│  │  • /api/heatmap (density aggregation)                 │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│           DATABASE (PostgreSQL + PostGIS)                    │
│  Tables:                                                     │
│  • aircraft                    					           │
│  • aircraft_positions              					       │
│  • alerts                          				           │
│  • geofences 						                           │
│                                                              │
│  Indexes:                                                    │
│  • GIST spatial indexes on all geometry columns              │
│  • B-tree on timestamps for temporal queries                 │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│           FRONTEND (React + Deck.gl)                         │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  3D Map Component (Deck.gl)                           │   │
│  │  • ScatterplotLayer (aircraft points)                 │   │
│  │  • PathLayer (trajectories)                           │   │
│  │  • HexagonLayer (density heatmap)                     │   │
│  │  • MapBox GL (dark-v11 tiles)                         │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Control Panels                                       │   │
│  │  • View controls (2D/3D, pitch, bearing)              │   │
│  │  • Layer toggles                                      │   │
│  │  • Alert management                                   │   │
│  │  • Aircraft details                                   │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

**Real-time Pipeline:**
```
OpenSky API → FastAPI endpoint → Data validation → 
PostGIS insertion → Anomaly detection → Alert generation → 
Frontend query → Deck.gl rendering (60 FPS)
```

**Query Optimization:**
- Spatial indexes (GIST) reduce query time from ~2s to <100ms
- Viewport filtering limits data transfer (1,000 aircraft max per request)
- H3 indexing enables O(1) spatial lookups

---

## 📊 Performance Metrics

### API Response Times
- **Spatial queries:** <100ms (bounding box with 1,000 results)
- **Trajectory queries:** <50ms (single aircraft, 24h history)
- **Alert queries:** <30ms (filtered by severity/type)
- **Heatmap aggregation:** <200ms (H3 density calculation)

### Frontend Rendering
- **Frame rate:** 60 FPS sustained with 1,000+ aircraft points
- **3D mode:** Smooth pitch/bearing adjustments (<16ms per frame)
- **Layer toggling:** Instant (<16ms)
- **Initial load:** <2s (Docker localhost environment)

### Database Performance
- **Spatial index efficiency:** 95%+ queries use index-only scans
- **Query planning:** PostGIS GIST indexes reduce lookup from O(n) to O(log n)
- **Concurrent connections:** Handles 50+ simultaneous API requests

### Scalability Benchmarks
- **Tested with:** 21,000+ aircraft, 180,000+ position records
- **Memory usage:** ~150MB database (with indexes ~25MB)
- **API throughput:** 100+ requests/second (single uvicorn worker)

---

## 🔧 Development

### Project Structure
```
geospatial-intelligence-platform/
├── backend/
│   ├── anomaly_detection.py     # 5 detection algorithms
│   ├── clean_db.py              # Database cleanup utility
│   ├── crud.py                  # Database operations
│   ├── data_ingestion.py        # OpenSky API integration
│   ├── database.py              # SQLAlchemy setup
│   ├── main.py                  # FastAPI application + endpoints
│   ├── models.py                # SQLAlchemy models
│   ├── scheduler.py             # APScheduler (OpenSky polling)
│   ├── schema.py                # Pydantic validation schemas
│   ├── spatial_queries.py       # PostGIS query helpers
│   ├── test_opensky.py          # OpenSky API tester
│   ├── populate_test_data_with_trajectory.py  # Test data generator
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.tsx           # Main Deck.gl component
│   │   │   ├── ViewControls.tsx      # 3D controls (pitch/bearing)
│   │   │   ├── AlertPanel.tsx        # Alert management UI
│   │   │   ├── FloatingAlertButton.tsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   ├── useAircraftData.ts    # Aircraft data fetching
│   │   │   └── useAlerts.ts          # Alert management
│   │   ├── services/
│   │   │   └── api.ts                # Axios HTTP client
│   │   └── ...
│	├── public/                       # Static assets
│   ├── ...
│   ├── .env.local                    # Environment vars (gitignored)
│   ├── .gitignore                    # Git ignore rules
├── docs/
│   └── screenshots/             # Portfolio screenshots
│       ├──  ...
├── docker-compose.yml           # PostgreSQL + Redis only
└── README.md
```

### Running Development Server
```bash
# Backend (auto-reload on code changes)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (hot module replacement)
cd frontend
npm run dev
```

### Database Management
```bash
# Clean database (remove all data)
cd backend
python clean_db.py

# Populate with test data
python populate_test_data_with_trajectory.py

# Direct database access
docker exec -it geoint-postgis psql -U geoint -d geoint
```

### API Documentation
Access interactive Swagger UI at http://localhost:8000/docs after starting the backend.

Key endpoints:
- `GET /api/aircraft` - Query aircraft by bounding box
- `GET /api/aircraft/{icao24}/trajectory` - Get flight path
- `GET /api/alerts` - List active alerts with filters
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /api/heatmap/density` - Get H3 aggregated density data

---

## 🎯 Use Cases

### Defense & Intelligence Applications
This system demonstrates capabilities directly applicable to:

1. **Battlefield Management**
   - Real-time asset tracking (ground vehicles, aircraft, drones)
   - Multi-sensor data fusion
   - Spatial anomaly detection for threat assessment

2. **Border Surveillance**
   - Geofence violation alerts (restricted airspace)
   - Pattern-of-life analysis (trajectory clustering)
   - Automated threat classification

3. **Maritime Domain Awareness**
   - Ship tracking (AIS integration - planned)
   - Fishing vessel behavior analysis
   - Port activity monitoring

4. **Critical Infrastructure Protection**
   - Perimeter security (geofence alerts)
   - Unauthorized drone detection
   - Proximity warnings for sensitive facilities

### Commercial Applications
- **Airline Operations:** Flight delay prediction, route optimization
- **Logistics:** Fleet management, delivery tracking
- **Smart Cities:** Traffic flow analysis, urban planning
- **Environmental Monitoring:** Emissions tracking, noise pollution

---

## 🚧 Roadmap & Future Enhancements

### Phase 1: Data Source Expansion (2-3 weeks)
- [ ] **AIS ship tracking integration** (MarineTraffic API)
- [ ] **Weather data overlay** (OpenWeatherMap)
- [ ] **GDELT event correlation** (geopolitical events)
- [ ] **Satellite imagery integration** (background context)

### Phase 2: Advanced Analytics (3-4 weeks)
- [ ] **Predictive trajectory modeling** (LSTM neural networks)
- [ ] **Collision detection** (proximity warnings)
- [ ] **Pattern-of-life analysis** (behavioral clustering)
- [ ] **Temporal correlation** (event-driven anomalies)

### Phase 3: Production Features (2-3 weeks)
- [ ] **WebSocket real-time updates** (sub-second latency)
- [ ] **User authentication** (JWT-based)
- [ ] **Alert rule builder** (custom geofences, conditions)
- [ ] **Report generation** (PDF exports, analytics)
- [ ] **Mobile-responsive design**

### Phase 4: ML Enhancements (4-6 weeks)
- [ ] **Reinforcement learning** for adaptive alerting
- [ ] **Graph neural networks** for trajectory prediction
- [ ] **Automated threat classification** (supervised learning)
- [ ] **Federated learning** for privacy-preserving analytics

### Infrastructure Improvements
- [ ] **Docker multi-service setup** (currently only database; add backend + frontend containers)
- [ ] **Redis caching implementation** (reduce PostgreSQL load)
- [ ] **Nginx reverse proxy** (load balancing, SSL termination)
- [ ] **Prometheus + Grafana** (monitoring dashboards)
- [ ] **CI/CD pipeline** (GitHub Actions for automated testing/deployment)
- [ ] **Kubernetes deployment** (production-grade orchestration)



## 📚 Learning Resources

This project draws on concepts from:

### Geospatial Computing
- [PostGIS Documentation](https://postgis.net/documentation/)
- [H3 Hexagonal Indexing](https://h3geo.org/)
- [Shapely Geometric Operations](https://shapely.readthedocs.io/)

### Anomaly Detection
- [scikit-learn Outlier Detection](https://scikit-learn.org/stable/modules/outlier_detection.html)
- [DBSCAN Clustering](https://en.wikipedia.org/wiki/DBSCAN)
- [Isolation Forest Algorithm](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)

### Visualization
- [Deck.gl Documentation](https://deck.gl/docs)
- [MapBox GL JS](https://docs.mapbox.com/mapbox-gl-js/)
- [WebGL Performance Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices)

---

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome!


## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenSky Network** for free aircraft tracking data
- **MapBox** for beautiful map tiles
- **Uber H3** for hexagonal indexing technology
- **Deck.gl Team** for exceptional WebGL visualization library

