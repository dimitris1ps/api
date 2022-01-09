from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from sqlmodel import Session, select
from typing import Optional, List

from models import Ratings, Tokens, Statistics
from database import engine

import pandas as pd
from datetime import datetime

import os

BASE_DIR = os.path.dirname(os.path.realpath("__file__"))
EARTH_CRED = "earth7eeb1af8861c4bb29c50bdb4815d5381"
EARTH_USER = 'Earthmark'
COMPANIES_THRESHOLD = 20

app=FastAPI(title="Earthmark API")

session=Session(bind=engine)

@app.get('/rating', response_model=list,
         status_code=status.HTTP_200_OK)
def get_ratings(user: str, token: Optional[str] = None, companies: Optional[str] = 'all'):

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

@app.get('/statistics', response_class=HTMLResponse,
         status_code=status.HTTP_200_OK)
def get_stats(user: str, token: str, companies: Optional[str] = None):
    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Username and or token does not match. Please contact the admin')
    else:
        with Session(engine) as sess:
            results = [el for el in session.execute("Select * from Statistics")]
        df = pd.DataFrame(results, columns = ['id', 'client', 'api_calls', 'company_calls', 'report_date', 'report_month'])
        return df.to_html(index=False)


@app.get('/statistics/report', response_class=FileResponse,
         status_code=status.HTTP_200_OK)
def get_stats(user: str, token: str, companies: Optional[str] = None):
    if not((user.lower() == EARTH_USER.lower()) & (token == EARTH_CRED)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Username and or token does not match. Please contact the admin')
    else:
        with Session(engine) as sess:
            results = [el for el in session.execute("Select * from Statistics")]
        df = pd.DataFrame(results, columns = ['id', 'client', 'api_calls', 'company_calls', 'report_date', 'report_month'])
        df.to_csv(BASE_DIR+'\\report.csv')
        return BASE_DIR+'\\report.csv'











# @app.post('/books', response_model=Book,
#           status_code=status.HTTP_201_CREATED)
# async def create_a_book(book:Book):
#     new_book = Book(title=book.title, description=book.description)

#     session.add(new_book)

#     session.commit()

#     return new_book
    
    

# @app.get('/book/{book_id}', response_model=Book)
# async def get_a_book(book_id:int):
#     statement = select(Book).where(Book.id==book_id)

#     result = session.exec(statement).first()

#     if result == None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#     return result

    


# @app.put('/book/{book_id}', response_model=Book)
# async def update_a_book(book_id:int,book:Book):
#     statement = select(Book).where(Book.id==book_id)

#     result = session.exec(statement).first()

#     result.title = book.title
#     result.description = book.description

#     session.commit()

#     return result


    

# @app.delete('/book/{book_id}', status_code=status.HTTP_204_NO_CONTENT)
# async def delete_a_book(book_id:int):
#     statement = select(Book).where(Book.id==book_id)

#     result = session.exec(statement).one_or_none()

#     if result == None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Resource Not Found")

#     session.delete(result)

#     return result
