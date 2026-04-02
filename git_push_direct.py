"""
Git commit and push using GitPython library
"""
import sys
from git import Repo, GitCommandError

repo_path = r'C:\Users\iksan\dev\aldudu-academy'

try:
    repo = Repo(repo_path)
    
    # Check if repo is clean
    print("=" * 60)
    print("REPO STATUS")
    print("=" * 60)
    print(f"Branch: {repo.active_branch}")
    print(f"Is dirty: {repo.is_dirty()}")
    
    # Get untracked files
    untracked = repo.untracked_files
    if untracked:
        print(f"\nUntracked files ({len(untracked)}):")
        for f in untracked[:10]:  # Show first 10
            print(f"  - {f}")
        if len(untracked) > 10:
            print(f"  ... and {len(untracked) - 10} more")
    
    # Files to add
    files_to_add = [
        'app/services/rasch_threshold_service.py',
        'app/services/rasch_analysis_service.py',
        'app/services/rasch_anchor_service.py',
        'app/services/rasch_scheduled_service.py',
        'app/blueprints/rasch.py',
        'docs/cron_job_setup.md',
    ]
    
    print("\n" + "=" * 60)
    print("ADDING FILES")
    print("=" * 60)
    
    for file in files_to_add:
        try:
            repo.index.add([file])
            print(f"✓ Added: {file}")
        except Exception as e:
            print(f"✗ Failed to add {file}: {e}")
    
    # Commit
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
    
    repo.index.commit(commit_message)
    print("✓ Commit successful!")
    
    # Push
    print("\n" + "=" * 60)
    print("PUSHING TO GITHUB")
    print("=" * 60)
    
    origin = repo.remote(name='origin')
    push_info = origin.push(repo.active_branch)
    
    if push_info:
        for info in push_info:
            print(f"Pushed to: {info.remote_ref}")
        print("\n✓ Successfully pushed to GitHub!")
    else:
        print("\nPush completed")
    
except GitCommandError as e:
    print(f"Git error: {e}")
    print("\nManual steps required:")
    print("1. Open terminal in project directory")
    print("2. Run: git add <files>")
    print("3. Run: git commit -m 'Your message'")
    print("4. Run: git push")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
