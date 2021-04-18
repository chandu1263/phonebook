from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
from validation import validate_email, validate_phonenumber

models.Base.metadata.create_all(bind=engine)

phonebook = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@phonebook.post("/users/addUser/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """[creates an user with requested parameters if valid]

    Args:
        user (schemas.UserCreate): [user]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400 Bad Request, Invalid email] 
        HTTPException: [400 Bad Request, Invalid Phone number]
        HTTPException: [400 Bad Request, email already registered]
        HTTPException: [400 Bad Request, Phone number already registered]

    Returns:
        [user]: [if user creation is successfull]
    """
    
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email")
    if not validate_phonenumber(user.phonenumber):
        raise HTTPException(status_code=400, detail="Invalid Phone number")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = crud.get_user_by_phonenumber(db, phonenumber=user.phonenumber)
    if db_user:
        raise HTTPException(status_code=400, detail="Phone Number already registered")
    return crud.create_user(db=db, user=user)


@phonebook.get("/users/{param}/", response_model=schemas.User)
def get_user_by_emailid(param: str, db: Session = Depends(get_db)):
    """[Returns a user if exists with parameter as email or Phone number]

    Args:
        param (str): [email or phone number]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [404, User not found]
        HTTPException: [400, Invalid Parameter, Please use a valid email or phone number]

    Returns:
        [user]: [returns name, email, phonenumber if user with requested paramter existed]
    """
    
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        return db_user
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@phonebook.post("/users/{param}/addcontact/", response_model=schemas.Contact)
def create_contact_for_user(param: str, token: str, contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    """[creates a contact for the user if token validates with the user]

    Args:
        param (str): [email or phone number]
        token (str): [authorization token]
        contact (schemas.ContactCreate): [contact (name, email, phonenumber)]
        db (Session, optional): [database dependancy]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, not a valid email or phone number]
        HTTPException: [401, token provided doesn't give access to add the contact to the user]
        HTTPException: [404, user not found]

    Returns:
        [contact]: [returns the contact details]
    """
    
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.create_user_contact(db=db, contact=contact, user_id=db_user.id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.create_user_contact(db=db, contact=contact, user_id=db_user.id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")
    

@phonebook.get("/users/{param}/contacts", response_model=List[schemas.Contact])
def get_contacts_of_user(param: str, token: str, db: Session = Depends(get_db)):
    """[get the contacts of the user with given mail or phone number]

    Args:
        param (str): [mail or phone number]
        token (str): [authorization token]
        db (Session, optional): [database dependancy]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, not a valid email or phone number]
        HTTPException: [401, token provided doesn't give access to add the contact to the user]
        HTTPException: [404, user not found]

    Returns:
        [List[contact]]: [returns list of contacts of the given user]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.get_contacts(db=db, user_id=db_user.id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.get_contacts(db=db, user_id=db_user.id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")
    


if __name__=="__main__":
    uvicorn.run(phonebook, host="0.0.0.0", port=8000)
