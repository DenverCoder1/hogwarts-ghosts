from database.models import (
    DATABASE_ENGINE,
    VERIFIED_CATEGORIES,
    Verifieds,
    CustomCommands,
    Prefixes,
    SheetTethers,
    SheetTemplates,
    Reminders,
)

from database.database_utils import (
    get_prefixes,
    get_verifieds,
    get_trusteds,
    get_solvers,
    get_testers,
    get_custom_commands,
    get_reminders,
)

PREFIXES = get_prefixes()
VERIFIEDS = get_verifieds()
TRUSTEDS = get_trusteds()
SOLVERS = get_solvers()
TESTERS = get_testers()
CUSTOM_COMMANDS = get_custom_commands()
REMINDERS = get_reminders()
