from fastapi import FastAPI, status, Query
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from sqlmodel import Session, select
from typing import Optional, List

from models import Ratings, Tokens, Statistics
from database import engine

import pandas as pd
from datetime import datetime
from uuid import uuid4

import os

BASE_DIR = os.path.dirname(os.path.realpath("__file__"))
URL = "http://127.0.0.1"
EARTH_CRED = "earth7eeb1af8861c4bb29c50bdb4815d5381"
EARTH_USER = 'Earthmark'
COMPANIES_THRESHOLD = 20

API_DESCRIPTION = """
The Earthmark API shares business & environment sustainability metrics. 🌍🌱🌳

## The Metrics

You can retrieve company information related to **business score**, **environment score** the **governance transparency score** and an **Earthmark ratings** which is derived from all the previous metrics.

## Info

You will be able to:

* **Retrieve company metrics**

Earthmark is able to:

* **Retrieve company metrics**
* **Create, update, delete access tokens**
* **View report on api usage**

## Contact
"""

tags_metadata = [
    {
        "name": "Ratings",
        "description": """Retrieve company metrics (
                          <code><b><font color='#001f75'>Clients</font></b></code>, 
                          <code><b><font color='#780000'>Earthmark</font></b></code>)
                          """
    },
    {
        "name": "Companies",
        "description": """View the companies for which info exist (
                          <code><b><font color='#001f75'>Clients</font></b></code>, 
                          <code><b><font color='#780000'>Earthmark</font></b></code>)
                          """
    },
    {
        "name": "Report",
        "description": "View or export report on API usage (<code><b><font color='#780000'>Earthmark</font></b></code>)"
    },
    {
        "name": "Tokens",
        "description": "Create, Update, Delete or View access tokens (<code><b><font color='#780000'>Earthmark</font></b></code>)"
    },
]

app=FastAPI(title="Earthmark API", description=API_DESCRIPTION, 
    contact={
        "name": "Anastasis Stamatis",
        "url": "https://www.dataphoria.gr/",
        "email": "anastasis@dataphoria.gr ",
    }, openapi_tags=tags_metadata)

session=Session(bind=engine)

@app.get('/rating', response_model=list, status_code=status.HTTP_200_OK, tags=["Ratings"])
def get_ratings(user: str, token: str, companies: Optional[str] = 'all'):
    """Retrieve company metrics such as business, environment and governance transparency scores 
       as well as the Earthmark rating.<br><br>
       Examples for retrieving **one** company info:<br>
       <a href="http://127.0.0.1:8000/ratings?user=<username>&token=<access_token>&companies=Nike" target="_blank">http://127.0.0.1:8000/ratings?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>&companies=<font color="red">Nike</font></a><br>
       The <i><font color="red">\<username\></font></i> and <i><font color="red">\<access_tokens\></font></i> will be provided to you by **Earthmark**<br>
       <br>Examples for retrieving **more than one** company info:<br>
       <a href="http://127.0.0.1:8000/ratings?user=<username>&token=<access_token>&companies=Nike" target="_blank">http://127.0.0.1:8000/ratings?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>&companies=<font color="red">Nike</font>;<font color="red">Parcel2go</font>;<font color="red">B & Q</font></a><br>
       Seperate each company with a semicolon <b><font color="red">;</font></b><br> Info from up to **50** companies can be retrieved<br>
       <br>Earthmark can also retrieve **all** info:<br>
       <a href="http://127.0.0.1:8000/ratings?user=<username>&token=<access_token>" target="_blank">http://127.0.0.1:8000/ratings?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font></a><br>
       """

    res = [el for el in session.execute(f"Select token, package from Tokens where lower(client) = '{user.lower()}'")]

    companies = ["'"+cmp.strip()+"'" for cmp in companies.lower().split(';') if cmp.strip() != ""]
    num_of_companies = len(companies)
    companies = ",".join(companies)

    # Create or update report
    # exists_ = [el for el in session.execute(f"""Select id from Statistics 
    #                                                   where lower(client) = '{user.lower()}' and 
    #                                                         report_date = '{str(datetime.date(datetime.now()))}'""")]

    flag = 0
    with Session(engine) as sess:
        statement = select(Statistics).where(Statistics.client == user.lower(), 
                                             Statistics.report_date == str(datetime.date(datetime.now())))
        try:
            exists_ = sess.exec(statement).one()
            flag = 1
        except:
            pass


    if flag:
        with Session(engine) as sess:
            exists_.api_calls += 1
            exists_.company_calls += num_of_companies
            sess.add(exists_)
            sess.commit()

    else:
        session.add(Statistics(client=user.lower(), 
                               api_calls=1, 
                               company_calls=num_of_companies, 
                               report_date=str(datetime.date(datetime.now())), 
                               report_month=str(datetime.date(datetime.today().replace(day=1)))))
        session.commit()




    if (num_of_companies > COMPANIES_THRESHOLD):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f'Too many company requests ({num_of_companies}), please limit to 10.')

    if ((len(res) == 0) & (user.lower() != EARTH_USER.lower())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f'Please provide appropreate user name.')

    if len(res):
        if (token == res[0][0]):

            if (res[0][1] in ['small', 'medium']):
                results = [el for el in session.execute(f"""Select company, 
                                                                   earthmark_rating 
                                                                   from Ratings 
                                                                   where lower(company) in ({companies})""")]
            else:
                results = [el for el in session.execute(f"""Select company, 
                                                                  business_info_score, 
                                                                  environment_score,
                                                                  governance_transparency_score,
                                                                  earthmark_rating 
                                                                  from Ratings 
                                                                  where lower(company) in ({companies})""")]


            if (len(results) == 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                    detail='No results returned. Please provide valid company values, semicolon seperated')

            return results

    if (token == EARTH_CRED):
        if (companies == "'all'"):
            results = [el for el in session.execute(f"Select * from Ratings")]
        else:
            results = [el for el in session.execute(f"Select * from Ratings where lower(company) in ({companies})")]
        return results

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
        detail='Username and or token does not match. Please contact the admin')


#################################################################################################################

@app.get('/companies', response_class=HTMLResponse, status_code=status.HTTP_200_OK, tags=["Companies"])
def get_companies(user: str, token: str):
    """See which companies we have sustainability info for.<br><br>
       Example:<br>
       <a href="http://127.0.0.1:8000/companies?user=<username>&token=<access_token>" target="_blank">http://127.0.0.1:8000/companies?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font></a><br>
       The <i><font color="red">\<username\></font></i> and <i><font color="red">\<access_tokens\></font></i> will be provided to you by **Earthmark**<br>
       """
    if ((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        results = [el for el in session.execute("Select company from Ratings")]
        df = pd.DataFrame(results, columns = ['company'])
        return df.to_html(index=False)


    res = [el for el in session.execute(f"""Select client from Tokens 
                                            where lower(client) = '{user.lower()}' and token = '{token}'""")]
    if len(res):
        #TODO: add statistics update

        with Session(engine) as sess:
            statement = select(Statistics).where(Statistics.client == user.lower(), 
                                                 Statistics.report_date == str(datetime.date(datetime.now())))
            try:
                exists_ = sess.exec(statement).one()
                exists_.api_calls += 1
                sess.add(exists_)
                sess.commit()
            except:
                session.add(Statistics(client=user.lower(), 
                                   api_calls=1, 
                                   company_calls=0, 
                                   report_date=str(datetime.date(datetime.now())), 
                                   report_month=str(datetime.date(datetime.today().replace(day=1)))))
                session.commit()            


        results = [el for el in session.execute("Select company from Ratings order by company")]
        df = pd.DataFrame(results, columns = ['company'])
        return df.to_html(index=False)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Username and or token does not match. Please contact the admin')


####################################################################################################################

@app.get('/statistics', response_class=HTMLResponse, status_code=status.HTTP_200_OK, tags=["Report"])
def get_stats(user: str, token: str):
    """View api usage<br><br>
       Example:<br>
       <a href="http://127.0.0.1:8000/statistics?user=<username>&token=<access_token>" target="_blank">http://127.0.0.1:8000/statistics?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font></a><br>
       <br>Can be viewed only from Earthmark.
       """
    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Username and or token does not match. Please contact the admin')
    else:
        with Session(engine) as sess:
            results = [el for el in session.execute("Select * from Statistics")]
        df = pd.DataFrame(results, columns = ['id', 'client', 'api_calls', 'company_calls', 'report_date', 'report_month'])
        return df.to_html(index=False)


@app.get('/statistics/report', response_class=FileResponse, status_code=status.HTTP_200_OK, tags=["Report"])
def get_stats(user: str, token: str):
    """Download report of api usage<br><br>
       Example:<br>
       <a href="http://127.0.0.1:8000/statistics/report?user=<username>&token=<access_token>" target="_blank">http://127.0.0.1:8000/statistics/report?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font></a><br>
       <br>Can be export only from Earthmark.
       """
    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Username and or token does not match. Please contact the admin')
    else:
        with Session(engine) as sess:
            results = [el for el in session.execute("Select * from Statistics")]
        df = pd.DataFrame(results, columns = ['id', 'client', 'api_calls', 'company_calls', 'report_date', 'report_month'])
        df.to_csv(BASE_DIR+'\\report.csv')
        return BASE_DIR+'\\report.csv'


@app.get('/token/create', status_code=status.HTTP_200_OK, response_model=list, tags=["Tokens"])
def create_token(user: str, 
                 token: str, 
                 client: str, 
                 package: str = Query(None, title="Type of package",
                                            description="Possible packages are: small, medium, large and xlarge",
                                            example="package=medium",
                                            regex="^small$|^medium$|^large$|^xlarge$"),
                 email: Optional[str] = None, 
                 contact_person: Optional[str] = None, 
                 delete: bool = False):
    """Create, update or delete access token<br><br>
       Create-Update example:<br>
       <a href="http://127.0.0.1:8000/token/create?user=<username>&token=<access_token>&client=<cleint_name>&package=xlarge&email=info@somedomain.com&contact_person=first last" target="_blank">
       http://127.0.0.1:8000/token/create?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>&client=<font color="red"><client_name></font>&package=<font color="red">xlarge</font>&email=<font color="red">info@somedomain.com</font>&contact_person=<font color="red">first last</font>
       </a><br>
       The <i><font color="red">\<username\></font></i> and <i><font color="red">\<access_tokens\></font></i> are Earthmarks'. The package parameter can be one of the following: small, medium, large or xlarge<br>
       If the client exists then it gets updated with a new token and with have the package specified in the url. If the client does not exist, then a it is created.

       <br><br>
       Delete example:<br>
       <a href="http://127.0.0.1:8000/token/create?user=<username>&token=<access_token>&client=<cleint_name>&delete=true" target="_blank">
       http://127.0.0.1:8000/token/create?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>&client=<font color="red"><client_name></font>&delete=<font color="red">true</font>
       </a><br>
       if the client exists then the user and access token gets deleted.
       """

    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Username and or token does not match. Please contact the admin')

    if delete:
        try:
            with Session(engine) as sess:
                statement = select(Tokens).where(Tokens.client == client)
                res = sess.exec(statement).one()
                sess.delete(res)
                sess.commit()
            return [f'Deleted client {client}']
        except:
            return [f'Client {client} does not exist']

    if not(package):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Please provide package. Examples are: small, medium, large, xlarge')


    flag = 0
    with Session(engine) as sess:
        statement = select(Tokens).where(Tokens.client == client.lower(), Tokens.package == package)
        try:
            exists_ = sess.exec(statement).one()
            flag = 1
        except:
            pass


    if flag:
        with Session(engine) as sess:
            if email:
                exists_.email = email
            if contact_person:
                exists_.contact_person = contact_person

            exists_.token = uuid4().hex
            exists_.package = package
            exists_.create_date = str(datetime.now())
            session.add(exists_)
            session.commit()
    else:
        session.add(Tokens(client = client.lower(), 
                           token = uuid4().hex, 
                           package = package, 
                           email = email,
                           contact_person = contact_person,
                           create_date=str(datetime.now())))
        session.commit()

    res = [el for el in session.execute(f"""Select id, 
                                                   client, 
                                                   token, 
                                                   package, 
                                                   email, 
                                                   contact_person, 
                                                   create_date
                                            from Tokens 
                                            where lower(client) = '{client.lower()}'""")]

    return res


@app.get('/token/view', status_code=status.HTTP_200_OK, response_class=HTMLResponse, tags=["Tokens"])
def view_token(user: str, 
               token: str, 
               client: Optional[str] = None):
    """View client list along with tokens<br><br>
       Example of token for *one* client:<br>
       <a href="http://127.0.0.1:8000/token/view?user=<username>&token=<access_token>&client=<cleint_name>" target="_blank">
       http://127.0.0.1:8000/token/create?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>&client=<font color="red"><client_name></font>
       </a><br>
       The <i><font color="red">\<username\></font></i> and <i><font color="red">\<access_tokens\></font></i> are Earthmarks'.<br>
       It searches for the client specified in the db and returns the info along with the token.

       <br><br>
       Example retrieving *all* tokens:<br>
       <a href="http://127.0.0.1:8000/token/create?user=<username>&token=<access_token>" target="_blank">
       http://127.0.0.1:8000/token/create?user=<font color="red">\<username\></font>&token=<font color="red"><access_token></font>
       </a><br>
       Returns all client info along with their tokens.
       """

    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Username and or token does not match. Please contact the admin')

    if client:
        clients = ["'"+cmp.strip()+"'" for cmp in client.lower().split(';') if cmp.strip() != ""]
        clients = ",".join(clients)

        reslt = [el for el in session.execute(f"""Select * from Tokens 
                                                  where lower(client) in ({clients})""")]
        if (len(reslt) == 0):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Client(s) do not exist in the database.')

    else:
        reslt = [el for el in session.execute("Select * from Tokens order by client")]

    df = pd.DataFrame(reslt, columns = ['id', 'client', 'token', 'package', 'email', 'contact_person', 'create_date'])

    return df.to_html(index=False)

