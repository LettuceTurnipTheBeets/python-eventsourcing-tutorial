"""
extended domain model for tutorial..add detail before pushing to github
"""
from __future__ import annotations
from typing import Any, List
from decimal import Decimal
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute

def get_simple_repr(obj):
    attributes = ("%s=%r" % (k, v) for k, v in obj.__dict__.items())
    return "<%s(%s)>" % (obj.__class__.__name__, ', '.join(attributes))

"""
The Person aggregate root controls everything to do with a 
legal person in law. For example, a legal person will have a certain
number of shareholdings, each represented by a share certificate.
Where a legal person sells shares to another, that is an event related to
the legal person rather than the company or the shares themselves.
"""
class Person(AggregateRoot):
    __subclassevents__ = True
    
    class Event(AggregateRoot.Event):
        pass

    def __init__(self, name: str, **kwargs: Any):
        super().__init__(**kwargs)
        self._name = name
        self.shareholdings = []
    
    def __repr__(self):
        return f"<Person(name='{self.name}')>"

    @attribute
    def name(self):
        pass

    def record_new_shareholding(self, shares_issued: Shares) -> None: 
        self.__trigger_event__(
            Person.NewShareholdingRecorded,
            shares_issued=shares_issued,
            shareholder_name=self.name
        )
    
    class NewShareholdingRecorded(Event):
        def mutate(event, legal_person):
            legal_person.shareholdings.append(event.shares_issued)

"""
The Company aggregate root is the entry point for controlling all
actions and objects related to a company, including its share classes,
shares and shareholders. 
"""
class Company(AggregateRoot):
    __subclassevents__ = True

    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._name = name
        self.share_classes = {}
        self.allotted = []
        self.issued = []

    def __repr__(self):
        return f"<Company(name='{self.name}')>"

    @attribute
    def name(self):
        pass

    class Event(AggregateRoot.Event):
        pass

    def create_share_class(
            self,
            name: str,
            nominal_value: float or Decimal,
            entitled_to_dividends: bool = True,
            entitled_to_capital: bool = True,
            votes_per_share: int = 1,
            redeemable: bool = False
        ) -> None: 
            new_share_class = ShareClass(
                name=name, 
                nominal_value=nominal_value, 
                entitled_to_dividends=entitled_to_dividends,
                entitled_to_capital=entitled_to_capital,
                votes_per_share=votes_per_share,
                redeemable=redeemable
            )
            self.__trigger_event__(Company.ShareClassWasCreated, new_share_class=new_share_class)

    class ShareClassWasCreated(Event):
        def mutate(event, company):
            company.share_classes[event.new_share_class.name] = event.new_share_class

    def allot_shares(
        self,
        legal_person: Person,
        share_class: ShareClass,
        number_of_shares: int
    ) -> None: 
        if type(share_class) is not ShareClass:
            raise ShareClassError(f"Expected <class 'ShareClass'>: got {type(share_class)}")
        if share_class.name not in self.share_classes:
            raise ShareClassError(f"No such share class: {share_class.name}")
        new_shares = Shares(number=number_of_shares, share_class=share_class, in_company=self)
        new_shareholding = Shareholding(legal_person=legal_person, shares=new_shares, status="ALLOTTED")
        self.__trigger_event__(Company.NewSharesAllotted, new_shareholding=new_shareholding)

    class NewSharesAllotted(Event):
        def mutate(event, company):
            company.allotted.append(event.new_shareholding)

    def issue_shares(
        self, 
        to_person: Shareholding, 
        issue_date: Decimal = None
    ) -> None:
        allotments = [a for a in self.allotted if a.legal_person == to_person] 
        if not allotments: 
            raise ShareholdingError(f"No shares allotted to {to_person}")
        self.__trigger_event__(Company.SharesIssued, shares_to_issue=allotments)

    def issue_all_shares(
        self, 
        issue_date: Decimal = None
    ) -> None: 
        if not self.allotted: 
            raise ShareholdingError(f"No shares allotted")
        allotments = self.allotted.copy()
        self.__trigger_event__(Company.SharesIssued, shares_to_issue=allotments)

    class SharesIssued(Event):
        def mutate(event, company):
            for shareholding in event.shares_to_issue:
                company.allotted.remove(shareholding)
                company.issued.append(shareholding)

    # TODO: need to rewrite this
    # def get_share_class_data(self, share_class: ShareClass) -> dict:
    #     if share_class.name not in self.share_classes:
    #         raise ShareClassError(f"{self.name} has no share class: {share_class}")
    #     total_number_of_shares = 0
    #     aggregate_nominal_value = 0
    #     for sh in self.issued:
    #         for holding in sh.shareholding:
    #             if holding.share_class == share_class:
    #                 total_number_of_shares += holding.number
    #                 aggregate_nominal_value += (holding.number * holding.share_class.nominal_value)
    #     return dict(
    #         share_class = share_class.name,
    #         total_number_of_shares = total_number_of_shares, 
    #         aggregate_nominal_value = aggregate_nominal_value,
    #     )

class Shareholding(object):
    def __init__(
        self, 
        legal_person: Person, 
        shares: Shares, 
        status: str = "ALLOTTED"
    ) -> None:
        self.legal_person = legal_person
        self.shareholding = shares
        self.status = status

    def __repr__(self):
        return f"<Shareholding(legal_person={self.legal_person}, shares={self.shareholding}, status='{self.status}')>"

class ShareClass(object):
    def __init__(
        self,
        name: str = "ordinary",
        nominal_value: float = 0.0001,
        entitled_to_dividends: bool = True,
        entitled_to_capital: bool = True,
        votes_per_share: int = 1,
        redeemable: bool = False,
        decimal_precision: bool = False,
    ) -> None:
        self.name = name
        self.entitled_to_dividends = entitled_to_dividends
        self.entitled_to_capital = entitled_to_capital
        self.votes_per_share = votes_per_share
        self.redeemable = redeemable
        if decimal_precision: 
            self.nominal_value = Decimal(nominal_value)
        else:
            self.nominal_value = nominal_value

    def __repr__(self):
        return get_simple_repr(self)

class Shares(object): 
    def __init__(
        self, 
        number: int, 
        share_class: ShareClass,
        in_company: Company
    ) -> None:
        self.number = number
        self.share_class = share_class or ShareClass(
                name="ordinary", 
                nominal_value=1,
                entitled_to_dividends=True,
                entitled_to_capital=True,
                votes_per_share=1,
                redeemable=False
            )
        self.company_id = in_company.id
        self.company_name = in_company.name

    def __repr__(self):
        return get_simple_repr(self)

class ShareClassError(Exception):
    pass

class ShareholdingError(Exception):
    pass

# quick tests
if __name__ == "__main__":
    from eventsourcing.domain.model.events import subscribe
    all_events = []
    def add_to_all_events_record(event) -> None:
        all_events.extend(event)
    subscribe(handler=add_to_all_events_record)

    def print_events(events):
        for num, e in enumerate(events, 1):
            print(num, e, "\n")

    # set up
    jack = Person.__create__(name="Jack")
    jack.__save__()
    
    company = Company.__create__(name="Company Ltd")
    company.create_share_class(name="ordinary", nominal_value=0.001)    
    ord = company.share_classes["ordinary"]

    company.allot_shares(legal_person=jack, share_class=ord, number_of_shares=100)
    company.allot_shares(legal_person=jack, share_class=ord, number_of_shares=251)
    company.allot_shares(legal_person=jack, share_class=ord, number_of_shares=29151)

    # company.issue_shares(jack)
    company.__save__()
