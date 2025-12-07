# config.py - VERSIÓN OPTIMIZADA
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import os
from pathlib import Path

# ============================================
# CONFIGURACIÓN DE PATHS
# ============================================

@dataclass
class PathConfig:
    """Configuración centralizada de paths"""
    
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent)
    DATA_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)
    CACHE_DIR: Path = field(init=False)
    BITACORA_FILE: Path = field(init=False)
    STRATEGY_CACHE_FILE: Path = field(init=False)
    
    def __post_init__(self):
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.LOGS_DIR = self.ROOT_DIR / "logs"
        self.CACHE_DIR = self.ROOT_DIR / ".cache"
        self.BITACORA_FILE = self.DATA_DIR / "bitacora_trades.csv"
        self.STRATEGY_CACHE_FILE = self.CACHE_DIR / "strategy_cache.json"
        
        # Crear directorios
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.CACHE_DIR.mkdir(exist_ok=True)


# ============================================
# UNIVERSO DE ACTIVOS
# ============================================

@dataclass
class AssetUniverse:
    """Universo de activos organizados por categoría"""
    
    INDICES: List[str] = field(default_factory=lambda: ["SPY", "QQQ", "DIA"])
    CRYPTO: List[str] = field(default_factory=lambda: ["BTC-USD", "ETH-USD", "SOL-USD"])
    TECH: List[str] = field(default_factory=lambda: ["MSFT", "AAPL", "NVDA"])
    COMMUNICATIONS: List[str] = field(default_factory=lambda: ["GOOGL", "META", "NFLX"])
    CYCLICAL: List[str] = field(default_factory=lambda: ["AMZN", "TSLA", "HD"])
    FINANCIALS: List[str] = field(default_factory=lambda: ["JPM", "V", "MA"])
    HEALTHCARE: List[str] = field(default_factory=lambda: ["LLY", "UNH", "JNJ"])
    DEFENSIVE: List[str] = field(default_factory=lambda: ["WMT", "PG", "COST"])
    ENERGY: List[str] = field(default_factory=lambda: ["XOM", "CVX", "COP"])
    INDUSTRIAL: List[str] = field(default_factory=lambda: ["CAT", "UNP", "GE"])
    MATERIALS: List[str] = field(default_factory=lambda: ["LIN", "NEE", "SHW"])
    
    def get_all_tickers(self) -> List[str]:
        return (
            self.INDICES + self.CRYPTO + self.TECH + self.COMMUNICATIONS + 
            self.CYCLICAL + self.FINANCIALS + self.HEALTHCARE + 
            self.DEFENSIVE + self.ENERGY + self.INDUSTRIAL + self.MATERIALS
        )
    
    def get_by_sector(self, sector: str) -> List[str]:
        sector_map = {
            'INDICES': self.INDICES, 'CRYPTO': self.CRYPTO, 'TECH': self.TECH,
            'COMMUNICATIONS': self.COMMUNICATIONS, 'CYCLICAL': self.CYCLICAL,
            'FINANCIALS': self.FINANCIALS, 'HEALTHCARE': self.HEALTHCARE,
            'DEFENSIVE': self.DEFENSIVE, 'ENERGY': self.ENERGY,
            'INDUSTRIAL': self.INDUSTRIAL, 'MATERIALS': self.MATERIALS
        }
        return sector_map.get(sector.upper(), [])
    
    def get_sector_for_ticker(self, ticker: str) -> str:
        for sector_name in ['INDICES', 'CRYPTO', 'TECH', 'COMMUNICATIONS', 
                           'CYCLICAL', 'FINANCIALS', 'HEALTHCARE', 'DEFENSIVE',
                           'ENERGY', 'INDUSTRIAL', 'MATERIALS']:
            if ticker in getattr(self, sector_name):
                return sector_name
        return 'UNKNOWN'


# ============================================
# GESTIÓN DE RIESGO
# ============================================

@dataclass
class RiskConfig:
    """Configuración de gestión de riesgo"""
    
    capital_total: float = field(default_factory=lambda: float(os.getenv('CAPITAL_TOTAL', '10000')))
    riesgo_por_operacion: float = 0.02
    atr_multiplier: float = 1.5
    rr_ratio: float = 2.0
    max_posiciones_simultaneas: int = 5
    max_riesgo_portafolio: float = 0.10
    
    def __post_init__(self):
        if self.capital_total <= 0:
            raise ValueError(f"Capital total debe ser > 0")
        if not (0 < self.riesgo_por_operacion <= 0.1):
            raise ValueError(f"Riesgo debe estar entre 0 y 10%")


# ============================================
# MAPA DE ESTRATEGIAS
# ============================================

@dataclass
class StrategyMapping:
    """Mapa de estrategias óptimas por ticker"""
    
    strategies: Dict[str, Dict[str, any]] = field(default_factory=lambda: {
        "SPY": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 9, 'slow': 21}},
        "QQQ": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
        "DIA": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
        "BTC-USD": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 8, 'slow': 21}},
        "ETH-USD": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
        "SOL-USD": {"strategy": "Bollinger Breakout", "params": {'window': 20, 'std_dev': 2}},
        "MSFT": {"strategy": "Awesome Oscillator", "params": {'fast': 3, 'slow': 10}},
        "AAPL": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
        "NVDA": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
        "GOOGL": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
        "META": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 100}},
        "NFLX": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
        "AMZN": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
        "TSLA": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
        "HD": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
        "JPM": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 200}},
        "V": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
        "MA": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},
        "LLY": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
        "UNH": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 25, 'rsi_high': 70}},
        "JNJ": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
        "WMT": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 200}},
        "PG": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
        "COST": {"strategy": "Awesome Oscillator", "params": {'fast': 5, 'slow': 34}},
        "XOM": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},
        "CVX": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},
        "COP": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
        "CAT": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
        "UNP": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
        "GE": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 200}},
        "LIN": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
        "NEE": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
        "SHW": {"strategy": "Bollinger Breakout", "params": {'window': 20, 'std_dev': 2}}
    })
    
    def get_strategy(self, ticker: str) -> Dict[str, any]:
        return self.strategies.get(ticker.upper())
    
    def has_strategy(self, ticker: str) -> bool:
        return ticker.upper() in self.strategies


# ============================================
# CONFIGURACIÓN DE APLICACIÓN
# ============================================

@dataclass
class AppConfig:
    """Configuración general de la aplicación"""
    
    app_name: str = "TradeXpert Pro"
    app_version: str = "2.0.0"
    page_icon: str = "📡"
    layout: str = "wide"
    cache_ttl_seconds: int = 3600
    data_refresh_interval: int = 300
    max_workers_paralelo: int = 5
    timeout_download: int = 30
    max_tickers_por_escaneo: int = 50
    min_datos_historicos: int = 50
    log_level: str = "INFO"
    log_to_file: bool = True


# ============================================
# INSTANCIAS GLOBALES
# ============================================

PATHS = PathConfig()
ASSETS = AssetUniverse()
RISK = RiskConfig()
STRATEGY_MAP_OBJ = StrategyMapping()
APP = AppConfig()

# Compatibilidad con código legacy
TICKERS = ASSETS.get_all_tickers()
CAPITAL_TOTAL = RISK.capital_total
RIESGO_POR_OPERACION = RISK.riesgo_por_operacion
ATR_MULTIPLIER = RISK.atr_multiplier
RR_RATIO = RISK.rr_ratio
STRATEGY_MAP = STRATEGY_MAP_OBJ.strategies
