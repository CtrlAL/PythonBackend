"""Метаклассы: классы, экземплярами которых являются другие классы.

В Python всё — объект:
  - число 42 → экземпляр int
  - строка "hi" → экземпляр str
  - класс MyClass → экземпляр type

type — метакласс по умолчанию. Все классы создаются через type().
Метакласс — это "класс для класса". Позволяет перехватить создание класса
и модифицировать его до того, как он станет полноценным типом.

Запуск: python 06_metaclasses.py
"""


# ══════════════════════════════════════════════════════════════════
# 1. type() — порождает классы динамически
# ══════════════════════════════════════════════════════════════════

# type(name, bases, dict) — основной способ создания класса
# Класс, написанный через class — это то же самое, что вызов type()

# Этот класс:
class Hello:
    greeting = "привет"

    def say_hello(self):
        return self.greeting

# Эквивалент через type():
HelloDyn = type("HelloDyn", (), {"greeting": "привет", "say_hello": lambda self: self.greeting})

obj1 = Hello()
obj2 = HelloDyn()

print("1. type() — порождение классов")
print(f"  Hello через class:   {obj1.say_hello()}")
print(f"  HelloDyn через type: {obj2.say_hello()}")
print(f"  type(Hello):         {type(Hello)}")        # <class 'type'>
print(f"  type(Hello) == type: {type(Hello) is type}")  # True


# ══════════════════════════════════════════════════════════════════
# 2. Простейший метакласс: перехват __new__
# ══════════════════════════════════════════════════════════════════

class UpperAttrMeta(type):
    """Метакласс: все атрибуты класса автоматически Becomes UPPERCASE."""

    def __new__(mcs, name, bases, namespace):
        upper_attrs = {}
        for key, value in namespace.items():
            if not key.startswith("_"):
                upper_attrs[key.upper()] = value
            else:
                upper_attrs[key] = value  # приватные — без изменений

        return super().__new__(mcs, name, bases, upper_attrs)


class MyClass(metaclass=UpperAttrMeta):
    greeting = "привет"
    count = 42

    def say_hello(self):
        return f"{self.GREETING}! count={self.COUNT}"


print("\n2. Metaclass: uppercasing атрибутов")
obj = MyClass()
print(f"  obj.GREETING: {obj.GREETING}")
print(f"  obj.COUNT:    {obj.COUNT}")
print(f"  obj.say_hello(): {obj.say_hello()}")
# greeting → GREETING, count → COUNT
# say_hello остаётся (приватный метод)
# Но на самом деле say_hello тоже становится SAY_HELLO — это может быть проблемой


# ══════════════════════════════════════════════════════════════════
# 3. Синглтон через метакласс
# ══════════════════════════════════════════════════════════════════

class SingletonMeta(type):
    """Метакласс: только один экземпляр класса."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    def __init__(self, url: str = "sqlite:///:memory:"):
        self.url = url
        self.connected = True

    def query(self, sql: str) -> str:
        return f"выполняю '{sql}' на {self.url}"


print("\n3. Singleton через метакласс")
db1 = Database("postgresql://localhost/mydb")
db2 = Database("sqlite:///:memory:")  # аргумент игнорируется!

print(f"  db1 is db2:       {db1 is db2}")          # True
print(f"  db1.url:          {db1.url}")               # postgresql://...
print(f"  db2.url:          {db2.url}")               # postgresql://... (тот же!)
print(f"  db1.query('1'):   {db1.query('SELECT 1')}")


# ══════════════════════════════════════════════════════════════════
# 4. Валидация атрибутов через метакласс
# ══════════════════════════════════════════════════════════════════

class ValidatedMeta(type):
    """Метакласс: проверяет, что все публичные атрибуты имеют аннотации
    и значения соответствующих типов."""

    def __new__(mcs, name, bases, namespace):
        annotations = namespace.get("__annotations__", {})

        for key in list(namespace.keys()):
            if key.startswith("_"):
                continue
            if key in annotations and key in namespace:
                value = namespace[key]
                expected = annotations[key]
                if not isinstance(value, expected):
                    raise TypeError(
                        f"атрибут '{key}' должен быть {expected.__name__}, "
                        f"а не {type(value).__name__}"
                    )

        return super().__new__(mcs, name, bases, namespace)


class Config(metaclass=ValidatedMeta):
    MAX_RETRIES: int = 3
    TIMEOUT: float = 30.0
    DEBUG: bool = False

    # Раскомментируй — будет TypeError:
    # MAX_RETRIES: int = "три"  # str вместо int


print("\n4. Валидация типов через метакласс")
print(f"  Config.MAX_RETRIES: {Config.MAX_RETRIES} (int)")
print(f"  Config.TIMEOUT:     {Config.TIMEOUT} (float)")
print(f"  Config.DEBUG:       {Config.DEBUG} (bool)")


# ══════════════════════════════════════════════════════════════════
# 5. Регистрация классов (plugin system)
# ══════════════════════════════════════════════════════════════════

_registry = {}


class PluginMeta(type):
    """Метакласс: автоматически регистрирует все классы с атрибутом name."""
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        plugin_name = namespace.get("name")
        if plugin_name:
            _registry[plugin_name] = cls

        return cls


class Plugin(metaclass=PluginMeta):
    """Базовый класс для плагинов."""
    name: str = ""

    def execute(self):
        raise NotImplementedError


class JsonPlugin(metaclass=PluginMeta):
    name = "json"

    def execute(self):
        return "парсю JSON"


class XmlPlugin(metaclass=PluginMeta):
    name = "xml"

    def execute(self):
        return "парсю XML"


class CsvPlugin(metaclass=PluginMeta):
    name = "csv"

    def execute(self):
        return "парсю CSV"


print("\n5. Plugin registration через метакласс")
print(f"  реестр: {list(_registry.keys())}")

for name, plugin_cls in _registry.items():
    instance = plugin_cls()
    print(f"  {name}: {instance.execute()}")


# ══════════════════════════════════════════════════════════════════
# 6. Автоматическое добавление методов
# ══════════════════════════════════════════════════════════════════

class AddReprMeta(type):
    """Метакласс: автоматически добавляет __repr__ на основе аннотаций."""

    def __new__(mcs, name, bases, namespace):
        annotations = namespace.get("__annotations__", {})

        if annotations and "__repr__" not in namespace:
            def make_repr(fields):
                def __repr__(self):
                    parts = [f"{f}={getattr(self, f)!r}" for f in fields]
                    return f"{name}({', '.join(parts)})"
                return __repr__

            namespace["__repr__"] = make_repr(list(annotations.keys()))

        return super().__new__(mcs, name, bases, namespace)


class User(metaclass=AddReprMeta):
    name: str
    age: int
    email: str

    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email


class Product(metaclass=AddReprMeta):
    title: str
    price: float

    def __init__(self, title: str, price: float):
        self.title = title
        self.price = price


print("\n6. Авто-__repr__ через метакласс")
user = User("Алиса", 25, "alice@mail.com")
product = Product("Ноутбук", 999.99)
print(f"  user:    {user}")
print(f"  product: {product}")


# ══════════════════════════════════════════════════════════════════
# 7. __init_subclass__ — современная альтернатива (Python 3.6+)
# ══════════════════════════════════════════════════════════════════

# Когда метаклассы — это overkill, используй __init_subclass__

class Base:
    subclasses_registry = {}

    def __init_subclass__(cls, plugin_name: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if plugin_name:
            Base.subclasses_registry[plugin_name] = cls

    def execute(self):
        raise NotImplementedError


class FastJsonPlugin(Base, plugin_name="fast_json"):
    def execute(self):
        return "быстрый JSON"


class FastXmlPlugin(Base, plugin_name="fast_xml"):
    def execute(self):
        return "быстрый XML"


print("\n7. __init_subclass__ (альтернатива метаклассам)")
print(f"  реестр: {list(Base.subclasses_registry.keys())}")
for name, cls in Base.subclasses_registry.items():
    print(f"  {name}: {cls().execute()}")


# ══════════════════════════════════════════════════════════════════
# 8. Цепочка метаклассов
# ══════════════════════════════════════════════════════════════════

class DebugMeta(type):
    """Логирует создание класса."""
    def __new__(mcs, name, bases, namespace):
        print(f"  [DebugMeta] создаю класс '{name}'")
        return super().__new__(mcs, name, bases, namespace)


class TimingMeta(type):
    """Логирует создание класса (в реальном коде — время)."""
    def __new__(mcs, name, bases, namespace):
        print(f"  [TimingMeta] создаю класс '{name}'")
        return super().__new__(mcs, name, bases, namespace)


class MultiMeta(DebugMeta, TimingMeta):
    """Композиция метаклассов."""
    pass


class Service(metaclass=MultiMeta):
    pass


print("\n8. Цепочка метаклассов")
s = Service()


# ══════════════════════════════════════════════════════════════════
# ИТОГО: когда что использовать
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  КОГДА ЧТО ИСПОЛЬЗОВАТЬ")
print("=" * 60)
print("""
  Метаклассы:
    ✓ Синглтон, валидация, плагины, фреймворки (Django ORM, SQLAlchemy)
    ✓ Когда нужен контроль над СОЗДАНИЕМ класса

  __init_subclass__:
    ✓ Простая регистрация, шаблонный метод
    ✓ Когда нужен контроль над НАСЛЕДОВАНИЕМ

  Декораторы класса:
    ✓ Простые модификации (добавить метод, логирование)
    ✓ Когда не нужен контроль над созданием/наследованием

  Если сомневаешься — начни с декоратора.
  Если не хватает — __init_subclass__.
  Если всё ещё не хватает — метакласс.
""")
