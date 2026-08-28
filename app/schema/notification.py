from datetime import datetime
from pydantic import BaseModel


class NotificationItem(BaseModel):
    """
    One thing that happened, in a shape the admin panel can render without
    knowing which table it came from.

    `id` is prefixed with the source ("payment:<uuid>") so ids from different
    tables cannot collide in the same list.
    """
    id: str
    type: str
    title: str
    detail: str | None = None
    created_at: datetime
    link: str | None = None


class NotificationList(BaseModel):
    items: list[NotificationItem]
