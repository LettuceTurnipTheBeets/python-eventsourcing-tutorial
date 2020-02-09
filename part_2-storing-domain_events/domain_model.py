"""
This is part of the code accompanying this article: 
https://www.eventsorcery.com/python-eventsourcing-tutorial-part-2-event-store/

This file amends ../part_1-domain_layer/version_6.py as described
in the above post. 
"""
from typing import Any, List
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute

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

class Company(AggregateRoot):
    __subclassevents__ = True

    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._name = name
        self.shareholders = []
        self.share_classes = []

    def __repr__(self):
        return f"Company(name='{self.name}')"

    @attribute
    def name(self):
        pass

    def create_share_class(
            self,
            name: str,
            nominal_value: float,
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
            new_shareclass = ShareClass(
                name=event.name, 
                nominal_value=event.nominal_value, 
                votes_per_share=event.votes_per_share
            )
            company.share_classes.append(new_shareclass)

    def add_new_shareholder(
        self,
        shareholder_name: str,
        share_class: ShareClass,
        number_of_shares: int
    ) -> None: 
        self.__trigger_event__(
            Company.NewShareholderWasAdded,
            shareholder_name=shareholder_name,
            share_class=share_class,
            number_of_shares=number_of_shares
        )

    class NewShareholderWasAdded(Event):
        def mutate(event, company):
            new_shares = Shares(
                number=event.number_of_shares, 
                share_class=event.share_class
            )
            new_shareholder = Shareholder(name=event.shareholder_name)
            new_shareholder.shares_held.append(new_shares)
            company.shareholders.append(new_shareholder)

events = []

def add_to_event_record(event: Company.Event) -> None:
    events.extend(event)

def is_company_event(event: Any) -> bool: 
    return all(isinstance(e, Company.Event) for e in event)

def test_domain_model():
    # Get subscriber ready
    from eventsourcing.domain.model.events import subscribe
    global events
    subscribe(handler=add_to_event_record, predicate=is_company_event)

    # Set up 
    new_company = Company.__create__(name="Rocinante Limited")
    new_company.create_share_class(name="ordinary", nominal_value=0.0001)
    initial_shareholders = ["James Holden", "Amos Burton", "Naomi Nagata", "Alex Kamal"]
    for person in initial_shareholders:
        new_company.add_new_shareholder(
            shareholder_name = person,
            number_of_shares = 2500,
            share_class = new_company.share_classes[0]
        )
    new_company.__save__()

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

    # Check that our event log has some stuff in it
    assert len(events) == 6

    return (new_company, events)


if __name__ == "__main__":
    newco, events = test_domain_model()
    print("All domain model tests passed")
     