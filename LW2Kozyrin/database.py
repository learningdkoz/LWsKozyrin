from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
