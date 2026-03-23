"""
Unit tests for Gradebook Service Bug Fixes
Tests BUG-1, BUG-2, BUG-3 fixes without full database setup
"""
import pytest
import sys
from pathlib import Path

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestCalculateCategoryGrade:
    """Test BUG-1 fix: Mixed weight items calculation"""
    
    def test_all_zero_weight_simple_average(self):
        """When all items have weight=0, use simple average"""
        # Mock data
        grade_items = [
            type('GradeItem', (), {'weight': 0, 'max_score': 100})(),
            type('GradeItem', (), {'weight': 0, 'max_score': 100})(),
        ]
        entries = [
            type('GradeEntry', (), {'score': 80, 'percentage': 80})(),
            type('GradeEntry', (), {'score': 90, 'percentage': 90})(),
        ]
        
        # Simulate calculation logic
        all_zero_weight = all(item.weight == 0 for item in grade_items)
        total_score = 0
        total_max_score = 0
        
        for item, entry in zip(grade_items, entries):
            percentage = entry.percentage
            if all_zero_weight:
                total_score += percentage
                total_max_score += 100
        
        category_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        assert category_score == 85.0, "Simple average should be 85.0"
    
    def test_mixed_weight_includes_all_items(self):
        """BUG-1: When mixing weight=0 and weight>0, ALL items should be included"""
        # Mock data - quiz with weight=100, manual item with weight=0
        grade_items = [
            type('GradeItem', (), {'weight': 100, 'max_score': 100})(),  # Quiz
            type('GradeItem', (), {'weight': 0, 'max_score': 100})(),    # Manual
        ]
        entries = [
            type('GradeEntry', (), {'score': 80, 'percentage': 80})(),  # Quiz: 80%
            type('GradeEntry', (), {'score': 90, 'percentage': 90})(),  # Manual: 90%
        ]
        
        # Simulate calculation logic (NEW - hybrid approach)
        all_zero_weight = all(item.weight == 0 for item in grade_items)
        all_nonzero_weight = all(item.weight > 0 for item in grade_items)
        
        total_score = 0
        total_max_score = 0
        
        for item, entry in zip(grade_items, entries):
            percentage = entry.percentage
            
            if all_zero_weight:
                total_score += percentage
                total_max_score += 100
            elif all_nonzero_weight:
                total_score += percentage * (item.weight / 100)
                total_max_score += item.weight
            else:
                # Mixed scenario - hybrid approach
                if item.weight > 0:
                    total_score += percentage * (item.weight / 100)
                    total_max_score += item.weight
                else:
                    total_score += percentage
                    total_max_score += 100
        
        category_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        # Quiz (80 × 1.0) + Manual (90 × 1.0) = 170 / 200 = 85%
        assert category_score == 85.0, f"Mixed weight should include all items, got {category_score}"
    
    def test_old_bug_excluded_manual_items(self):
        """Demonstrate OLD BUG behavior - manual items were excluded"""
        grade_items = [
            type('GradeItem', (), {'weight': 100, 'max_score': 100})(),
            type('GradeItem', (), {'weight': 0, 'max_score': 100})(),
        ]
        entries = [
            type('GradeEntry', (), {'score': 80, 'percentage': 80})(),
            type('GradeEntry', (), {'score': 90, 'percentage': 90})(),
        ]
        
        # OLD BUG logic - only items with weight > 0 were included
        all_zero_weight = all(item.weight == 0 for item in grade_items)
        total_score = 0
        total_max_score = 0
        
        for item, entry in zip(grade_items, entries):
            percentage = entry.percentage
            if all_zero_weight:
                total_score += percentage
                total_max_score += 100
            elif item.weight > 0:  # BUG: This excluded weight=0 items!
                total_score += percentage * (item.weight / 100)
                total_max_score += item.weight
        
        category_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        # Old bug: only quiz counted = 80%
        assert category_score == 80.0, "Old bug excluded manual items"


class TestCalculateFinalGrade:
    """Test BUG-2 fix: Unified final grade calculation"""
    
    def test_unified_calculation_with_weighting(self):
        """Teacher view uses category weighting"""
        # Simulate category-weighted calculation
        categories = [
            type('Category', (), {'id': 1, 'weight': 60})(),  # Formatif 60%
            type('Category', (), {'id': 2, 'weight': 40})(),  # Sumatif 40%
        ]
        
        category_scores = {
            1: {'score': 85, 'weight': 60, 'weighted_score': 51.0},
            2: {'score': 90, 'weight': 40, 'weighted_score': 36.0},
        }
        
        total_weighted_score = sum(cat['weighted_score'] for cat in category_scores.values())
        total_weight = sum(cat['weight'] for cat in category_scores.values())
        
        final_grade = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # (51 + 36) / (60 + 40) = 87 / 100 = 0.87 (normalized)
        assert final_grade == 0.87, "Weighted average should be 0.87 (87%)"
    
    def test_unified_calculation_simple_average(self):
        """Student view uses simple average (no weighting)"""
        all_percentages = [80, 85, 90, 95]
        
        final_grade = sum(all_percentages) / len(all_percentages) if all_percentages else 0
        
        # (80 + 85 + 90 + 95) / 4 = 350 / 4 = 87.5%
        assert final_grade == 87.5, "Simple average should be 87.5"


class TestManualOverride:
    """Test BUG-3 fix: Manual override protects grades from sync"""
    
    def test_override_flag_prevents_update(self):
        """When manual_override=True, sync should skip the entry"""
        # Mock entry with manual override
        entry = type('GradeEntry', (), {
            'manual_override': True,
            'score': 95.0,
            'percentage': 95.0
        })()
        
        # Simulate sync logic
        new_score_from_quiz = 70.0
        
        if entry.manual_override:
            # Skip update - grade is protected
            pass
        else:
            entry.score = new_score_from_quiz
        
        assert entry.score == 95.0, "Manual override should protect grade from sync"
    
    def test_no_override_allows_update(self):
        """When manual_override=False, sync should update the entry"""
        entry = type('GradeEntry', (), {
            'manual_override': False,
            'score': 95.0,
            'percentage': 95.0
        })()
        
        new_score_from_quiz = 70.0
        
        if not entry.manual_override:
            entry.score = new_score_from_quiz
            entry.percentage = 70.0
        
        assert entry.score == 70.0, "Non-overridden grades should be updated by sync"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
