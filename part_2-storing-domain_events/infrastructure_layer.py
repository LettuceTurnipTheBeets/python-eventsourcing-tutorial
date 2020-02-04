"""
This is part of the code accompanying this article: 
https://www.eventsorcery.com/python-eventsourcing-tutorial-part-2-event-store/ 
"""

from eventsourcing.infrastructure.sqlalchemy.datastore import SQLAlchemySettings, SQLAlchemyDatastore
from eventsourcing.infrastructure.sqlalchemy.records import StoredEventRecord
from eventsourcing.infrastructure.sqlalchemy.manager import SQLAlchemyRecordManager
from eventsourcing.infrastructure.sequenceditem import StoredEvent
from eventsourcing.infrastructure.sequenceditemmapper import SequencedItemMapper
from eventsourcing.infrastructure.eventstore import EventStore
from eventsourcing.utils.cipher.aes import AESCipher
from eventsourcing.utils.random import encode_random_bytes, decode_bytes

cipher_key = encode_random_bytes(num_bytes=32)
cipher = AESCipher(cipher_key=decode_bytes(cipher_key))

def construct_sqlalchemy_db(uri="sqlite://"):
    db = SQLAlchemyDatastore(
        settings=SQLAlchemySettings(uri), 
        tables=(StoredEventRecord,)
    )
    db.setup_connection()
    db.drop_tables()
    db.setup_tables()
    return db

def create_event_store(db):
    record_manager = SQLAlchemyRecordManager(
        session=db.session, 
        sequenced_item_class=StoredEvent, 
        record_class=StoredEventRecord, 
        application_name="CompanyApp",
        contiguous_record_ids=True 
    )
    event_mapper = SequencedItemMapper(
        sequenced_item_class=StoredEvent,
        cipher=cipher
        )
    event_store = EventStore(
        record_manager=record_manager, 
        event_mapper=event_mapper
    )
    return event_store

if __name__ == "__main__":
    from domain_model import test_domain_model
    newco, events = test_domain_model()
    print("Domain model tests passed")

    # set up the event store
    database = construct_sqlalchemy_db()
    event_store = create_event_store(database)

    # add the old global events to the event store
    event_store.store_events(events)
    
    # manually add a new event to the event store
    newco.add_new_shareholder(shareholder_name="Mars Investments", share_class=newco.share_classes[0], number_of_shares=1000)
    newco.__save__()
    domain_event_as_stored_item = event_store.event_mapper.item_from_event(events[-1])
    event_store.record_manager.record_item(domain_event_as_stored_item)

    # verify that our event store contains the newest event
    assert event_store.get_most_recent_event(newco.id).shareholder_name == "Mars Investments"
    assert len(event_store.list_events(newco.id)) == 7
    print("Event store tests passed")

    # create and test a repository
    from eventsourcing.infrastructure.eventsourcedrepository import EventSourcedRepository
    repo = EventSourcedRepository(event_store)
    newco_before_investment = repo.get_entity(newco.id, at=5)
    assert 'Mars Investments' not in [sh.name for sh in newco_before_investment.shareholders] 
    print("Event sourced repository tests passed")