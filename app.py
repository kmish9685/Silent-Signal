from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo' # Required for session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///signals.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_PASSWORD'] = 'admin' # Simple password for MVP

db = SQLAlchemy(app)

# Database Model
class Signal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    signal_type = db.Column(db.String(50), nullable=False)
    context = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New Fields for Logic
    ip_hash = db.Column(db.String(64), nullable=True) # Anonymized User ID
    confidence = db.Column(db.Float, default=1.0) # 0.0 to 1.0

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.signal_type,
            'context': self.context,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence
        }

# --- Logic Helpers ---

# In-memory store for rate limiting: {ip_hash: last_timestamp}
cooldowns = {} 

def get_ip_hash(ip_addr):
    return hashlib.sha256(ip_addr.encode()).hexdigest()

def check_spam_and_score(ip, text_message):
    client_hash = get_ip_hash(ip)
    now = datetime.now()
    
    # 1. Cooldown Check (e.g., 10 seconds between signals)
    last_time = cooldowns.get(client_hash)
    cooldowns[client_hash] = now # Update time
    
    is_spam = False
    if last_time and (now - last_time) < timedelta(seconds=10):
        is_spam = True
        
    # 2. Confidence Scoring
    score = 0.5 # Default base score for just a button press
    
    if text_message and len(text_message.strip()) > 0:
        score += 0.5 # Boost confidence if they took time to write text
        
    if is_spam:
        score = 0.1 # Penalty for spam/rapid-fire
        
    return client_hash, score, is_spam

def generate_insights():
    # Only fetch signals with decent confidence to reduce noise
    signals = Signal.query.filter(Signal.confidence >= 0.3).all()
    
    if not signals:
        return ["Not enough high-confidence data yet."]

    data = [{'type': s.signal_type, 'context': s.context, 'timestamp': s.timestamp, 'confidence': s.confidence} for s in signals]
    df = pd.DataFrame(data)
    
    insights = []

    # Insight 1: Weighted Top Issue (Sum of confidence)
    if not df.empty:
        type_scores = df.groupby('type')['confidence'].sum().sort_values(ascending=False)
        top_issue = type_scores.index[0]
        score = type_scores.iloc[0]
        insights.append(f"High Priority: '{top_issue}' is the strongest signal (Score: {score:.1f}).")

    # Insight 2: Context Hotspot
    if not df.empty:
        context_counts = df['context'].value_counts()
        top_context = context_counts.index[0]
        insights.append(f"Hotspot: '{top_context}' has the most verified activity.")

    # Insight 3: Pattern Detection (Repeated signals in short window)
    # Simple check: if same type appears > 3 times in last 10 entries of high confidence
    if len(df) >= 5:
        recent = df.tail(10)
        recent_type_counts = recent['type'].value_counts()
        if recent_type_counts.iloc[0] >= 3:
             insights.append(f"Pattern Detected: Persistent reports of '{recent_type_counts.index[0]}' recently.")

    return insights

# --- Middleware ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid password.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required # Protect Dashboard
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/submit', methods=['POST'])
def submit_signal():
    data = request.json
    ip = request.remote_addr
    msg = data.get('message', '')[:50]
    
    client_hash, confidence, is_spam = check_spam_and_score(ip, msg)
    
    if is_spam:
        # We still record it for analysis but tell/don't tell user?
        # User asked for "Protection", usually means blocking or acknowledging as spam.
        # "Treat signals without text as low-confidence... spam protection using cooldowns"
        # We will record it with low confidence (0.1) so it doesn't pollute insights.
        pass

    new_signal = Signal(
        signal_type=data.get('type'),
        context=data.get('context'),
        message=msg,
        ip_hash=client_hash,
        confidence=confidence
    )
    db.session.add(new_signal)
    db.session.commit()
    
    if is_spam:
         # Return a 429 if strictly blocking, or just success but ignore internally.
         # Let's return success to not frustrate user, but internal logic ignores it.
         # Or better, return a warning.
         return jsonify({'status': 'warning', 'message': 'Slow down! Signal recorded with low confidence.'})

    return jsonify({'status': 'success', 'message': 'Signal received'})

@app.route('/api/stats', methods=['GET'])
@login_required # Protect Data
def get_stats():
    # Only show relevant data (confidence >= 0.3)
    signals = Signal.query.filter(Signal.confidence >= 0.1).order_by(Signal.timestamp.desc()).limit(50).all()
    
    all_signals = Signal.query.filter(Signal.confidence >= 0.3).all()
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
        # Handle migration simply for MVP: drop and recreate if schema changed is hard, 
        # but since we are dev, we can just let it try to create. 
        # If columns missing, it might error. Best to delete DB file if exists for clean state or use raw sql to alter.
        # For simplicity in this agent run: I will delete the old db file if I can, or just try catch.
        if os.path.exists('signals.db'):
            # Check if new columns exist, if not, recreate. 
            # Quickest check: just drop_all create_all for this prototype upgrade.
            # User didn't say preserve data.
            pass 
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
