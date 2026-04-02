"""Script untuk commit dan push perubahan ke GitHub"""
import subprocess
import sys
import os

# Change to project directory
os.chdir(r'C:\Users\iksan\dev\aldudu-academy')

def run_git_command(args):
    """Run git command and return output"""
    try:
        # Try using Git for Windows default installation path
        git_paths = [
            r'C:\Program Files\Git\cmd\git.exe',
            r'C:\Program Files (x86)\Git\cmd\git.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Git\cmd\git.exe'),
        ]
        
        git_exe = None
        for path in git_paths:
            if os.path.exists(path):
                git_exe = path
                break
        
        if git_exe:
            cmd = [git_exe] + args
        else:
            # Fallback to git in PATH
            cmd = ['git'] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=r'C:\Users\iksan\dev\aldudu-academy'
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        
        return result.stdout
    
    except Exception as e:
        print(f"Exception: {e}")
        return None

# Step 1: Check status
print("=" * 60)
print("GIT STATUS")
print("=" * 60)
status = run_git_command(['status', '--short'])
if status:
    print(status)
else:
    print("Could not get git status. Please run git commands manually.")
    sys.exit(1)

# Step 2: Add changed files
print("\n" + "=" * 60)
print("ADDING FILES")
print("=" * 60)

files_to_add = [
    'app/services/rasch_threshold_service.py',
    'app/services/rasch_analysis_service.py',
    'app/services/rasch_anchor_service.py',
    'app/services/rasch_scheduled_service.py',
    'app/blueprints/rasch.py',
    'docs/cron_job_setup.md',
]

for file in files_to_add:
    result = run_git_command(['add', file])
    if result is not None:
        print(f"✓ Added: {file}")
    else:
        print(f"✗ Failed to add: {file}")

# Step 3: Check diff
print("\n" + "=" * 60)
print("STAGED CHANGES")
print("=" * 60)
diff = run_git_command(['diff', '--cached', '--stat'])
if diff:
    print(diff)

# Step 4: Commit
print("\n" + "=" * 60)
print("COMMITTING")
print("=" * 60)

commit_message = """Fix: Critical backend bugs & workflow improvements

Bug Fixes (Critical):
1. Infinite auto-trigger loop - Add status check before triggering analysis
2. Extreme score bias - Exclude extreme scores from JMLE, use extrapolation

Workflow Improvements:
1. Anchor values mechanism for late submissions
2. Scheduled batch service for nightly re-analysis
3. Auto-process late submissions using anchor values
4. Bloom taxonomy UX - Add optional feature indicators

New Files:
- app/services/rasch_anchor_service.py
- app/services/rasch_scheduled_service.py
- docs/cron_job_setup.md

Modified Files:
- app/services/rasch_threshold_service.py
- app/services/rasch_analysis_service.py
- app/blueprints/rasch.py

API Endpoints Added:
- POST /quizzes/<id>/process-late-submissions
- POST /analyses/<id>/re-run
- POST /admin/batch/nightly-analysis
- POST /admin/batch/late-submissions
"""

commit_result = run_git_command(['commit', '-m', commit_message])
if commit_result:
    print(commit_result)
else:
    print("Commit may have failed (no changes or error)")

# Step 5: Push
print("\n" + "=" * 60)
print("PUSHING TO GITHUB")
print("=" * 60)
print("Note: You may need to enter GitHub credentials")

push_result = run_git_command(['push', '-u', 'origin', 'HEAD'])
if push_result:
    print(push_result)
    print("\n✓ Successfully pushed to GitHub!")
else:
    print("\n✗ Push failed. Please try manually:")
    print("  git push -u origin HEAD")

print("\n" + "=" * 60)
