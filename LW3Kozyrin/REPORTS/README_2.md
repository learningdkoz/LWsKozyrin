<div style="
  font-family: 'Times New Roman', Times, serif;
  font-size: 14pt;
  line-height: 1.5;
">
<p align="center">
Министерство науки и высшего образования Российской Федерации  
Федеральное государственное автономное образовательное учреждение  
высшего образования  
</p>

<p align="center">
<b>«Уральский федеральный университет<br>
имени первого Президента России Б.Н. Ельцина»</b>
</p>

<p align="center">
Институт радиоэлектроники и информационных технологий – РтФ  
<br>
ШПиАО «Прикладной анализ данных»
</p>

<br>
<br>
<br>

<h2 align="center">ОТЧЕТ</h2>

<p align="center">
по лабораторной работе №2  
</p>

<p align="center">
<b>«Работа с SQLAlchemy и alembic»</b>
</p>

<br>
<br>
<br>

<p align="center">
Преподаватель: Кузьмин Денис Иванович  
</p>

<p align="center">
Обучающийся группы РИМ–150950  
<br>
Козырин Дмитрий Алексеевич
</p>

<br>
<br>
<br>
<br>

<p align="center">
Екатеринбург  
<br>
2025
</p>





---
### Цель работы

Освоить принципы работы с библиотеками SQLAlchemy и Alembic для создания и управления реляционными базами данных на Python, изучить механизмы миграции базы данных 

### Ход работы

1. Инициализация нового проекта со всеми необходимыми зависимостями

<img width="1543" height="460" alt="image" src="https://github.com/user-attachments/assets/b03ae732-add8-4fd6-937b-26910b9dc762" />

2. Инициализация миграций командой

```bash
alembic init migrations
```

3. Вписываем строку подключения и инициализируем Base

```python
target_metadata = Base.metadata
```

<img width="1364" height="363" alt="image" src="https://github.com/user-attachments/assets/43bf228c-6859-45d4-b5bb-af118ef0de41" />

4. Примениям миграцию

```bach
alembic revision --autogenerate и alembic upgrade head
```

<img width="1281" height="286" alt="image" src="https://github.com/user-attachments/assets/37fc2811-2862-41cc-9a02-f908955319e8" />

5. Инициализируем entity

```python
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)  # Новое поле
    addresses = relationship("Address", back_populates="user")


class Address(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="addresses")


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    address_id = Column(Integer, ForeignKey('addresses.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    user = relationship("User")
    address = relationship("Address")
    product = relationship("Product")
```

6. Подключаем движок и заполняем БД тестовыми данными

6.1. До этого обновили модель пользователей, добавив поле описания и написали Entities Product/Order

```python
engine = create_engine('postgresql://postgres:viking676@localhost/LW2Kozyrin')
Session = sessionmaker(bind=engine)
session = Session()


from models import User, Address, Order, Product

for i in range(1, 6):
    user = User(name=f'User number {i}')
    address = Address(email=f'user{i}@test.com', user=user)
    session.add(user)
    session.add(address)

session.commit()

from sqlalchemy.orm import selectinload

users = session.query(User).options(selectinload(User.addresses)).all()

for user in users:
    print(f"User: {user.name}")
    for address in user.addresses:
        print(f"  Address: {address.email}")


for i in range(1, 6):
    product = Product(name=f'Product number {i}', price=123 * i)
    session.add(product)

users = session.query(User).all()
addresses = session.query(Address).all()
products = session.query(Product).all()

for i in range(5):
    order = Order(
        user_id=users[i].id,
        address_id=addresses[i].id,
        product_id=products[i].id
    )
    session.add(order)

session.commit()
session.close()
``` 

### Итоговая структура данных

<img width="862" height="700" alt="image" src="https://github.com/user-attachments/assets/3c64cd5e-83f9-4634-9563-208929015c77" />


### Ответы на вопросы

1. Какие есть подходы маппинга в SQLAlchemy? Когда следует использовать каждый подход?.

SQLAlchemy предлагает два подхода к маппингу: декларативный и императивный (классический). Декларативный подход, использующий базовый класс `declarative_base()`, является стандартным и рекомендуется для новых проектов, так как он интуитивно понятен и объединяет определение таблицы и класса модели. Императивный подход, при котором таблица и класс определяются отдельно, а затем связываются с помощью `mapper()`, полезен для более сложных сценариев, например, при интеграции с существующими схемами базы данных или системами, где требуется явный контроль над маппингом.

2. Как Alembic отслеживает текущую версию базы данных?

Alembic отслеживает текущую версию базы данных через таблицу `alembic_version`, которая автоматически создается в целевой базе данных. Эта таблица содержит единственную запись с идентификатором последней примененной ревизии миграции, что позволяет Alembic определять, какие миграции уже применены, а какие - нет.

3. Какие типы связей между таблицами вы реализовали в данной работе?.

В рамках данной работы были реализованы связи между таблицами двух типов: связь "один-ко-многим" (например, между пользователями и их адресами) и связь "многие-ко-многим" (например, между заказами и продуктами через промежуточную таблицу ассоциации).

4. Что такое миграция базы данных и почему она важна?

Миграция базы данных — это управляемое изменение ее схемы, которое записывается в виде версионируемого скрипта. Важность миграций заключается в том, что они позволяют систематически применять и откатывать изменения схемы, обеспечивая согласованность структуры базы данных между различными окружениями (разработка, тестирование, продакшен) и упрощая совместную работу над проектом.

5. Как обрабатываются отношения многие-ко-многим в SQLAlchemy?

Для обработки отношений "многие-ко-многим" в SQLAlchemy создается ассоциативная таблица, содержащая внешние ключи, ссылающиеся на первичные ключи связываемых таблиц. Затем в моделях классов с помощью конструкции `relationship` и параметра `secondary`, указывающего на эту ассоциативную таблицу, определяется связь, позволяя удобно работать с связанными объектами.

6. Каков порядок действий при возникновении конфликта версий в Alembic?  

При возникновении конфликта версий в Alembic рекомендуется следующий порядок действий: сначала анализируется история миграций и текущее состояние с помощью команд `alembic history` и `alembic current`. Затем, чтобы разрешить конфликт, можно либо откатить базу до общей версии с помощью `alembic downgrade` и заново применить миграции до актуальной версии (`alembic upgrade head`), либо создать новую ревизию слияния командой `alembic merge`, которая объединит расходящиеся ветки изменений. Выбор способа зависит от конкретной ситуации и предпочтений команды.


</div>
