# test_putaway_strategy is not imported (as on 19.0): two of its tests describe an older
# semantic of _check_can_be_used (quantity ignored) and fail against the current code.
from . import (
    test_avoid_putaway,
    test_avoid_root_location,
    test_capacity_access_rights,
    test_prefer_existing_stock,
    test_putaway,
    test_validation,
)
