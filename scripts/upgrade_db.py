import os
import subprocess
import sys

def run_flask_db_upgrade():
    """Run 'flask db upgrade' using the current Python interpreter."""
    env = os.environ.copy()
    env['FLASK_APP'] = 'app.py'
    
    cmd = [sys.executable, '-m', 'flask', 'db', 'upgrade']
    print('Running:', ' '.join(cmd))
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error running upgrade")
        print(res.stdout)
        print(res.stderr)
        raise SystemExit(f'flask db upgrade failed with code {res.returncode}')
    else:
        print(res.stdout)
        print(res.stderr)

if __name__ == '__main__':
    run_flask_db_upgrade()
