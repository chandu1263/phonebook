from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
from validation import validate_email, validate_phonenumber

models.Base.metadata.create_all(bind=engine)

phonebook = FastAPI()
ADMIN_TOKEN = "123456"

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
        raise HTTPException(status_code=409, detail="Email already registered")
    db_user = crud.get_user_by_phonenumber(db, phonenumber=user.phonenumber)
    if db_user:
        raise HTTPException(status_code=409, detail="Phone Number already registered")
    return crud.create_user(db=db, user=user)


@phonebook.get("/users/{param}/")
def get_user_by_param(param: str, token: str, db: Session = Depends(get_db)):
    """[Returns a user if exists with parameter as email or Phone number]

    Args:
        param (str): [email or phone number]
        token (Str): [token for authorization]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [404, User not found]
        HTTPException: [400, Invalid Parameter, Please use a valid email or phone number]
        HTTPException: [401, Unauthorized action]

    Returns:
        [user]: [returns name, email, phonenumber if user with requested parameter existed]
    """
    
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            return JSONResponse(status_code=200, content={"mail": db_user.email,"phonenumber": db_user.phonenumber}) 
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            return JSONResponse(status_code=200, content={"mail": db_user.email,"phonenumber": db_user.phonenumber}) 
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.get('/premiumUser/getUser/{param}')
def get_user(param: str, premium_user_param: str, premium_user_token, db: Session = Depends(get_db)):
    """[get user for premium user]

    Args:
        param (str): [email or phone number of requested user]
        premium_user_param (str): [email or phone number of premium user]
        premium_user_token ([type]): [premium user token]
        db (Session, optional): [description]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [404, User not found]
        HTTPException: [404, Premium user not found]
        HTTPException: [400, Invalid Parameter, Please use a valid email or phone number]
        HTTPException: [400, Invalid Parameter, Please use a valid email or phone number for premium user]
        HTTPException: [401, Unauthorized action, only premium users allowed]

    Returns:
        [user]: [returns user name, user email, user phone number]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    if (not validate_email(premium_user_param)) and (not validate_phonenumber(premium_user_param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid premium user email or premium user phone number")
    db_user = crud.get_user_by_email(db=db, email=premium_user_param)
    if db_user is not None:
        if db_user.premium == False:
            raise HTTPException(status_code=401, detail="Unauthorized access, only premium users allowed")
        if db_user.token == premium_user_token:
            requested_user = crud.get_user_by_email(db=db, email=param)
            if requested_user is not None:
                return JSONResponse(status_code=200, 
                                    content={"name": requested_user.name, 
                                             "mail": requested_user.email, 
                                             "phonenumber": requested_user.phonenumber})
            requested_user = crud.get_user_by_phonenumber(db=db, email=param)
            if requested_user is not None:
                return JSONResponse(status_code=200, 
                                    content={"name": requested_user.name, 
                                             "mail": requested_user.email, 
                                             "phonenumber": requested_user.phonenumber})
            raise HTTPException(status_code=404, detail="No user not found by given parameter")
        else:
            raise HTTPException(status_code=401, detail="Invalid token for the premium user")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=premium_user_param)
    if db_user is not None:
        if db_user.premium == False:
            raise HTTPException(status_code=401, detail="Unauthorized access, only premium users allowed")
        if db_user.token == premium_user_token:
            requested_user = crud.get_user_by_email(db=db, email=param)
            if requested_user is not None:
                return JSONResponse(status_code=200, 
                                    content={"name": requested_user.name, 
                                             "mail": requested_user.email, 
                                             "phonenumber": requested_user.phonenumber})
            requested_user = crud.get_user_by_phonenumber(db=db, email=param)
            if requested_user is not None:
                return JSONResponse(status_code=200, 
                                    content={"name": requested_user.name, 
                                             "mail": requested_user.email, 
                                             "phonenumber": requested_user.phonenumber})
            raise HTTPException(status_code=404, detail="No user not found by given parameter")
        else:
            raise HTTPException(status_code=401, detail="Invalid token for the premium user")
    raise HTTPException(status_code=404, detail="No premium user not found by given parameter")

@phonebook.post("/users/{param}/addContact/", response_model=schemas.Contact)
def create_contact_for_user(param: str, token: str, contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    """[creates a contact for the user if token validates with the user]

    Args:
        param (str): [email or phone number]
        token (str): [authorization token]
        contact (schemas.ContactCreate): [contact (name, email, phonenumber)]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

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
            if(crud.contact_check(db=db, user_id=db_user.id, contact_mail=contact.email, contact_phonenumber=contact.phonenumber)):
                raise HTTPException(status_code=409, detail="a contact already exists with provided mail and phone number") 
            return crud.create_user_contact(db=db, contact=contact, user_id=db_user.id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
        
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            if(crud.contact_check(db=db, user_id=db_user.id, contact_mail=contact.email, contact_phonenumber=contact.phonenumber)):
                raise HTTPException(status_code=409, detail="a contact already exists with provided mail and phone number")
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
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

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


@phonebook.put("/users/{param}/updateUserEmail/", response_model=schemas.User)
def update_user_email(param: str, token: str, update_param: str, db: Session = Depends(get_db)):
    """[update user email]

    Args:
        param (str): [email or phonenumber]
        token (str): [authorization token]
        update_param (str): [new to be update email]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid to be updated email]
        HTTPException: [400, invlaid email or phonenumber]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found with given param]
        HTTPException: [description]

    Returns:
        [user]: [updated user details]
    """
    if (update_param is None) or update_param == "":
        raise HTTPException(status_code=204, detail="update param has no content")
    if not validate_email(update_param):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please provide a valid new email")
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.update_user_email(db=db, user_id=db_user.id, mail=update_param)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.update_user_email(db=db, user_id=db_user.id, mail=update_param)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.put("/users/{param}/updateUserPhonenumber/", response_model=schemas.User)
def update_user_phonenumber(param: str, token: str, update_param: str, db: Session = Depends(get_db)):
    """[update user phone number]

    Args:
        param (str): [email or phonenumber]
        token (str): [authorization token]
        update_param (str): [new to be update phone number]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid to be updated phone number]
        HTTPException: [400, invlaid email or phonenumber]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found with given param]
        HTTPException: [description]

    Returns:
        [user]: [updated user details]
    """
    if (update_param is None) or update_param == "":
        raise HTTPException(status_code=204, detail="update param has no content") 
    if not validate_phonenumber(update_param):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please provide a valid new phone number")
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.update_user_phonenumber(db=db, user_id=db_user.id, phone_number=update_param)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            return crud.update_user_phonenumber(db=db, user_id=db_user.id, phone_number=update_param)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")
    
@phonebook.delete("/users/{param}/deleteUser/")
def delete_user(param: str, token: str, db: Session = Depends(get_db)):
    """[delete user]

    Args:
        param (str): [email or phone number]
        token (str): [authorization token]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid mail or phone number]
        HTTPException: [405, method not allowed]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found]

    Returns:
        [response]: [json message]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            if crud.delete_user(db=db, user_id=db_user.id):
                return JSONResponse(status_code=200, content={"message" : "User successfully deleted"})
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            if crud.delete_user(db=db, user_id=db_user.id):
                return JSONResponse(status_code=200, content={"message" : "User successfully deleted"})
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.put("/users/{param}/updateContactEmail")
def update_user_contact_email(param: str, email: str, newmail: str, token: str, db: Session = Depends(get_db)):
    """[Update email of a contact for a user]

    Args:
        param (str): [email or phonenumber to identify user]
        email (str): [email of the contact that need to be updated]
        newmail (str): [new email]
        token (str): [authorization token]
        db (Session, optional): [database dependancy]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid mail or phone number]
        HTTPException: [405, method not allowed]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found]

    Returns:
        [contact]: [updated contact]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    if (not validate_email(email)) or (not validate_email(newmail)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please provide a valid email")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                return crud.update_contact_email(db=db, user_id=db_user.id, email=email, mail=newmail)
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                return crud.update_contact_email(db=db, user_id=db_user.id, email=email, mail=newmail)
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.put("/users/{param}/updateContactPhonenumber")
def update_user_contact_phonenumber(param: str, phonenumber: str, newphonenumber: str, token: str, db: Session = Depends(get_db)):
    """[Update phonenumber of a contact for a user]

    Args:
        param (str): [email or phonenumber to identify user]
        phonenumber (str): [phonenumber of the contact that need to be updated]
        newphonenumber (str): [new phonenumber]
        token (str): [authorization token]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid mail or phone number]
        HTTPException: [405, method not allowed]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found]

    Returns:
        [contact]: [updated contact]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please use a valid email or phone number")
    if (not validate_phonenumber(phonenumber)) or (not validate_phonenumber(newphonenumber)):
        raise HTTPException(status_code=400, detail="Invalid Parameter, Please provide a phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                return crud.update_contact_phonenumber(db=db, user_id=db_user.id, phonenumber=phonebook, newphonenumber=newphonenumber)
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                return crud.update_contact_phonenumber(db=db, user_id=db_user.id, phonenumber=phonebook, newphonenumber=newphonenumber)
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.delete("/users/{param}/deleteUserContact")
def delete_user_contact(param: str, token: str, contact_param: str, db: Session = Depends(get_db)):
    """[delete contact of a user]

    Args:
        param (str): [email or phone number of user]
        token (str): [authorization token]
        contact_param (str): [email or phone number of contact]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid mail or phone number]
        HTTPException: [405, method not allowed]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found]
        HTTPException: [405, No such contact exists]

    Returns:
        [JSONResponse]: [200, Contact successfully deleted]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="param: Invalid Parameter, Please use a valid email or phone number")
    if (not validate_email(contact_param)) and (not validate_phonenumber(contact_param)):
        raise HTTPException(status_code=400, detail="contact_param: Invalid Parameter, Please use a valid email or phone number")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                if crud.delete_contact(db=db, user_id=db_user.id, contact_param=contact_param):
                    return JSONResponse(status_code=200, content={"message" : "Contact successfully deleted"})
                else:
                    raise HTTPException(status_code=405, detail="No such contact exists")
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        if db_user.token == token:
            try:
                if crud.delete_contact(db=db, user_id=db_user.id, contact_param=contact_param):
                    return JSONResponse(status_code=200, content={"message" : "Contact successfully deleted"})
                else:
                    raise HTTPException(status_code=405, detail="No such contact exists")
            except:
                raise HTTPException(status_code=405, detail="Method not allowed")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized action, please provide valid token")
    raise HTTPException(status_code=404, detail="User not found")


@phonebook.post("/admin/{param}/premiumUser")
def make_premium_user(param: str, admin_token: str, db: Session = Depends(get_db)):
    """[activate a user's premium access]

    Args:
        param (str): [email or phone number of the user]
        admin_token (str): [admin token]
        db (Session, optional): [database dependency]. Defaults to Depends(get_db).

    Raises:
        HTTPException: [400, invalid mail or phone number]
        HTTPException: [405, method not allowed]
        HTTPException: [401, unauthorized action]
        HTTPException: [404, user not found]

    Returns:
        [JSONResponse]: [200, Successfully activated user's premium access]
    """
    if (not validate_email(param)) and (not validate_phonenumber(param)):
        raise HTTPException(status_code=400, detail="param: Invalid Parameter, Please use a valid email or phone number")
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access, please provide valid admin token")
    db_user = crud.get_user_by_email(db=db, email=param)
    if db_user is not None:
        try:
            crud.update_user_premium_status(db=db, user_id=db_user.id)
            return JSONResponse(status_code=200, content={"message" : "successfully updated the user premium status"})
        except:
            raise HTTPException(status_code=405, detail="Method not allowed")
    db_user = crud.get_user_by_phonenumber(db=db, phonenumber=param)
    if db_user is not None:
        try:
            crud.update_user_premium_status(db=db, user_id=db_user.id)
            return JSONResponse(status_code=200, content={"message" : "successfully updated the user premium status"})
        except:
            raise HTTPException(status_code=405, detail="Method not allowed")
    if db_user is not None:
        return JSONResponse(status_code=200, content={"successfully updated the user premium status"})
    raise HTTPException(status_code=404, detail="User not found")
    