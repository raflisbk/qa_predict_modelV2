"""
Reset Collection State
Reset collection progress to start from scratch

Usage:
    python scripts/reset_collection_state.py --type daily
    python scripts/reset_collection_state.py --type hourly
    python scripts/reset_collection_state.py --all
"""

import os
import sys
import argparse
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.utils.state_tracker import CollectionStateTracker


def main():
    parser = argparse.ArgumentParser(description="Reset collection state")
    parser.add_argument("--type", type=str, choices=['daily', 'hourly', 'all'],
                       help="Type of collection to reset")
    parser.add_argument("--confirm", action="store_true",
                       help="Confirm reset (required)")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    if not args.confirm:
        logger.error("Please add --confirm flag to confirm reset")
        logger.info("This will delete all collection progress!")
        sys.exit(1)
    
    tracker = CollectionStateTracker()
    
    if args.type == 'daily':
        logger.warning("Resetting DAILY collection state...")
        tracker.reset_collection("daily_collection")
        logger.success("Daily collection state reset!")
        
    elif args.type == 'hourly':
        logger.warning("Resetting HOURLY collection state...")
        tracker.reset_collection("hourly_collection")
        logger.success("Hourly collection state reset!")
        
    elif args.type == 'all' or args.type is None:
        logger.warning("Resetting ALL collection state...")
        tracker.reset_all()
        logger.success("All collection state reset!")
    
    logger.info(f"\nState file: {tracker.state_file}")
    logger.info("You can now start collection from scratch")


if __name__ == "__main__":
    main()
