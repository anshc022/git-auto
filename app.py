import os
import datetime
from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import subprocess

# Set environment variables for GitHub OAuth (Replace with your actual values)
os.environ['GITHUB_CLIENT_ID'] = 'Ov23liy0PPSPZMZYeHN4'
os.environ['GITHUB_CLIENT_SECRET'] = '57e1101894d535278fe4afdf56344daf39c840d6'

# Initialize the Flask app and OAuth object
app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Configure session to persist correctly
app.config['SESSION_COOKIE_NAME'] = 'flask_oauth_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'  # Store session in filesystem
oauth = OAuth(app)

# GitHub OAuth setup
github = oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    client_kwargs={'scope': 'repo'},
)

@app.route('/')
def index():
    # Main page with form to input repository details
    return render_template('index.html')

@app.route('/login')
def login():
    # GitHub OAuth redirect
    return github.authorize_redirect(redirect_uri=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    # Logout user
    session.pop('github_token', None)
    return redirect(url_for('index'))

@app.route('/login/authorized')
def authorized():
    # Handle OAuth callback and retrieve user info
    token = github.authorize_access_token()
    session['github_token'] = token

    user_info = github.get('https://api.github.com/user')
    user_data = user_info.json()
    name = user_data.get('name', 'No name provided')
    login = user_data.get('login', 'No username provided')
    avatar_url = user_data.get('avatar_url', '')

    # Get repositories
    repos_url = user_data.get('repos_url', '')
    repos_info = github.get(repos_url)
    repos_data = repos_info.json()

    # Render profile page
    return render_template('profile.html', name=name, login=login, avatar_url=avatar_url, repos_data=repos_data)

@app.route('/generate_commits', methods=['POST'])
def generate_commits():
    # Get user input from the form
    username = session.get('github_username')
    repo_name = request.form['repo_name']
    total_days = int(request.form['total_days'])
    commit_frequency = int(request.form['commit_frequency'])
    
    # Set GitHub repository link
    repo_link = f"https://github.com/{username}/{repo_name}.git"

    # Generate commits logic
    now = datetime.datetime.now()
    pointer = 0
    ctr = 1
    for day in range(total_days, 0, -1):
        for commit in range(commit_frequency):
            commit_date = now + datetime.timedelta(days=-pointer)
            format_date = commit_date.strftime("%Y-%m-%d")
            
            # Generate commit
            commit_message = f"commit {ctr}: {format_date}"
            os.system(f"git add .")
            os.system(f"git commit --date=\"{format_date} 12:15:10\" -m \"{commit_message}\"")
            print(f"commit {ctr}: {format_date}")
            ctr += 1
        pointer += 1

    # Push commits to GitHub
    os.system(f"git remote add origin {repo_link}")
    os.system("git branch -M main")
    os.system("git push -u origin main -f")

    return "Commits generated and pushed successfully!"

if __name__ == '__main__':
    app.run(debug=True)