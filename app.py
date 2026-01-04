from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///signals.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Signal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    signal_type = db.Column(db.String(50), nullable=False)
    context = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=True) # Optional text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.signal_type,
            'context': self.context,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

# AI Logic (Simple rule-based)
def generate_insights():
    signals = Signal.query.all()
    if not signals:
        return ["No data available yet. Start submitting signals!"]

    data = [{'type': s.signal_type, 'context': s.context, 'timestamp': s.timestamp} for s in signals]
    df = pd.DataFrame(data)

    insights = []
    
    # Insight 1: Most Common Issue
    top_issue = df['type'].mode()[0]
    count = df[df['type'] == top_issue].shape[0]
    insights.append(f"Top Pain Point: ' {top_issue}' is the most reported signal ({count} reports).")

    # Insight 2: Context with most friction
    top_context = df['context'].mode()[0]
    insights.append(f"Hotspot Alert: The '{top_context}' area is receiving the highest volume of feedback.")

    # Insight 3: Recent Activity (Spike Detection - crude)
    # Check last 5 signals for a trend
    if len(df) >= 5:
        recent = df.tail(5)
        recent_top_type = recent['type'].mode()[0]
        insights.append(f"Trending Now: Recent reports are dominated by '{recent_top_type}'.")
    
    return insights

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/submit', methods=['POST'])
def submit_signal():
    data = request.json
    new_signal = Signal(
        signal_type=data.get('type'),
        context=data.get('context'),
        message=data.get('message', '')[:50] # Truncate to avoid abuse, user said max 5 words approx
    )
    db.session.add(new_signal)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Signal received'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    signals = Signal.query.order_by(Signal.timestamp.desc()).limit(50).all()
    
    # Counts for charts
    all_signals = Signal.query.all()
    df = pd.DataFrame([{'type': s.signal_type, 'context': s.context} for s in all_signals])
    
    type_counts = df['type'].value_counts().to_dict() if not df.empty else {}
    context_counts = df['context'].value_counts().to_dict() if not df.empty else {}

    return jsonify({
        'recent_signals': [s.to_dict() for s in signals],
        'type_counts': type_counts,
        'context_counts': context_counts,
        'insights': generate_insights()
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
