# EcoSort AI: Smart Waste Management System

A cutting-edge, AI-powered system that completely automates and optimizes municipal waste collection mapping. It tracks live bin capacities, predicts overflow via multi-variate ARIMA models, identifies waste types securely via MobileNetV2 computer vision, and employs an autonomous routing scheduler to dispatch active fleets dynamically.

---

## 🚀 Features

- **Automated Fleet Dispatch**: Live tracking of deployed trucks, idle trucks, and bins. Fully automated algorithms dispatch optimal idle trucks to predictive high-volume hotspots immediately upon capacity triggers.
- **Computer Vision Classification**: TensorFlow/Keras-based MobileNetV2 integrates directly with user endpoints to evaluate submitted images as Organic, Recyclable, Hazardous, or Other in sub-second speeds.
- **Adaptive Forecasting**: Integrates `statsmodels.tsa.arima` utilizing 30-day sinusoidal bin-fill historical data to generate robust 7-day predictive curves.
- **Admin Command Dashboard**: Fully built without SPA framework-bloat. A pure, lightweight, asynchronous HTML/JS dashboard styled in a beautiful modern dark mode. 
- **Security**: Robust cryptographic `bcrypt` password hashing mapped to `python-jose` secure JWT infrastructure to ensure only authenticated administrative bodies can execute schedules or edit core datasets.

---

## 🛠 Project Structure

```text
├── app/
│   ├── api/            # API Route dependencies & JWT Authentication handling
│   ├── core/           # Security models & hashing
│   ├── database/       # SQLAlchemy engine & Base model bindings
│   ├── forecast/       # ARIMA ML services
│   ├── ml/             # Convolutional Neural Network (CNN) integration bindings
│   ├── models/         # Database Table descriptors (Truck, Bin, Classifications)
│   ├── routes/         # Endpoints for Frontend Data binding
│   ├── schemas/        # High-validation Pydantic interfaces
│   └── scheduler/      # Dispatch and pathing simulation logic
├── frontend/           # The monolithic admin UI
├── .env.example        # Environment deployment variables map
├── init_db.py          # Fresh-database construction script
├── main.py             # Uvicorn entrypoint & primary ASGI application 
├── seed_data.py        # Mock-data payload generators (e.g 30 day sinusoids)
└── requirements.txt    # Project Python Dependencies
```

---

## 🏁 Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.9+ installed and optionally set up a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate  # (Windows: .venv\\Scripts\\activate)
```

### 2. Installation
Install the required backend and machine learning dependencies.

```bash
pip install -r requirements.txt
```

### 3. Environment Config
Copy the example environment securely. Note that the default SQLite integration perfectly simulates standard operating capabilities without modification.

```bash
cp .env.example .env
```

### 4. Database Initialization & Seeding
Initialize the necessary SQL models and populate the database with demonstration data metrics.

```bash
python init_db.py
python seed_data.py
# (Alternative: python seed_real_data.py to test directly with your CNN real image collections)
```

### 5. Running the Application
Launch the backend. It automatically binds the necessary SPA static mounts.

```bash
uvicorn main:app --reload --port 8000
```

Navigate to [http://localhost:8000](http://localhost:8000) to view the Admin framework.

---

## 🛡 Authentication

The admin dashboard endpoints are robustly secured via JWT mechanisms. 
Default credentials shipped across the `.env` module:
- **Email**: `admin@ecosort.com`
- **Password**: `admin123`

---

*Developed for robust infrastructure integration and scalable fleet capabilities across massive city metrics.*
