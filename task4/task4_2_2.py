def inst(parent=None, members=None, *args, **kwargs):
    if members is None:
        members = {}

    # Ну типа наследование
    parent_members = {}
    if parent is not None:
        parent_members.update(parent("CONTEXT")["members"])
    parent_members.update(members)

    context = {"members": parent_members}

    def obj(act, name=None, *args, **kwargs):
        match act:
            case "GET":  # чтение переменной
                if name not in context["members"]:
                    raise AttributeError(f"'{name}' не существуе")
                member = context["members"][name]
                if member["access"] != "public": #только паблик
                    raise AttributeError(f"'{name}' ошибка доступа")
                return member["value"]

            case "CALL":  # вызов метода 
                if name not in context["members"]:
                    raise AttributeError(f"Метод '{name}' не существуе")
                member = context["members"][name]
                if not callable(member["value"]):
                    raise TypeError(f"'{name}' вообще не метод")
                return member["value"](context, *args, **kwargs)

            case "CONTEXT":  # для наследования
                return context

            case _:
                raise ValueError(f"Это что такое? {act}")

    return obj


# Создаём пользователя
user = inst(
    members={
        "name": {"value": "Lex", "access": "public"},
        "password": {"value": "12345", "access": "private"},
        "phone": {"value": "+7(917)842-95-20", "access": "private"},
        "authenticate": {
            "value": lambda ctx, pwd: pwd == ctx["members"]["password"]["value"],
            "access": "public",
        },
        "get_phone": {
            "value": lambda ctx: f"tel: {ctx['members']['phone']['value']}",
            "access": "public",
        },
    }
)

# Публичное поле — можно читать
print(user("GET", "name"))  # Lex

# Приватное поле — нельзя читать напрямую!
# print(user("GET", "password"))  #  AttributeError

# Но методы работают
print(user("CALL", "authenticate", "12345"))  # True
print(user("CALL", "authenticate", "wrong"))  # False
print(user("CALL", "get_phone"))  # tel: +7(917)842-95-20


# Наследование: создаём админа на основе user
admin = inst(
    parent=user,
    members={
        "role": {"value": "admin", "access": "public"},
        "admin_key": {"value": "SECRET", "access": "private"},
    },
)

print(admin("GET", "name"))  #  Lex (унаследовано)
print(admin("GET", "role"))  #  admin

print(admin("CALL", "authenticate", "12345"))  #  True
print(admin("CALL", "get_phone"))  #  tel: +7(917)842-95-20


# Гость
guest = inst(
    members={
        "name": {"value": "Anonymous", "access": "public"},
        "password": {"value": None, "access": "private"},
        "phone": {"value": "N/A", "access": "private"},
        "authenticate": {
            "value": lambda ctx, pwd: False,
            "access": "public",
        },  # гость не может аутентифицироваться
        "get_phone": {
            "value": lambda ctx: "Phone not available",
            "access": "public",
        },  # и пусть без телефона сидит
    }
)


# Щас как агрегировать будем
company = inst(
    members={
        "name": {"value": "SibintokHard", "access": "public"},
        "employees": {"value": [], "access": "private"},
        "add_employee": {
            "value": lambda ctx, emp: ctx["members"]["employees"]["value"].append(emp),
            "access": "public",
        },
        "list_employees": {
            "value": lambda ctx: [
                emp("GET", "name") for emp in ctx["members"]["employees"]["value"]
            ],
            "access": "public",
        },
        "notify_all": {
            "value": lambda ctx: [
                emp("CALL", "get_phone") for emp in ctx["members"]["employees"]["value"]
            ],
            "access": "public",
        },
        "authenticate_employee": {
            "value": lambda ctx, emp_name, pwd: next(
                (
                    emp("CALL", "authenticate", pwd)
                    for emp in ctx["members"]["employees"]["value"]
                    if emp("GET", "name") == emp_name
                ),
                False,
            ),
            "access": "public",
        },
    }
)

# Добавляем сотрудников
company("CALL", "add_employee", user)
company("CALL", "add_employee", admin)
company("CALL", "add_employee", guest)

# Полиморфизм в действии
print("Сотрудники:", company("CALL", "list_employees"))
print("Контакты:")
for phone in company("CALL", "notify_all"):
    print("tel: ", phone)

print(company("CALL", "authenticate_employee", "Lex", "12345"))  # True
print(company("CALL", "authenticate_employee", "Anonymous", "any"))  # False
print(company("CALL", "authenticate_employee", "Loh", "123"))  # False

# Напрямую
print("Admin phone:", admin("CALL", "get_phone"))
print("Guest auth:", guest("CALL", "authenticate", "test"))
