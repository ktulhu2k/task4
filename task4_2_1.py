def inst(parent=None, act="NEW", cdic=None, name=None, *args, **kwargs):
    if cdic is None:
        cdic = {}

    # По-хорошему надо храниить всё цепочку наследований, чтобы иметь возможность дергать super от super.
    # Но у меня пупок развяжется всё это реализовывать. Сделаем проще.
    if parent is None:
        parent_pub_var = {}
        parent_prot_var = {}
        parent_priv_var = {}
        parent_pub_meth = {}
        parent_prop_meth = {}
        parent_priv_meth = {}
    else:
        pctx = parent("CONTEXT")  # контекст предка
        parent_pub_var = pctx["pub_var"]
        parent_prot_var = pctx["prot_var"]
        parent_priv_var = pctx["priv_var"]
        parent_pub_meth = pctx["pub_meth"]
        parent_prop_meth = pctx["prop_meth"]
        parent_priv_meth = pctx["priv_meth"]

    # Ну типа наследование
    pub_var = {**parent_pub_var, **cdic.get("pub_var", {})}
    prot_var = {**parent_prot_var, **cdic.get("prot_var", {})}
    priv_var = {**parent_priv_var, **cdic.get("priv_var", {})}
    pub_meth = {**parent_pub_meth, **cdic.get("pub_meth", {})}
    prop_meth = {**parent_prop_meth, **cdic.get("prop_meth", {})}
    priv_meth = {**parent_priv_meth, **cdic.get("priv_meth", {})}

    # будем замыканиями на контекст имитировать поля и методы
    context = {
        "pub_var": pub_var,
        "prot_var": prot_var,
        "priv_var": priv_var,
        "pub_meth": pub_meth,
        "prop_meth": prop_meth,
        "priv_meth": priv_meth,
    }

    match act:
        case "NEW":

            def obj(
                act="VAR", name=None, *a, **kw
            ):  # симулируем, что можем в инстанции
                match act:
                    case "VAR":
                        # Только публичные переменные доступны напрямую
                        return context["pub_var"][name]
                    case "METH":
                        func = context["pub_meth"][name]
                        return func(context, *a, **kw)
                    case "CONTEXT":
                        return context
                    case _:
                        raise ValueError(f"Это что такое? {act}")

            return obj
        case "VAR":
            return context["pub_var"][name]
        case "METH":
            func = context["pub_meth"][name]
            return func(context, *args, **kwargs)
        case "CONTEXT":
            return context
        case _:
            raise ValueError(f"Это что такое? {act}")


# Типа объект с приватной переменной
user = inst(
    act="NEW",
    cdic={
        "pub_var": {"name": "Lex"},
        "priv_var": {"password": "12345", "phone": "+7(917)842-95-20"},
        "pub_meth": {
            "authenticate": lambda ctx, pwd: pwd == ctx["priv_var"]["password"],
            "get_phone": lambda ctx: f"tel: {ctx['priv_var']['phone']}",
        },
    },
)

# Публичное поле — можно читать
print(user("VAR", "name"))  #

# Приватное поле — НЕЛЬЗЯ читать напрямую!
# print(user("VAR", "password"))

# Но методы могут использовать приватные данные
print(user("METH", "authenticate", "12345"))  #  True
print(user("METH", "authenticate", "wrong"))  #  False
print(user("METH", "get_phone"))  #

# Наследование от user приватных переменных
admin = inst(
    parent=user,
    act="NEW",
    cdic={
        "pub_var": {"role": "admin"},
        "priv_var": {"admin_key": "SECRET"},  # дополняем приватные данные
    },
)


print(admin("VAR", "name"))  #  Lex (унаследовано)
print(admin("VAR", "role"))  #  admin


print(admin("METH", "authenticate", "12345"))  #  True
print(admin("METH", "get_phone"))

# Гость — тоже пользователь, но без пароля
guest = inst(
    act="NEW",
    cdic={
        "pub_var": {"name": "Anonymous"},
        "priv_var": {"password": None, "phone": "N/A"},
        "pub_meth": {
            "authenticate": lambda ctx,
            pwd: False,  # гость не может аутентифицироваться
            "get_phone": lambda ctx: "Phone not available",  # и пусть без телефона сидит
        },
    },
)

# Щас как агрегировать будем
company = inst(
    act="NEW",
    cdic={
        "pub_var": {
            "name": "SibintokHard",
            "employees": [],  # список ссылок на пользователей
        },
        "pub_meth": {
            "add_employee": lambda ctx, emp: ctx["pub_var"]["employees"].append(emp),
            "list_employees": lambda ctx: [
                emp("VAR", "name") for emp in ctx["pub_var"]["employees"]
            ],
            "notify_all": lambda ctx: [
                emp("METH", "get_phone") for emp in ctx["pub_var"]["employees"]
            ],
            "authenticate_employee": lambda ctx,
            emp_name,
            pwd: next(  # не до конца понимаю этот генератор, но он работает
                (
                    emp("METH", "authenticate", pwd)
                    for emp in ctx["pub_var"]["employees"]
                    if emp("VAR", "name") == emp_name
                ),
                False,
            ),
        },
    },
)

# Добавляем сотрудников в компанию
company("METH", "add_employee", user)
company("METH", "add_employee", admin)
company("METH", "add_employee", guest)

# Полиморфизм: все имеют методы authenticate и get_phone
print("Сотрудники:", company("METH", "list_employees"))

print("Контакты:")
for phone in company("METH", "notify_all"):
    print("tel: ", phone)

# Полиморфная аутентификация
print(company("METH", "authenticate_employee", "Lex", "12345"))  # True (user или admin)
print(company("METH", "authenticate_employee", "Anonymous", "any"))  # False (guest)
print(company("METH", "authenticate_employee", "Loh", "123"))  # False (нет такого)

# Агрегирование: объекты живут независимо
print("\nНапрямую:")
print("Admin phone:", admin("METH", "get_phone"))
print("Guest auth:", guest("METH", "authenticate", "test"))
