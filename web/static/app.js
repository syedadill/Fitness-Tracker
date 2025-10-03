// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State Management
let currentUser = null;
let weightChart = null;
let workoutPieChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setTodayDates();
});

// ============================================================================
// Authentication & Session Management
// ============================================================================

function checkAuth() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = savedUser;
        showDashboard();
    } else {
        showAuthSection();
    }
}

function showAuthSection() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
}

function showDashboard() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('currentUsername').textContent = `Welcome, ${currentUser}!`;
    
    loadDashboardData();
}

function showAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.auth-tab');
    
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    }
}

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${username}`);
        const data = await response.json();
        
        if (data.success) {
            currentUser = username;
            localStorage.setItem('currentUser', username);
            showToast('Login successful!', 'success');
            showDashboard();
        } else {
            showToast('User not found', 'error');
        }
    } catch (error) {
        showToast('Login failed: ' + error.message, 'error');
    }
}

async function register(event) {
    event.preventDefault();
    
    const userData = {
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        full_name: document.getElementById('regFullName').value || undefined,
        target_weight: parseFloat(document.getElementById('regTargetWeight').value) || undefined,
        weekly_workout_minutes: parseInt(document.getElementById('regWeeklyMinutes').value) || undefined
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Registration successful!', 'success');
            currentUser = userData.username;
            localStorage.setItem('currentUser', userData.username);
            showDashboard();
        } else {
            showToast('Registration failed: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Registration failed: ' + error.message, 'error');
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    showToast('Logged out successfully', 'success');
    showAuthSection();
}

// ============================================================================
// Navigation & Tab Management
// ============================================================================

function showTab(tabName) {
    const tabs = document.querySelectorAll('.nav-tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Load data for the selected tab
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'workouts':
            loadWorkouts();
            break;
        case 'meals':
            loadMeals();
            break;
        case 'weight':
            loadWeightLogs();
            break;
    }
}

// ============================================================================
// Dashboard
// ============================================================================

async function loadDashboardData() {
    if (!currentUser) return;
    
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    // Format dates as YYYY-MM-DD in local timezone
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    const fromDate = formatDate(thirtyDaysAgo);
    const toDate = formatDate(today);
    
    try {
        // Load workouts
        const workoutsResponse = await fetch(
            `${API_BASE_URL}/workouts/${currentUser}?from_date=${fromDate}&to_date=${toDate}`
        );
        const workoutsData = await workoutsResponse.json();
        
        // Load meals
        const mealsResponse = await fetch(
            `${API_BASE_URL}/meals/${currentUser}?from_date=${fromDate}&to_date=${toDate}`
        );
        const mealsData = await mealsResponse.json();
        
        // Load weight logs
        const weightResponse = await fetch(
            `${API_BASE_URL}/weight-logs/${currentUser}?from_date=${fromDate}&to_date=${toDate}`
        );
        const weightData = await weightResponse.json();
        
        updateDashboardStats(workoutsData.workouts || [], mealsData.meals || [], weightData.logs || []);
        updateWeightChart(weightData.logs || []);
        updateWorkoutChart(workoutsData.workouts || []);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Error loading dashboard data', 'error');
    }
}

function updateDashboardStats(workouts, meals, weightLogs) {
    const totalMinutes = workouts.reduce((sum, w) => sum + w.duration_minutes, 0);
    const currentWeight = weightLogs.length > 0 ? weightLogs[weightLogs.length - 1].weight_kg : '--';
    
    document.getElementById('totalWorkouts').textContent = workouts.length;
    document.getElementById('totalMinutes').textContent = totalMinutes;
    document.getElementById('totalMeals').textContent = meals.length;
    document.getElementById('currentWeight').textContent = currentWeight !== '--' ? currentWeight.toFixed(1) : '--';
}

function updateWeightChart(logs) {
    const ctx = document.getElementById('weightChart');
    
    if (weightChart) {
        weightChart.destroy();
    }
    
    const sortedLogs = logs.sort((a, b) => new Date(a.date) - new Date(b.date));
    const labels = sortedLogs.map(log => new Date(log.date).toLocaleDateString());
    const data = sortedLogs.map(log => log.weight_kg);
    
    weightChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Weight (kg)',
                data: data,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function updateWorkoutChart(workouts) {
    const ctx = document.getElementById('workoutChart');
    
    if (workoutPieChart) {
        workoutPieChart.destroy();
    }
    
    // Count workouts by type
    const workoutTypes = {};
    workouts.forEach(workout => {
        workoutTypes[workout.type] = (workoutTypes[workout.type] || 0) + 1;
    });
    
    const labels = Object.keys(workoutTypes);
    const data = Object.values(workoutTypes);
    const colors = [
        '#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'
    ];
    
    workoutPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ============================================================================
// Workouts Management
// ============================================================================

function showAddWorkoutForm() {
    document.getElementById('addWorkoutForm').style.display = 'block';
    document.getElementById('workoutDate').value = new Date().toISOString().split('T')[0];
}

function hideAddWorkoutForm() {
    document.getElementById('addWorkoutForm').style.display = 'none';
    document.getElementById('addWorkoutForm').querySelector('form').reset();
}

async function addWorkout(event) {
    event.preventDefault();
    
    const workoutData = {
        user_id: currentUser,
        type: document.getElementById('workoutType').value,
        duration_minutes: parseInt(document.getElementById('workoutDuration').value),
        intensity: document.getElementById('workoutIntensity').value,
        date: document.getElementById('workoutDate').value,
        notes: document.getElementById('workoutNotes').value || undefined
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/workouts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(workoutData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Workout added successfully!', 'success');
            hideAddWorkoutForm();
            loadWorkouts();
        } else {
            showToast('Failed to add workout: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function loadWorkouts() {
    if (!currentUser) return;
    
    const fromDate = document.getElementById('workoutsFromDate').value;
    const toDate = document.getElementById('workoutsToDate').value;
    
    let url = `${API_BASE_URL}/workouts/${currentUser}`;
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            displayWorkouts(data.workouts);
        } else {
            showToast('Failed to load workouts', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function displayWorkouts(workouts) {
    const container = document.getElementById('workoutsList');
    
    if (workouts.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🏋️</div><p>No workouts found. Add your first workout!</p></div>';
        return;
    }
    
    container.innerHTML = workouts.map(workout => `
        <div class="item-card">
            <div class="item-header">
                <div>
                    <div class="item-title">${workout.type.charAt(0).toUpperCase() + workout.type.slice(1)}</div>
                    <div class="item-date">${new Date(workout.date).toLocaleDateString()}</div>
                </div>
                <span class="badge badge-${workout.intensity}">${workout.intensity.toUpperCase()}</span>
            </div>
            <div class="item-details">
                <div class="item-detail">
                    <span class="item-detail-label">Duration</span>
                    <span class="item-detail-value">${workout.duration_minutes} min</span>
                </div>
                ${workout.notes ? `
                <div class="item-detail">
                    <span class="item-detail-label">Notes</span>
                    <span class="item-detail-value">${workout.notes}</span>
                </div>
                ` : ''}
            </div>
            <div class="item-actions">
                <button class="btn btn-danger" onclick="deleteWorkout('${workout._id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function deleteWorkout(workoutId) {
    if (!confirm('Are you sure you want to delete this workout?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/workouts/${workoutId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Workout deleted successfully', 'success');
            loadWorkouts();
        } else {
            showToast('Failed to delete workout', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// Meals Management
// ============================================================================

function showAddMealForm() {
    document.getElementById('addMealForm').style.display = 'block';
    const now = new Date();
    // Format for datetime-local input (YYYY-MM-DDThh:mm)
    // Use local time, not UTC
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('mealTime').value = `${year}-${month}-${day}T${hours}:${minutes}`;
}

function hideAddMealForm() {
    document.getElementById('addMealForm').style.display = 'none';
    document.getElementById('addMealForm').querySelector('form').reset();
}

async function addMeal(event) {
    event.preventDefault();
    
    const protein = parseFloat(document.getElementById('mealProtein').value) || 0;
    const carbs = parseFloat(document.getElementById('mealCarbs').value) || 0;
    const fat = parseFloat(document.getElementById('mealFat').value) || 0;
    
    const mealData = {
        user_id: currentUser,
        name: document.getElementById('mealName').value,
        calories: parseInt(document.getElementById('mealCalories').value),
        time: document.getElementById('mealTime').value,
        macros: {
            protein: protein,
            carbs: carbs,
            fat: fat
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/meals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mealData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Meal added successfully!', 'success');
            hideAddMealForm();
            loadMeals();
        } else {
            showToast('Failed to add meal: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function loadMeals() {
    if (!currentUser) return;
    
    const fromDate = document.getElementById('mealsFromDate').value;
    const toDate = document.getElementById('mealsToDate').value;
    
    let url = `${API_BASE_URL}/meals/${currentUser}`;
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            displayMeals(data.meals);
        } else {
            showToast('Failed to load meals', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function displayMeals(meals) {
    const container = document.getElementById('mealsList');
    
    if (meals.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🍽️</div><p>No meals found. Log your first meal!</p></div>';
        return;
    }
    
    container.innerHTML = meals.map(meal => `
        <div class="item-card">
            <div class="item-header">
                <div>
                    <div class="item-title">${meal.name}</div>
                    <div class="item-date">${new Date(meal.time).toLocaleString()}</div>
                </div>
            </div>
            <div class="item-details">
                <div class="item-detail">
                    <span class="item-detail-label">Calories</span>
                    <span class="item-detail-value">${meal.calories} kcal</span>
                </div>
                ${meal.macros && meal.macros.protein !== undefined ? `
                <div class="item-detail">
                    <span class="item-detail-label">Protein</span>
                    <span class="item-detail-value">${meal.macros.protein}g</span>
                </div>
                ` : ''}
                ${meal.macros && meal.macros.carbs !== undefined ? `
                <div class="item-detail">
                    <span class="item-detail-label">Carbs</span>
                    <span class="item-detail-value">${meal.macros.carbs}g</span>
                </div>
                ` : ''}
                ${meal.macros && meal.macros.fat !== undefined ? `
                <div class="item-detail">
                    <span class="item-detail-label">Fat</span>
                    <span class="item-detail-value">${meal.macros.fat}g</span>
                </div>
                ` : ''}
            </div>
            <div class="item-actions">
                <button class="btn btn-danger" onclick="deleteMeal('${meal._id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function deleteMeal(mealId) {
    if (!confirm('Are you sure you want to delete this meal?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/meals/${mealId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Meal deleted successfully', 'success');
            loadMeals();
        } else {
            showToast('Failed to delete meal', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// Weight Logs Management
// ============================================================================

function showAddWeightForm() {
    document.getElementById('addWeightForm').style.display = 'block';
    document.getElementById('weightDate').value = new Date().toISOString().split('T')[0];
}

function hideAddWeightForm() {
    document.getElementById('addWeightForm').style.display = 'none';
    document.getElementById('addWeightForm').querySelector('form').reset();
}

async function addWeight(event) {
    event.preventDefault();
    
    const weightData = {
        user_id: currentUser,
        weight_kg: parseFloat(document.getElementById('weightValue').value),
        date: document.getElementById('weightDate').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/weight-logs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(weightData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Weight logged successfully!', 'success');
            hideAddWeightForm();
            loadWeightLogs();
        } else {
            showToast('Failed to log weight: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function loadWeightLogs() {
    if (!currentUser) return;
    
    const fromDate = document.getElementById('weightFromDate').value;
    const toDate = document.getElementById('weightToDate').value;
    
    let url = `${API_BASE_URL}/weight-logs/${currentUser}`;
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            displayWeightLogs(data.logs);
        } else {
            showToast('Failed to load weight logs', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function displayWeightLogs(logs) {
    const container = document.getElementById('weightLogsList');
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚖️</div><p>No weight logs found. Log your weight!</p></div>';
        return;
    }
    
    // Sort by date descending
    const sortedLogs = logs.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    container.innerHTML = sortedLogs.map(log => `
        <div class="item-card">
            <div class="item-header">
                <div>
                    <div class="item-title">${log.weight_kg} kg</div>
                    <div class="item-date">${new Date(log.date).toLocaleDateString()}</div>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn btn-danger" onclick="deleteWeightLog('${log._id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function deleteWeightLog(logId) {
    if (!confirm('Are you sure you want to delete this weight log?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/weight-logs/${logId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Weight log deleted successfully', 'success');
            loadWeightLogs();
        } else {
            showToast('Failed to delete weight log', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// Reports
// ============================================================================

async function generateReport() {
    if (!currentUser) return;
    
    const fromDate = document.getElementById('reportFromDate').value;
    const toDate = document.getElementById('reportToDate').value;
    
    if (!fromDate || !toDate) {
        showToast('Please select both from and to dates', 'error');
        return;
    }
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/reports/${currentUser}?from_date=${fromDate}&to_date=${toDate}`
        );
        const data = await response.json();
        
        if (data.success) {
            displayReport(data.report);
        } else {
            showToast('Failed to generate report: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function displayReport(report) {
    const container = document.getElementById('reportContent');
    
    let html = `
        <h2>Fitness Report for ${report.user.username}</h2>
        <p class="item-date">Period: ${new Date(report.period.start_date).toLocaleDateString()} to ${new Date(report.period.end_date).toLocaleDateString()} (${report.period.days} days)</p>
    `;
    
    // Workout section
    if (report.workouts) {
        const ws = report.workouts;
        html += `
            <div class="report-section">
                <h3>🏋️ Workouts</h3>
                <div class="report-stats">
                    <div class="report-stat">
                        <div class="report-stat-label">Total Sessions</div>
                        <div class="report-stat-value">${ws.total_workouts}</div>
                    </div>
                    <div class="report-stat">
                        <div class="report-stat-label">Total Minutes</div>
                        <div class="report-stat-value">${ws.total_minutes}</div>
                    </div>
                    <div class="report-stat">
                        <div class="report-stat-label">Average Duration</div>
                        <div class="report-stat-value">${ws.average_duration.toFixed(1)} min</div>
                    </div>
                </div>
                ${ws.intensity_breakdown ? `
                <p>Intensity: ${ws.intensity_breakdown.low || 0} low, ${ws.intensity_breakdown.medium || 0} medium, ${ws.intensity_breakdown.high || 0} high</p>
                ` : ''}
            </div>
        `;
    }
    
    // Nutrition section
    if (report.nutrition) {
        const ns = report.nutrition;
        html += `
            <div class="report-section">
                <h3>🍽️ Nutrition</h3>
                <div class="report-stats">
                    <div class="report-stat">
                        <div class="report-stat-label">Meals Logged</div>
                        <div class="report-stat-value">${ns.total_meals}</div>
                    </div>
                    <div class="report-stat">
                        <div class="report-stat-label">Avg Daily Calories</div>
                        <div class="report-stat-value">${ns.average_daily_calories.toFixed(1)}</div>
                    </div>
                </div>
                ${ns.average_daily_macros ? `
                <p>Average daily macros: P:${ns.average_daily_macros.protein.toFixed(1)}g, C:${ns.average_daily_macros.carbs.toFixed(1)}g, F:${ns.average_daily_macros.fat.toFixed(1)}g</p>
                ` : ''}
            </div>
        `;
    }
    
    // Weight section
    if (report.weight) {
        const wt = report.weight;
        html += `
            <div class="report-section">
                <h3>⚖️ Weight</h3>
                <div class="report-stats">
                    <div class="report-stat">
                        <div class="report-stat-label">Measurements</div>
                        <div class="report-stat-value">${wt.entries}</div>
                    </div>
                    ${wt.start_weight ? `
                    <div class="report-stat">
                        <div class="report-stat-label">Start Weight</div>
                        <div class="report-stat-value">${wt.start_weight} kg</div>
                    </div>
                    ` : ''}
                    ${wt.end_weight ? `
                    <div class="report-stat">
                        <div class="report-stat-label">End Weight</div>
                        <div class="report-stat-value">${wt.end_weight} kg</div>
                    </div>
                    ` : ''}
                    ${wt.change !== undefined && wt.change !== null ? `
                    <div class="report-stat">
                        <div class="report-stat-label">Change</div>
                        <div class="report-stat-value">${wt.change > 0 ? '+' : ''}${wt.change} kg</div>
                    </div>
                    ` : ''}
                </div>
                ${wt.trend ? `<p>Trend: ${wt.trend}</p>` : ''}
            </div>
        `;
    }
    
    // Summary section
    if (report.summary) {
        html += `
            <div class="report-section">
                <h3>� Summary</h3>
                <pre style="white-space: pre-wrap; font-family: inherit;">${report.summary}</pre>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ============================================================================
// Utility Functions
// ============================================================================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function setTodayDates() {
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const thirtyDaysAgoStr = thirtyDaysAgo.toISOString().split('T')[0];
    
    // Set default date ranges
    document.getElementById('workoutsFromDate').value = thirtyDaysAgoStr;
    document.getElementById('workoutsToDate').value = today;
    document.getElementById('mealsFromDate').value = thirtyDaysAgoStr;
    document.getElementById('mealsToDate').value = today;
    document.getElementById('weightFromDate').value = thirtyDaysAgoStr;
    document.getElementById('weightToDate').value = today;
    document.getElementById('reportFromDate').value = thirtyDaysAgoStr;
    document.getElementById('reportToDate').value = today;
}
