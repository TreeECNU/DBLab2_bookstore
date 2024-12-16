from fe import conf
from fe.access import seller, auth


def register_new_seller(user_id, password) -> seller.Seller:
    a = auth.Auth(conf.URL)
    code = a.register(user_id, password)
    print(f"register_new_seller code = {code}")
    assert code == 200
    s = seller.Seller(conf.URL, user_id, password)
    return s
