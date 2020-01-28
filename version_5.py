"""
This is part of the code accompanying this article: 

Version 5 adapts the existing domain model to use the Python
eventsourcing library. 
"""
from uuid import uuid4
from typing import Any
from datetime import datetime

def get_simple_repr(obj):
    attributes = ("%s=%r" % (k, v) for k, v in obj.__dict__.items())
    return "<%s(%s)>" % (obj.__class__.__name__, ', '.join(attributes))

class Shareholder:
    def __init__(self, name: str) -> None:
        self.name = name
        self.shares_held = []

    def __repr__(self):
        return get_simple_repr(self)

class ShareClass:
    def __init__(
        self,
        name: str = "ordinary",
        nominal_value: float = 0.0001,
        entitled_to_dividends: bool = True,
        entitled_to_capital: bool = True,
        votes_per_share: int = 1,
        redeemable: bool = False
    ) -> None:
        self.name = name
        self.nominal_value = nominal_value 
        self.entitled_to_dividends = entitled_to_dividends
        self.entitled_to_capital = entitled_to_capital
        self.votes_per_share = votes_per_share
        self.redeemable = redeemable

    def __repr__(self):
        return get_simple_repr(self)

class Shares: 
    def __init__(
        self, 
        number: int, 
        share_class: ShareClass
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

    def __repr__(self):
        return get_simple_repr(self)

class Company:
    def __init__(self, name: str) -> None:
        self.name = name
        self.id = uuid4()
        self.shareholders = []
        self.share_classes = []
        self.events = []

    def __repr__(self):
        return f"Company(name='{self.name}', len(share_classes)={len(self.share_classes)}, len(events)={len(self.events)})"

    def create_share_class(
            self,
            name: str,
            nominal_value: float,
            entitled_to_dividends: bool = True,
            entitled_to_capital: bool = True,
            votes_per_share: int = 1,
            redeemable: bool = False
        ) -> None: 
            event = self.ShareClassWasCreated(
                name=name,
                nominal_value=nominal_value,
                entitled_to_dividends=entitled_to_dividends,
                entitled_to_capital=entitled_to_capital,
                votes_per_share=votes_per_share,
                redeemable=redeemable
            )
            event.apply(self)
            self.events.append(event)

    class ShareClassWasCreated:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__['created_on'] = f"{datetime.now():%Y-%m-%d at %H:%M:%S%z}"
            self.__dict__.update(kwargs)
        
        def apply(event, company):
            new_shareclass = ShareClass(
                name=event.name, 
                nominal_value=event.nominal_value, 
                votes_per_share=event.votes_per_share
            )
            company.share_classes.append(new_shareclass)

        def __repr__(self):
            return "ShareClassWasCreated(" + ', '.join(
                    "{0}={1!r}".format(*item) for item in self.__dict__.items()
                ) + ')'

    def add_new_shareholder(
        self,
        shareholder_name: str,
        share_class: ShareClass,
        number_of_shares: int
    ) -> None: 
        event = self.NewShareholderWasAdded(
            shareholder_name=shareholder_name,
            share_class=share_class,
            number_of_shares=number_of_shares
        )
        event.apply(self)
        self.events.append(event)

    class NewShareholderWasAdded:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__['added_on'] = f"{datetime.now():%Y-%m-%d at %H:%M:%S%z}"
            self.__dict__.update(kwargs)
        
        def apply(event, company):
            new_shares = Shares(
                number=event.number_of_shares, 
                share_class=event.share_class
            )
            new_shareholder = Shareholder(name=event.shareholder_name)
            new_shareholder.shares_held.append(new_shares)
            company.shareholders.append(new_shareholder)

        def __repr__(self):
            return "NewShareholderWasAdded(" + ', '.join(
                    "{0}={1!r}".format(*item) for item in self.__dict__.items()
                ) + ')'


def test_version_4():
    new_company = Company(name="Rocinante Limited")
    new_company.create_share_class(name="ordinary", nominal_value=0.0001)
    
    initial_shareholders = ["James Holden", "Amos Burton", "Naomi Nagata", "Alex Kamal"]
    for person in initial_shareholders:
        new_company.add_new_shareholder(
            shareholder_name = person,
            number_of_shares = 2500,
            share_class = new_company.share_classes[0]
        )

    # Check that the company has a newly created ordinary share class
    assert new_company.share_classes[0].name == "ordinary"
    assert new_company.share_classes[0].nominal_value == 0.0001

    # Check our shareholders
    assert new_company.name == "Rocinante Limited"
    assert "James Holden" and "Naomi Nagata" in [sh.name for sh in new_company.shareholders]
    assert len(new_company.shareholders) == 4

    # Check that James Holden has 2500 ordinary shares of £0.0001 each
    assert new_company.shareholders[0].shares_held[0].number == 2500
    assert new_company.shareholders[0].shares_held[0].share_class.name == "ordinary"
    assert new_company.shareholders[0].shares_held[0].share_class.nominal_value == 0.0001

    # Check that we have something useful in our new event log
    assert len(new_company.events) == 5
    assert isinstance(new_company.events[0], Company.ShareClassWasCreated)
    assert hasattr(new_company.events[0], "created_on")
    isinstance(new_company.events[1], Company.NewShareholderWasAdded)
    assert new_company.events[1].shareholder_name == "James Holden"

    return new_company

if __name__ == "__main__":
    newco = test_version_4()
    print(newco)
    for num, event in enumerate(newco.events, 1):
        print(num, event, "\n")
    
    

     