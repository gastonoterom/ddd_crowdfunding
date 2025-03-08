# Satoshi Spark 🚀 🔥

## Crowdfunding via bitcoin lightning. 

The project implements Domain-Driven Design (DDD) and the Command Query Responsibility Segregation (CQRS) pattern.

Intended for educational purposes only.

## Table of Contents

- [Introduction](#introduction)
- [Project Structure](#project-structure)
- [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
- [Command Query Responsibility Segregation (CQRS)](#command-query-responsibility-segregation-cqrs)
- [Units of Work](#units-of-work)
- [Transactional Outboxes](#transactional-outboxes)
- [Distributed Systems](#distributed-systems)
- [Getting Started](#getting-started)
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


### Abstract Repositories

Repositories are used to abstract the persistence layer from the domain.
Here (in DDD-land), we don't want to couple the domain with a specific database or ORM implementation.

#### Example: Coupling our domain with some specific ORM or DB implementation
```python
import orm_library

class CampaignAggregate(orm_library.ORMClass):
    entity_id = orm_library.ORMColumn(type=orm_library.types.String)
    is_active = orm_library.ORMColumn(type=orm_library.types.postgres.SmallInt)
    ... 
```

Can you see the 'problem' with this code? 

What if we want to change the ORM library? 
How can we write unit tests without being at the mercy of the ORM library?

The solution? Reverse the dependencies.

The domain will define repository interfaces (ports), and later we can define specific implementations (adapters) for the ORM library or database we choose.

But... How can we model the concept of an ACID database transaction using DDD? This seems impossible!

The answer is... Units of Work! 😉

### Unit of Work

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
```

#### Example: UOW in action

```python
async def register_campaign_donation(
    command: TransferSucceededEvent,
) -> None:
    # This context manager creates a uow and starts a transaction
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

### Read model



## Distributed Systems

Even though this application is a monolith, we don't do direct communication between contexts. 
Instead, we use messages to communicate between contexts.

How can we ensure that messages are delivered reliably? How can we reliable send messages related to a transaction?
How can we handle distributed transactions then? We can't use a traditional ACID transaction across multiple contexts.

If only someone could come up with a solution for this... 🤔

## Transactional Outboxes: How to ensure messages are reliably sent

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

### Choreography Based Sagas: How to distribute transactions across multiple contexts


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
