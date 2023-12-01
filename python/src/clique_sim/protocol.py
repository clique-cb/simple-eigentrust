from abc import ABC, abstractmethod


class Protocol(ABC):
    """
    Abstract base class for protocols.
    A Protocol is something which supports a set of _users_,
    each of which can do _actions_.
    
    Actions are:
    - Deposit money to the protocol
    - Withdraw money from the protocol
    - Get available balance
    - Get locked balance (balance which cannot be transferred or withdrawn)
    - Transfer money to another user
    - Establish or modify a _trust link_ towards another user.
    - Get the global user trust (which is basically user's credit limit)
    - Get the user debt (total or towards another user)
    - Borrow money from the protocol (up to the credit limit)
    - Repay the debt (fully or in part)
    
    Trust links are directed and capacitated.

    Also, global protocol stats:
    - TVL
    - Total debt
    """

    @abstractmethod
    def add_user(self, user_id: str):
        """
        Add a user to the protocol.
        """
        pass

    @abstractmethod
    def deposit(self, user_id: str, amount: int):
        """
        Deposit money to the protocol.
        """
        pass

    @abstractmethod
    def withdraw(self, user_id: str, amount: int):
        """
        Withdraw money from the protocol.
        """
        pass

    @abstractmethod
    def available_balance(self, user_id: str) -> int:
        """
        Get the available balance of a user.
        """
        pass
    
    @abstractmethod
    def locked_balance(self, user_id: str) -> int:
        """
        Get the locked balance of a user.
        """
        pass

    @abstractmethod
    def transfer(self, user_id: str, amount: int, recipient_id: str):
        """
        Transfer money to another user.
        """
        pass

    @abstractmethod
    def set_trust(self, user_id: str, amount: int, recipient_id: str):
        """
        Establish a trust link towards another user.
        """
        pass

    @abstractmethod
    def credit_limit(self, user_id: str) -> int:
        """
        Get the global trust of a user.
        """
        pass

    @abstractmethod
    def debt(self, user_id: str, recipient_id: str = None) -> int:
        """
        Get the debt of a user.
        """
        pass

    @abstractmethod
    def borrow(self, user_id: str, amount: int):
        """
        Borrow money from the protocol.
        """
        pass

    @abstractmethod
    def repay(self, user_id: str, amount: int):
        """
        Repay the debt.
        """
        pass

    @abstractmethod
    def total_value_locked(self) -> int:
        """
        Get the total value locked in the protocol.
        """
        pass

    @abstractmethod
    def total_debt(self) -> int:
        """
        Get the total debt in the protocol.
        """
        pass



