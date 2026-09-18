from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.product import Product
from app.repositories import admin_repository, product_repository


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


def get_admin_or_404(db: Session, admin_id: int) -> Admin:
    admin = admin_repository.get_by_id(db, admin_id)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found.")
    return admin
