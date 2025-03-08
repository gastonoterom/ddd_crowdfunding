# Satoshi Spark 🚀 🔥

_Crowdfunding via bitcoin lightning_

## Table of Contents

TODO: table of contents

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
- **Bitcoin**: Manages Bitcoin Lightning Network-related operations, such as invoices.
- **Dashboard**: Provides a read-only context where users can view their activities.

Each bounded context encapsulates its own domain logic and interacts with other contexts only through messages.

### Aggregates, the building block of our write domain

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


### Abstract Repositories, avoid the ORM jail

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

# Generic abstract repository class
class Repository[T: Aggregate](ABC):
    @abstractmethod
    async def _find_by_id(self, entity_id: str) -> T | None:
        pass

    @abstractmethod
    async def _add(self, entity: T) -> None:
        pass

    @abstractmethod
    async def _update(self, entity: T) -> None:
        pass
    
    ###################################
    # This part will be explained later:
    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    def __track_object(self, obj: T) -> None:
        self.__uow.track_object(obj, lambda: self._update(obj))

    async def add(self, entity: T) -> None:
        await self._add(entity)
        self.__track_object(entity)

    async def find_by_id(self, entity_id: str) -> T | None:
        obj = await self._find_by_id(entity_id)

        if obj is not None:
            self.__track_object(obj)

        return obj
    ###################################

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

#### Example: UOW in action

```python
async def register_campaign_donation(
    command: TransferSucceededEvent,
) -> None:
    # Entering this context manager creates a uow and starts a transaction

    async with make_unit_of_work() as uow:
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

I hope this covers the previous commented part of the repository implementation 😅.
 
## Command Query Responsibility Segregation (CQRS)

CQRS is used to separate the read and write operations of the application. 
Commands are used to change the state of the system, while queries are used to retrieve data.

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

### Write model

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

## Transactional Outboxes: message reliability

Transactional Outboxes ensure that messages are reliably sent even if the system crashes. They store messages in a database table and process them asynchronously.

#### Example: Transactional Outbox

```python
class TransactionalOutbox(ABC):
    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    @abstractmethod
    async def store(self, messages: list[Message]) -> None:
        pass
```

### Choreography Based Sagas: distributed transactions across contexts

Exercise for the reader: Implement this application as a distributed system instead of a monolith 😳.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Blog Articles

For more information, check out the following blog articles:

- [Domain-Driven Design (DDD)](link-to-your-article)
- [Units of Work](link-to-your-article)
- [Transactional Outboxes](link-to-your-article)
- [Distributed Systems](link-to-your-article)
