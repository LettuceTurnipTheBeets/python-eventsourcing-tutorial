"""
This code accompanies part 3 of my tutorial on the Python
eventsourcing library, which you can read here: 

https://www.eventsorcery.com/python-eventsourcing-tutorial-part-3-application-layer/

2020 (c) Zarek Rahman
zarek@techlawyer.co.uk

Licensed under GNU/GPL3.
"""

import unittest
from uuid import UUID
from decimal import Decimal
from domain_model import Person, Company
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.utils.random import encoded_random_bytes
from app import CompanyApp

class TestCompanyApp(unittest.TestCase):
    
    def setUp(self):
        self.app = CompanyApp(
            uri="sqlite://",
            cipher_key=encoded_random_bytes(num_bytes=32),
            persist_event_type=(Company.Event, Person.Event)
        )
        self.jim_id = self.app.involve_person(
            title="Mr", 
            name="James Holden", 
            address="Earth", 
            date_of_birth = "08/1987"
        )        
        self.naomi_id = self.app.involve_person(
            title="Miss", 
            name="Naomi Nagata", 
            address="The Belt", 
            date_of_birth = "03/1992"
        )
        self.amos_id = self.app.involve_person(
            title="Mr", 
            name="Amos Burton", 
            address="Earth", 
            date_of_birth = "02/1991"
        )        
        self.alex_id = self.app.involve_person(
            title="Mr", 
            name="Alex Kamal", 
            address="Mars", 
            date_of_birth = "08/1985"
        )
        self.company_id = self.app.prepare_new_company(
            name="Rocinante Limited", 
            address="Space", 
            sic_code=27151,
            initial_directors_ids=[self.jim_id, self.naomi_id]
        )        

    def tearDown(self):
        # Close the app when done to remove any persistence policy handlers
        self.app.close()

    def test_application_object(self):
        self.assertIsInstance(self.app, SQLAlchemyApplication)
                
    def test_persons_can_be_involved_at_app_level(self):
        # At the app level, we can only deal with aggregates by id. 
        self.assertIsInstance(self.jim_id, UUID)
        self.assertIsInstance(self.amos_id, UUID)
        self.assertIsInstance(self.naomi_id, UUID)
        self.assertIsInstance(self.alex_id, UUID)
        
        # We can use the app repository to recreate jim from his id.
        jim = self.app.repository[self.jim_id]
        self.assertIsInstance(jim, Person)
        self.assertEqual(jim.name, "James Holden")

    def test_new_company_can_be_prepared_and_directors_appointed(self):
        # Test that we can recreate the company using its unique id
        self.assertIsInstance(self.company_id, UUID)
        company = self.app.repository[self.company_id]
        self.assertIsInstance(company, Company)
        self.assertEqual(company.name, "Rocinante Limited")

        # Test that Jim and Naomi are recorded as directors
        directors = company.get_officers(officer_type="director")
        self.assertEqual(len(directors), 2)
        self.assertIn(self.jim_id, [director.person_id for director in directors])
        self.assertIn(self.naomi_id, [director.person_id for director in directors])

    def test_ordinary_shares_can_be_issued(self):
        nom_val = Decimal("0.0001")

        self.app.issue_ordinary_shares(
            in_company_id=self.company_id,
            to_person_id=self.jim_id, 
            number_of_shares=2500, 
            nominal_value_per_share=nom_val, 
            price_paid_per_share=nom_val
        )
        self.app.issue_ordinary_shares(
            in_company_id=self.company_id,
            to_person_id=self.amos_id, 
            number_of_shares=2500, 
            nominal_value_per_share=nom_val, 
            price_paid_per_share=nom_val
        )
        self.app.issue_ordinary_shares(
            in_company_id=self.company_id,
            to_person_id=self.naomi_id, 
            number_of_shares=2500, 
            nominal_value_per_share=nom_val, 
            price_paid_per_share=nom_val
        )
        self.app.issue_ordinary_shares(
            in_company_id=self.company_id,
            to_person_id=self.alex_id, 
            number_of_shares=2500, 
            nominal_value_per_share=nom_val, 
            price_paid_per_share=nom_val
        )
        company = self.app.repository[self.company_id]
        
        self.assertEqual(len(company.get_shareholdings(share_class_name="ordinary")), 4)
        ord_statement = company.statement["ordinary"]
        self.assertEqual(ord_statement["total_shares_issued"], 10_000)
        self.assertEqual(ord_statement["aggregate_nominal_value"], 1.0000)
        self.assertEqual(ord_statement["total_price_paid"], 1.0000)
        self.assertEqual(ord_statement["aggregate_amount_unpaid"], 0)
    
        # Remember that when shares are issued in a company, the shareholder's details are 
        # entered into the company's register of members. The company must also issue a
        # share certificate to the shareholder which is proof that they hold the shares.

        jim = self.app.repository[self.jim_id]
        company = self.app.repository[self.company_id]
        jim_shares_company_record = company.get_shareholdings(person=jim)
        self.assertEqual(len(jim_shares_company_record), 1)
        jim_shares_person_record = jim.get_shareholdings(company=company)
        self.assertEqual(len(jim_shares_person_record), 1)


if __name__ == "__main__":
    unittest.main(exit=False)
        