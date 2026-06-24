#!/usr/bin/env python
"""
Main entry point for the Order Management System.

This script provides a unified interface for:
1. Running the main application (demo)
2. Running tests with coverage
3. Generating coverage reports
"""

import subprocess
import sys
import os
import argparse


def run_app():
    """Run the main application."""
    print("=" * 60)
    print("ЗАПУСК ПРИЛОЖЕНИЯ - Order Management System")
    print("=" * 60)
    
    # Import and run main
    from app.main import main
    main()


def run_tests(verbose=True, coverage=True, html_report=True):
    """
    Run tests with optional coverage.
    
    Args:
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        html_report: Generate HTML coverage report
    """
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if coverage:
        cmd.append("--cov=app")
        cmd.append("--cov-report=term-missing")
        
        if html_report:
            cmd.append("--cov-report=html")
    
    if verbose:
        cmd.append("-v")
    
    print("=" * 60)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 60)
    print(f"Команда: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    if html_report and coverage:
        print("\n" + "=" * 60)
        print("✅ Отчет о покрытии создан в htmlcov/index.html")
        print("=" * 60)
    
    return result.returncode


def run_tests_watch():
    """Run tests in watch mode (requires pytest-watch)."""
    try:
        import pytest_watch  # noqa
        cmd = [sys.executable, "-m", "ptw", "tests/"]
        print("=" * 60)
        print("ЗАПУСК ТЕСТОВ В РЕЖИМЕ НАБЛЮДЕНИЯ")
        print("=" * 60)
        result = subprocess.run(cmd)
        return result.returncode
    except ImportError:
        print("❌ pytest-watch не установлен. Установите: pip install pytest-watch")
        return 1


def show_help():
    """Show help message."""
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║              ORDER MANAGEMENT SYSTEM - RUN COMMANDS              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Команды:                                                         ║
║    python run.py app          - Запустить основное приложение    ║
║    python run.py test         - Запустить все тесты              ║
║    python run.py test -v      - Запустить тесты с подробным выводом║
║    python run.py test --no-cov - Запустить тесты без покрытия   ║
║    python run.py watch        - Запустить тесты в режиме наблюдения║
║    python run.py coverage     - Показать отчет о покрытии        ║
║    python run.py help         - Показать эту справку             ║
║                                                                   ║
║  Примеры:                                                         ║
║    python run.py app                                              ║
║    python run.py test -v                                          ║
║    python run.py test --no-cov                                    ║
║    python run.py watch                                            ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(help_text)


def show_coverage():
    """Show coverage report."""
    cmd = [sys.executable, "-m", "coverage", "report", "-m"]
    print("=" * 60)
    print("ОТЧЕТ О ПОКРЫТИИ")
    print("=" * 60)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point for the run script."""
    parser = argparse.ArgumentParser(
        description="Order Management System - Run Script",
        add_help=False
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["app", "test", "watch", "coverage", "help"],
        help="Command to execute"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Disable HTML coverage report"
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message"
    )
    
    # Parse known args to handle help properly
    args, unknown = parser.parse_known_args()
    
    if args.help or args.command == "help":
        show_help()
        return 0
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Execute command
    if args.command == "app":
        return run_app()
    
    elif args.command == "test":
        return run_tests(
            verbose=args.verbose,
            coverage=not args.no_cov,
            html_report=not args.no_html
        )
    
    elif args.command == "watch":
        return run_tests_watch()
    
    elif args.command == "coverage":
        return show_coverage()
    
    else:
        show_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
