from bounded_contexts.accounting.aggregates import Account, Deposit, Withdrawal

account_id = "account_id"
idempotency_key = "idempotency_key"


def test_account() -> None:
    account = Account(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    assert account
    assert account.available_funds == 0


def test_balance() -> None:
    account = Account(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    account.deposit(Deposit(idempotency_key=idempotency_key, amount=30))
    assert account.available_funds == 30

    account.deposit(Deposit(idempotency_key=idempotency_key + "_2", amount=70))
    assert account.available_funds == 100

    account.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=60))

    assert account.available_funds == 40

    account.withdraw(Withdrawal(idempotency_key=idempotency_key + "_2", amount=40))

    assert account.available_funds == 0


def test_ignore_duplicate_deposits() -> None:
    account = Account(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    account.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert account.available_funds == 100

    account.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert account.available_funds == 100


def test_ignore_duplicate_withdrawals() -> None:
    account = Account(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    account.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert account.available_funds == 100

    account.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=10))
    assert account.available_funds == 90

    account.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=10))
    assert account.available_funds == 90


def test_cant_withdraw_above_limit() -> None:
    account = Account(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    account.deposit(Deposit(idempotency_key=idempotency_key, amount=10))
    assert account.available_funds == 10

    try:
        account.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=11))
        assert False, "Should have raised an error"

    except ValueError as e:
        assert str(e) == "Insufficient funds to withdraw '11'"
        assert account.available_funds == 10
