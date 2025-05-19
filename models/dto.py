"""
Data Transfer Objects (DTOs) for the application
"""
from dataclasses import dataclass
from typing import Dict, Optional, List, Any


@dataclass
class AssetDto:
    """Data Transfer Object for Asset operations"""
    name: str
    account_id: str
    product_type: str
    allocation: Dict[str, float]
    geo_allocation: Dict[str, Dict[str, float]]
    current_value: float
    cost_basis: Optional[float] = None
    currency: str = "EUR"
    notes: str = ""
    todo: str = ""
    isin: Optional[str] = None
    ounces: Optional[float] = None
    user_id: Optional[str] = None
    id: Optional[str] = None


@dataclass
class BankDto:
    """Data Transfer Object for Bank operations"""
    name: str
    user_id: str
    notes: str = ""
    id: Optional[str] = None


@dataclass
class AccountDto:
    """Data Transfer Object for Account operations"""
    label: str
    bank_id: str
    account_type: str
    id: Optional[str] = None


@dataclass
class FilterCriteria:
    """Data Transfer Object for filter criteria"""
    bank_id: Optional[str] = None
    account_id: Optional[str] = None
    category: Optional[str] = None
    product_type: Optional[str] = None
    search_query: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SortCriteria:
    """Data Transfer Object for sort criteria"""
    field: str
    ascending: bool = True


@dataclass
class PaginationOptions:
    """Data Transfer Object for pagination options"""
    page: int = 0
    items_per_page: int = 10
    total_items: int = 0


@dataclass
class QueryResult:
    """Generic query result with pagination information"""
    items: List[Any]
    pagination: PaginationOptions
    filters: Optional[FilterCriteria] = None
    sort: Optional[SortCriteria] = None
    total_value: Optional[float] = None
