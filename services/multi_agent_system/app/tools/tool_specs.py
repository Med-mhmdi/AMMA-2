EXPENSE_TOOL_SPECS = {
    "create_expense": {
        "required_fields": [
            "description",
            "type",
            "amount",
            "transaction_date",
            "category",
        ]
    },
    "update_expense": {
        "required_fields": []
    },
    "delete_expense": {
        "required_fields": []
    },
    "list_expenses": {
        "required_fields": []
    },
    "create_category": {
        "required_fields": [
            "category",
        ]
    },
    "update_category": {
        "required_fields": []
    },
    "delete_category": {
        "required_fields": [
            "category",
        ]
    },
    "list_categories": {
        "required_fields": []
    },
}


LOAN_TOOL_SPECS = {
    "create_loan": {
        "required_fields": [
            "person_name",
            "type",
            "amount",
            "date_created",
        ]
    },
    "update_loan": {
        "required_fields": []
    },
    "update_loan_status": {
        "required_fields": [
            "person_name",
            "status",
        ]
    },
    "delete_loan": {
        "required_fields": []
    },
    "list_loans": {
        "required_fields": []
    },
}