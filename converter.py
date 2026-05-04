import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# ---------- КОНФИГУРАЦИЯ ----------
API_KEY = "ВАШ_API_КЛЮЧ"          # Замените на реальный ключ
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/"
HISTORY_FILE = "conversion_history.json"

# ---------- ЗАГРУЗКА / СОХРАНЕНИЕ ИСТОРИИ ----------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ---------- ПОЛУЧЕНИЕ КУРСА (внешний API) ----------
def get_exchange_rate(from_currency, to_currency):
    try:
        response = requests.get(BASE_URL + from_currency, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["result"] == "success":
            rate = data["conversion_rates"].get(to_currency)
            if rate:
                return rate
            else:
                messagebox.showerror("Ошибка", f"Валюта {to_currency} не найдена")
                return None
        else:
            messagebox.showerror("Ошибка API", "Не удалось получить курс")
            return None
    except Exception as e:
        messagebox.showerror("Ошибка сети", str(e))
        return None

# ---------- ГЛАВНОЕ ОКНО ----------
class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("600x500")
        self.history = load_history()

        # Доступные валюты (распространённый список)
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "CAD", "CHF", "TRY", "UAH"]

        # Интерфейс
        # Выбор "из"
        tk.Label(root, text="Из валюты:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.from_combo = ttk.Combobox(root, values=self.currencies, state="readonly")
        self.from_combo.grid(row=0, column=1, padx=10, pady=10)
        self.from_combo.set("USD")

        # Выбор "в"
        tk.Label(root, text="В валюту:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.to_combo = ttk.Combobox(root, values=self.currencies, state="readonly")
        self.to_combo.grid(row=1, column=1, padx=10, pady=10)
        self.to_combo.set("EUR")

        # Сумма
        tk.Label(root, text="Сумма:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.amount_entry = tk.Entry(root)
        self.amount_entry.grid(row=2, column=1, padx=10, pady=10)

        # Кнопка конвертации
        self.convert_btn = tk.Button(root, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # Результат
        self.result_label = tk.Label(root, text="Результат: ", font=("Arial", 12, "bold"))
        self.result_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Таблица истории (Treeview)
        self.tree = ttk.Treeview(root, columns=("date", "from_amt", "from_cur", "to_amt", "to_cur"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("from_amt", text="Сумма (исх.)")
        self.tree.heading("from_cur", text="Из")
        self.tree.heading("to_amt", text="Сумма (результат)")
        self.tree.heading("to_cur", text="В")
        self.tree.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Кнопки управления историей
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=5)
        tk.Button(btn_frame, text="Сохранить историю", command=self.save_history_to_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Загрузить историю", command=self.load_history_from_file).pack(side=tk.LEFT, padx=5)

        # Заполняем таблицу из загруженной истории
        self.refresh_history_table()

        # Настройка веса строк/столбцов для растяжения
        root.grid_rowconfigure(5, weight=1)
        root.grid_columnconfigure(1, weight=1)

    def convert(self):
        # Проверка ввода суммы
        amount_str = self.amount_entry.get().strip()
        if not amount_str:
            messagebox.showerror("Ошибка", "Введите сумму")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
            return

        from_cur = self.from_combo.get()
        to_cur = self.to_combo.get()
        if from_cur == to_cur:
            result = amount
        else:
            rate = get_exchange_rate(from_cur, to_cur)
            if rate is None:
                return
            result = amount * rate

        # Отображаем результат
        result_text = f"{amount:.2f} {from_cur} = {result:.2f} {to_cur}"
        self.result_label.config(text=f"Результат: {result_text}")

        # Добавляем запись в историю
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_amount": amount,
            "from_currency": from_cur,
            "to_amount": round(result, 2),
            "to_currency": to_cur
        }
        self.history.append(record)
        save_history(self.history)
        self.refresh_history_table()

    def refresh_history_table(self):
        # Очистить таблицу
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Заполнить заново
        for entry in self.history:
            self.tree.insert("", tk.END, values=(
                entry["date"],
                entry["from_amount"],
                entry["from_currency"],
                entry["to_amount"],
                entry["to_currency"]
            ))

    def save_history_to_file(self):
        """Принудительное сохранение (фактически уже сохраняется после каждой конвертации, но можно отдельно)"""
        save_history(self.history)
        messagebox.showinfo("Информация", "История сохранена в JSON")

    def load_history_from_file(self):
        """Загрузка истории из JSON (перезаписывает текущую)"""
        self.history = load_history()
        self.refresh_history_table()
        messagebox.showinfo("Информация", f"Загружено {len(self.history)} записей")

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()