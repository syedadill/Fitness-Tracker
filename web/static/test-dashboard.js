/**
 * Dashboard Integration Test Script
 * 
 * To use this test:
 * 1. Open your browser's Developer Tools (F12)
 * 2. Copy and paste this entire script into the Console
 * 3. Run the test by calling: testDashboard()
 */

async function testDashboard() {
    console.log('🧪 Starting Dashboard Integration Test...\n');
    
    const API_BASE_URL = 'http://127.0.0.1:5000/api';
    const username = localStorage.getItem('currentUser');
    
    if (!username) {
        console.error('❌ No user logged in. Please login first.');
        return;
    }
    
    console.log(`✅ Current user: ${username}\n`);
    
    // Calculate date range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    const fromDate = thirtyDaysAgo.toISOString().split('T')[0];
    const toDate = today.toISOString().split('T')[0];
    
    console.log(`📅 Date range: ${fromDate} to ${toDate}\n`);
    
    // Test 1: Fetch Workouts
    console.log('Test 1: Fetching workouts...');
    try {
        const workoutsResponse = await fetch(
            `${API_BASE_URL}/workouts/${username}?from_date=${fromDate}&to_date=${toDate}`
        );
        const workoutsData = await workoutsResponse.json();
        
        if (workoutsData.success) {
            const workouts = workoutsData.workouts || [];
            console.log(`✅ Workouts fetched: ${workouts.length} workouts`);
            if (workouts.length > 0) {
                console.log(`   Sample workout:`, workouts[0]);
                // Verify field names
                if (workouts[0].duration_minutes !== undefined) {
                    console.log(`   ✅ duration_minutes field present`);
                } else {
                    console.log(`   ❌ WARNING: duration_minutes field missing!`);
                }
            }
        } else {
            console.log(`❌ Failed to fetch workouts: ${workoutsData.error}`);
        }
    } catch (error) {
        console.error(`❌ Error fetching workouts:`, error);
    }
    console.log('');
    
    // Test 2: Fetch Meals
    console.log('Test 2: Fetching meals...');
    try {
        const mealsResponse = await fetch(
            `${API_BASE_URL}/meals/${username}?from_date=${fromDate}&to_date=${toDate}`
        );
        const mealsData = await mealsResponse.json();
        
        if (mealsData.success) {
            const meals = mealsData.meals || [];
            console.log(`✅ Meals fetched: ${meals.length} meals`);
            if (meals.length > 0) {
                console.log(`   Sample meal:`, meals[0]);
                // Verify macros structure
                if (meals[0].macros && meals[0].macros.protein !== undefined) {
                    console.log(`   ✅ macros.protein field present`);
                } else {
                    console.log(`   ❌ WARNING: macros structure incorrect!`);
                }
            }
        } else {
            console.log(`❌ Failed to fetch meals: ${mealsData.error}`);
        }
    } catch (error) {
        console.error(`❌ Error fetching meals:`, error);
    }
    console.log('');
    
    // Test 3: Fetch Weight Logs
    console.log('Test 3: Fetching weight logs...');
    try {
        const weightResponse = await fetch(
            `${API_BASE_URL}/weight-logs/${username}?from_date=${fromDate}&to_date=${toDate}`
        );
        const weightData = await weightResponse.json();
        
        if (weightData.success) {
            const logs = weightData.logs || [];
            console.log(`✅ Weight logs fetched: ${logs.length} logs`);
            if (logs.length > 0) {
                console.log(`   Sample log:`, logs[0]);
                // Verify field names
                if (logs[0].weight_kg !== undefined) {
                    console.log(`   ✅ weight_kg field present`);
                } else {
                    console.log(`   ❌ WARNING: weight_kg field missing!`);
                }
            }
        } else {
            console.log(`❌ Failed to fetch weight logs: ${weightData.error}`);
        }
    } catch (error) {
        console.error(`❌ Error fetching weight logs:`, error);
    }
    console.log('');
    
    // Test 4: Check Dashboard Stats
    console.log('Test 4: Checking dashboard stats elements...');
    const totalWorkouts = document.getElementById('totalWorkouts');
    const totalMinutes = document.getElementById('totalMinutes');
    const totalMeals = document.getElementById('totalMeals');
    const currentWeight = document.getElementById('currentWeight');
    
    if (totalWorkouts && totalMinutes && totalMeals && currentWeight) {
        console.log(`✅ All stat card elements found`);
        console.log(`   Total Workouts: ${totalWorkouts.textContent}`);
        console.log(`   Total Minutes: ${totalMinutes.textContent}`);
        console.log(`   Total Meals: ${totalMeals.textContent}`);
        console.log(`   Current Weight: ${currentWeight.textContent}`);
    } else {
        console.log(`❌ Some stat card elements missing`);
        console.log(`   totalWorkouts: ${totalWorkouts ? '✅' : '❌'}`);
        console.log(`   totalMinutes: ${totalMinutes ? '✅' : '❌'}`);
        console.log(`   totalMeals: ${totalMeals ? '✅' : '❌'}`);
        console.log(`   currentWeight: ${currentWeight ? '✅' : '❌'}`);
    }
    console.log('');
    
    // Test 5: Check Charts
    console.log('Test 5: Checking chart elements...');
    const weightChartCanvas = document.getElementById('weightChart');
    const workoutChartCanvas = document.getElementById('workoutChart');
    
    if (weightChartCanvas && workoutChartCanvas) {
        console.log(`✅ All chart canvases found`);
        console.log(`   Weight Chart: ${weightChartCanvas ? '✅' : '❌'}`);
        console.log(`   Workout Chart: ${workoutChartCanvas ? '✅' : '❌'}`);
    } else {
        console.log(`❌ Some chart canvases missing`);
        console.log(`   weightChart: ${weightChartCanvas ? '✅' : '❌'}`);
        console.log(`   workoutChart: ${workoutChartCanvas ? '✅' : '❌'}`);
    }
    console.log('');
    
    console.log('🏁 Dashboard Integration Test Complete!\n');
    console.log('If you see any ❌ errors above, there may be integration issues.');
    console.log('If everything is ✅, your dashboard is working correctly!');
}

// Instructions
console.log('Dashboard Test Script Loaded!');
console.log('To run the test, type: testDashboard()');
