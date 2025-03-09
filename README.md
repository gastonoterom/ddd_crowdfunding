# Satoshi Spark 🚀 🔥

_Crowdfunding via bitcoin lightning_

## Table of Contents

- [Introduction](#introduction)
- [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
  - [Aggregates: the building block of our domain](#aggregates-the-building-block-of-our-domain)
  - [Abstract Repositories: avoid the ORM jail](#abstract-repositories-avoid-the-orm-jail)
  - [Unit of Work: How to handle database transactions in the domain model](#unit-of-work-how-to-handle-database-transactions-in-the-domain-model)
- [Command Query Responsibility Segregation (CQRS)](#command-query-responsibility-segregation-cqrs)
  - [Write model](#write-model)
  - [Read model](#read-model)
- [Distributed Systems](#distributed-systems)
  - [Transactional Outboxes: handle message reliability](#transactional-outboxes-handle-message-reliability)
  - [Choreography Based Sagas: distributed transactions across contexts](#choreography-based-sagas-distributed-transactions-across-contexts)
  - [From monolith to microservices](#from-monolith-to-microservices)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Satoshi Spark is designed to facilitate crowdfunding campaigns via the Bitcoin Lightning Network. 

This little project is a playground for exploring Domain-Driven Design (DDD), 
Command Query Responsibility Segregation (CQRS), and distributed systems concepts.

## Domain-Driven Design (DDD)

The project follows DDD principles to ensure a clear and maintainable codebase. 

Satoshi Spark is organized into several bounded contexts, each representing a distinct part of the domain:

- **Common**: Contains abstract and basic aggregate/ports/adapter definitions.
- **Auth**: Handles authentication and user management.
- **Accounting**: Manages account balances and transactions.
- **Crowdfunding**: Manages crowdfunding campaigns and donations.
- **Bitcoin**: Manages Bitcoin Lightning Network-related operations, such as invoices.
- **Dashboard**: Provides a read-only context where users can view their activities.

Each bounded context encapsulates its own domain logic and interacts with other contexts only through messages.

### Aggregates: the building block of our domain

In Domain-Driven Design (DDD), aggregates define consistency boundaries in the write domain, ensuring that all changes within them maintain business rules and integrity. 
Each aggregate consists of closely related entities and has a root entity that controls modifications.

Repository operations only retrieve and persist aggregate roots.

```python
class Aggregate(ABC):
    def __init__(self, entity_id: str) -> None:
        self.__entity_id = entity_id

    @property
    def entity_id(self) -> str:
        return self.__entity_id

    def __eq__(self, other) -> bool:
        if not isinstance(other, Aggregate):
            return False
        return self.entity_id == other.entity_id
```


### Abstract Repositories: avoid the ORM jail

Repositories are used to abstract the persistence layer from the domain.
Here (in DDD-land), we don't want to couple the domain with a specific database or ORM implementation.

#### Example: Coupling our domain with some specific ORM or DB implementation
```python
import orm_library

class CampaignAggregate(orm_library.ORMClass):
    entity_id = orm_library.ORMColumn(type=orm_library.types.String)
    goal = orm_library.ORMColumn(type=orm_library.types.Integer)
    ... 
```

Can you see the 'problem' with this code? 

What if we want to change the ORM library? 
How can we write unit tests without being at the mercy of the ORM library?

The solution? Reverse the dependencies.

The domain will define repository interfaces (ports), and later we can define specific implementations (adapters) for the ORM library or database we choose.

#### Example: Abstract Repository
```python
# See how our new aggregate is not coupled with any specific ORM or DB implementation
class Campaign(Aggregate):
    def __init__(self, entity_id: str, goal: int, ...) -> None:
        super().__init__(entity_id)
        self.goal = goal
        ...

# Generic abstract repository class (no support for DB transactions yet, see next topic for it)
class Repository[T: Aggregate](ABC):
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> T | None:
        pass

    @abstractmethod
    async def add(self, entity: T) -> None:
        pass

    @abstractmethod
    async def update(self, entity: T) -> None:
        pass

class CampaignRepository(Repository[Campaign], ABC):
    pass
```

I suspect you can already guess the overall idea on how to implement a specific repository for a Postgres database, right? 😉

If not, don't worry! There are plenty of examples in the codebase. 

You can also submit a PR to add more examples for different libraries or engines!

### Unit of Work: How to handle database transactions in the domain model

If you've been paying closed attention, you'll notice that we haven't talked about transactions at all.

Creating database transactions is trivial, 
but how can we ensure the domain does not become polluted with database-specific code?

The answer is... Units of Work!

The Unit of Work pattern is used to manage transactions and ensure data consistency. 
It tracks changes to aggregates and commits them as a single transaction.
This pattern represents an abstraction for any database (SQL or not) transaction, 
de-coupling the domain from particular database implementations.

#### Example: UOW in action

```python
async def register_campaign_donation(
    command: TransferSucceededEvent,
) -> None:
    # Entering this context manager creates a uow and starts a transaction

    async with uow_factory() as uow:
        campaign_id: str = command.metadata["campaign_id"]

        campaign: Campaign = await campaign_repository(uow).find_by_id(
            campaign_id
        )

        # Notice how we don't have to explicitly call any persistence method on the aggregate,
        # as the UOW will take care of that for us
        campaign.donate(
            Donation(
                idempotency_key=command.idempotency_key,
                amount=command.amount,
                account_id=command.from_account_id,
            )
        )

    # Leaving the context manager will: 
    # * persist the aggregate changes
    # * store the messages in the transactional outbox
    # * commit the transaction
```

#### Example: Abstract Unit of Work

```python
# Abstract unit of work (UOW)
class UnitOfWork(ABC):
    def __init__(self) -> None:
        self._messages: list[Message] = []  # The domain emits event to the UOW
        self._tracked_objects: list[tuple[object, Callable]] = []  # The UOW keeps track of aggregates to persist their changes 

    def emit(self, message: Message) -> None:
        self._messages.append(message)

    # Before commit, the UOW calls the persistence callback of each tracked object
    # and stores the messages in a transactional outbox (more on this later)
    async def commit(self) -> None:
        for obj, persistence_callback in self._tracked_objects:
            await persistence_callback()

        await outbox(self).store(self._messages)
        await self._commit()

    async def rollback(self) -> None:
        self._messages.clear()
        self._tracked_objects.clear()
        await self._rollback()

    @abstractmethod
    async def _commit(self) -> None:
        pass

    @abstractmethod
    async def _rollback(self) -> None:
        pass
```

#### Example: Abstract Repository implementation

```python
# Generic abstract repository class
class Repository[T: Aggregate](ABC):
    # We initialize the repository with a UOW
    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    def __track_object(self, obj: T) -> None:
        self.__uow.track_object(obj, lambda: self._update(obj))

    # Every time we add or we find an object, we track it so they are persisted on-commit
    async def add(self, entity: T) -> None:
        await self._add(entity)
        self.__track_object(entity)

    async def find_by_id(self, entity_id: str) -> T | None:
        obj = await self._find_by_id(entity_id)

        if obj is not None:
            self.__track_object(obj)

        return obj

    @abstractmethod
    async def _find_by_id(self, entity_id: str) -> T | None:
        pass

    @abstractmethod
    async def _add(self, entity: T) -> None:
        pass

    @abstractmethod
    async def _update(self, entity: T) -> None:
        pass
```

#### Example: Postgres Unit Of Work implementation

```python
# Postgres specific implementation
class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, conn: asyncpg.Connection, transaction: Transaction) -> None:
        super().__init__()
        self.__conn = conn
        self.__transaction = transaction

    @property
    def conn(self) -> asyncpg.Connection:
        return self.__conn

    async def _commit(self) -> None:
        await self.__transaction.commit()

    async def _rollback(self) -> None:
        await self.__transaction.rollback()

# Postgres UOW context manager factory
@contextlib.asynccontextmanager
async def make_postgres_unit_of_work() -> AsyncGenerator[PostgresUnitOfWork, None]:
    async with postgres_pool.get_pool().acquire() as conn:
        transaction = conn.transaction(isolation="repeatable_read")
        await transaction.start()

        uow = PostgresUnitOfWork(
            conn,
            transaction,
        )

        try:
            yield uow

            await uow.commit()
        except BaseException:
            await uow.rollback()
            raise
```

I hope this covers the previous commented part of the repository implementation 😅.
 
## Command Query Responsibility Segregation (CQRS)

CQRS is used to separate the read and write operations of the application. 
Commands are used to change the state of the system, while queries are used to retrieve data.

### Write model

Commands are written as imperative verbs (do something...), while events are written as past verbs (something happened...).

#### Example: Command and Event

```python
# Crowdfunding context example command:
@dataclass(frozen=True)
class CreateCampaign(Command):
    entity_id: str
    account_id: str
    title: str
    description: str
    goal: int

    
# Accounting context example event:
@dataclass(frozen=True)
class TransferSucceededEvent(Event):
    idempotency_key: str
    from_account_id: str
    to_account_id: str
    amount: int
    metadata: dict
```

The write model consists of the aggregates, repositories, units of work, and messages used to change the state of the system.
Here, consistency and integrity are the main concerns. Performance, although always relevant, is not the primary focus.

#### Example: Write model command handler
```python
async def handle_register(
    command: RegisterAccount,
) -> None:
    async with make_unit_of_work() as uow:
        account = Account(
            account_id=command.account_id,
            username=command.username.lower(),
            password=command.hashed_password,
        )

        await account_repository(uow).add(account)

        uow.emit(SignupEvent(account_id=account.account_id))
```

### Read model

The read model consists of the queries and views used to retrieve data from the system.
These operations do not affect the state of the system, and should be optimized for speed. 

This model can implement caches, projections, and other tricks to improve performance.
It might not always be 1 on 1 with the write model, but it should not matter.

#### Example: Read model query handler
```python
@dataclass(frozen=True)
class DashboardView:
    account_id: str
    balance: int
    campaigns: list[CampaignView]
    ...


async def view_dashboard_query(account_id: str) -> DashboardView:
    return await dashboard_view_factory().create_dashboard_view(account_id=account_id)

class DashboardViewFactory(ABC):
    @abstractmethod
    async def create_dashboard_view(self, account_id: str) -> DashboardView:
        pass

class PostgresDashboardViewFactory(DashboardViewFactory):
    async def create_dashboard_view(self, account_id: str) -> DashboardView :
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow("SQL Query...")

        assert row
        return DashboardView(**row)
```

## Distributed Systems

Even though this application is a monolith, we don't do direct communication between contexts. 
Instead, we use messages to communicate between them.

This comes with some considerations:

* How can we ensure that messages are delivered reliably? 💀
* How can we ensure that messages are not lost? 💀
* How can we handle inter-context database transactions? 💀

If only someone could come up with a solution for these problems... 🤔

### Transactional Outboxes: reliability send messages

Transactional Outboxes ensure that messages are reliably sent even if the system crashes.
They store messages in a database table and process them asynchronously.

Consider this scenario:
1. We start a database transaction
2. We do changes to the domain write model
3. We commit the database transaction
4. We emit messages to a messaging engine (think of kafka or whatever)

What happens if our application crashes after step 3?
The transaction is saved, but the messages are lost.
Important business processes might not be triggered, and the system might end up in an inconsistent state.

Now the following:
1. We start a database transaction
2. We do changes to the domain write model
3. We emit messages to a different messaging engine (think of kafka or whatever)
4. We commit the database transaction

What happens if our application crashes after step 3?
The messages are sent, but the transaction was rolled back.
This is also very bad, imagine that we send a 'payment processed event', but the db never saved it.

A solution for this is to store the messages in a database table, in the same transaction as the domain changes.
Then, after commit, a processor periodically polls this table and sends the messages to the messaging engine.
After sending the messages, they can be deleted. 

1. We start a database transaction (i.e. postgres)
2. We do changes to the domain write model
3. We store the events in a postgres database table
4. We commit the database transaction
5. After transaction, we periodically poll the table and send the messages to the messaging engine
6. After dispatch, we delete the messages

Now, if our application crashes after step 3, there should be no issues!
Either the transaction commits and the messages are sent, or the transaction rolls back and the messages are never sent.

What happens if the processor crashes after step 5? Between sending the message and deleting it.
As you can imagine, the messages will be sent twice. This is called 'at least once' delivery and is what most messaging engines implement.
This is why it is important to make sure that the message handlers are idempotent.

#### Example: Transactional Outbox and Outbox processor

```python
# This class stores the messages in the database when the uow commits
class TransactionalOutbox(ABC):
    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    @abstractmethod
    async def store(self, messages: list[Message]) -> None:
        pass

    
# This class is supposed to run separately, in a periodic task or even a different process. 
# This will iterate over the messages
class TransactionalOutboxProcessor(ABC):
    async def process_messages(self) -> None:
        messages = await self._fetch_messages()

        await self._dispatch_messages(messages)

        await self._destroy_messages(messages)

    @abstractmethod
    async def _fetch_messages(self) -> list[Message]:
        pass

    @abstractmethod
    async def _dispatch_messages(self, messages: list[Message]) -> None:
        pass

    @abstractmethod
    async def _destroy_messages(self, messages: list[Message]) -> None:
        pass
```

#### Example: Postgres implementation of a transactional outbox
```python

class PostgresTransactionalOutbox(TransactionalOutbox):
    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def store(self, messages: list[Message]) -> None:
        if not messages:
            return

        await self.uow.conn.executemany("sql query...")

class PostgresTransactionalOutboxProcessor(TransactionalOutboxProcessor):
    async def _fetch_messages(self) -> list[Message]:
        async with postgres_pool.get_pool().acquire() as conn:
            rows = await conn.fetch("sql query...")
        return [self.__row_to_message(row) for row in rows]

    async def _dispatch_messages(self, messages: list[Message]) -> None:
        results = await asyncio.gather(
            *[event_bus.handle(message) for message in messages],
            return_exceptions=True,
        )
        exceptions = [result for result in results if isinstance(result, Exception)]
        if exceptions:
            for exc in exceptions:
                logger.error(f"Error processing message: {exc}")

    async def _destroy_messages(self, messages: list[Message]) -> None:
        async with postgres_pool.get_pool().acquire() as conn:
            await conn.execute("sql query...")
        
    def __row_to_message(self, row: dict) -> Message:
        ...
```

### Choreography Based Sagas: distributed transactions across contexts

Here, we'll see how to handle distributed transactions across contexts using a choreography-based saga.

Basically, instead of having one ACID transaction, we have multiple smaller transactions that are coordinated by messages.

We'll use this example: __A user requests a withdraw to a bitcoin wallet.__

#### Example: Bitcoin withdraw saga, happy path

* First transaction, bitcoin context (saga starting point):
  * User requests a withdrawal
  * Bitcoin context creates an invoice with a pending status
  * Bitcoin context emits a WithdrawRequestedEvent (The transactional outbox ensures this event is sent)

* Second transaction, accounting context:
  * The system verifies the user's balance
  * The system accepts the withdrawal
  * The system updates the account's balance and stores the financial operation
  * The system emits a WithdrawalAcceptedEvent (The transactional outbox ensures this event is sent)

* Third transaction, bitcoin context:
  * The bitcoin processor pays for the invoice
  * The bitcoin context updates the invoice status to paid

#### Example: Bitcoin withdraw saga, insufficient balance

* First transaction, bitcoin context (saga starting point):
  * User requests a withdrawal for X amount above their limit (this can happen if the view model is outdated)
  * Bitcoin context creates an invoice with a pending status
  * Bitcoin context emits a WithdrawRequestedEvent (The transactional outbox ensures this event is sent)

* Second transaction, accounting context:
  * The system verifies the user's balance
  * The system rejects the withdrawal
  * The system emits a WithdrawalRejectedEvent (The transactional outbox ensures this event is sent)

* Third transaction, bitcoin context:
  * The bitcoin invoice is rejected, or deleted

Idempotency is crucial in all steps, as the system might crash at any point and messages should be able to be
processed multiple times.

If the system crashes in any step, the saga should be retried until it completes successfully.

You can see how, even thought there is not one big transaction, the system is still consistent.

This concept is called __Eventual Consistency__

### From monolith to microservices

The nice thing about this architecture is that it is very easy to split into microservices, as the bounded contexts are independent.

We can:

1. Create one service, repository, ci/cd flow, etc... per bounded context.
2. Move from a single database per project to a multiple database/schema per service pattern.
3. Replace the in-process message bus with a real message broker (like Kafka or RabbitMQ)
4. Deploy the applications separately.

But of course, there are many more considerations when moving to a microservice architecture.  

I'll leave this migration as an exercise to the reader 😳.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
