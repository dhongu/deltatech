selection_solution = [
    ("assigned", "Assigned"),  # trimis catre  - T
    ("favorable", "Favorable"),  # rezolvat (favorabil )       F
    ("unfavorable", "Unfavorable"),  # rezolvat (  nefavorabil ) N
    ("partial", "Partial"),  # rezolvat (  partial)      P
    ("decline", "Declined Competence"),  # rezolvat  Dc
    ("internal", "Internal"),
]


selection_state = (
    [("new", "New"), ("progress", "In Progress"),]  #  # document aflat in operare  - O
    + selection_solution
    + [("cancel", "Cancel"), ("done", "Done"),]  # nu
)
