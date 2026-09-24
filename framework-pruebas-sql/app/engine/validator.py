"""
Módulo de validación para el Framework de Pruebas.
Implementa el Patrón Strategy para evaluar dinámicamente los resultados
de la ejecución SQL contra los criterios esperados.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Union

class ValidationStrategy(ABC):
    """Interfaz base que define el contrato para cualquier regla de validación."""
    
    @abstractmethod
    def evaluate(self, execution_data: Any, expected_value: str) -> bool:
        """
        Evalúa el resultado devuelto por la base de datos contra el valor esperado.
        
        Args:
            execution_data: Resultado entregado por TargetDatabaseExecutor (dict, list o número).
            expected_value: El valor configurado en el caso de prueba.
            
        Returns:
            bool: True si la prueba pasa (PASS), False si falla (FAIL).
        """
        pass


class RowCountValidation(ValidationStrategy):
    """Estrategia para validar la cantidad exacta de filas devueltas (SELECT) o afectadas (DML)."""
    
    def evaluate(self, execution_data: Any, expected_value: str) -> bool:
        try:
            expected_count = int(str(expected_value).strip())
        except (ValueError, TypeError):
            # Valor esperado no numérico devuelve resultado controlado (FAIL)
            return False

        actual_count = 0
        if isinstance(execution_data, dict):
            # Si el ejecutor no tuvo éxito (ej. error sintáctico), la validación falla
            if not execution_data.get("success", True):
                return False
                
            stmt_type = execution_data.get("statement_type", "").upper()
            if stmt_type == "SELECT":
                actual_count = execution_data.get("rowcount", len(execution_data.get("rows", [])))
            else:
                actual_count = execution_data.get("rowcount", 0)
        elif isinstance(execution_data, list):
            actual_count = len(execution_data)
        elif isinstance(execution_data, int):
            actual_count = execution_data
        else:
            return False

        return actual_count == expected_count


class ExistenceValidation(ValidationStrategy):
    """Estrategia para validar si la consulta devolvió registros o afectó filas."""
    
    def evaluate(self, execution_data: Any, expected_value: str) -> bool:
        expect_exists = str(expected_value).strip().upper() == "TRUE"
        
        has_data = False
        if isinstance(execution_data, dict):
            if not execution_data.get("success", True):
                return False
            stmt_type = execution_data.get("statement_type", "").upper()
            if stmt_type == "SELECT":
                has_data = execution_data.get("rowcount", len(execution_data.get("rows", []))) > 0
            else:
                has_data = execution_data.get("rowcount", 0) > 0
        elif isinstance(execution_data, list):
            has_data = len(execution_data) > 0
        elif isinstance(execution_data, int):
            has_data = execution_data > 0

        return has_data == expect_exists


class ValidationContext:
    """
    Contexto principal que recibe la data de ejecución y delega la evaluación
    a la estrategia inyectada en tiempo de ejecución.
    """
    
    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ValidationStrategy) -> None:
        """Permite cambiar la estrategia de validación dinámicamente."""
        self._strategy = strategy

    def execute_validation(self, execution_data: Any, expected_value: str) -> bool:
        """Ejecuta la evaluación utilizando la estrategia actual."""
        return self._strategy.evaluate(execution_data, expected_value)