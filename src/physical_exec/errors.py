class PhysicalExecutionError(RuntimeError):
    """Base error with no implication that an action was executed."""

class InputRejected(PhysicalExecutionError):
    """Rejected before any physical action; safe to request a new decision."""

class AmbiguousExecution(PhysicalExecutionError):
    """An action might have executed. Never retry it or reset automatically."""

class ProtocolError(PhysicalExecutionError):
    pass

class ProviderError(PhysicalExecutionError):
    pass

class BudgetExceeded(PhysicalExecutionError):
    pass
