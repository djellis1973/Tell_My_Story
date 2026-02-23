import streamlit as st
import json
from datetime import datetime
import pandas as pd
from pathlib import Path
import re
import hashlib
import plotly.express as px

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Tell My Story - Admin Dashboard",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SIMPLE ADMIN AUTH - Uses Streamlit secrets
# ============================================================================
def check_admin_password():
    """Simple password check for admin access using secrets"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.title("👑 Admin Dashboard Login")
        
        st.info("""
        **Note:** This is the admin dashboard login. 
        Use the admin credentials from your Streamlit secrets.
        """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Admin Username", placeholder="Enter admin username from secrets")
            password = st.text_input("Admin Password", type="password", placeholder="Enter admin password from secrets")
            
            if st.button("Login", type="primary", use_container_width=True):
                # Check against secrets
                secret_username = st.secrets.get("ADMIN_USERNAME")
                secret_password = st.secrets.get("ADMIN_PASSWORD")
                
                if not secret_username or not secret_password:
                    st.error("❌ Admin credentials not configured in secrets!")
                    st.info("Please add ADMIN_USERNAME and ADMIN_PASSWORD to your Streamlit secrets.")
                elif username == secret_username and password == secret_password:
                    st.session_state.admin_authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        return False
    return True

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================
def load_all_users():
    """Load all user accounts from the accounts folder"""
    accounts_dir = Path("accounts")
    if not accounts_dir.exists():
        return []
    
    users = []
    for account_file in accounts_dir.glob("*_account.json"):
        try:
            with open(account_file, 'r') as f:
                account = json.load(f)
            
            # Load user data file for stats
            user_id = account['user_id']
            data_file = Path(f"user_data_{hashlib.md5(user_id.encode()).hexdigest()[:8]}.json")
            
            stats = {
                'total_words': 0,
                'total_answers': 0,
                'last_active': None
            }
            
            if data_file.exists():
                with open(data_file, 'r') as f:
                    user_data = json.load(f)
                    
                # Calculate stats
                for session_id, session_data in user_data.get('responses', {}).items():
                    answers = session_data.get('questions', {})
                    stats['total_answers'] += len(answers)
                    for q_data in answers.values():
                        if q_data.get('answer'):
                            text_only = re.sub(r'<[^>]+>', '', q_data['answer'])
                            stats['total_words'] += len(re.findall(r'\w+', text_only))
                    
                    # Get last active
                    timestamps = [q.get('timestamp') for q in answers.values() if q.get('timestamp')]
                    if timestamps:
                        latest = max(timestamps)
                        if not stats['last_active'] or latest > stats['last_active']:
                            stats['last_active'] = latest
            
            # Combine account and stats
            users.append({
                'user_id': user_id,
                'email': account.get('email', ''),
                'first_name': account.get('profile', {}).get('first_name', ''),
                'last_name': account.get('profile', {}).get('last_name', ''),
                'created_at': account.get('created_at', ''),
                'last_login': account.get('last_login', ''),
                'subscription': account.get('subscription', {'status': 'free', 'tier': 'free'}),
                'total_words': stats['total_words'],
                'total_answers': stats['total_answers'],
                'last_active': stats['last_active'],
                'account_data': account
            })
        except Exception as e:
            st.error(f"Error loading {account_file}: {e}")
    
    # Sort by creation date
    users.sort(key=lambda x: x['created_at'], reverse=True)
    return users

def save_user_subscription(user_id, subscription_data):
    """Update a user's subscription status"""
    try:
        account_file = Path(f"accounts/{user_id}_account.json")
        if account_file.exists():
            with open(account_file, 'r') as f:
                account = json.load(f)
            
            account['subscription'] = subscription_data
            account['subscription']['last_updated'] = datetime.now().isoformat()
            
            with open(account_file, 'w') as f:
                json.dump(account, f, indent=2)
            
            return True
    except Exception as e:
        st.error(f"Error saving: {e}")
    return False

def check_user_exists(email):
    """Check if a user with this email already exists"""
    email_clean = email.lower().strip()
    accounts_dir = Path("accounts")
    if not accounts_dir.exists():
        return False
    
    for account_file in accounts_dir.glob("*_account.json"):
        try:
            with open(account_file, 'r') as f:
                account = json.load(f)
                if account.get('email', '').lower().strip() == email_clean:
                    return True
        except:
            pass
    return False

def test_user_login(email, password):
    """Test if a user can login - for debugging"""
    email_clean = email.lower().strip()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    accounts_dir = Path("accounts")
    if not accounts_dir.exists():
        return "No accounts folder found"
    
    for account_file in accounts_dir.glob("*_account.json"):
        try:
            with open(account_file, 'r') as f:
                account = json.load(f)
                if account.get('email', '').lower().strip() == email_clean:
                    stored_hash = account.get('password_hash', '')
                    if stored_hash == password_hash:
                        return "✅ Login would succeed!"
                    else:
                        return f"❌ Password mismatch. Stored hash: {stored_hash[:10]}..., Your hash: {password_hash[:10]}..."
        except:
            pass
    return "❌ User not found"

# ============================================================================
# MAIN ADMIN INTERFACE
# ============================================================================
if not check_admin_password():
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .user-row {
        background: white;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .active-badge {
        background: #27ae60;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .free-badge {
        background: #95a5a6;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .debug-box {
        background: #f0f0f0;
        padding: 1rem;
        border-radius: 5px;
        font-family: monospace;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="admin-header">
    <h1>👑 Tell My Story - Admin Dashboard</h1>
    <p>Manage users, subscriptions, and monitor usage</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for refresh
if 'refresh_users' not in st.session_state:
    st.session_state.refresh_users = True  # Start with True to load on first run

# Load all users (will refresh when flag is set)
if st.session_state.refresh_users:
    with st.spinner("Loading user data..."):
        users = load_all_users()
        st.session_state.users = users
        st.session_state.refresh_users = False
else:
    users = st.session_state.get('users', [])

# Sidebar stats
with st.sidebar:
    st.title("📊 Quick Stats")
    
    total_users = len(users)
    active_subs = sum(1 for u in users if u['subscription'].get('status') == 'active')
    total_words = sum(u['total_words'] for u in users)
    
    st.metric("Total Users", total_users)
    st.metric("Active Subscriptions", active_subs)
    st.metric("Total Words", f"{total_words:,}")
    
    st.divider()
    
    if st.button("🔄 Refresh User List", use_container_width=True):
        st.session_state.refresh_users = True
        st.rerun()
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 User Management", 
    "📈 Analytics", 
    "➕ Add User",
    "🔧 Debug Login"
])

with tab1:
    st.header("User Management")
    
    # Search
    search = st.text_input("🔍 Search by email or name", placeholder="Type to filter...")
    
    # Filter users
    filtered_users = users.copy()
    
    if search:
        search_lower = search.lower()
        filtered_users = [
            u for u in filtered_users 
            if search_lower in u['email'].lower() or 
               search_lower in f"{u['first_name']} {u['last_name']}".lower()
        ]
    
    st.info(f"Showing {len(filtered_users)} users")
    
    # User list
    for user in filtered_users:
        status = user['subscription'].get('status', 'free')
        tier = user['subscription'].get('tier', 'free')
        
        # Status badge
        if status == 'active':
            badge = f'<span class="active-badge">✅ ACTIVE ({tier})</span>'
        else:
            badge = '<span class="free-badge">🆓 FREE</span>'
        
        # Created date
        created = datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d') if user['created_at'] else 'Unknown'
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"""
                **{user['email']}** - {user['first_name']} {user['last_name']}  
                <small>📅 Joined: {created} | 📝 {user['total_words']:,} words</small>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(badge, unsafe_allow_html=True)
            with col3:
                if st.button("✏️ Edit", key=f"edit_{user['user_id']}"):
                    st.session_state['editing_user'] = user
                    st.rerun()
            with col4:
                if st.button("🗑️ Delete", key=f"delete_{user['user_id']}"):
                    st.session_state['deleting_user'] = user
                    st.rerun()
            st.markdown("---")
    
    # Edit user modal
    if 'editing_user' in st.session_state:
        user = st.session_state['editing_user']
        
        st.divider()
        st.subheader(f"✏️ Edit Subscription: {user['email']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_status = user['subscription'].get('status', 'free')
            new_status = st.selectbox(
                "Subscription Status",
                ["free", "active"],
                index=0 if current_status == "free" else 1
            )
            
            if new_status == "active":
                tier = st.selectbox(
                    "Tier",
                    ["premium", "lifetime"],
                    index=0 if user['subscription'].get('tier') == "premium" else 1
                )
            else:
                tier = "free"
            
            if st.button("💾 Save Changes", type="primary"):
                subscription_data = {
                    "status": new_status,
                    "tier": tier,
                    "last_updated": datetime.now().isoformat()
                }
                
                if save_user_subscription(user['user_id'], subscription_data):
                    st.success(f"✅ Updated subscription for {user['email']}")
                    st.session_state.refresh_users = True
                    del st.session_state['editing_user']
                    st.rerun()
        
        with col2:
            st.write("**Current Stats:**")
            st.write(f"Words: {user['total_words']:,}")
            st.write(f"Answers: {user['total_answers']}")
        
        if st.button("← Cancel"):
            del st.session_state['editing_user']
            st.rerun()
    
    # Delete confirmation
    if 'deleting_user' in st.session_state:
        user = st.session_state['deleting_user']
        
        st.warning(f"⚠️ Are you sure you want to delete {user['email']}? This cannot be undone!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete"):
                # Delete account file
                account_file = Path(f"accounts/{user['user_id']}_account.json")
                data_file = Path(f"user_data_{hashlib.md5(user['user_id'].encode()).hexdigest()[:8]}.json")
                
                if account_file.exists():
                    account_file.unlink()
                if data_file.exists():
                    data_file.unlink()
                
                st.success(f"User {user['email']} deleted")
                st.session_state.refresh_users = True
                del st.session_state['deleting_user']
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                del st.session_state['deleting_user']
                st.rerun()

with tab2:
    st.header("Analytics Dashboard")
    
    if users:
        # Convert to DataFrame
        df = pd.DataFrame(users)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", len(df))
        with col2:
            active_count = len(df[df['subscription'].apply(lambda x: x.get('status') == 'active')])
            st.metric("Active Subscriptions", active_count)
        with col3:
            st.metric("Total Words", f"{df['total_words'].sum():,}")
        
        # Simple chart
        st.subheader("Subscription Status")
        status_counts = df['subscription'].apply(lambda x: x.get('status', 'free')).value_counts()
        st.bar_chart(status_counts)
        
    else:
        st.info("No user data available")

with tab3:
    st.header("Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*")
            email = st.text_input("Email*")
        with col2:
            last_name = st.text_input("Last Name*")
            password = st.text_input("Password*", type="password")
        
        status = st.selectbox("Subscription Status", ["active", "free"])
        
        # Add a unique key to prevent double submission
        submitted = st.form_submit_button("Create User", type="primary")
        
        if submitted:
            if first_name and last_name and email and password:
                # Check if user already exists
                if check_user_exists(email):
                    st.error(f"❌ User with email {email} already exists!")
                else:
                    # Create user ID
                    user_id = hashlib.sha256(f"{email}{datetime.now()}".encode()).hexdigest()[:12]
                    
                    # Clean email
                    email_clean = email.lower().strip()
                    
                    # Create account data
                    account = {
                        "user_id": user_id,
                        "email": email_clean,
                        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
                        "account_type": "self",
                        "created_at": datetime.now().isoformat(),
                        "last_login": None,
                        "profile": {
                            "first_name": first_name.strip(),
                            "last_name": last_name.strip(),
                            "email": email_clean,
                            "gender": "",
                            "birthdate": "",
                            "timeline_start": "",
                            "occupation": "",
                            "hometown": "",
                            "current_location": "",
                            "family": "",
                            "education": "",
                            "life_philosophy": "",
                            "legacy_hopes": ""
                        },
                        "narrative_gps": {},
                        "privacy_settings": {
                            "profile_public": False,
                            "stories_public": False,
                            "allow_sharing": False,
                            "data_collection": True,
                            "encryption": True
                        },
                        "settings": {
                            "email_notifications": True,
                            "auto_save": True,
                            "privacy_level": "private",
                            "theme": "light",
                            "email_verified": False,
                            "daily_word_goal": 500
                        },
                        "stats": {
                            "total_sessions": 0,
                            "total_words": 0,
                            "account_age_days": 0,
                            "last_active": datetime.now().isoformat()
                        },
                        "streak_data": {
                            "current_streak": 0,
                            "longest_streak": 0,
                            "last_write_date": None,
                            "streak_history": [],
                            "milestones": {
                                "first_story": False,
                                "seven_day_streak": False,
                                "five_thousand_words": False,
                                "first_session_complete": False
                            }
                        },
                        "subscription": {
                            "status": status,
                            "tier": "premium" if status == "active" else "free",
                            "activated_at": datetime.now().isoformat() if status == "active" else None,
                            "expires_at": None,
                            "notes": "",
                            "last_updated": datetime.now().isoformat()
                        }
                    }
                    
                    # Save account
                    Path("accounts").mkdir(exist_ok=True)
                    account_file = Path(f"accounts/{user_id}_account.json")
                    with open(account_file, 'w') as f:
                        json.dump(account, f, indent=2)
                    
                    # Create empty data file
                    data_file = Path(f"user_data_{hashlib.md5(user_id.encode()).hexdigest()[:8]}.json")
                    with open(data_file, 'w') as f:
                        json.dump({"responses": {}}, f)
                    
                    st.success(f"✅ User created successfully!")
                    st.info(f"Email: {email_clean}\nPassword: {password}")
                    
                    # Test the login immediately
                    test_result = test_user_login(email_clean, password)
                    if "✅" in test_result:
                        st.success(f"Login test: {test_result}")
                    else:
                        st.error(f"Login test: {test_result}")
                    
                    # Force refresh
                    st.session_state.refresh_users = True
                    st.rerun()
            else:
                st.error("Please fill all required fields")

with tab4:
    st.header("🔧 Debug Login Tool")
    st.write("Test if a user can login to the main app")
    
    col1, col2 = st.columns(2)
    with col1:
        test_email = st.text_input("Test Email", key="test_email")
    with col2:
        test_password = st.text_input("Test Password", type="password", key="test_password")
    
    if st.button("Test Login", type="primary"):
        if test_email and test_password:
            result = test_user_login(test_email, test_password)
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)
        else:
            st.warning("Enter email and password")
    
    # Show raw account files for debugging
    with st.expander("📁 View Raw Account Files"):
        accounts_dir = Path("accounts")
        if accounts_dir.exists():
            for account_file in accounts_dir.glob("*_account.json"):
                with open(account_file, 'r') as f:
                    data = json.load(f)
                st.json(data)
        else:
            st.info("No accounts folder found")
