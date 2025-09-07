"""
Persons API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.person import Person, PersonType
from app.models.group import Group
from app.api.groups import get_user_accessible_groups
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[PersonResponse])
async def get_persons(
    person_type: Optional[PersonType] = Query(None, description="Filter by person type"),
    search: Optional[str] = Query(None, description="Search in name, email, CPF/CNPJ"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all persons with optional filters based on user group permissions"""
    # Get accessible groups for the user
    accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
    
    query = select(Person, func.count(Group.id).label('group_count')).outerjoin(Group, Person.id == Group.person_id)
    
    # Filter by accessible groups for non-admin users
    if not current_user.is_admin:
        if not accessible_groups:
            # User has no group permissions, return empty list
            return []
        query = query.where(
            (Group.id.in_(accessible_groups)) |
            (Group.id.is_(None))  # Include persons without group
        )
    
    # Apply filters
    conditions = []
    if person_type:
        conditions.append(Person.person_type == person_type)
    if active is not None:
        conditions.append(Person.active == active)
    if search:
        search_condition = or_(
            Person.name.ilike(f"%{search}%"),
            Person.email.ilike(f"%{search}%"),
            Person.cpf.ilike(f"%{search}%"),
            Person.cnpj.ilike(f"%{search}%")
        )
        conditions.append(search_condition)
    
    if conditions:
        query = query.where(*conditions)
    
    query = query.group_by(Person.id).order_by(Person.name)
    
    result = await db.execute(query)
    persons_with_counts = result.all()
    
    persons = []
    for person, group_count in persons_with_counts:
        person_dict = {
            "id": person.id,
            "name": person.name,
            "person_type": person.person_type,
            "email": person.email,
            "phone": person.phone,
            "address": person.address,
            "city": person.city,
            "state": person.state,
            "zip_code": person.zip_code,
            "country": person.country,
            "active": person.active,
            "cpf": person.cpf,
            "birth_date": person.birth_date,
            "cnpj": person.cnpj,
            "company_name": person.company_name,
            "trade_name": person.trade_name,
            "created_at": person.created_at,
            "updated_at": person.updated_at,
            "group_count": group_count
        }
        persons.append(PersonResponse(**person_dict))
    
    return persons

@router.post("/", response_model=PersonResponse)
async def create_person(
    person_create: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new person"""
    # Check if email already exists
    result = await db.execute(select(Person).where(Person.email == person_create.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person with this email already exists"
        )
    
    # Check group permissions for non-admin users
    if not current_user.is_admin and person_create.group_id:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if person_create.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create persons in this group"
            )
    
    # Check CPF uniqueness for physical persons
    if person_create.person_type == PersonType.PHYSICAL and person_create.cpf:
        result = await db.execute(select(Person).where(Person.cpf == person_create.cpf))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this CPF already exists"
            )
    
    # Check CNPJ uniqueness for legal persons
    if person_create.person_type == PersonType.LEGAL and person_create.cnpj:
        result = await db.execute(select(Person).where(Person.cnpj == person_create.cnpj))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this CNPJ already exists"
            )
    
    # Create person
    db_person = Person(**person_create.dict())
    db.add(db_person)
    await db.commit()
    await db.refresh(db_person)
    
    return PersonResponse(
        id=db_person.id,
        name=db_person.name,
        person_type=db_person.person_type,
        email=db_person.email,
        phone=db_person.phone,
        address=db_person.address,
        city=db_person.city,
        state=db_person.state,
        zip_code=db_person.zip_code,
        country=db_person.country,
        active=db_person.active,
        cpf=db_person.cpf,
        birth_date=db_person.birth_date,
        cnpj=db_person.cnpj,
        company_name=db_person.company_name,
        trade_name=db_person.trade_name,
        created_at=db_person.created_at,
        updated_at=db_person.updated_at,
        group_count=0
    )

@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific person"""
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        # Check if person belongs to any group the user has access to
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if accessible_groups:
            person_groups_result = await db.execute(
                select(Group.id).where(Group.person_id == person_id)
            )
            person_groups = {row[0] for row in person_groups_result.all()}
            if not person_groups.intersection(accessible_groups):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this person"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this person"
            )
    
    # Get group count
    group_count_result = await db.execute(
        select(func.count(Group.id)).where(Group.person_id == person_id)
    )
    group_count = group_count_result.scalar() or 0
    
    return PersonResponse(
        id=person.id,
        name=person.name,
        person_type=person.person_type,
        email=person.email,
        phone=person.phone,
        address=person.address,
        city=person.city,
        state=person.state,
        zip_code=person.zip_code,
        country=person.country,
        active=person.active,
        cpf=person.cpf,
        birth_date=person.birth_date,
        cnpj=person.cnpj,
        company_name=person.company_name,
        trade_name=person.trade_name,
        created_at=person.created_at,
        updated_at=person.updated_at,
        group_count=group_count
    )

@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    person_update: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a person"""
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if accessible_groups:
            person_groups_result = await db.execute(
                select(Group.id).where(Group.person_id == person_id)
            )
            person_groups = {row[0] for row in person_groups_result.all()}
            if not person_groups.intersection(accessible_groups):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to modify this person"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this person"
            )
        
        # Check if user is trying to change group to one they don't have access to
        if person_update.group_id and person_update.group_id not in accessible_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to assign persons to this group"
            )
    
    # Check email uniqueness if being updated
    if person_update.email and person_update.email != person.email:
        existing_result = await db.execute(
            select(Person).where(Person.email == person_update.email)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this email already exists"
            )
    
    # Check CPF uniqueness if being updated
    if person_update.cpf and person_update.cpf != person.cpf:
        existing_result = await db.execute(
            select(Person).where(Person.cpf == person_update.cpf)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this CPF already exists"
            )
    
    # Check CNPJ uniqueness if being updated
    if person_update.cnpj and person_update.cnpj != person.cnpj:
        existing_result = await db.execute(
            select(Person).where(Person.cnpj == person_update.cnpj)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this CNPJ already exists"
            )
    
    # Update person
    update_data = person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)
    
    await db.commit()
    await db.refresh(person)
    
    # Get group count
    group_count_result = await db.execute(
        select(func.count(Group.id)).where(Group.person_id == person_id)
    )
    group_count = group_count_result.scalar() or 0
    
    return PersonResponse(
        id=person.id,
        name=person.name,
        person_type=person.person_type,
        email=person.email,
        phone=person.phone,
        address=person.address,
        city=person.city,
        state=person.state,
        zip_code=person.zip_code,
        country=person.country,
        active=person.active,
        cpf=person.cpf,
        birth_date=person.birth_date,
        cnpj=person.cnpj,
        company_name=person.company_name,
        trade_name=person.trade_name,
        created_at=person.created_at,
        updated_at=person.updated_at,
        group_count=group_count
    )

@router.delete("/{person_id}")
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a person"""
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Check permissions for non-admin users
    if not current_user.is_admin:
        accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
        if accessible_groups:
            person_groups_result = await db.execute(
                select(Group.id).where(Group.person_id == person_id)
            )
            person_groups = {row[0] for row in person_groups_result.all()}
            if not person_groups.intersection(accessible_groups):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this person"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this person"
            )
    
    # Check if person has groups
    group_count_result = await db.execute(
        select(func.count(Group.id)).where(Group.person_id == person_id)
    )
    group_count = group_count_result.scalar() or 0
    
    if group_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete person with groups. Please delete or reassign groups first."
        )
    
    await db.delete(person)
    await db.commit()
    
    return {"message": "Person deleted successfully"}

