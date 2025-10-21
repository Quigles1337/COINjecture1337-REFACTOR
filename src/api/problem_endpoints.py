"""
Problem Submission API Endpoints for COINjecture

Provides REST API for submitting computational problems and managing solutions.
Integrates with the user_submissions module for problem pool management.
"""

from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from user_submissions.submission import ProblemSubmission, SolutionRecord
    from user_submissions.pool import ProblemPool
    from user_submissions.aggregation import AggregationStrategy
    from core.blockchain import HardwareType, ProblemTier
except ImportError:
    # Fallback for direct execution
    from src.user_submissions.submission import ProblemSubmission, SolutionRecord
    from src.user_submissions.pool import ProblemPool
    from src.user_submissions.aggregation import AggregationStrategy
    from src.core.blockchain import HardwareType, ProblemTier

# Create blueprint for problem management
problem_bp = Blueprint('problem', __name__, url_prefix='/v1/problem')

# Global problem pool instance
problem_pool = ProblemPool()

@problem_bp.route('/submit', methods=['POST'])
def submit_problem():
    """Submit a computational problem for solving."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "No JSON data provided"
            }), 400
        
        # Validate required fields
        problem_type = data.get('problem_type')
        problem_template = data.get('problem_template', {})
        bounty = data.get('bounty', 0.0)
        aggregation = data.get('aggregation', 'ANY')
        aggregation_params = data.get('aggregation_params', {})
        min_quality = data.get('min_quality', 0.0)
        
        if not problem_type:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "problem_type is required"
            }), 400
        
        if bounty <= 0:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "bounty must be greater than 0"
            }), 400
        
        # Validate aggregation strategy
        try:
            aggregation_enum = AggregationStrategy(aggregation.lower())
        except ValueError:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": f"Invalid aggregation strategy. Must be one of: {[s.value for s in AggregationStrategy]}"
            }), 400
        
        # Create problem submission
        submission = ProblemSubmission(
            problem_type=problem_type,
            problem_template=problem_template,
            seeding_strategy="template",
            aggregation=aggregation_enum,
            aggregation_params=aggregation_params,
            bounty_per_solution=bounty,
            min_quality=min_quality
        )
        
        # Generate submission ID
        submission_id = f"submission-{int(time.time())}-{len(problem_pool.pending_problems)}"
        
        # Add to problem pool
        problem_pool.add_submission(submission_id, submission)
        
        return jsonify({
            "status": "success",
            "submission_id": submission_id,
            "problem_type": problem_type,
            "bounty": bounty,
            "aggregation": aggregation,
            "message": "Problem submitted successfully"
        }), 201
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500

@problem_bp.route('/list', methods=['GET'])
def list_problems():
    """List available problems for mining."""
    try:
        tier = request.args.get('tier', 'TIER_2_DESKTOP')
        limit = int(request.args.get('limit', 50))
        
        # Get all open problems
        open_problems = [
            {
                "submission_id": sid,
                "problem_type": p.problem_type,
                "bounty": p.bounty_per_solution,
                "aggregation": p.aggregation.value,
                "solutions_count": len(p.solutions_collected),
                "status": p.status,
                "is_accepting": p.is_accepting_solutions()
            }
            for sid, p in problem_pool.pending_problems.items()
            if p.is_accepting_solutions()
        ]
        
        # Sort by priority score (highest first)
        open_problems.sort(key=lambda x: x['bounty'], reverse=True)
        open_problems = open_problems[:limit]
        
        return jsonify({
            "status": "success",
            "problems": open_problems,
            "count": len(open_problems),
            "tier": tier
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500

@problem_bp.route('/<submission_id>', methods=['GET'])
def get_problem_details(submission_id: str):
    """Get detailed information about a specific problem."""
    try:
        submission = problem_pool.get_submission(submission_id)
        if not submission:
            return jsonify({
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Problem {submission_id} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "submission_id": submission_id,
            "problem_type": submission.problem_type,
            "problem_template": submission.problem_template,
            "bounty": submission.bounty_per_solution,
            "aggregation": submission.aggregation.value,
            "aggregation_params": submission.aggregation_params,
            "min_quality": submission.min_quality,
            "status": submission.status,
            "solutions_count": len(submission.solutions_collected),
            "is_accepting": submission.is_accepting_solutions()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500

@problem_bp.route('/<submission_id>/solutions', methods=['GET'])
def get_problem_solutions(submission_id: str):
    """Get all solutions for a specific problem."""
    try:
        submission = problem_pool.get_submission(submission_id)
        if not submission:
            return jsonify({
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Problem {submission_id} not found"
            }), 404
        
        solutions = []
        for solution in submission.solutions_collected:
            solutions.append({
                "block_number": solution.block_number,
                "block_hash": solution.block_hash,
                "miner_address": solution.miner_address,
                "solution": solution.solution,
                "solution_quality": solution.solution_quality,
                "work_score": solution.work_score,
                "solve_time": solution.solve_time,
                "energy_used": solution.energy_used,
                "verified": solution.verified,
                "bounty_paid": solution.bounty_paid,
                "bonus_paid": solution.bonus_paid,
                "timestamp": solution.timestamp
            })
        
        return jsonify({
            "status": "success",
            "submission_id": submission_id,
            "solutions": solutions,
            "count": len(solutions)
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500

@problem_bp.route('/<submission_id>/solution', methods=['POST'])
def submit_solution(submission_id: str):
    """Submit a solution for a specific problem."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "No JSON data provided"
            }), 400
        
        # Validate required fields
        block_number = data.get('block_number')
        block_hash = data.get('block_hash')
        miner_address = data.get('miner_address')
        problem_instance = data.get('problem_instance', {})
        solution = data.get('solution')
        solution_quality = data.get('solution_quality', 0.0)
        work_score = data.get('work_score', 0.0)
        solve_time = data.get('solve_time', 0.0)
        energy_used = data.get('energy_used', 0.0)
        
        if not all([block_number, block_hash, miner_address, solution is not None]):
            return jsonify({
                "status": "error",
                "error": "INVALID",
                "message": "block_number, block_hash, miner_address, and solution are required"
            }), 400
        
        # Get the problem submission
        submission = problem_pool.get_submission(submission_id)
        if not submission:
            return jsonify({
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Problem {submission_id} not found"
            }), 404
        
        if not submission.is_accepting_solutions():
            return jsonify({
                "status": "error",
                "error": "CLOSED",
                "message": "Problem is no longer accepting solutions"
            }), 400
        
        # Create solution record
        solution_record = SolutionRecord(
            block_number=block_number,
            block_hash=block_hash,
            miner_address=miner_address,
            problem_instance=problem_instance,
            solution=solution,
            solution_quality=solution_quality,
            work_score=work_score,
            solve_time=solve_time,
            energy_used=energy_used,
            verified=True,  # Assume verified for now
            verification_time=time.time()
        )
        
        # Record the solution
        problem_pool.record_solution(submission_id, solution_record)
        
        return jsonify({
            "status": "success",
            "submission_id": submission_id,
            "solution_quality": solution_quality,
            "work_score": work_score,
            "bounty_earned": submission.bounty_per_solution,
            "message": "Solution recorded successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500

@problem_bp.route('/stats', methods=['GET'])
def get_problem_stats():
    """Get statistics about the problem pool."""
    try:
        total_problems = len(problem_pool.pending_problems)
        open_problems = sum(1 for p in problem_pool.pending_problems.values() if p.is_accepting_solutions())
        complete_problems = sum(1 for p in problem_pool.pending_problems.values() if p.status == 'complete')
        
        total_bounty = sum(p.bounty_per_solution for p in problem_pool.pending_problems.values())
        total_solutions = sum(len(p.solutions_collected) for p in problem_pool.pending_problems.values())
        
        return jsonify({
            "status": "success",
            "stats": {
                "total_problems": total_problems,
                "open_problems": open_problems,
                "complete_problems": complete_problems,
                "total_bounty": total_bounty,
                "total_solutions": total_solutions
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "INTERNAL",
            "message": str(e)
        }), 500
