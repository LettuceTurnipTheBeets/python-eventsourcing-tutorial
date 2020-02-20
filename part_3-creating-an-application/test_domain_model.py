"""
This code accompanies part 3 of my tutorial on the Python
eventsourcing library, which you can read here: 

https://www.eventsorcery.com/python-eventsourcing-tutorial-part-3-application-layer/

2020 (c) Zarek Rahman
zarek@techlawyer.co.uk

Licensed under GNU/GPL3.
"""

import unittest
from datetime import datetime
from decimal import Decimal
from domain_model import Person, Company, Officer, Shareholding, ShareClass

class TestCompany(unittest.TestCase):

    def setUp(self):
        self.company = Company.prepare_new(
          name="Company Limited", 
          registered_office="10 Downing Street, London",
          registered_office_country="England and Wales",
          company_type="Private limited by shares",
          sic_code=18535,
          model_articles=True,
          custom_articles=False,
          restricted_articles=False
        )
        self.joris = Person.involve(
            title="Mr",
            name="Joris Bohnson", 
            address="23 Fleet Street, London, EC4Y 1UJ",
            former_names = ["Chuck Norris", "Bruce Lee"],
            date_of_birth = "05/1962",
        )
        self.tonald = Person.involve(
            title="Mr",
            name="Tonald Drump", 
            address="160 Pennsylvania Ave",
            date_of_birth = "09/2001",
        )
        self.company.issue_shares(
            person=self.joris, 
            share_class_name="ordinary", 
            number_of_shares=235, 
            nominal_value_per_share=Decimal("0.01"), 
            price_paid_per_share=Decimal("0.01"),
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        )
        self.company.issue_shares(
            person=self.tonald, 
            share_class_name="ordinary", 
            number_of_shares=51, 
            nominal_value_per_share=Decimal("0.01"), 
            price_paid_per_share=Decimal("121.00"),
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        )
        self.company.issue_shares(
            person=self.joris, 
            share_class_name="deferred", 
            number_of_shares=925, 
            nominal_value_per_share=Decimal("0.01"), 
            price_paid_per_share=Decimal("0.01"),
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        )
        self.company.issue_shares(
            person=self.joris, 
            share_class_name="preference", 
            number_of_shares=2395, 
            nominal_value_per_share=Decimal("0.01"), 
            price_paid_per_share=Decimal("2.34"),
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        ) 

    def test_person_can_be_involved(self):
        self.assertIsInstance(self.joris.name, str)
        self.assertIsInstance(self.joris.address, str)
        self.assertIsInstance(self.joris.date_of_birth, str)
        self.assertEqual(self.joris.name, "Joris Bohnson")
        self.assertEqual(self.joris.address, "23 Fleet Street, London, EC4Y 1UJ")
        self.assertEqual(len(self.joris.former_names), 2)
        
    def test_new_company_can_be_prepared(self):
        self.assertIsInstance(self.company.name, str)
        self.assertIsInstance(self.company.registered_office, str)
        self.assertIsInstance(self.company.company_type, str)
        self.assertIsInstance(self.company.sic_code, int)
        self.assertIn("Limited" or "Ltd", self.company.name)
        self.assertEqual(self.company.name, "Company Limited")
        self.assertEqual(self.company.registered_office, "10 Downing Street, London")
        self.assertEqual(self.company.registered_office_country, "England and Wales")
        self.assertEqual(self.company.company_type, "Private limited by shares")
        self.assertTrue(0o100 <= self.company.sic_code <= 99999)
        self.assertTrue(self.company.model_articles)
        self.assertFalse(self.company.custom_articles)
        self.assertFalse(self.company.restricted_articles)
        self.assertFalse(self.company.incorporated)
        
    def test_officers(self):
        self.company.add_officer(
            person=self.joris, 
            officer_type="director", 
            appointment_date="11 February 2020",
            occupation = "Chimney Sweep",
        )
        self.company.add_officer(
            person=self.joris, 
            officer_type="secretary", 
            appointment_date="11 February 2020"
        )
        joris_appointments = self.company.get_appointments(self.joris)
        self.assertEqual(len(joris_appointments), 2)
        self.assertIsInstance(joris_appointments[0], Officer)
        self.assertEqual(joris_appointments[0].service_address, self.joris.address)
        self.assertEqual(joris_appointments[0].officer_type, "director")
        self.assertEqual(len(self.company.directors), 1)
        self.assertTrue(self.company.has_sole_director)
        self.assertEqual(self.company.secretary.person_name, self.joris.name)
    
    def test_shares_can_be_issued_and_found(self):    
        all_joris_shares = self.company.get_shareholdings(person=self.joris)
        self.assertEqual(len(all_joris_shares), 3)

        joris_deferred_only = self.company.get_shareholdings(person=self.joris, share_class_name="deferred")
        self.assertEqual(len(joris_deferred_only), 1)
        
        all_ordinary = self.company.get_shareholdings(share_class_name="ordinary")
        self.assertEqual(len(all_ordinary), 2)

        all_shareholdings = self.company.get_shareholdings()
        self.assertEqual(len(all_shareholdings), len(self.company.shareholdings))
        self.assertEqual(all_shareholdings[1].shareholder_id, self.tonald.id)

        one_shareholding = all_joris_shares[0]
        self.assertIsInstance(one_shareholding, Shareholding)
        self.assertEqual(one_shareholding.shareholder_id, self.joris.id)
        self.assertEqual(one_shareholding.number_of_shares, 235)
        self.assertEqual(one_shareholding.share_class_name, "ordinary")
        self.assertEqual(one_shareholding.price_paid_per_share, "0.01")

        share_certificate = one_shareholding.certificate
        self.assertEqual(share_certificate, "Share certificate: Joris Bohnson of 23 Fleet Street, London, EC4Y 1UJ holds 235 ordinary shares of GBP £0.01 each in the capital of Company Limited")

        ordinary = self.company.get_share_class(one_shareholding.share_class_name)
        self.assertIsInstance(ordinary, ShareClass)
        self.assertEqual(ordinary.name, "ordinary")
        self.assertEqual(ordinary.nominal_value_per_share, Decimal("0.01"))
        self.assertEqual(ordinary.total_shareholdings, 2)
        self.assertEqual(ordinary.votes_per_share, 1)
        self.assertTrue(ordinary.entitled_to_dividends)
        self.assertTrue(ordinary.entitled_to_capital)
        self.assertFalse(ordinary.redeemable)

    def test_statement_of_capital_calculations(self):
        ordinary_class = self.company.get_share_class("ordinary")
        self.assertIsInstance(ordinary_class, ShareClass)
        self.assertEqual(ordinary_class.nominal_value_per_share, Decimal("0.01"))
        self.assertEqual(ordinary_class.total_number_of_shares, 286)
        self.assertEqual(ordinary_class.aggregate_nominal_value, Decimal("0.02"))
        self.assertEqual(ordinary_class.aggregate_amount_unpaid, Decimal("0.00"))

        pref_shareholding = self.company.get_shareholdings(share_class_name="preference")[0]
        self.assertIsInstance(pref_shareholding, Shareholding)
        self.assertEqual(pref_shareholding.share_premium, Decimal("2.33"))

        statement = self.company.statement
        self.assertIsInstance(statement, dict)
        self.assertEqual(statement['ordinary']['total_shares_issued'], 286)
        self.assertEqual(statement['ordinary']['aggregate_nominal_value'], Decimal("2.86")), 
        self.assertEqual(statement['ordinary']['total_price_paid'], Decimal("6173.35"))
        self.assertEqual(statement['deferred']['total_shares_issued'], 925)
        self.assertEqual(statement['preference']['total_shares_issued'], 2395)
        
if __name__ == "__main__":
    unittest.main(exit=False)
        
