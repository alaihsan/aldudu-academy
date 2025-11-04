import os
import subprocess
import sys

def run_flask_db_migrate(message):
    """Run 'flask db migrate' using the current Python interpreter."""
    env = os.environ.copy()
    env['FLASK_APP'] = 'app:create_app'
    
    cmd = [sys.executable, '-m', 'flask', 'db', 'migrate', '-m', message]
    print('Running:', ' '.join(cmd))
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error running migration")
        print(res.stdout)
        print(res.stderr)
        raise SystemExit(f'flask db migrate failed with code {res.returncode}')
    else:
        print(res.stdout)
        print(res.stderr)

if __name__ == '__main__':
    run_flask_db_migrate('Add created_at and updated_at to quiz')
