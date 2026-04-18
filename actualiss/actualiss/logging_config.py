"""
Structured logging configuration for actualiss package.

This module provides centralized logging setup with support for both console and file output,
verbose logging levels, and structured formatting for better debugging and monitoring.
"""

import logging
import sys
from pathlib import Path


def setup_logging(verbose=False, log_file=None):
    """
    Configure structured logging for the actualiss package.

    Args:
        verbose (bool): Enable DEBUG level logging. Defaults to INFO level.
        log_file (str, optional): Path to log file for file logging. If None, only console logging.

    Returns:
        logging.Logger: Configured root logger for the 'actualiss' package.
    """
    # Determine log level
    level = logging.DEBUG if verbose else logging.INFO

    # Get or create root logger for actualiss package
    logger = logging.getLogger("actualiss")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicate logs
    logger.handlers.clear()

    # Console handler - always present
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler - only if log_file is specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(
            logging.DEBUG
        )  # Always log DEBUG to file for detailed debugging
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Log initialization
    logger.info(
        f"Logging initialized - Level: {logging.getLevelName(level)}, File: {log_file or 'Console only'}"
    )

    return logger


def get_logger(name):
    """
    Get a logger instance for a specific module within the actualiss package.

    Args:
        name (str): Module name (e.g., 'actual_client', 'processors.swisscard')

    Returns:
        logging.Logger: Logger instance for the specified module.
    """
    return logging.getLogger(f"actualiss.{name}")


def log_api_call(logger, method_name, **kwargs):
    """
    Log an API call with method name and parameters (excluding sensitive data).

    Args:
        logger (logging.Logger): Logger instance to use
        method_name (str): Name of the API method being called
        **kwargs: Additional parameters to log (sensitive data will be filtered)
    """
    # Filter out potentially sensitive parameters
    safe_kwargs = {}
    sensitive_keys = {"password", "token", "secret", "key", "auth"}

    for key, value in kwargs.items():
        if key.lower() in sensitive_keys:
            safe_kwargs[key] = "***FILTERED***"
        else:
            safe_kwargs[key] = value

    logger.debug(f"Calling actual.{method_name}() with: {safe_kwargs}")


def log_api_success(logger, method_name, result_summary=None):
    """
    Log successful API call completion.

    Args:
        logger (logging.Logger): Logger instance to use
        method_name (str): Name of the API method that succeeded
        result_summary (str, optional): Summary of the result for logging
    """
    if result_summary:
        logger.info(f"{method_name} succeeded: {result_summary}")
    else:
        logger.info(f"{method_name} succeeded")


def log_api_error(logger, method_name, error, **context):
    """
    Log API call error with full stack trace and context.

    Args:
        logger (logging.Logger): Logger instance to use
        method_name (str): Name of the API method that failed
        error (Exception): The exception that occurred
        **context: Additional context information
    """
    context_str = f" Context: {context}" if context else ""
    logger.error(
        f"{method_name} failed: {error}{context_str}",
        exc_info=True,  # Include full stack trace
    )
