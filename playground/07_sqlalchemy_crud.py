"""SQLAlchemy: полный CRUD-репозиторий + запросы + оптимизация.

Реальный пример: интернет-магазин (Users → Orders → Products → Categories).
Всё через AsyncSession + Repository Pattern.

Зависимости: pip install sqlalchemy[asyncio] aiosqlite
Запуск:      python 07_sqlalchemy_crud.py
"""

import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
    text,
    update,
    delete,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
    joinedload,
    contains_eager,
    lazyload,
)


# ══════════════════════════════════════════════════════════════════
# 1. МОДЕЛИ (связи: Category → Product → Order → User)
# ══════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(__file__), "playground.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")

    products: Mapped[list["Product"]] = relationship(
        back_populates="category", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}')"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products", lazy="joined")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    city = Column(String(100), default="")

    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}')"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    status = Column(String(20), default="pending")  # pending / shipped / delivered

    user: Mapped["User"] = relationship(back_populates="orders", lazy="joined")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Order(id={self.id}, status='{self.status}')"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # цена на момент заказа

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items", lazy="joined")

    def __repr__(self) -> str:
        return f"OrderItem(product_id={self.product_id}, qty={self.quantity})"


# ══════════════════════════════════════════════════════════════════
# 2. ДВИЖОК + ФАБРИКА СЕССИЙ
# ══════════════════════════════════════════════════════════════════

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ══════════════════════════════════════════════════════════════════
# 3. REPOSITORY: полный CRUD
# ══════════════════════════════════════════════════════════════════

class UserRepository:
    """CRUD для пользователей."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, email: str, city: str = "") -> User:
        user = User(name=name, email=email, city=city)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def search_by_name(self, pattern: str) -> list[User]:
        stmt = select(User).where(User.name.ilike(f"%{pattern}%"))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProductRepository:
    """CRUD для товаров."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, name: str, price: float, stock: int, category_id: int
    ) -> Product:
        product = Product(name=name, price=price, stock=stock, category_id=category_id)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> list[Product]:
        stmt = select(Product).order_by(Product.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_stock(self, product_id: int, delta: int) -> Optional[Product]:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock + delta)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(product_id)

    async def delete(self, product_id: int) -> bool:
        stmt = delete(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


class OrderRepository:
    """CRUD для заказов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(
        self, user_id: int, items: list[dict]
    ) -> Order:
        """Создаёт заказ с товарами.

        items: [{"product_id": 1, "quantity": 2}, ...]
        """
        order = Order(user_id=user_id)
        self.session.add(order)
        await self.session.flush()  # получаем order.id

        for item in items:
            product = await self._get_product(item["product_id"])
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=product.price,
            )
            self.session.add(order_item)

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def _get_product(self, product_id: int) -> Product:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        product = result.scalars().one()
        if product.stock <= 0:
            raise ValueError(f"Товар '{product.name}' закончился")
        product.stock -= 1
        return product

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_orders(self, user_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, order_id: int, status: str) -> Optional[Order]:
        stmt = update(Order).where(Order.id == order_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(order_id)


# ══════════════════════════════════════════════════════════════════
# 4. ЗАПРОСЫ С ФИЛЬТРАМИ
# ══════════════════════════════════════════════════════════════════

async def demo_filters() -> None:
    async with async_session() as session:
        # ── Простой фильтр ─────────────────────────────────────
        stmt = select(Product).where(Product.price > 100)
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  цена > 100: {len(products)} товаров")

        # ── Несколько условий (AND) ────────────────────────────
        stmt = select(Product).where(
            Product.price > 50,
            Product.stock > 0,
        )
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  цена > 50 И stock > 0: {len(products)}")

        # ── OR через | ─────────────────────────────────────────
        stmt = select(Product).where(
            (Product.price < 10) | (Product.price > 500)
        )
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  цена < 10 ИЛИ > 500: {len(products)}")

        # ── IN ─────────────────────────────────────────────────
        stmt = select(Product).where(Product.category_id.in_([1, 2]))
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  category_id IN [1,2]: {len(products)}")

        # ── LIKE / ilike (регистронезависимый) ──────────────────
        stmt = select(Product).where(Product.name.ilike("%phone%"))
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  name LIKE '%phone%': {len(products)}")

        # ── BETWEEN ────────────────────────────────────────────
        stmt = select(Product).where(Product.price.between(50, 200))
        result = await session.execute(stmt)
        products = result.scalars().all()
        print(f"  цена BETWEEN 50..200: {len(products)}")

        # ── IS NULL / IS NOT NULL ──────────────────────────────
        stmt = select(User).where(User.city.isnot(None), User.city != "")
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"  city IS NOT NULL: {len(users)}")

        # ── ORDER BY + LIMIT + OFFSET (пагинация) ─────────────
        stmt = (
            select(Product)
            .order_by(Product.price.desc())
            .limit(5)
            .offset(0)
        )
        result = await session.execute(stmt)
        top5 = result.scalars().all()
        print(f"  топ-5 самых дорогих: {[p.name for p in top5]}")

        # ── SELECT конкретных колонок (не整个 объект) ───────────
        stmt = select(Product.name, Product.price).where(Product.price > 100)
        result = await session.execute(stmt)
        rows = result.all()
        print(f"  только name + price: {rows[:3]}")


# ══════════════════════════════════════════════════════════════════
# 5. JOIN'ы
# ══════════════════════════════════════════════════════════════════

async def demo_joins() -> None:
    async with async_session() as session:

        # ── INNER JOIN: товары с названиями категорий ───────────
        stmt = (
            select(Product.name, Product.price, Category.name.label("category"))
            .join(Category, Product.category_id == Category.id)
            .where(Product.price > 100)
        )
        result = await session.execute(stmt)
        rows = result.all()
        print(f"  товары > 100 с категориями:")
        for name, price, cat in rows[:5]:
            print(f"    {name} ({cat}): {price} руб.")

        # ── LEFT JOIN: все товары, даже без категории ───────────
        # (у нас FK не nullable, поэтому LEFT и INNER дают одинаковый результат)
        stmt = (
            select(
                Category.name.label("category"),
                func.count(Product.id).label("product_count"),
            )
            .outerjoin(Product, Category.id == Product.category_id)
            .group_by(Category.name)
            .order_by(func.count(Product.id).desc())
        )
        result = await session.execute(stmt)
        rows = result.all()
        print(f"\n  товаров по категориям:")
        for cat, count in rows:
            print(f"    {cat}: {count}")

        # ── МНОГОКОЛЕННЫЙ JOIN: User → Order → OrderItem → Product ──
        stmt = (
            select(
                User.name.label("user"),
                Order.id.label("order_id"),
                Product.name.label("product"),
                OrderItem.quantity,
                OrderItem.unit_price,
            )
            .join(Order, User.id == Order.user_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, OrderItem.product_id == Product.id)
            .order_by(User.name, Order.id)
        )
        result = await session.execute(stmt)
        rows = result.all()
        print(f"\n  все заказы (User → Order → Product):")
        for user, order_id, product, qty, price in rows[:8]:
            print(f"    {user} #{order_id}: {product} × {qty} @ {price}")

        # ── SELF JOIN (пример) ──────────────────────────────────
        # Найти товары одной категории, стоящие дороже других
        stmt = (
            select(
                Product.name.label("expensive"),
                Category.name.label("category"),
                Product.price,
            )
            .join(Category)
            .where(Product.price > 100)
            .order_by(Category.name, Product.price.desc())
        )
        result = await session.execute(stmt)
        rows = result.all()
        print(f"\n  дорогие товары (>100):")
        for name, cat, price in rows[:5]:
            print(f"    [{cat}] {name}: {price}")


# ══════════════════════════════════════════════════════════════════
# 6. ЗАГРУЗКА ВЛОЖЕННЫХ СУЩНОСТЕЙ (Eager vs Lazy)
# ══════════════════════════════════════════════════════════════════

async def demo_eager_loading() -> None:
    async with async_session() as session:

        # ── selectinload: подгружает связанные объекты ОТДЕЛЬНЫМ запросом ──
        # SQL: SELECT * FROM users; SELECT * FROM orders WHERE user_id IN (...)
        stmt = (
            select(User)
            .options(selectinload(User.orders))
            .limit(3)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"  selectinload (2 запроса):")
        for user in users:
            print(f"    {user.name}: {len(user.orders)} заказов")

        # ── joinedload: подгружает через JOIN ───────────────────
        # SQL: SELECT * FROM users JOIN orders ON ...
        stmt = (
            select(User)
            .options(joinedload(User.orders))
            .limit(3)
        )
        result = await session.execute(stmt)
        users = result.scalars().unique().all()  # unique() обязателен!
        print(f"\n  joinedload (1 запрос с JOIN):")
        for user in users:
            print(f"    {user.name}: {len(user.orders)} заказов")

        # ── lazyload (по умолчанию): запрос при обращении ───────
        stmt = select(User).limit(3)
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"\n  lazyload (запрос при обращении):")
        for user in users:
            # Вот тут SQLAlchemy делает SELECT * FROM orders WHERE user_id = ...
            orders_count = len(user.orders)  # N+1 запрос!
            print(f"    {user.name}: {orders_count} заказов (отдельный запрос!)")

        # ── contains_eager: когда JOIN делаем вручную ───────────
        stmt = (
            select(User)
            .join(Order)
            .options(contains_eager(User.orders))
            .where(Order.status == "delivered")
        )
        result = await session.execute(stmt)
        users = result.scalars().unique().all()
        print(f"\n  contains_eager (ручной JOIN + маппинг):")
        for user in users:
            print(f"    {user.name}: доставленные заказы")


# ══════════════════════════════════════════════════════════════════
# 7. АГРЕГАЦИИ: COUNT, SUM, AVG, GROUP BY, HAVING
# ══════════════════════════════════════════════════════════════════

async def demo_aggregations() -> None:
    async with async_session() as session:

        # ── Простой COUNT ──────────────────────────────────────
        count = (await session.execute(
            select(func.count(User.id))
        )).scalar()
        print(f"  всего пользователей: {count}")

        # ── SUM: общая сумма всех заказов ──────────────────────
        total = (await session.execute(
            select(func.sum(OrderItem.quantity * OrderItem.unit_price))
        )).scalar()
        print(f"  общая сумма продаж: {total:.2f} руб.")

        # ── AVG: средний чек ───────────────────────────────────
        avg_check = (await session.execute(
            select(func.avg(OrderItem.quantity * OrderItem.unit_price))
        )).scalar()
        print(f"  средний чек: {avg_check:.2f} руб.")

        # ── GROUP BY: сумма продаж по категориям ───────────────
        stmt = (
            select(
                Category.name.label("category"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("total"),
                func.count(OrderItem.id).label("items_sold"),
            )
            .join(Product, Category.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Category.name)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
        )
        result = await session.execute(stmt)
        rows = result.all()
        print(f"\n  продажи по категориям:")
        for cat, total, items in rows:
            print(f"    {cat}: {total:.2f} руб. ({items} шт.)")

        # ── HAVING: категории с продажами > 500 ────────────────
        stmt_having = (
            select(
                Category.name.label("category"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("total"),
            )
            .join(Product, Category.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Category.name)
            .having(func.sum(OrderItem.quantity * OrderItem.unit_price) > 500)
        )
        result = await session.execute(stmt_having)
        rows = result.all()
        print(f"\n  категории с продажами > 500:")
        for cat, total in rows:
            print(f"    {cat}: {total:.2f} руб.")

        # ── SUBQUERY: товары дороже средней цены ───────────────
        subq = select(func.avg(Product.price)).scalar_subquery()
        stmt_sub = (
            select(Product.name, Product.price)
            .where(Product.price > subq)
            .order_by(Product.price.desc())
        )
        result = await session.execute(stmt_sub)
        rows = result.all()
        print(f"\n  товары дороже средней цены:")
        for name, price in rows:
            print(f"    {name}: {price}")

        # ── СЛОЖНЫЙ АГРЕГАТ: топ-3 пользователя по сумме покупок ──
        stmt_top = (
            select(
                User.name,
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_spent"),
                func.count(Order.id).label("order_count"),
            )
            .join(Order, User.id == Order.user_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .group_by(User.name)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .limit(3)
        )
        result = await session.execute(stmt_top)
        rows = result.all()
        print(f"\n  топ-3 покупателя:")
        for name, total, orders in rows:
            print(f"    {name}: {total:.2f} руб. ({orders} заказов)")


# ══════════════════════════════════════════════════════════════════
# 8. ОПТИМИЗАЦИЯ ЗАПРОСОВ
# ══════════════════════════════════════════════════════════════════

async def demo_optimization() -> None:
    async with async_session() as session:

        # ── ПРОБЛЕМА N+1: lazy loading ─────────────────────────
        # 1 запрос на users + N запросов на orders каждого = N+1
        print("  ❌ N+1 (lazyload):")
        t0 = time.perf_counter()
        stmt = select(User).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()
        for user in users:
            _ = len(user.orders)  # отдельный запрос!
        t1 = time.perf_counter()
        print(f"     {len(users)} пользователей: {(t1-t0)*1000:.1f} мс")

        # ── РЕШЕНИЕ: selectinload ──────────────────────────────
        # 1 запрос на users + 1 запрос на orders (IN ...)
        print("\n  ✅ selectinload:")
        t0 = time.perf_counter()
        stmt = select(User).options(selectinload(User.orders)).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()
        for user in users:
            _ = len(user.orders)  # уже загружено!
        t1 = time.perf_counter()
        print(f"     {len(users)} пользователей: {(t1-t0)*1000:.1f} мс")

        # ── РЕШЕНИЕ: joinedload ────────────────────────────────
        # 1 запрос с JOIN (но может дублировать строки)
        print("\n  ✅ joinedload:")
        t0 = time.perf_counter()
        stmt = select(User).options(joinedload(User.orders)).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().unique().all()
        for user in users:
            _ = len(user.orders)
        t1 = time.perf_counter()
        print(f"     {len(users)} пользователей: {(t1-t0)*1000:.1f} мс")

        # ── TIPS ───────────────────────────────────────────────
        print("\n  📋 Советы по оптимизации:")
        print("     1. selectinload — для HasMany (отдельный IN-запрос)")
        print("     2. joinedload — для HasOne (JOIN)")
        print("     3. lazyload — только если точно знаешь что связь не нужна")
        print("     4. contains_eager — когда JOIN делаете руками")
        print("     5.oload() — для вложенных selectinload (load=selectinload(Foo.bar).selectinload(Bar.baz))")
        print("     6. select().columns() вместо select() — только нужные колонки")
        print("     7. limit() + offset() — всегда для пагинации")
        print("     8. exists() вместо count() — быстрее для проверки 'есть ли записи'")

        # ── EXISTS вместо COUNT ─────────────────────────────────
        has_users = (await session.execute(
            select(select(User).exists())
        )).scalar()
        print(f"\n  EXISTS (быстро): {has_users}")

        # ── ONLY needed columns ────────────────────────────────
        stmt = select(User.name, User.email).limit(5)
        result = await session.execute(stmt)
        rows = result.all()
        print(f"  только name+email: {rows[:3]}")


# ══════════════════════════════════════════════════════════════════
# 9. RAW SQL (когда ORM не хватает)
# ══════════════════════════════════════════════════════════════════

async def demo_raw_sql() -> None:
    async with async_session() as session:

        # ── Window functions (ранжирование) ────────────────────
        result = await session.execute(text("""
            SELECT
                user_name,
                total,
                RANK() OVER (ORDER BY total DESC) as rank
            FROM (
                SELECT
                    u.name as user_name,
                    SUM(oi.quantity * oi.unit_price) as total
                FROM users u
                JOIN orders o ON u.id = o.user_id
                JOIN order_items oi ON o.id = oi.order_id
                GROUP BY u.name
            )
            ORDER BY rank
        """))
        rows = result.all()
        print(" .window functions (ранжирование):")
        for name, total, rank in rows:
            print(f"    #{rank} {name}: {total:.2f} руб.")

        # ── CTE (Common Table Expression) ──────────────────────
        result = await session.execute(text("""
            WITH category_stats AS (
                SELECT
                    c.name as category,
                    SUM(oi.quantity * oi.unit_price) as revenue,
                    COUNT(DISTINCT o.id) as orders_count
                FROM categories c
                JOIN products p ON c.id = p.category_id
                JOIN order_items oi ON p.id = oi.product_id
                JOIN orders o ON oi.order_id = o.id
                GROUP BY c.name
            )
            SELECT * FROM category_stats
            WHERE revenue > 0
            ORDER BY revenue DESC
        """))
        rows = result.all()
        print(f"\n  CTE (статистика по категориям):")
        for cat, revenue, orders in rows:
            print(f"    {cat}: {revenue:.2f} руб. ({orders} заказов)")


# ══════════════════════════════════════════════════════════════════
# 10. SEED ДАННЫХ
# ══════════════════════════════════════════════════════════════════

async def seed_data() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Категории
        categories = [
            Category(name="Электроника", description="Телефоны, ноутбуки"),
            Category(name="Одежда", description="Футболки, куртки"),
            Category(name="Книги", description="Программирование, фантастика"),
            Category(name="Дом", description="Мебель, декор"),
        ]
        session.add_all(categories)
        await session.flush()

        # Товары
        products = [
            Product(name="iPhone 15", price=89990, stock=50, category_id=1),
            Product(name="MacBook Pro", price=199990, stock=20, category_id=1),
            Product(name="AirPods", price=12990, stock=100, category_id=1),
            Product(name="Футболка Python", price=1990, stock=200, category_id=2),
            Product(name="Куртка зимняя", price=7990, stock=30, category_id=2),
            Product(name="Fluent Python", price=2490, stock=15, category_id=3),
            Product(name="Python Cookbook", price=1890, stock=25, category_id=3),
            Product(name="Django for Professionals", price=2990, stock=10, category_id=3),
            Product(name="Стул офисный", price=14990, stock=5, category_id=4),
            Product(name="Стол письменный", price=24990, stock=3, category_id=4),
        ]
        session.add_all(products)
        await session.flush()

        # Пользователи
        users = [
            User(name="Алиса", email="alice@mail.com", city="Москва"),
            User(name="Борис", email="boris@mail.com", city="Санкт-Петербург"),
            User(name="Вика", email="vika@mail.com", city="Москва"),
            User(name="Глеб", email="gleb@mail.com", city="Казань"),
            User(name="Даша", email="dasha@mail.com", city="Санкт-Петербург"),
        ]
        session.add_all(users)
        await session.flush()

        # Заказы
        orders_data = [
            (1, "delivered", [(1, 1), (3, 2)]),
            (1, "delivered", [(6, 1), (7, 1)]),
            (2, "shipped", [(2, 1)]),
            (2, "pending", [(4, 3), (5, 1)]),
            (3, "delivered", [(3, 1), (8, 2)]),
            (3, "shipped", [(9, 1)]),
            (4, "delivered", [(10, 1), (4, 5)]),
            (5, "pending", [(1, 1), (2, 1)]),
        ]
        for user_id, status, items in orders_data:
            order = Order(user_id=user_id, status=status)
            session.add(order)
            await session.flush()
            for prod_id, qty in items:
                product = products[prod_id - 1]
                session.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.price,
                ))

        await session.commit()
        print(f"[seed] создано: {len(categories)} категорий, {len(products)} товаров, "
              f"{len(users)} пользователей, {len(orders_data)} заказов")


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════

async def main() -> None:
    await seed_data()

    print("\n" + "=" * 55)
    print("1. Фильтры: where, in, like, between, order_by")
    print("=" * 55)
    await demo_filters()

    print("\n" + "=" * 55)
    print("2. JOIN'ы: inner, left, многоколенный")
    print("=" * 55)
    await demo_joins()

    print("\n" + "=" * 55)
    print("3. Загрузка связей: selectinload vs joinedload vs lazyload")
    print("=" * 55)
    await demo_eager_loading()

    print("\n" + "=" * 55)
    print("4. Агрегации: count, sum, avg, group by, having, subquery")
    print("=" * 55)
    await demo_aggregations()

    print("\n" + "=" * 55)
    print("5. Оптимизация: N+1, selectinload, exists, columns")
    print("=" * 55)
    await demo_optimization()

    print("\n" + "=" * 55)
    print("6. Raw SQL: window functions, CTE")
    print("=" * 55)
    await demo_raw_sql()

    # Уборка
    await engine.dispose()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n[db] {DB_PATH} удалён")


if __name__ == "__main__":
    asyncio.run(main())
