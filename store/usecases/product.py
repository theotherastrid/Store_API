from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException
from datetime import datetime

class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, minimo: Optional[Decimal] = None, maximo: Optional[Decimal] = None) -> List[ProductOut]:
        filtro = {}

        if minimo is not None or maximo is not None:
            filtro["price"] = {}
            if minimo is not None:
                filtro["price"]["$gte"] = float(minimo)
            if maximo is not None:
                filtro["price"]["$lte"] = float(maximo)

        return [ProductOut(**item) async for item in self.collection.find(filtro)]

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        objeto = body.model.dump(exclude_none=True)
        objeto["updated_at"] = datetime.now()
        
        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": objeto},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
