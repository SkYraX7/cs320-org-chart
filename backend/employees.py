import links
import pymongo
import json
import jwt
import datetime
import dns

# Return a tree of employees with depth tree depth rooted with employee_doc
def employee_tree(db: pymongo.MongoClient, employee_doc: dict, tree_depth: int):
    employee_id = employee_doc["employeeId"]
    company_id = employee_doc["companyId"]
    is_manager = bool(employee_doc["isManager"])
    link_to_manager = links.get("company/{}/employee/{}/manager".format(company_id, employee_id))
    link_to_employees = links.get("company/{}/employee/{}".format(company_id, employee_id))

    employees = None if not is_manager else link_to_employees if tree_depth == 0 else [
        employee_tree(db, employee, tree_depth - 1)
        for employee in db["Employees"].find(
            {"managerId": employee_id, "companyId": company_id}
        )    
    ]

    return {
        "firstName": employee_doc["firstName"],
        "lastName": employee_doc["lastName"],
        "companyName": "TODO",
        "positionTitle": employee_doc["positionTitle"],
        "isManager": is_manager,
        "email": employee_doc["email"],
        "employeeId": employee_doc["employeeId"],
        "companyId": employee_doc["companyId"],
        "startDate": employee_doc["startDate"],
        "manager": link_to_manager,
        "managerId": employee_doc.get("managerId"),
        "employees": employees,
        "actions": { # TODO

        }
    }

def employee_by_id(db: pymongo.MongoClient, company_id: int , employee_id: int, tree_depth: int):
    employee_doc: dict = db["Employees"].find_one(
        {"employeeId": employee_id, "companyId": company_id}
    )
    if employee_doc is None:
        return json.dumps({ "error": "not found"})
    return employee_tree(db, employee_doc, tree_depth)

def employee_manager_by_id(db: pymongo.MongoClient, company_id: int, employee_id: int, levels: int, tree_depth: int):
    employee_doc: dict = db["Employees"].find_one(
        {"employeeId": employee_id, "companyId": company_id}
    )
    managerID = employee_doc.get("managerID")
    employee_doc_2: dict = db["Employees"].find_one(
        {"employeeId": managerID, "companyId": company_id}
    )
    return employee_tree(db, employee_doc_2, tree_depth)


def login(db: pymongo.MongoClient, company_id: int, username: str, password: str):
    pload = {
        'companyId': company_id,
        'username': username,
        'password': password
    }
    employee_found: dict = db["Employees"].find_one(pload)
    if employee_found:
        auth_token =  encode_auth_token(db, company_id, username)
        return auth_token
    else:
        return -1

def encode_auth_token(db: pymongo.MongoClient, company_id: int, username: str):
    """
    Generates the auth_token
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + timedelta(days = 0, hours = 1, seconds = 0),
            'iat': datetime.datetime.utcnow(),
            'cid': company_id,
            'uid': username
        }
        return jwt.encode(payload, app.config.get('SECRET_KEY'), algorithm='HS256')
    except Exception as e:
        return e

def decode_auth_token(db: pymongo.MongoClient, auth_token):
    """
    Decodes the auth token
    """
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'))
        return payload['username']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def add_employee_to_db(db: pymongo.MongoClient, employee_dict: dict):
    #add employee
    #change to take in json
    print("ATTEMPT ADD")
    db["Employees"].insert_one(employee_dict)
    return "success?"

def drop_employee_from_db(db: pymongo.MongoClient, dropped_employee: dict):
    #get all employees under current and set their manager to new manager
    #employees under is a cursor object

    employee_check = db["Employees"].delete_one(dropped_employee)

    employees_under = db["Employees"].find(
        {"managerId" : dropped_employee.get("employeeId"), "companyId" : dropped_employee.get("companyId")}
    )
    # loop through current managers workers and call the edit their manager
    for employee in employees_under:
        db["Employees"].find_one_and_update(employee,
            {'$set': {"managerId" : dropped_employee.get("managerId")}})
    return employee_check


def edit_employee(db: pymongo.MongoClient, employee_Id: str, updated: dict):
    return db["Employees"].replace_one(db["Employees"].find_one({"employeeId": employee_Id}), updated) #return_document=pymongo.ReturnDocument.AFTER)


