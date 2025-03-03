from bounded_contexts.wallets.aggregates import Wallet, Deposit, Withdrawal

account_id = "account_id"
idempotency_key = "idempotency_key"


def test_wallet() -> None:
    wallet = Wallet(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    assert wallet
    assert wallet.available_funds == 0


def test_wallet_balance() -> None:
    wallet = Wallet(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    wallet.deposit(Deposit(idempotency_key=idempotency_key, amount=30))
    assert wallet.available_funds == 30

    wallet.deposit(Deposit(idempotency_key=idempotency_key + "_2", amount=70))
    assert wallet.available_funds == 100

    wallet.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=60))

    assert wallet.available_funds == 40

    wallet.withdraw(Withdrawal(idempotency_key=idempotency_key + "_2", amount=40))

    assert wallet.available_funds == 0


def test_ignore_duplicate_deposits() -> None:
    wallet = Wallet(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    wallet.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert wallet.available_funds == 100

    wallet.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert wallet.available_funds == 100


def test_ignore_duplicate_withdrawals() -> None:
    wallet = Wallet(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    wallet.deposit(Deposit(idempotency_key=idempotency_key, amount=100))
    assert wallet.available_funds == 100

    wallet.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=10))
    assert wallet.available_funds == 90

    wallet.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=10))
    assert wallet.available_funds == 90


def test_cant_withdraw_above_limit() -> None:
    wallet = Wallet(
        account_id=account_id,
        deposits=[],
        withdrawals=[],
    )

    wallet.deposit(Deposit(idempotency_key=idempotency_key, amount=10))
    assert wallet.available_funds == 10

    try:
        wallet.withdraw(Withdrawal(idempotency_key=idempotency_key, amount=11))
        assert False, "Should have raised an error"

    except ValueError as e:
        assert str(e) == "Insufficient funds to withdraw '11'"
        assert wallet.available_funds == 10
