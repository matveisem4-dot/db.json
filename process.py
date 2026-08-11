import sys
import json
import os
import hashlib

SALT = "NeoBank_Secure_Salt_2026"

def hash_data(data_str: str) -> str:
    return hashlib.sha256((data_str + SALT).encode('utf-8')).hexdigest()

def main():
    if len(sys.argv) < 3:
        print("Недостаточно аргументов")
        sys.exit(1)

    event_type = sys.argv[1]
    payload_raw = sys.argv[2]
    
    try:
        payload = json.loads(payload_raw)
    except Exception as e:
        print(f"Ошибка парсинга JSON payload: {e}")
        sys.exit(1)

    if not os.path.exists("db.json"):
        db = {"terminals": {}, "clients": []}
    else:
        with open("db.json", "r", encoding="utf-8") as f:
            db = json.load(f)

    # 1. РЕГИСТРАЦИЯ ТЕРМИНАЛА
    if event_type == "register_terminal":
        term_id = payload.get("terminal_id")
        if "terminals" not in db:
            db["terminals"] = {}
        
        db["terminals"][term_id] = {
            "name": payload.get("name", "Касса"),
            "purpose": payload.get("purpose", "Продажи"),
            "registered": True,
            "blocked": False
        }
        print(f"Терминал {term_id} зарегистрирован.")

    # 2. ОПЛАТА ЧЕРЕЗ NFC
    elif event_type == "pay_transaction":
        term_id = payload.get("terminal_id")
        uid = payload.get("uid", "").upper()
        amount = float(payload.get("amount", 0))

        term = db.get("terminals", {}).get(term_id)
        if not term or not term.get("registered"):
            print("ОШИБКА: Терминал не зарегистрирован!")
            sys.exit(1)
        if term.get("blocked"):
            print("ОШИБКА: Терминал заблокирован!")
            sys.exit(1)

        client = next((c for c in db.get("clients", []) if c.get("uid") == uid), None)
        if not client:
            print("ОШИБКА: Карта не найдена!")
            sys.exit(1)

        if client["balance"] < amount:
            print(f"ОШИБКА: Недостаточно средств! Баланс: {client['balance']}")
            sys.exit(1)

        client["balance"] -= amount
        print(f"Успешная оплата {amount} ₽. Новый баланс: {client['balance']}")

    # 3. СОЗДАНИЕ КАРТЫ АДМИНОМ
    elif event_type == "create_card":
        if "clients" not in db:
            db["clients"] = []
            
        new_client = {
            "name": payload.get("name"),
            "card": payload.get("card"),
            "pin_hash": hash_data(payload.get("pin")),
            "cvc_hash": hash_data(payload.get("cvc")),
            "uid": payload.get("uid", "").upper(),
            "balance": float(payload.get("balance", 0))
        }
        db["clients"].append(new_client)
        print(f"Карта {payload.get('card')} успешно создана.")

    # 4. БЛОКИРОВКА / РАЗБЛОКИРОВКА ТЕРМИНАЛА
    elif event_type == "toggle_terminal_block":
        term_id = payload.get("terminal_id")
        block_state = payload.get("blocked", False)
        if term_id in db.get("terminals", {}):
            db["terminals"][term_id]["blocked"] = block_state
            print(f"Статус блокировки {term_id} изменен на {block_state}")

    # Сохраняем обновленные данные в db.json
    with open("db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
