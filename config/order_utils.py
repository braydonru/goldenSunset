from datetime import datetime
from routes.deps.db_session import SessionDep
from models.user import User



def date_formater(date:datetime):
    return date.strftime('%Y/%m/%d')

def query_email(id:int,db:SessionDep):
    user= db.get(User,id)
    return user.email
