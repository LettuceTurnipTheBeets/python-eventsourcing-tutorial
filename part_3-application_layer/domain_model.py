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

    def create_share_class(
            self,
            name: str,
            nominal_value: float or Decimal,
            entitled_to_dividends: bool = True,
            entitled_to_capital: bool = True,
            votes_per_share: int = 1,
            redeemable: bool = False
        ) -> None: 
            self.__trigger_event__(
                Company.ShareClassWasCreated,
                name=name,
                nominal_value=nominal_value,
                entitled_to_dividends=entitled_to_dividends,
                entitled_to_capital=entitled_to_capital,
                votes_per_share=votes_per_share,
                redeemable=redeemable
            )

    class Event(AggregateRoot.Event):
        pass

    class ShareClassWasCreated(Event):
        def mutate(event, company):
            new_share_class = ShareClass(
                name=event.name, 
                nominal_value=event.nominal_value, 
                votes_per_share=event.votes_per_share
            )
            company.share_classes[new_share_class.name] = new_share_class

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
        self.__trigger_event__(
            Company.NewSharesAllotted,
            legal_person=legal_person,
            share_class=share_class,
            number_of_shares=number_of_shares
        )

    class NewSharesAllotted(Event):
        def mutate(event, company):
            new_shares = Shares(
                number=event.number_of_shares, 
                share_class=event.share_class,
                in_company=company
            )
            new_shareholder = Shareholder(
                legal_person=event.legal_person,
                shares=new_shares,
                status="ALLOTTED"
            )
            company.allotted.append(new_shareholder)

    def get_allotments(self, to_person: Person = None) -> List:
        if not to_person:
            return self.allotted
        return [a for a in self.allotted if a.legal_person == to_person] 
            
    def issue_shares(
        self, 
        to_person: Shareholder, 
        issue_date: Decimal = None 
    ) -> None:
        allotments = self.get_allotments(to_person)
        if not allotments: 
            raise ShareholderError(f"No shares allotted to {to_person}")
        self.__trigger_event__(
            Company.SharesIssued, 
            shares_to_issue=allotments, 
            number_of_issuances=len(allotments),
            issue_date=issue_date
        )

    def issue_all_allotted_shares(
        self, 
        issue_date: Decimal = None
    ) -> None: 
        self.__trigger_event__(
            Company.SharesIssued, 
            shares_to_issue=self.allotted,
            number_of_issuances=len(self.allotted),
            issue_date=issue_date
        )

    class SharesIssued(Event):
        def mutate(event, company): 
            print("allotted before issue", len(company.allotted))
            allot_now = event.shares_to_issue.copy()
            company.allotted = [shares for shares in company.allotted if shares not in allot_now]
            while allot_now:
                company.issued.append(allot_now.pop())
            # try:
                # if called outside of the try/except
                # this fails with ValueError: list.remove(x): x not in list
                # for s in event.shares_to_issue:
                #     company.issued.append(s)
                #     company.allotted.remove(s)
            # except ValueError:
            #     pass
            print("allotted after issue", len(company.allotted))

    def get_share_class_data(self, share_class: ShareClass) -> dict:
        if share_class.name not in self.share_classes:
            raise ShareClassError(f"{self.name} has no share class: {share_class}")

        total_number_of_shares = 0
        aggregate_nominal_value = 0
        # need to rewrite this
        for sh in self.issued:
            for holding in sh.shareholding:
                if holding.share_class == share_class:
                    total_number_of_shares += holding.number
                    aggregate_nominal_value += (holding.number * holding.share_class.nominal_value)

        return dict(
            share_class = share_class.name,
            total_number_of_shares = total_number_of_shares, 
            aggregate_nominal_value = aggregate_nominal_value,
        )

class Shareholder(object):
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
        return f"<Shareholder(legal_person={self.legal_person}, shares={self.shareholding}, status='{self.status}')>"

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

class ShareholderError(Exception):
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
    vic = Person.__create__(name="Vic")
    hood = Person.__create__(name="Hood")

    for person in [jack, vic, hood]:
        person.__save__()
    
    company = Company.__create__(name="Company Ltd")
    company.create_share_class(name="ordinary", nominal_value=0.001)    
    company.create_share_class(name="preferred", nominal_value=0.001)
    ord = company.share_classes["ordinary"]
    pref = company.share_classes["preferred"]

    # allot 2 sets of shares to jack (one pref, one ord)
    company.allot_shares(legal_person=jack, share_class=ord, number_of_shares=100)
    company.allot_shares(legal_person=jack, share_class=pref, number_of_shares=10120)
    # allot 2 more sets of ord shares to the others
    company.allot_shares(legal_person=vic, share_class=ord, number_of_shares=100)
    company.allot_shares(legal_person=hood, share_class=ord, number_of_shares=100)
    
    # check that all of the above are stored in company.allotted
    assert len(company.allotted) == 4
    # check that 2 of the above are for jack only
    assert len(company.get_allotments(jack)) == 2    

    # issue the shares to jack only
    company.issue_shares(jack)
    company.__save__()

    # check that only 2 sets of shares have been issued
    assert len(company.issued) == 2
    # check that no more shares should be issued to jack
    assert len(company.get_allotments(jack)) == 0
    # check that 2 sets of shares remain in company.allotted
    assert len(company.allotted) == 2

    company.issue_all_allotted_shares()
    company.__save__()
    assert len(company.allotted) == 0
    assert len(company.issued) == 4