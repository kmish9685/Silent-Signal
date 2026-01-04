# SilentSignal MVP

**SilentSignal** is an AI-powered anonymous campus feedback tool. It allows students to send one-click signals about their environment (e.g., "Confusing", "Time-Wasting", "Idea") which are aggregated into a dashboard with real-time insights.

## Features
- **Anonymous Submission**: No login required.
- **One-Click Signals**: 5 preset buttons for quick feedback.
- **Context Awareness**: Users can select their location (Classroom, Library, etc.).
- **Live Dashboard**: Visualizes signal trends and heatmaps.
- **AI Insights**: Automatically detects top pain points and location hotspots.

## Project Structure
```
Silent Signal/
├── app.py              # Main Flask application & API
├── requirements.txt    # Dependencies
├── static/
│   ├── style.css       # Modern dark-themed styling
│   └── script.js       # Frontend logic (submission & charts)
└── templates/
    ├── index.html      # Student submission interface
    └── dashboard.html  # Admin insights dashboard
```

## Setup & Run locally

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    python app.py
    ```

3.  **Access the App**:
    - **Submission Page**: [http://localhost:5001](http://localhost:5001)
    - **Dashboard**: [http://localhost:5001/dashboard](http://localhost:5001/dashboard)

## Technologies
- **Backend**: Python (Flask, SQLAlchemy, Pandas)
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Visualization**: Chart.js
- **Database**: SQLite (built-in)

## Demo Notes
- The app runs on **port 5001** by default to avoid conflicts.
- "AI Insights" are generated based on simple aggregation and trend detection rules defined in `app.py`.
