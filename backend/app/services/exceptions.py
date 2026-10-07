class ConfigurationError(Exception):
    pass


class LLMError(Exception):
    pass


class JSONParseError(Exception):
    pass


class PromptNotFoundError(Exception):
    pass


class JobOwnershipLostError(Exception):
    pass
