import copy

from django.utils.functional import LazyObject, empty


class LazySettings(LazyObject):
    def _setup(self, name=None):
        from django.conf import settings
        from .default import CONFIG as DEFAULT_CONFIG
        CONFIG = copy.copy(DEFAULT_CONFIG)
        CONFIG.update(settings.CONFIG)

        # Ensure we always have our exception configuration...
        for exc_category in ['unauthorized', 'not_found', 'recoverable']:
            if exc_category not in CONFIG['exceptions']:
                default_exc_config = DEFAULT_CONFIG['exceptions'][exc_category]
                CONFIG['exceptions'][exc_category] = default_exc_config

        # Ensure our password validator always exists...
        if 'regex' not in CONFIG['password_validator']:
            default_pw_regex = DEFAULT_CONFIG['password_validator']['regex']
            CONFIG['password_validator']['regex'] = default_pw_regex
        if 'help_text' not in CONFIG['password_validator']:
            default_pw_help = DEFAULT_CONFIG['password_validator']['help_text']
            CONFIG['password_validator']['help_text'] = default_pw_help

        self._wrapped = CONFIG

    def __getitem__(self, name, fallback=None):
        if self._wrapped is empty:
            self._setup(name)
        return self._wrapped.get(name, fallback)

CONFIG = LazySettings()
