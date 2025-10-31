from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from backend.deps import get_current_user
from core.agents.data_collector.repo import DataRepo
import pandas as pd
import io
from typing import Optional

router = APIRouter(prefix="/api", tags=["catalog"]) 

async def get_repo() -> DataRepo:
    repo = DataRepo()
    await repo.init()
    return repo


@router.post("/catalog/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    token: str = Query(...),
    current_user = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    if not file.filename.endswith((".csv", ".json")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV or JSON file.")

    contents = await file.read()

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_json(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    required_columns = {"sku", "title", "currency", "current_price", "cost", "stock"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}",
        )

    try:
        df["current_price"] = pd.to_numeric(df["current_price"])
        df["cost"] = pd.to_numeric(df["cost"])
        df["stock"] = pd.to_numeric(df["stock"]).astype(int)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data types: {str(e)}")

    if (df["current_price"] < 0).any() or (df["cost"] < 0).any():
        raise HTTPException(status_code=400, detail="Prices and costs must be non-negative")

    if (df["stock"] < 0).any():
        raise HTTPException(status_code=400, detail="Stock must be non-negative")

    if df["sku"].duplicated().any():
        raise HTTPException(status_code=400, detail="Duplicate SKU values found in file")

    owner_id = str(current_user["user_id"])
    rows_data = df.to_dict("records")

    try:
        rows_inserted = await repo.upsert_products(rows_data, owner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "success": True,
        "filename": file.filename,
        "rows_processed": len(rows_data),
        "rows_inserted": rows_inserted,
        "owner_id": owner_id,
    }


@router.get("/catalog/products")
async def get_products(
    token: str = Query(...),
    current_user = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    owner_id = str(current_user["user_id"])

    try:
        products = await repo.get_products_by_owner(owner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"success": True, "count": len(products), "products": products}


@router.get("/catalog/products/{sku}")
async def get_product(
    sku: str,
    token: str = Query(...),
    current_user = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    owner_id = str(current_user["user_id"])

    try:
        product = await repo.get_product_by_sku_and_owner(sku, owner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"success": True, "product": product}


@router.delete("/catalog/products/{sku}")
async def delete_product(
    sku: str,
    token: str = Query(...),
    current_user = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    owner_id = str(current_user["user_id"])

    try:
        rows_affected = await repo.delete_product_by_owner(sku, owner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"success": True, "message": "Product deleted successfully", "rows_affected": rows_affected}


@router.delete("/catalog/products")
async def delete_all_products(
    token: str = Query(...),
    current_user = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    owner_id = str(current_user["user_id"])

    try:
        rows_affected = await repo.delete_all_products_by_owner(owner_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"success": True, "message": f"All products deleted successfully", "rows_affected": rows_affected}
