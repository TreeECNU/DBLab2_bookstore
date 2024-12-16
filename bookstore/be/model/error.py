error_code = {
    401: "authorization fail.",
    511: "non exist user id {}",
    512: "exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",

    520: "not be paid, order id {}",
    521: "cannot be canceled, order id {}",
    522: "no store for user, user id {}",
    523: "Book with keyword {} not found.",
    524: "Store with ID {} not found.",
    525: "Book with ID {} not found in store with ID {}.",

    526: "order is canceled, order id {}",
    527: "order is paid, order id {}",
    528: "order is confirmed, order id {}",
    529: "order is shipped, order id {}",
    530: "Database operation error: {}",
}


def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    return 519, error_code[519].format(order_id)

def error_book_not_found(keyword):
    return 523, error_code[523].format(keyword)

def error_store_not_found(store_id):
    return 524, error_code[524].format(store_id)

def error_book_not_found_in_the_store(keyword, store_id):
    return 525, error_code[525].format(keyword, store_id)

def db_operation_error(e):
    return 530, error_code[530].format(str(e))

def error_not_be_paid(order_id):
    return 520, error_code[520].format(order_id)

def error_cannot_be_canceled(order_id):
    return 521, error_code[521].format(order_id)

def error_no_store_found(user_id):
    return 522, error_code[522].format(user_id)

def error_authorization_fail():
    return 401, error_code[401]

def error_order_is_canceled(order_id):
    return 526, error_code[526]

def error_order_is_paid(order_id):
    return 527, error_code[527]

def error_order_is_confirmed(order_id):
    return 528, error_code[528]

def error_order_is_shipped(order_id):
    return 529, error_code[529]
def error_and_message(code, message):
    return code, message