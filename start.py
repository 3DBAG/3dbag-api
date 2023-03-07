from app import app, db_users, views, logging
from sqlalchemy import exc 

with app.app_context():
    db_users.create_all()
    logging.info("DB created")
    # db_users.drop_all()
    b = views.UserAuth(username="user", password="1234", role=views.Permission.ADMINISTRATOR)
    try :
        db_users.session.add(b)
        db_users.session.commit()
        logging.info("Admin created")
    except exc.IntegrityError:
        logging.warning("Admin exists")