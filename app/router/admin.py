from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, cast, String, func
import sqlalchemy as sa
from typing import Annotated, List, Optional

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.models.user import User, UserRole
from app.models.program import Program
from app.models.registration import ProgramRegistration, PaymentStatus
from app.models.payment import Payment
from app.models.membership import Membership
from app.models.membership_registration import MembershipRegistration
from app.schema.auth import UserResponse, AdminUserCreate
from app.schema.analytics import DashboardAnalytics, StatCard, AnalyticsTrendResponse, TrendDataPoint
from app.schema.notification import NotificationItem, NotificationList
from app.services.settings_service import settings_service
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["admin"])

# Admins and Super Admins can view user data
admin_access = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])
super_admin_only = RoleChecker([UserRole.SUPER_ADMIN])

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)],
    q: Optional[str] = None
):
    """List all users with optional search. Accessible by Admin and Super Admin."""
    query = select(User)
    
    if q:
        search_filter = or_(
            User.full_name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.phone_number.ilike(f"%{q}%"),
            cast(User.id, String).ilike(f"%{q}%")
        )
        query = query.where(search_filter)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    payload: AdminUserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Add a participant from the admin panel. Accessible by Admin and Super Admin."""
    # email and phone_number are both unique columns: check first so a clash is a
    # 409 naming the field rather than an IntegrityError surfacing as a 500.
    clashes = []
    if payload.email:
        clashes.append(User.email == payload.email)
    if payload.phone_number:
        clashes.append(User.phone_number == payload.phone_number)

    existing = (await db.execute(select(User).where(or_(*clashes)))).scalars().first()
    if existing:
        field = "email address" if payload.email and existing.email == payload.email else "phone number"
        raise HTTPException(status_code=409, detail=f"A participant with this {field} already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        nickname=payload.nickname,
        gender=payload.gender,
        dob=payload.dob,
        occupation=payload.occupation,
        address=payload.address,
        role=UserRole.USER,
        is_active=True,
        # Added by an admin, so no OTP round-trip is required.
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/promote-to-admin/{user_id}", response_model=UserResponse)
async def promote_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    super_admin: Annotated[User, Depends(super_admin_only)]
):
    """Promote a user to Admin. Accessible by Super Admin only."""
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalars().first()
    if user:
        user.role = UserRole.ADMIN
        await db.commit()
    return user

@router.get("/analytics", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Get dashboard analytics with 30-day growth comparisons."""
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    async def get_stats(start_date, end_date=None):
        # Participants
        part_query = select(func.count(ProgramRegistration.id))
        if end_date:
            part_query = part_query.where(ProgramRegistration.created_at >= start_date, ProgramRegistration.created_at < end_date)
        else:
            part_query = part_query.where(ProgramRegistration.created_at >= start_date)
        
        # Revenue with Currency Conversion (Base: MYR)
        # We use a CASE statement to convert SGD and USD to MYR if needed
        revenue_expr = func.sum(
            sa.case(
                (Program.currency == 'SGD', ProgramRegistration.amount_paid * 3.5),
                (Program.currency == 'USD', ProgramRegistration.amount_paid * 4.7),
                else_=ProgramRegistration.amount_paid
            )
        )
        rev_query = select(revenue_expr).join(Program, ProgramRegistration.program_id == Program.id)
        
        if end_date:
            rev_query = rev_query.where(ProgramRegistration.created_at >= start_date, ProgramRegistration.created_at < end_date)
        else:
            rev_query = rev_query.where(ProgramRegistration.created_at >= start_date)
            
        # Completion (Paid in full)
        comp_query = select(func.count(ProgramRegistration.id)).where(ProgramRegistration.payment_status == PaymentStatus.COMPLETED)
        if end_date:
            comp_query = comp_query.where(ProgramRegistration.created_at >= start_date, ProgramRegistration.created_at < end_date)
        else:
            comp_query = comp_query.where(ProgramRegistration.created_at >= start_date)

        # Active Programs (Current state)
        prog_query = select(func.count(Program.id)).where(Program.is_active == True)

        part_res = await db.execute(part_query)
        rev_res = await db.execute(rev_query)
        comp_res = await db.execute(comp_query)
        prog_res = await db.execute(prog_query)

        return {
            "participants": part_res.scalar() or 0,
            "revenue": float(rev_res.scalar() or 0),
            "completed": comp_res.scalar() or 0,
            "programs": prog_res.scalar() or 0
        }

    current = await get_stats(thirty_days_ago)
    previous = await get_stats(sixty_days_ago, thirty_days_ago)

    # Total cumulative counts for display
    total_participants_res = await db.execute(select(func.count(ProgramRegistration.id)))
    
    # Total Revenue Cumulative with Currency Conversion
    total_revenue_expr = func.sum(
        sa.case(
            (Program.currency == 'SGD', ProgramRegistration.amount_paid * 3.5),
            (Program.currency == 'USD', ProgramRegistration.amount_paid * 4.7),
            else_=ProgramRegistration.amount_paid
        )
    )
    total_revenue_res = await db.execute(select(total_revenue_expr).join(Program, ProgramRegistration.program_id == Program.id))
    
    total_completed_res = await db.execute(select(func.count(ProgramRegistration.id)).where(ProgramRegistration.payment_status == PaymentStatus.COMPLETED))
    
    total_participants = total_participants_res.scalar() or 0
    total_revenue = float(total_revenue_res.scalar() or 0)
    total_completed = total_completed_res.scalar() or 0
    
    completion_rate = (total_completed / total_participants * 100) if total_participants > 0 else 0
    prev_completion_rate = (previous["completed"] / previous["participants"] * 100) if previous["participants"] > 0 else 0

    def calc_change(curr, prev):
        if prev == 0:
            return 100.0 if curr > 0 else 0.0
        return round(((curr - prev) / prev) * 100, 1)

    return DashboardAnalytics(
        total_participants=StatCard(
            value=total_participants,
            change_percentage=calc_change(current["participants"], previous["participants"]),
            is_growth=current["participants"] >= previous["participants"],
            label="Total Participants"
        ),
        active_programs=StatCard(
            value=current["programs"],
            change_percentage=0.0, # Program count is usually stable
            is_growth=True,
            label="Active Programs"
        ),
        total_revenue=StatCard(
            value=total_revenue,
            change_percentage=calc_change(current["revenue"], previous["revenue"]),
            is_growth=current["revenue"] >= previous["revenue"],
            label="Total Revenue"
        ),
        completion_rate=StatCard(
            value=round(completion_rate, 1),
            change_percentage=round(completion_rate - prev_completion_rate, 1),
            is_growth=completion_rate >= prev_completion_rate,
            label="Completion Rate"
        )
    )

@router.get("/analytics/trends", response_model=AnalyticsTrendResponse)
async def get_analytics_trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)],
    period: Optional[str] = "30d",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get income and participant trends with optional date filters."""
    # Determine date range
    if period == "7d":
        start = datetime.now() - timedelta(days=7)
        end = datetime.now()
        period_label = "Last 7 Days"
    elif period == "30d":
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        period_label = "Last 30 Days"
    elif start_date and end_date:
        start = start_date
        end = end_date
        period_label = f"{start.strftime('%b %d')} - {end.strftime('%b %d')}"
    else:
        # Default to 30 days
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        period_label = "Last 30 Days"

    # Ensure start/end are at day boundaries for consistent filtering
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Revenue calculation with Currency Conversion (Base: MYR)
    revenue_expr = func.sum(
        sa.case(
            (Program.currency == 'SGD', ProgramRegistration.amount_paid * 3.5),
            (Program.currency == 'USD', ProgramRegistration.amount_paid * 4.7),
            else_=ProgramRegistration.amount_paid
        )
    )

    query = select(
        func.date(ProgramRegistration.created_at).label("day"),
        func.count(ProgramRegistration.id).label("participants"),
        revenue_expr.label("revenue")
    ).join(Program, ProgramRegistration.program_id == Program.id)\
    .where(ProgramRegistration.created_at >= start, ProgramRegistration.created_at <= end)\
    .group_by(func.date(ProgramRegistration.created_at))\
    .order_by(func.date(ProgramRegistration.created_at).asc())

    result = await db.execute(query)
    rows = result.all()
    
    # Map existing data
    data_map = {row.day.strftime("%Y-%m-%d"): row for row in rows}
    
    trends = []
    total_rev = 0
    total_part = 0

    # Fill in all dates in the range
    current_date = start.date()
    end_date_limit = end.date()
    
    while current_date <= end_date_limit:
        date_str = current_date.strftime("%Y-%m-%d")
        row = data_map.get(date_str)
        
        rev = float(row.revenue or 0) if row else 0.0
        part = row.participants if row else 0
        
        trends.append(TrendDataPoint(
            date=date_str,
            participants=part,
            revenue=rev
        ))
        total_rev += rev
        total_part += part
        
        current_date += timedelta(days=1)

    return AnalyticsTrendResponse(
        trends=trends,
        total_revenue=total_rev,
        total_participants=total_part,
        period_label=period_label
    )


@router.get("/notifications", response_model=NotificationList)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)],
    limit: int = 20
):
    """
    Recent activity for the admin bell: completed payments, programme
    registrations, membership applications and new participants.

    There is no notifications table. Rather than introduce one and have to
    backfill it, this reads the events straight from the rows that represent
    them, so the feed is correct for history that already exists. Each source is
    queried for its own newest `limit`, then merged and trimmed — cheaper than
    a UNION across four tables with different columns, and the per-source limit
    keeps one busy source from starving the others out of the query.

    Read state is not stored: the panel tracks what the operator has already
    seen locally, which needs no schema and no per-admin bookkeeping.

    Which kinds appear is filtered here rather than in the browser, so a kind the
    operator has switched off in Settings costs nothing to fetch and cannot leak
    into the unread count.
    """
    limit = max(1, min(limit, 100))
    items: list[NotificationItem] = []

    enabled = (await settings_service.get(db)).enabled_notification_types()
    if not enabled:
        return NotificationList(items=[])

    # Payments — only completed ones. A pending payment is just a registration
    # that has not been paid for, which is already its own notification.
    payments = [] if "payment" not in enabled else (await db.execute(
        select(Payment)
        .where(func.lower(Payment.status) == "completed")
        .options(
            selectinload(Payment.registration).selectinload(ProgramRegistration.user),
            selectinload(Payment.registration).selectinload(ProgramRegistration.program),
        )
        .order_by(Payment.created_at.desc())
        .limit(limit)
    )).scalars().all()

    for p in payments:
        reg = p.registration
        who = reg.user.full_name if reg and reg.user else "Someone"
        prog = reg.program.program_name if reg and reg.program else None
        items.append(NotificationItem(
            id=f"payment:{p.id}",
            type="payment",
            title=f"{who} paid {p.currency} {p.amount:,.2f}",
            detail=f"for {prog}" if prog else None,
            created_at=p.created_at,
            link=f"/programs/{reg.program_id}" if reg else None,
        ))

    registrations = [] if "program_registration" not in enabled else (await db.execute(
        select(ProgramRegistration)
        .options(
            selectinload(ProgramRegistration.user),
            selectinload(ProgramRegistration.program),
        )
        .order_by(ProgramRegistration.created_at.desc())
        .limit(limit)
    )).scalars().all()

    for r in registrations:
        who = r.user.full_name if r.user else "Someone"
        prog = r.program.program_name if r.program else "a programme"
        items.append(NotificationItem(
            id=f"registration:{r.id}",
            type="program_registration",
            title=f"{who} registered for {prog}",
            detail=f"Payment {r.payment_status.value.lower()}" if r.payment_status else None,
            created_at=r.created_at,
            link=f"/programs/{r.program_id}",
        ))

    applications = [] if "membership_application" not in enabled else (await db.execute(
        select(MembershipRegistration)
        .options(
            selectinload(MembershipRegistration.user),
            selectinload(MembershipRegistration.membership),
        )
        .order_by(MembershipRegistration.created_at.desc())
        .limit(limit)
    )).scalars().all()

    for a in applications:
        who = a.user.full_name if a.user else "Someone"
        name = a.membership.name if a.membership else "a membership"
        items.append(NotificationItem(
            id=f"membership:{a.id}",
            type="membership_application",
            title=f"{who} applied for {name}",
            detail=f"{a.membership_type} - {a.status}" if a.membership_type else a.status,
            created_at=a.created_at,
            link="/memberships/applications",
        ))

    participants = [] if "participant" not in enabled else (await db.execute(
        select(User)
        .where(User.role == UserRole.USER)
        .order_by(User.created_at.desc())
        .limit(limit)
    )).scalars().all()

    for u in participants:
        items.append(NotificationItem(
            id=f"user:{u.id}",
            type="participant",
            title=f"{u.full_name} joined",
            detail=u.email or u.phone_number,
            created_at=u.created_at,
            link="/users",
        ))

    items.sort(key=lambda i: i.created_at, reverse=True)
    return NotificationList(items=items[:limit])
