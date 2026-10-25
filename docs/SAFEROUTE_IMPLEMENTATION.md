# SafeRoute — Safety-Aware Route Planning for Women
## Architectural Audit and Implementation Design Note

**Date:** 2026-10-25  
**Branch:** `safepath`  
**Application:** SafeMate — Confidential Survivor Shield  

---

### 1. Existing System Architecture Audit

#### 1.1 Backend Architecture
- **Framework:** FastAPI with Uvicorn ASGI server.
- **API Prefix:** Configured via `settings.API_V1_PREFIX` (`/api/v1`).
- **Database:** SQLite database with SQLAlchemy 2.0 ORM, auto-migrating tables on startup (`safe_migrate_tables`).
- **Authentication & Authorization:** 
  - Dual Argon2 / Bcrypt password hashing with PyJWT stateless HS256 tokens.
  - Three distinct operating modes:
    1. **Personal Account:** Authenticated via JWT bearer token in `Authorization: Bearer <token>`.
    2. **Guest Mode:** Ephemeral scoped visitor tokens allowing exploration without persistent database pollution.
    3. **Judge Demo Mode:** Deterministic, safe simulation pathway preventing unauthorized live dispatches or carrier charges.
- **Existing Routers:**
  - `auth`: `/api/v1/auth` (register, login, guest token, user details).
  - `emergency`: `/api/v1/emergency` (emergency contacts, call logging, SOS dispatch).
  - `safewalk`: `/api/v1/safewalk` (trip token creation, breadcrumbs, live tracking, arrival check-in, escalation).
  - `evidence`: `/api/v1/evidence` (cryptographic vault uploads, SHA-256 fingerprinting).
  - `chatbot`: `/api/v1/chatbot` (9 trauma-informed triage state machines).
  - `detect` & `deepfake`: Still image & video deepfake neural screening.
  - `watermark`: High-speed bounded LSB steganographic recipient fingerprinting.
  - `health` & `model_info`: Readiness checks.

#### 1.2 Frontend Architecture
- **Framework:** Vanilla JavaScript + HTML5 + CSS3 built with Vite (`@vitejs/plugin-react` installed).
- **Design System:** Maitri trauma-informed design tokens (warm white/slate background, soft pink/crimson accents `#D90429`, `#881337`, deep navy `#0B132B`, accessible typography `Inter`, `Alice`, `Karma`).
- **UI Paradigm:** 
  - Sticky emergency exit tab (`ESC` panic camouflage into a cooking blog).
  - Clean hero mosaic with trauma survivor imagery.
  - Tools filter bar (`All Tools`, `Tell-Once`, `Emergency SOS`, `SafeWalk`, `Deepfake Scan`, `Evidence Vault`, `Leak Tracer`, `Legal Chatbot`).
  - Modular workspace modals opened via `openWorkspaceModal(modalId)` with zero clutter and strict focus.
- **SafeWalk Handoff Point:**
  - SafeWalk modal ID: `modal-feature-safewalk`.
  - Expects `destination: string` and `duration_minutes: int` to generate tracking tokens.

---

### 2. SafeRoute Integration Strategy

```
                                      +---------------------------------------------+
                                      |            SafeMate Client (UI)             |
                                      |  - Nav Link: "SafeRoute"                    |
                                      |  - Mode Selector: Walking vs Driving        |
                                      |  - Departure Time Selector                  |
                                      |  - MapLibre GL JS + OSM Vector/Raster Tiles |
                                      +----------------------+----------------------+
                                                             |
                                                             | REST Calls
                                                             v
+--------------------------------------------------------------------------------------------------------------------+
|                                         FastAPI Backend (/api/v1/routes/...)                                        |
+--------------------------------------------------------------------------------------------------------------------+
|  1. GET  /api/v1/routes/health       -> Service health & provider reachability                                     |
|  2. GET  /api/v1/routes/geocode      -> GeocodingService (Nominatim/OSM with debouncing & server-side cache)      |
|  3. GET  /api/v1/routes/places       -> PlacesService (Overpass API / bounded queries for shops, police, clinics) |
|  4. POST /api/v1/routes/plan         -> RoutingService (OSRM / OpenRouteService + NightActivityService scoring)   |
+--------------------------------------------------------------------------------------------------------------------+
                                                             |
                                                             v
+--------------------------------------------------------------------------------------------------------------------+
|                                    Night Activity Scoring Engine (0-100)                                           |
|  - Open-Establishment Coverage (25%)                                                                              |
|  - Distribution of Establishments / Segmentation (20%)                                                            |
|  - Road Characteristics / Highway Hierarchy (20%)                                                                 |
|  - Nearby Assistance Points: Police & Clinics (15%)                                                                |
|  - Public Transport Density (10%)                                                                                 |
|  - Verified CCTV Indicators (10%, renormalized when unavailable)                                                   |
|  - Longest Low-Activity Stretch detection (meters)                                                                 |
|  - Separate walking vs driving weight profiles                                                                     |
+--------------------------------------------------------------------------------------------------------------------+
                                                             |
                                                             | User selects preferred route -> "Start SafeWalk"
                                                             v
+--------------------------------------------------------------------------------------------------------------------+
|                                Existing SafeWalk Escort Session (/api/v1/safewalk)                                 |
|  - Pre-fills destination & duration_minutes                                                                        |
|  - Generates shareable guardian tracking token                                                                     |
+--------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Implementation Steps

1. **Backend Schemas (`backend/app/schemas/routes.py`):**
   - Coordinates, Geocode query/result, TravelMode enum (`walking`, `driving`), RoutePlanRequest, RouteFeature, ScoreBreakdown, RouteAlternative, RoutePlanResponse.
2. **Backend Services:**
   - `backend/app/services/geocoding_service.py`: Forward geocoding with caching, rate limiting, and fallback fixtures.
   - `backend/app/services/routing_service.py`: Real route geometries, distances, durations, and alternative paths via public routing infrastructure with offline sample fallbacks.
   - `backend/app/services/places_service.py`: Overpass API place retrieval (pharmacies, police stations, hospitals, convenience stores, petrol pumps, transit stops), opening hours parsing.
   - `backend/app/services/night_activity_service.py`: Configurable 0-100 scoring model, segmentation, longest low-activity stretch calculation, normalized missing data handling, and transparent breakdown.
3. **Backend API Router (`backend/app/api/routes/routes.py`):**
   - Register under `settings.API_V1_PREFIX + "/routes"`.
   - Wire into `backend/app/main.py`.
4. **Interactive Map & Frontend UI:**
   - Install/include MapLibre GL JS for real vector/raster mapping without API key requirements.
   - Add "SafeRoute" to navbar navigation and feature tools grid.
   - Build SafeRoute workspace modal: Origin/Destination inputs with suggestions, Leave Now / Time picker, Walking / Driving toggle, Route comparison cards, interactive map with styled route lines and category markers, detailed score breakdown, and "Start SafeWalk" handoff button.
5. **Testing & Verification:**
   - Automated backend unit & integration tests covering scoring, normalization, failure modes, geocoding, and SafeWalk handoff.
   - Frontend production build (`npm run build`).
