# Fitness Tracker - Example Workflow

This file contains a complete example workflow to demonstrate all features.

## Step 1: Register Users

```bash
# Register first user
python -m cli.main register \
  --username alice \
  --email alice@example.com \
  --full-name "Alice Johnson" \
  --target-weight 65 \
  --weekly-minutes 180

# Register second user
python -m cli.main register \
  --username bob \
  --email bob@example.com \
  --full-name "Bob Smith" \
  --target-weight 80 \
  --weekly-minutes 150
```

## Step 2: Log Workouts for Alice

```bash
# Monday - Running
python -m cli.main add-workout \
  --user alice \
  --type running \
  --duration 45 \
  --intensity high \
  --date 2025-10-01 \
  --notes "Morning run, felt great!"

# Tuesday - Yoga
python -m cli.main add-workout \
  --user alice \
  --type yoga \
  --duration 60 \
  --intensity low \
  --date 2025-10-02 \
  --notes "Relaxing yoga session"

# Wednesday - Cycling
python -m cli.main add-workout \
  --user alice \
  --type cycling \
  --duration 50 \
  --intensity medium \
  --date 2025-10-03 \
  --notes "Bike ride through the park"
```

## Step 3: Log Meals for Alice

```bash
# Day 1 meals
python -m cli.main add-meal \
  --user alice \
  --name "Greek yogurt with granola" \
  --calories 320 \
  --protein 18 \
  --carbs 45 \
  --fat 8 \
  --time "2025-10-01 07:30"

python -m cli.main add-meal \
  --user alice \
  --name "Quinoa bowl with vegetables" \
  --calories 450 \
  --protein 15 \
  --carbs 72 \
  --fat 12 \
  --time "2025-10-01 12:00"

python -m cli.main add-meal \
  --user alice \
  --name "Salmon with sweet potato" \
  --calories 520 \
  --protein 42 \
  --carbs 48 \
  --fat 18 \
  --time "2025-10-01 18:30"

# Day 2 meals
python -m cli.main add-meal \
  --user alice \
  --name "Smoothie bowl" \
  --calories 280 \
  --protein 12 \
  --carbs 52 \
  --fat 6 \
  --time "2025-10-02 08:00"

python -m cli.main add-meal \
  --user alice \
  --name "Chicken salad" \
  --calories 380 \
  --protein 38 \
  --carbs 28 \
  --fat 14 \
  --time "2025-10-02 13:00"
```

## Step 4: Log Weight for Alice

```bash
python -m cli.main log-weight --user alice --weight 67.5 --date 2025-10-01
python -m cli.main log-weight --user alice --weight 67.2 --date 2025-10-02
python -m cli.main log-weight --user alice --weight 67.0 --date 2025-10-03
python -m cli.main log-weight --user alice --weight 66.8 --date 2025-10-04
```

## Step 5: View Data

```bash
# List all workouts
python -m cli.main list-workouts --user alice

# List workouts for specific date range
python -m cli.main list-workouts --user alice --from 2025-10-01 --to 2025-10-02

# List meals
python -m cli.main list-meals --user alice --from 2025-10-01 --to 2025-10-02

# List with limit
python -m cli.main list-workouts --user alice --limit 2
```

## Step 6: Update Data

```bash
# Get workout ID from list-workouts command, then update
python -m cli.main update-workout \
  --id <WORKOUT_ID> \
  --duration 50 \
  --notes "Updated: Increased duration"

# Update meal
python -m cli.main update-meal \
  --id <MEAL_ID> \
  --calories 500 \
  --protein 45
```

## Step 7: Generate Progress Report

```bash
# Generate report for the week
python -m cli.main view-report \
  --user alice \
  --from 2025-10-01 \
  --to 2025-10-04

# Generate report without cache
python -m cli.main view-report \
  --user alice \
  --from 2025-10-01 \
  --to 2025-10-04 \
  --no-cache
```

## Step 8: Log Data for Bob

```bash
# Workouts
python -m cli.main add-workout \
  --user bob \
  --type "weight training" \
  --duration 60 \
  --intensity high \
  --date 2025-10-01

python -m cli.main add-workout \
  --user bob \
  --type running \
  --duration 30 \
  --intensity medium \
  --date 2025-10-02

# Meals
python -m cli.main add-meal \
  --user bob \
  --name "Protein shake" \
  --calories 250 \
  --protein 40 \
  --carbs 15 \
  --fat 5 \
  --time "2025-10-01 07:00"

# Weight
python -m cli.main log-weight --user bob --weight 82.0 --date 2025-10-01
python -m cli.main log-weight --user bob --weight 81.8 --date 2025-10-02
```

## Step 9: View Bob's Report

```bash
python -m cli.main view-report \
  --user bob \
  --from 2025-10-01 \
  --to 2025-10-02
```

## Step 10: Delete Operations (Optional)

```bash
# Delete a specific workout
python -m cli.main delete-workout --id <WORKOUT_ID>

# Delete a specific meal
python -m cli.main delete-meal --id <MEAL_ID>

# Delete entire user (WARNING: This deletes all user data)
# python -m cli.main delete-user --user bob
```

## Using with Docker

Prepend `docker-compose exec app` to any command:

```bash
docker-compose exec app python -m cli.main register --username alice --email alice@example.com
docker-compose exec app python -m cli.main view-report --user alice --from 2025-10-01 --to 2025-10-04
```

## Expected Report Output

When you run the report for Alice (Step 7), you should see something like:

```
================================================================================
Fitness Report for alice (2025-10-01 to 2025-10-04)
Period: 4 days

🏋️ Workouts: 3 sessions, 155 total minutes
   Average duration: 51.7 minutes
   Intensity: 1 low, 1 medium, 1 high

🍽️ Nutrition: 5 meals logged
   Average daily calories: 382.5
   Average daily macros: P:31.2g, C:61.2g, F:14.5g

⚖️ Weight: 4 measurements
   Start: 67.5 kg
   End: 66.8 kg
   Change: -0.7 kg (decreasing)
   Target: 65.0 kg (1.8 kg above target)

📊 Weekly workout goal: 180 minutes
   Actual average: 271.2 minutes/week
   ✅ Goal achieved!
================================================================================
```
