from sqlmodel import SQLModel, Session
from models import Ratings, Tokens
from database import engine

import pandas as pd
from datetime import datetime
from uuid import uuid4

print("CREATE DATABASE...")

SQLModel.metadata.create_all(engine)

## Initialize data in db


# Ratings Dummy data
# dummy data

company = ['Parcel2Go', 'ASOS', 'Coinbase', 'TripAdvisor', 'AliExpress', 
           'SHEIN', 'Boots', 'Freshly Comsetics ES', 'Ticketmaster', 
           'Iceland', 'B & Q', 'Headspace', 'The Works', 'Nike', 'Adobe', 
           'Aliexpress BR', 'Eneba', 'Marks and Spencer', 'Superdrug']

business_info_score = [10, 9, 0, 0, 4, 0, 9, 3, 5, 1, 5, 0, 10, 0, 6, 4, 6, 3, 3]
environment_score = [2, 3, 8, 0, 4, 0, 9, 6, 4, 6, 3, 7, 1, 6, 0, 4, 6, 9, 1]

governance_transparency_score = [9, 7, 0, 4, 3, 7, 7, 3, 3, 0, 7, 6, 6, 7, 10, 1, 6, 7, 3]
earthmark_rating = [3, 0, 9, 3, 0, 3, 0, 4, 5, 8, 8, 1, 6, 4, 5, 9, 10, 6, 7]

df = pd.DataFrame({'company':company, 'business_info_score':business_info_score, 'environment_score':environment_score,
             'governance_transparency_score':governance_transparency_score, 'earthmark_rating':earthmark_rating})

df['create_date'] = str(datetime.now())


# Tokens data
clients = ['abc', 'xyz', 'anastasis', 'omega']
package = ['small', 'medium', 'large', 'xlarge']
emails = ['info@abc.gr', 'contact@xyz.com', 'me@anastasis.gr', 'alpha@omega.com']
contacts = ['mike', None, 'Anna', None]

############## Populate db

## Ratings
with Session(engine) as session:
    for dict_elemnt in df.to_dict('records'):
        session.add(Ratings(company=dict_elemnt['company'], 
                            business_info_score=dict_elemnt['business_info_score'], 
                            environment_score=dict_elemnt['environment_score'], 
                            governance_transparency_score=dict_elemnt['governance_transparency_score'], 
                            earthmark_rating=dict_elemnt['earthmark_rating'],
                            create_date=dict_elemnt['create_date']
                           ))
    session.commit() 

## Tokens
with Session(engine) as session:
	for cl, pa, em, nm in zip(clients, package, emails, contacts):
		session.add(Tokens(client=cl, 
                           token=uuid4().hex, 
                           package=pa,
                           active=True,
                           email=em,
                           contact_person=nm,
                           create_date=str(datetime.now()), 
                           updated_date=str(datetime.now()) 
                          ))
	session.commit()