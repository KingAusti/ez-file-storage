from .auth import router as auth_router
from .data_entries import router as data_entries_router
from .tags import router as tags_router

__all__ = ["auth_router", "data_entries_router", "tags_router"]
