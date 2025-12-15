"""
Meteosource ETL Package

Pipeline para extracción de datos climáticos en tiempo real usando Meteosource API.
"""

from .meteosource_pipeline import run

__all__ = ["run"]
