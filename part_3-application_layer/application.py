from typing import Any
from uuid import uuid4
from domain_model import Person, Company
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication

class CompanyApp(SQLAlchemyApplication):
    persist_event_type = (Company.Event, Person.Event)

    def new_person(self, name: str) -> uuid4:
        person = Person.__create__(name=name)
        person.__save__()
        return person.id

    def new_company(self, name: str) -> uuid4:
        newco = Company.__create__(name=name)
        newco.__save__()
        return newco.id

    def allot_and_issue_ordinary_shares(
        self,
        company_id: uuid4,
        to_id: uuid4,
        number: int,
        nom_val: float
    ) -> None: 
        company = self.repository[company_id]
        # If the ordinary share class does not exist, create it
        if "ordinary" not in company.share_classes:
            company.create_share_class(
                name="ordinary",
                nominal_value=nom_val
            )
        # If it does exist, ensure the given nominal value matches            
        ord_nom_val = company.share_classes["ordinary"].nominal_value
        if ord_nom_val != nom_val:
            raise ValueError(f"Existing ordinary share class with nominal value of {ord_nom_val}")
        # A shareholder is a legal person who holds x number of shares
        new_shareholder = self.repository[to_id]
        # The shares are first allotted within the share class
        company.allot_shares(
            legal_person=new_shareholder,
            share_class=company.share_classes["ordinary"],
            number_of_shares=number
        )
        # Then they are issued
        company.issue_shares(new_shareholder)
        # There should be a corresponding event for the person
        # to record the new shareholding 
        company.__save__()


if __name__ == "__main__":
    app = CompanyApp()

    company_id = app.new_company("Company Ltd")

    jack_id = app.new_person(name="Jack")
    vic_id = app.new_person(name="Vic")
    hood_id = app.new_person(name="Hood")

    print("issuing the command")
    app.allot_and_issue_ordinary_shares(
        company_id=company_id, 
        to_id=jack_id, 
        number=100, 
        nom_val=0.001
    )

    print("recreating company")
    company = app.repository[company_id]

