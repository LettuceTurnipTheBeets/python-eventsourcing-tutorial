"""
This code accompanies part 3 of my tutorial on the Python
eventsourcing library, which you can read here: 

https://www.eventsorcery.com/python-eventsourcing-tutorial-part-3-application-layer/

2020 (c) Zarek Rahman
zarek@techlawyer.co.uk

Licensed under GNU/GPL3.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
from eventsourcing.domain.model.aggregate import AggregateRoot

class Person(AggregateRoot):
    # A person has to be identifiable and so should be designed as an entity
    # which has a unique id. It also serves as an aggregate because each
    # person will have certain events related only to them, controlling 
    # entities and objects that relate only to them. 

    __subclassevents__ = True

    class Event(AggregateRoot.Event):
        pass

    # We do not 'create' people within the context of a legal transaction.
    # Instead, we would probably 'involve' one. By using a verb like 'involve' 
    # rather than 'create' we move away from the CRUD based approach to something 
    # that more closely mirrors what happens in the domain.

    @classmethod
    def involve(
        cls,
        title: str, 
        name: str, 
        address: str,
        date_of_birth: str,
        former_names: list = None,
    ) -> Person:
        return cls.__create__(
            title=title, 
            name=name, 
            address=address, 
            date_of_birth=date_of_birth, 
            former_names=former_names,
            event_class=Person.PersonInvolved
        )

    class PersonInvolved(AggregateRoot.Created):
        pass

    def __init__(
        self, 
        title: str, 
        name: str, 
        address: str,
        date_of_birth: str,
        former_names: list,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._name = name
        self._address = address
        self._date_of_birth = date_of_birth
        if former_names:
            assert isinstance(former_names, list)
        self._former_names = former_names or []
        self._shareholdings = []
        self._appointments = []

    def __repr__(self) -> str:
        return f"<Person(name='{self.name}')>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @property
    def date_of_birth(self) -> str:
        return self._date_of_birth

    @property
    def former_names(self) -> str:
        return self._former_names
    
    @property
    def shareholdings(self) -> dict:
        return self._shareholdings
    
    def get_shareholdings(self, company: Company) -> List:
        return [holding for holding in self.shareholdings if holding.company_name == company.name]
    
    def record_shareholding(self, shareholding: Shareholding) -> None:
        assert isinstance(shareholding, Shareholding)
        if shareholding not in self._shareholdings:
            self.__trigger_event__(Person.ShareholdingRecorded, shareholding=shareholding)
    
    class ShareholdingRecorded(Event):
        def mutate(event, person):
            person._shareholdings.append(event.shareholding)

    def record_appointment(self, appointment: Officer) -> None:
        assert isinstance(appointment, Officer)
        if appointment not in self._appointments:
            self.__trigger_event__(Person.AppointmentRecorded, appointment=appointment)
    
    class AppointmentRecorded(Event):
        def mutate(event, person):
            person._appointments.append(event.appointment)

class Company(AggregateRoot):
    # A company is recognised as a legal entity under law. This model focuses
    # only on private companies limited by shares. This model has been developed
    # with a test driven approach, meaning that many features typically found
    # in a company are not modelled until needed by the domain expert. 

    # This version of the model concerns the incorporation of a company
    # and the allotment and issue of shares to its initial subscribers. 
    
    __subclassevents__ = True

    class Event(AggregateRoot.Event):
        pass

    # There is a distinction between preparing a company to be incorporated
    # and actually incorporating it. As lawyers, before we actually incorporate
    # a company for a client, we must first prepare it to be incorporated.
    # By using a verb like 'prepare' rather than 'create' we move away from
    # the CRUD based approach to something that more closely mirrors the domain.

    @classmethod
    def prepare_new(
        cls,
        name: str, 
        registered_office: str, 
        registered_office_country: str = "England and Wales",
        company_type: str = "Private limited by shares",
        sic_code: int = 74990,
        model_articles: bool = True,
        custom_articles: bool = False,
        restricted_articles: bool = False
    ) -> Company:
        return cls.__create__(
            name=name,
            registered_office=registered_office,
            registered_office_country=registered_office_country,
            company_type=company_type,
            sic_code=sic_code,
            model_articles=model_articles,
            custom_articles=custom_articles,
            restricted_articles=restricted_articles
        )

    def __init__(
        self, 
        name: str, 
        registered_office: str, 
        registered_office_country: str,
        company_type: str,
        sic_code: int,
        model_articles: bool,
        custom_articles: bool,
        restricted_articles: bool,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self._name = name
        self._registered_office = registered_office
        self._registered_office_country = registered_office_country
        self._share_classes = {}
        self._company_type = company_type
        self._sic_code = sic_code
        self._model_articles = model_articles
        self._custom_articles = custom_articles
        self._restricted_articles = restricted_articles
        self._officers = []
        self._incorporated = False
    
    def __repr__(self) -> str:
        return f"<Company(name='{self.name}', registered_office='{self.registered_office}', total_shareholdings={self.total_shareholdings}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def registered_office(self) -> str:
        return self._registered_office

    @property
    def registered_office_country(self) -> str:
        return self._registered_office_country

    @property 
    def company_type(self) -> str:
        return self._company_type

    @property
    def sic_code(self) -> str:
        return self._sic_code

    @property
    def model_articles(self) -> bool:
        return self._model_articles

    @property
    def custom_articles(self) -> bool:
        return self._custom_articles

    @property
    def restricted_articles(self) -> bool:
        return self._restricted_articles

    @property
    def incorporated(self) -> bool:
        return self._incorporated

    def add_officer(
        self, 
        person: Person, 
        officer_type: str, 
        appointment_date: str, 
        occupation: str = None
    ) -> None:
        assert isinstance(person, Person)
        assert isinstance(officer_type, str)
        assert isinstance(appointment_date, str)
        if occupation:
            assert isinstance(occupation, str)
        assert person not in self.get_officers(officer_type=officer_type), f"{person.name} is already appointed as {officer_type}"
        officer = Officer(
            company=self,
            person=person,
            officer_type=officer_type,
            appointment_date=appointment_date,
            occupation=occupation,
            service_address=person.address,
        )
        self.__trigger_event__(Company.OfficerAdded, officer=officer)
        return officer

    def get_officers(self, officer_type: str = None):
        if officer_type: 
            return [officer for officer in self._officers if officer.officer_type == officer_type]
        return self._officers

    def get_appointments(self, person: Person):
        return [officer for officer in self._officers if officer.person_id == person.id]

    class OfficerAdded(Event):
        def mutate(event, company):
            company._officers.append(event.officer)

    @property
    def directors(self) -> List:
        return [officer for officer in self._officers if officer.officer_type == "director"]

    @property
    def has_sole_director(self) -> bool:
        if len(self.directors) == 1:
            return True
        else:
            return False

    @property 
    def secretary(self) -> bool:
        sec = [officer for officer in self._officers if officer.officer_type == "secretary"]
        if sec:
            return sec[0]
        return None

    @property
    def share_classes(self) -> str:
        return self._share_classes 

    @property
    def shareholdings(self) -> list:
        return self.get_shareholdings()

    @property
    def total_shareholdings(self) -> int:
        return len(self.get_shareholdings())

    @property
    def statement(self) -> dict:
        results = {}
        for share_class_name, share_class in self._share_classes.items():
            results[share_class_name] = {
                "currency": share_class.currency,
                "total_shares_issued": share_class.total_number_of_shares,
                "nominal_value_per_share": share_class.nominal_value_per_share,
                "aggregate_nominal_value": share_class.nominal_value_per_share * share_class.total_number_of_shares,
                "total_price_paid": share_class.total_price_paid,
                "aggregate_amount_unpaid": share_class.aggregate_amount_unpaid,
                "votes_per_share": share_class.votes_per_share,
                "entitled_to_dividends": share_class.entitled_to_dividends,
                "entitled_to_capital": share_class.entitled_to_capital,
                "redeemable": share_class.redeemable
            }
        return results

    def issue_shares(
        self, 
        person: Person, 
        number_of_shares: int,
        share_class_name: str,
        nominal_value_per_share: Decimal,
        price_paid_per_share: Decimal,
        votes_per_share: int,
        entitled_to_dividends: bool,
        entitled_to_capital: bool,
        redeemable: bool,
        allotted_on: datetime = datetime.now(),
        issued_on: datetime = datetime.now(), 
        currency: str = "GBP",
    ) -> None:

        # In practice, shares are first allotted within a share class before being
        # issued to a person. In most cases, from the perspective of the company,
        # the act of allotment and issue happens together. 

        assert isinstance(person, Person)
        assert isinstance(number_of_shares, int)
        assert isinstance(share_class_name, str)
        assert isinstance(nominal_value_per_share, Decimal)
        assert isinstance(price_paid_per_share, Decimal)
        assert isinstance(votes_per_share, int)
        assert isinstance(entitled_to_dividends, bool)
        assert isinstance(entitled_to_capital, bool)
        assert isinstance(redeemable, bool)

        # A shareholding captures the idea of a person holding a certain number of
        # shares of a certain share class. The share class will have certain
        # rights attached to it. Each share class within a company must have a 
        # unique name, and all of the shares issued under it will be subject to
        # the rights attached to that share class going forward. It may be the 
        # case that a share class has a nominal value of £0.01 at the time the
        # shares are allotted and issued, but later the nominal value of the
        # share class is changed to £0.001. In practice it is unlikely that
        # share certificates would be reissued to a shareholder upon such a change
        # being made, so in order to reflect that immutability we can consider
        # easch 'Shareholding' a value object for the purposes of our model. 
        shareholding = Shareholding(
            company=self,
            shareholder=person,
            number_of_shares=number_of_shares,
            share_class_name=share_class_name,
            nominal_value_per_share=Decimal(nominal_value_per_share),
            price_paid_per_share=Decimal(price_paid_per_share),
            allotted_on=allotted_on,
            issued_on=issued_on
        )
        self.__trigger_event__(
            Company.SharesIssued, 
            shareholding=shareholding,
            share_class_name=share_class_name,
            nominal_value_per_share=nominal_value_per_share,
            votes_per_share=votes_per_share,
            entitled_to_dividends=entitled_to_dividends,
            entitled_to_capital=entitled_to_capital,
            redeemable=redeemable,            
            currency=currency
        )
        return shareholding


    class SharesIssued(Event):
        def mutate(event, company):
            try:
                share_class = company._share_classes[event.share_class_name]
            except KeyError:
                share_class = ShareClass(
                    name=event.share_class_name,
                    votes_per_share=event.votes_per_share,
                    entitled_to_dividends=event.entitled_to_dividends,
                    entitled_to_capital=event.entitled_to_capital,
                    redeemable=event.redeemable,                    
                    nominal_value_per_share=event.nominal_value_per_share,
                    currency=event.currency
                )
                company._share_classes[event.shareholding.share_class_name] = share_class
            assert isinstance(share_class, ShareClass)
            share_class.add_allotment(event.shareholding)

    # Once shares have been allotted, we need to be able to locate them. 
    def get_share_class(self, share_class_name) -> ShareClass:
        return self._share_classes.get(share_class_name)

    def get_shareholdings(self, person = None, share_class_name = None) -> List:
        if share_class_name:
            share_class = self.get_share_class(share_class_name)
            assert isinstance(share_class, ShareClass)
            if person:
                return [holding for holding in share_class.shareholdings if holding.shareholder_id == person.id]
            return share_class.shareholdings
        elif person and not share_class_name:
            persons_shareholdings = []
            for share_class_name in self._share_classes:
                for holding in self.share_classes[share_class_name].shareholdings:
                    if holding.shareholder_id == person.id:
                        persons_shareholdings.append(holding)
            return persons_shareholdings
        else: 
            all_shareholdings = []
            for share_class_name in self.share_classes:
                for holding in self.share_classes[share_class_name].shareholdings:
                    all_shareholdings.append(holding)
            return all_shareholdings

# An Officer is a person who has been appointed as either
# a director or a secretary of the company. 
class Officer(object):
    def __init__(
        self,
        company: Company,
        person: Person, 
        appointment_date: str,
        occupation: str = None,
        officer_type: str = "director", 
        service_address: str = None,
        former_names: list = None
    ): 
        assert officer_type in ["director", "secretary"], f"officer type must be either 'director' or 'secretary'"
        self.company_id = company.id
        self.company_name = company.name
        self.person_id = person.id
        self.person_name = person.name
        self.person_address = person.address
        self.officer_type = officer_type
        self.appointment_date = appointment_date
        self.occupation = occupation
        self.service_address = service_address
        self.former_names = former_names

    def __repr__(self):
        return f"<Officer(company_name='{self.company_name}', name='{self.person_name}', officer_type='{self.officer_type}')>"

    @property
    def name(self):
        return self.person_name
    
    @property 
    def address(self):
        return self.person_address
    

# Each share in the company has rights attached to it, and those rights 
# are defined with reference to the share class it belongs to. A company 
# can have any number of share classes, so long as the name is unique. 

class ShareClass(object):
    def __init__(
        self, name: str, 
        nominal_value_per_share: Decimal,
        votes_per_share: int,
        entitled_to_dividends: bool,
        entitled_to_capital: bool,
        redeemable: bool,        
        currency: str
    ) -> ShareClass:
        self._name = name
        self._shareholdings = []
        self._nominal_value_per_share = nominal_value_per_share
        self._votes_per_share = votes_per_share
        self._entitled_to_dividends = entitled_to_dividends
        self._entitled_to_capital = entitled_to_capital
        self._redeemable = redeemable                    
        self._currency = currency

    def __repr__(self):
        return f"<ShareClass(name='{self.name}', nominal_value={self.nominal_value}, total_shareholdings={self.total_shareholdings}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def nominal_value_per_share(self) -> Decimal:
        return self._nominal_value_per_share

    @property
    def votes_per_share(self) -> int:
        return self._votes_per_share

    @property
    def entitled_to_dividends(self) -> bool:
        return self._entitled_to_dividends

    @property
    def entitled_to_capital(self) -> bool:
        return self._entitled_to_capital

    @property
    def redeemable(self) -> bool:
        return self._redeemable

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def shareholdings(self) -> List:
        return self._shareholdings

    @property
    def total_shareholdings(self):
        return len(self.shareholdings)

    @property
    def total_number_of_shares(self):
        total = 0
        for shareholding in self._shareholdings:
            total += shareholding.number_of_shares
        return total

    @property
    def aggregate_nominal_value(self):
        total = Decimal("0.00")
        for shareholding in self._shareholdings:
            total += Decimal(shareholding.nominal_value_per_share)
        return total

    @property
    def total_price_paid(self):
        total = Decimal("0.00")
        for shareholding in self._shareholdings:
            total += Decimal(shareholding.price_paid_per_share) * Decimal(shareholding.number_of_shares)
        return total

    @property
    def aggregate_amount_unpaid(self):
        total = Decimal("0.00")
        for shareholding in self._shareholdings:
            total += Decimal(shareholding.unpaid_per_share) * Decimal(shareholding.number_of_shares)
        return total

    def add_allotment(self, allotment):
        self._shareholdings.append(allotment)
    

# A shareholding refers to shares held by a person in the capital of 
# a company. In practice, where a shareholding is allotted to a person,
# it is not considered issued until the board of the company registers
# that persons name in the company's register of members and issues a
# share certificate to them. For the purposes of this model it is sufficient
# to consider adding a 'Shareholding' to a 'ShareClass' as equivalent to
# entering the person's name into the register, while the certificate attribute
# provides the minimum information that should be shown on a physical certificate.

class Shareholding(object):
    def __init__(
        self, 
        shareholder: Person,
        company: Company,
        share_class_name: str,
        number_of_shares: int, 
        price_paid_per_share: Decimal,
        nominal_value_per_share: Decimal,
        allotted_on: str,
        issued_on: str,
        unpaid_per_share: Decimal = 0,
        currency: str = "GBP",
    ) -> Shareholding: 
        self.id = uuid4()
        self.company_name = company.name
        self.company_id = company.id
        self.shareholder_name = shareholder.name
        self.shareholder_address = shareholder.address
        self.shareholder_id = shareholder.id
        self.share_class_name = share_class_name
        self.number_of_shares = number_of_shares
        self.price_paid_per_share = str(price_paid_per_share)
        self.nominal_value_per_share = str(nominal_value_per_share)
        self.issued_on = issued_on
        self.allotted_on = allotted_on
        self.unpaid_per_share = unpaid_per_share
        self.currency = currency

    def __repr__(self):
        return f"<Shareholding(shareholder='{self.shareholder_name}', company_name='{self.company_name}', number_of_shares={self.number_of_shares}>"

    @property
    def certificate(self):
        return "Share certificate: {name} of {address} holds {no_shares} {share_class} shares of {curr} £{nom_val} each in the capital of {co_name}".format(
            name=self.shareholder_name,
            address=self.shareholder_address,
            no_shares=self.number_of_shares,
            share_class=self.share_class_name,
            curr=self.currency,
            nom_val=self.nominal_value_per_share,
            co_name=self.company_name
        )

    @property
    def share_premium(self) -> Decimal:
        paid = Decimal(self.price_paid_per_share)
        nom_val = Decimal(self.nominal_value_per_share)
        return paid - nom_val
    
if __name__ == "__main__":
    company = Company.prepare_new(
            name="Company Limited", 
            registered_office="10 Downing Street, London",
            registered_office_country="England and Wales",
            company_type="Private limited by shares",
            sic_code=18535,
            model_articles=True,
            custom_articles=False,
            restricted_articles=False
            )
    joris = Person.involve(
            title="Mr",
            name="Joris Bohnson", 
            address="23 Fleet Street, London, EC4Y 1UJ",
            former_names = ["Chuck Norris", "Bruce Lee"],
            date_of_birth = "05/1962",
        )    
    company.issue_shares(
            person=joris, 
            share_class_name="ordinary", 
            number_of_shares=51, 
            nominal_value_per_share=Decimal("0.01"), 
            price_paid_per_share=Decimal("121.00"),
            votes_per_share=1,
            entitled_to_dividends=True,
            entitled_to_capital=True,
            redeemable=False
        )