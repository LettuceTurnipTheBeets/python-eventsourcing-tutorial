"""
This code accompanies part 3 of my tutorial on the Python
eventsourcing library, which you can read here: 

https://www.eventsorcery.com/python-eventsourcing-tutorial-part-3-application-layer/

2020 (c) Zarek Rahman
zarek@techlawyer.co.uk

Licensed under GNU/GPL3.
"""

from typing import Any, List
from uuid import UUID
from decimal import Decimal
from domain_model import Person, Company
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication

class CompanyApp(SQLAlchemyApplication):

    def involve_person(
        self, 
        title: str, 
        name: str, 
        address: str, 
        date_of_birth: str,
        former_names: list = None
    ) -> UUID:
        person = Person.__create__(
            title=title, 
            name=name, 
            address=address, 
            date_of_birth=date_of_birth,
            former_names=former_names
        )
        person.__save__()
        return person.id

    def prepare_new_company(
        self, 
        name: str, 
        address: str, 
        sic_code: int,
        initial_directors_ids: list,
    ) -> UUID:
        assert isinstance(initial_directors_ids, list), "initial_directors_ids must be provided as a list"
        company = Company.__create__(
          name=name, 
          registered_office=address,
          sic_code=sic_code,
          registered_office_country="England and Wales",
          company_type="Private limited by shares",
          model_articles=True,
          custom_articles=False,
          restricted_articles=False
        )
        
        for director_id in initial_directors_ids:
            assert isinstance(director_id, UUID), "director must be of type UUID"
            director = self.repository[director_id]
            appointment = company.add_officer(person=director, officer_type="director", appointment_date="20-02-2020")
            director.record_appointment(appointment)
            director.__save__()
        company.__save__()
        return company.id
    
    def issue_ordinary_shares(
        self, 
        in_company_id: UUID,
        to_person_id: UUID, 
        number_of_shares: int,
        nominal_value_per_share: Decimal, 
        price_paid_per_share: Decimal
    ) -> None:
        assert isinstance(in_company_id, UUID)
        assert isinstance(to_person_id, UUID)
        company = self.repository[in_company_id]
        person = self.repository[to_person_id]
        shareholding = company.issue_shares(
            person=person, 
            share_class_name="ordinary", 
            number_of_shares=number_of_shares, 
            nominal_value_per_share=nominal_value_per_share, 
            price_paid_per_share=price_paid_per_share,
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        )
        company.__save__()
        person.record_shareholding(shareholding)
        person.__save__()

if __name__ == "__main__":
    # For using the Python shell

    app = CompanyApp(persist_event_type=(Company.Event, Person.Event))

    jim_id = app.involve_person(title="Mr", name="James Holden", address="Earth", date_of_birth = "08/1987")        
    amos_id = app.involve_person(title="Mr", name="Amos Burton", address="Earth", date_of_birth = "02/1991")        
    naomi_id = app.involve_person(title="Miss", name="Naomi Nagata", address="The Belt", date_of_birth = "03/1992")        
    alex_id = app.involve_person(title="Mr", name="Alex Kamal", address="Mars", date_of_birth = "08/1985")        
    company_id = app.prepare_new_company(name="Rocinante Limited", address="Space", sic_code=27151, initial_directors_ids=[jim_id, naomi_id])

    nom_val = Decimal("0.0001")

    app.issue_ordinary_shares(in_company_id=company_id, to_person_id=jim_id, number_of_shares=2500, nominal_value_per_share=nom_val, price_paid_per_share=nom_val)
    app.issue_ordinary_shares(in_company_id=company_id, to_person_id=naomi_id, number_of_shares=2500, nominal_value_per_share=nom_val, price_paid_per_share=nom_val)
    app.issue_ordinary_shares(in_company_id=company_id, to_person_id=amos_id, number_of_shares=2500, nominal_value_per_share=nom_val, price_paid_per_share=nom_val)
    app.issue_ordinary_shares(in_company_id=company_id, to_person_id=alex_id, number_of_shares=2500, nominal_value_per_share=nom_val, price_paid_per_share=nom_val)

    company = app.repository[company_id]

    for event in app.notification_log.get_items(start=0, stop=20):
        print(event, "\n")
