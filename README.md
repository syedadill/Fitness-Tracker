# Fitness Tracker

A simple fitness tracking application with both a web interface and CLI. Track workouts, meals, and weight progress with interactive charts and reports.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MongoDB (running on localhost:27017)
- Redis (running on localhost:6379)

### Installation

1. **Clone the repository** (or download the code)

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Start the application:**

**Web Interface** (Recommended):
```powershell
python web/app.py
```
Then open your browser to: **http://localhost:5000**

**OR use the CLI:**
```powershell
python -m cli.main --help
```

## 💻 Using the Web Interface

The easiest way to use the app is through the web interface:

1. **Open** http://localhost:5000 in your browser
2. **Register** a new account (just username, email, and goals)
3. **Login** with your username
4. **Use the dashboard** to:
   - View your fitness stats and charts
   - Add workouts, meals, and weight measurements
   - Generate progress reports
   - Filter and manage your data

### Features

- 📊 **Dashboard** - View stats and charts at a glance
- 🏋️ **Workouts** - Log exercise with type, duration, and intensity
- 🍽️ **Meals** - Track food with calories and macros
- ⚖️ **Weight** - Monitor weight progress over time
- 📈 **Reports** - Generate detailed fitness reports

## 🖥️ Using the CLI (PowerShell)

### Register a User

```powershell
python -m cli.main register --username john --email john@example.com --full-name "John Doe" --target-weight 75 --weekly-minutes 150
```

### Add a Workout

```powershell
python -m cli.main add-workout --user john --type running --duration 30 --intensity medium --date 2025-10-01
```

### Log a Meal

```powershell
python -m cli.main add-meal --user john --name "Chicken Salad" --calories 450 --protein 40 --carbs 35 --fat 18 --time "2025-10-01 12:30"
```

### Log Weight

```powershell
python -m cli.main log-weight --user john --weight 80.5 --date 2025-10-01
```

### View Report

```powershell
python -m cli.main view-report --user john --from 2025-10-01 --to 2025-10-31
```

### List Workouts

```powershell
python -m cli.main list-workouts --user john
```

### Get Help

```powershell
python -m cli.main --help
python -m cli.main add-workout --help
```

## 📁 Project Structure

```
fitness-tracker/
├── web/                    # Web interface
│   ├── app.py             # Flask server
│   ├── static/            # CSS, JavaScript
│   └── templates/         # HTML pages
├── cli/                   # Command-line interface
│   └── main.py           # CLI commands
├── services/             # Business logic
│   ├── db_service.py     # Database operations
│   ├── cache_service.py  # Redis caching
│   └── report_service.py # Report generation
├── models/               # Data validation
│   └── schemas.py       # Pydantic models
└── tests/               # Unit tests
```

## ⚙️ Configuration

Create a `.env` file to customize settings (optional):

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=fitness_tracker
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300
```

## 🧪 Testing

Run all tests:
```powershell
pytest tests/ -v
```

Run with coverage:
```powershell
pytest tests/ --cov --cov-report=html
```

## 🐳 Docker Setup (Optional)

If you prefer using Docker:

```powershell
docker-compose up -d
```

This starts MongoDB, Redis, and the application together.

## 🔧 Common Commands Reference

### User Management
- `register` - Create new user
- `delete-user` - Delete user and all data

### Workouts
- `add-workout` - Log new workout
- `list-workouts` - View workouts
- `update-workout` - Modify workout
- `delete-workout` - Remove workout

### Meals
- `add-meal` - Log new meal
- `list-meals` - View meals
- `update-meal` - Modify meal
- `delete-meal` - Remove meal

### Weight & Reports
- `log-weight` - Log weight measurement
- `view-report` - Generate fitness report

## 🆘 Troubleshooting

**"Failed to connect to MongoDB"**
- Make sure MongoDB is running on port 27017
- Or start it with: `mongod` (or use Docker)

**"Failed to connect to Redis"**
- Make sure Redis is running on port 6379
- The app will work without Redis (just slower reports)

**"Username already exists"**
- Choose a different username or delete the existing user

**Web interface not loading**
- Check that Flask is running: `python web/app.py`
- Make sure port 5000 is not in use
- Visit: http://localhost:5000 (not 127.0.0.1)

**Import errors**
- Install dependencies: `pip install -r requirements.txt`

## 📝 Example Workflow

Here's a complete example:

```powershell
# 1. Register
python -m cli.main register --username alice --email alice@example.com --target-weight 65 --weekly-minutes 120

# 2. Add some workouts
python -m cli.main add-workout --user alice --type running --duration 30 --intensity medium --date 2025-10-01
python -m cli.main add-workout --user alice --type yoga --duration 45 --intensity low --date 2025-10-02

# 3. Log meals
python -m cli.main add-meal --user alice --name "Breakfast Bowl" --calories 400 --protein 20 --carbs 50 --fat 15 --time "2025-10-01 08:00"

# 4. Track weight
python -m cli.main log-weight --user alice --weight 68.5 --date 2025-10-01

# 5. View progress
python -m cli.main view-report --user alice --from 2025-10-01 --to 2025-10-02
```

## 🎯 Features

✅ User registration with fitness goals  
✅ Workout tracking (type, duration, intensity)  
✅ Meal logging (calories, protein, carbs, fat)  
✅ Weight monitoring with trends  
✅ Progress reports with statistics  
✅ Modern web interface with charts  
✅ REST API for integrations  
✅ Redis caching for performance  
✅ Input validation  
✅ Comprehensive test suite (92% coverage)  

## 📚 API Documentation

The web server exposes REST endpoints at `http://localhost:5000/api/`:

- **Users**: `POST /api/users`, `GET /api/users/<username>`
- **Workouts**: `POST /api/workouts`, `GET /api/workouts/<username>`
- **Meals**: `POST /api/meals`, `GET /api/meals/<username>`
- **Weight**: `POST /api/weight-logs`, `GET /api/weight-logs/<username>`
- **Reports**: `GET /api/reports/<username>?from_date=2025-10-01&to_date=2025-10-31`

All endpoints return JSON with `{"success": true/false, ...}` format.

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## 📄 License

MIT License - Free to use and modify.

---

**Need Help?** Run any command with `--help` for detailed options:
```powershell
python -m cli.main add-workout --help
```
