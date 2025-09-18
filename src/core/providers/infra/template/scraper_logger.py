import sys
import traceback
from datetime import datetime
from typing import Optional, Any

class ScraperLogger:
    """
    Sistema de logging centralizado para scrapers.
    Permite rastreamento detalhado de operações e debug de problemas.
    """
    
    @staticmethod
    def info(provider_name: str, operation: str, message: str, **kwargs):
        """Log de informação geral"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_msg = f"[{timestamp}] [INFO] [{provider_name}] {operation}: {message}"
        if extra_info:
            log_msg += f" | {extra_info}"
        print(log_msg)
    
    @staticmethod
    def debug(provider_name: str, operation: str, message: str, data: Any = None, **kwargs):
        """Log de debug com dados opcionais"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_msg = f"[{timestamp}] [DEBUG] [{provider_name}] {operation}: {message}"
        if extra_info:
            log_msg += f" | {extra_info}"
        if data is not None:
            log_msg += f" | Data: {str(data)[:200]}{'...' if len(str(data)) > 200 else ''}"
        print(log_msg)
    
    @staticmethod
    def warning(provider_name: str, operation: str, message: str, **kwargs):
        """Log de aviso"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_msg = f"[{timestamp}] [WARNING] [{provider_name}] {operation}: {message}"
        if extra_info:
            log_msg += f" | {extra_info}"
        print(log_msg)
    
    @staticmethod
    def error(provider_name: str, operation: str, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log de erro com trace opcional"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_msg = f"[{timestamp}] [ERROR] [{provider_name}] {operation}: {message}"
        if extra_info:
            log_msg += f" | {extra_info}"
        
        if exception:
            log_msg += f" | Exception: {type(exception).__name__}: {str(exception)}"
            # Print stacktrace separadamente para melhor formatação
            print(log_msg)
            print(f"[{timestamp}] [ERROR] [{provider_name}] Stacktrace:")
            traceback.print_exc()
        else:
            print(log_msg)
    
    @staticmethod
    def success(provider_name: str, operation: str, message: str, **kwargs):
        """Log de sucesso"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        log_msg = f"[{timestamp}] [SUCCESS] [{provider_name}] {operation}: {message}"
        if extra_info:
            log_msg += f" | {extra_info}"
        print(log_msg)
    
    @staticmethod
    def http_request(provider_name: str, method: str, url: str, status_code: Optional[int] = None, **kwargs):
        """Log específico para requisições HTTP"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        
        if status_code:
            status_emoji = "✓" if 200 <= status_code < 300 else "✗"
            log_msg = f"[{timestamp}] [HTTP] [{provider_name}] {method} {url} -> {status_code} {status_emoji}"
        else:
            log_msg = f"[{timestamp}] [HTTP] [{provider_name}] {method} {url}"
        
        if extra_info:
            log_msg += f" | {extra_info}"
        print(log_msg)
    
    @staticmethod
    def parsing(provider_name: str, selector: str, found_count: int, expected_min: int = 0, **kwargs):
        """Log específico para parsing de HTML"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        
        status = "✓" if found_count >= expected_min else "⚠"
        log_msg = f"[{timestamp}] [PARSE] [{provider_name}] Selector: '{selector}' -> {found_count} elementos {status}"
        
        if extra_info:
            log_msg += f" | {extra_info}"
        print(log_msg)

# Decorador para automatizar logging de métodos
def log_method(operation_name: str = None):
    """
    Decorador para automatizar logging de entrada/saída de métodos
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            provider_name = getattr(self, 'name', self.__class__.__name__)
            op_name = operation_name or func.__name__
            
            # Log de entrada
            args_info = f"args={args}" if args else ""
            kwargs_info = f"kwargs={kwargs}" if kwargs else ""
            params = " | ".join(filter(None, [args_info, kwargs_info]))
            
            ScraperLogger.info(provider_name, op_name, "Iniciando operação", params=params)
            
            try:
                result = func(self, *args, **kwargs)
                
                # Log de sucesso
                result_info = ""
                if hasattr(result, '__len__'):
                    result_info = f"count={len(result)}"
                elif result:
                    result_info = f"type={type(result).__name__}"
                
                ScraperLogger.success(provider_name, op_name, "Operação concluída", result=result_info)
                return result
                
            except Exception as e:
                ScraperLogger.error(provider_name, op_name, "Operação falhou", exception=e)
                raise
        
        return wrapper
    return decorator