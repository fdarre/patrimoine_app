"""
Centralized session state manager for Streamlit applications
"""
from typing import Any, Dict, List, Optional

import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Centralized manager for Streamlit's session_state

    This class provides methods to safely get, set, and manage values in
    st.session_state with consistent naming and logging.
    """

    # Prefixes for different types of state
    PAGE_PREFIX = "page_"
    FORM_PREFIX = "form_"
    EDIT_PREFIX = "edit_"
    FILTER_PREFIX = "filter_"

    def __init__(self):
        """Initialize the session manager"""
        pass

    def get_page(self, key: str, default: int = 0) -> int:
        """
        Get a pagination page value

        Args:
            key: Base key for the page
            default: Default value if not found

        Returns:
            Current page value
        """
        full_key = f"{self.PAGE_PREFIX}{key}"
        return self.get(full_key, default)

    def set_page(self, key: str, value: int) -> None:
        """
        Set a pagination page value

        Args:
            key: Base key for the page
            value: Page value to set
        """
        full_key = f"{self.PAGE_PREFIX}{key}"
        self.set(full_key, value)

    def is_editing(self, item_type: str, item_id: str) -> bool:
        """
        Check if an item is being edited

        Args:
            item_type: Type of item (asset, bank, account)
            item_id: ID of the item

        Returns:
            True if the item is being edited
        """
        full_key = f"{self.EDIT_PREFIX}{item_type}_{item_id}"
        return self.get(full_key, False)

    def set_editing(self, item_type: str, item_id: str, is_editing: bool = True) -> None:
        """
        Set editing state for an item

        Args:
            item_type: Type of item (asset, bank, account)
            item_id: ID of the item
            is_editing: Whether the item is being edited
        """
        full_key = f"{self.EDIT_PREFIX}{item_type}_{item_id}"
        self.set(full_key, is_editing)

        # Log operation
        if is_editing:
            logger.info(f"Started editing {item_type} {item_id}")
        else:
            logger.info(f"Finished editing {item_type} {item_id}")

    def get_filter(self, section: str, filter_name: str, default: Any = None) -> Any:
        """
        Get a filter value

        Args:
            section: Section of the application
            filter_name: Name of the filter
            default: Default value if not found

        Returns:
            Current filter value
        """
        full_key = f"{self.FILTER_PREFIX}{section}_{filter_name}"
        return self.get(full_key, default)

    def set_filter(self, section: str, filter_name: str, value: Any) -> None:
        """
        Set a filter value

        Args:
            section: Section of the application
            filter_name: Name of the filter
            value: Filter value to set
        """
        full_key = f"{self.FILTER_PREFIX}{section}_{filter_name}"
        self.set(full_key, value)

    def get_form_value(self, form_name: str, field_name: str, default: Any = None) -> Any:
        """
        Get a form field value

        Args:
            form_name: Name of the form
            field_name: Name of the field
            default: Default value if not found

        Returns:
            Current field value
        """
        full_key = f"{self.FORM_PREFIX}{form_name}_{field_name}"
        return self.get(full_key, default)

    def set_form_value(self, form_name: str, field_name: str, value: Any) -> None:
        """
        Set a form field value

        Args:
            form_name: Name of the form
            field_name: Name of the field
            value: Field value to set
        """
        full_key = f"{self.FORM_PREFIX}{form_name}_{field_name}"
        self.set(full_key, value)

    def clear_form(self, form_name: str) -> None:
        """
        Clear all fields in a form

        Args:
            form_name: Name of the form
        """
        prefix = f"{self.FORM_PREFIX}{form_name}_"
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith(prefix)]

        for key in keys_to_clear:
            del st.session_state[key]

        logger.info(f"Cleared form {form_name}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from session_state

        Args:
            key: Key to get
            default: Default value if not found

        Returns:
            Value from session_state or default
        """
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in session_state

        Args:
            key: Key to set
            value: Value to set
        """
        st.session_state[key] = value

    def delete(self, key: str) -> None:
        """
        Delete a key from session_state

        Args:
            key: Key to delete
        """
        if key in st.session_state:
            del st.session_state[key]

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys in session_state with an optional prefix filter

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        if prefix is None:
            return list(st.session_state.keys())
        else:
            return [k for k in st.session_state.keys() if k.startswith(prefix)]

    def get_state_info(self) -> Dict[str, Any]:
        """
        Get information about the current session_state

        Returns:
            Dictionary with information about session_state
        """
        return {
            "total_keys": len(st.session_state),
            "page_keys": len(self.list_keys(self.PAGE_PREFIX)),
            "form_keys": len(self.list_keys(self.FORM_PREFIX)),
            "edit_keys": len(self.list_keys(self.EDIT_PREFIX)),
            "filter_keys": len(self.list_keys(self.FILTER_PREFIX)),
        }


# Create singleton instance
session_manager = SessionManager()
