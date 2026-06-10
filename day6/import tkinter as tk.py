import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

# ======================== ПОДКЛЮЧЕНИЕ К БД ========================
class DatabaseManager:
    """Класс для работы с БД и получения метаданных"""
    
    @staticmethod
    def connect_db():
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Ilya_6dfmO76mp=1000-7",
                database="Variant 3"
            )
            return connection
        except Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось подключиться: {e}")
            return None
    
    @staticmethod
    def get_all_tables():
        """Получить список всех таблиц в базе данных"""
        conn = DatabaseManager.connect_db()
        if not conn:
            return []
        
        cursor = conn.cursor()
        try:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось получить список таблиц: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_table_schema(table_name):
        """Получить структуру таблицы (колонки, типы, ключи)"""
        conn = DatabaseManager.connect_db()
        if not conn:
            return []
        
        cursor = conn.cursor()
        try:
            # Получаем информацию о колонках
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns_info = cursor.fetchall()
            
            # Получаем информацию о первичных ключах
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s 
                AND COLUMN_KEY = 'PRI'
            """, (table_name,))
            pk_columns = [row[0] for row in cursor.fetchall()]
            
            # Формируем структуру для приложения
            columns = []
            for col in columns_info:
                col_name = col[0]
                col_type = col[1]
                is_pk = col_name in pk_columns
                is_auto_increment = "auto_increment" in col[5] if col[5] else False
                is_nullable = col[2] == "YES"
                
                columns.append({
                    "name": col_name,
                    "label": col_name.replace("_", " ").title(),
                    "pk": is_pk,
                    "auto_increment": is_auto_increment,
                    "required": not is_nullable and not is_auto_increment,
                    "type": col_type
                })
            
            return columns
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось получить структуру таблицы: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

# ======================== ГЛАВНОЕ ПРИЛОЖЕНИЕ ========================
class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.current_table = None
        self.columns = []
        self.entries = {}
        self.tree = None
        
        self.root.title("Управление базами данных - PizzaDB")
        self.root.geometry("1100x650")
        
        self.create_widgets()
        self.load_tables()
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Верхняя панель с выбором таблицы
        top_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(top_frame, text="Выберите таблицу:", bg="#f0f0f0", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10, pady=5)
        
        self.table_combobox = ttk.Combobox(top_frame, width=30, state="readonly")
        self.table_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.table_combobox.bind("<<ComboboxSelected>>", self.on_table_selected)
        
        tk.Button(top_frame, text="🔄 Обновить список", command=self.load_tables,
                 bg="#4CAF50", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=10, pady=5)
        
        # Информационная метка
        self.info_label = tk.Label(top_frame, text="", bg="#f0f0f0", fg="#666")
        self.info_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Основная область (будет обновляться при выборе таблицы)
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def load_tables(self):
        """Загрузить список таблиц в комбобокс"""
        tables = DatabaseManager.get_all_tables()
        if tables:
            self.table_combobox['values'] = tables
            self.info_label.config(text=f"📊 Всего таблиц: {len(tables)}")
        else:
            self.table_combobox['values'] = []
            self.info_label.config(text="❌ Нет таблиц в базе данных")
    
    def on_table_selected(self, event):
        """При выборе таблицы - загружаем её структуру и данные"""
        self.current_table = self.table_combobox.get()
        if not self.current_table:
            return
        
        # Загружаем структуру таблицы
        self.columns = DatabaseManager.get_table_schema(self.current_table)
        if not self.columns:
            messagebox.showerror("Ошибка", f"Не удалось загрузить структуру таблицы {self.current_table}")
            return
        
        # Очищаем основную область и создаём интерфейс для текущей таблицы
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.create_table_interface()
        self.refresh_table()
        
        self.info_label.config(text=f"📋 Текущая таблица: {self.current_table} (столбцов: {len(self.columns)})")
    
    def create_table_interface(self):
        """Создание интерфейса для текущей таблицы"""
        # === Панель фильтрации и поиска ===
        filter_frame = tk.LabelFrame(self.main_frame, text="🔍 Фильтрация и поиск", 
                                     font=("Arial", 10, "bold"))
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Поиск:").pack(side=tk.LEFT, padx=5, pady=5)
        self.search_entry = tk.Entry(filter_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(filter_frame, text="🔍 Найти", command=self.search_records,
                 bg="#2196F3", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(filter_frame, text="📋 Показать всё", command=self.refresh_table,
                 bg="#FF9800", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=5, pady=5)
        
        # === Поля ввода для CRUD операций ===
        input_frame = tk.LabelFrame(self.main_frame, text="📝 Работа с записями",
                                   font=("Arial", 10, "bold"))
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.entries = {}
        
        # Разбиваем поля на строки (по 3-4 поля в строке)
        row_num = 0
        col_num = 0
        max_cols = 3
        
        for col in self.columns:
            # Пропускаем автоинкрементные поля
            if col.get('auto_increment'):
                continue
            
            # Создаём контейнер для поля
            field_frame = tk.Frame(input_frame)
            field_frame.grid(row=row_num, column=col_num, padx=10, pady=5, sticky="w")
            
            # Метка поля
            label_text = col['label']
            if col.get('required'):
                label_text += " *"
            
            label = tk.Label(field_frame, text=label_text, font=("Arial", 9))
            label.pack(anchor="w")
            
            # Поле ввода
            entry = tk.Entry(field_frame, width=25)
            entry.pack(pady=2)
            self.entries[col['name']] = entry
            
            col_num += 1
            if col_num >= max_cols:
                col_num = 0
                row_num += 1
        
        # Рамка с кнопками действий
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        buttons = [
            ("➕ Добавить", self.add_record, "#4CAF50"),
            ("✏️ Обновить", self.update_record, "#FFC107"),
            ("🗑️ Удалить", self.delete_record, "#F44336"),
            ("🧹 Очистить", self.clear_entries, "#9E9E9E"),
            ("📤 Экспорт в CSV", self.export_to_csv, "#00BCD4"),
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command,
                          bg=color, fg="white", font=("Arial", 9, "bold"),
                          cursor="hand2", width=15)
            btn.grid(row=0, column=i, padx=5, pady=5)
        
        # === Таблица данных ===
        tree_frame = tk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Скроллбары
        scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns_display = [col['name'] for col in self.columns]
        self.tree = ttk.Treeview(tree_frame, columns=columns_display, show="headings",
                                yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Настройка заголовков и ширины колонок
        for col in self.columns:
            self.tree.heading(col['name'], text=col['label'])
            # Автоматическая ширина в зависимости от длины названия
            width = max(100, min(200, len(col['label']) * 15))
            self.tree.column(col['name'], width=width, anchor="w" if col['type'] in ['varchar', 'text', 'char'] else "center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # Статус бар
        self.status_bar = tk.Label(self.main_frame, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
    
    def refresh_table(self):
        """Обновить данные в таблице"""
        if not self.current_table or not self.tree:
            return
        
        # Очищаем текущие данные
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        columns_names = [col['name'] for col in self.columns]
        query = f"SELECT {', '.join([f'`{name}`' for name in columns_names])} FROM `{self.current_table}`"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert("", tk.END, values=row)
            
            self.status_bar.config(text=f"✅ Загружено записей: {len(rows)}")
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            self.status_bar.config(text=f"❌ Ошибка: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def search_records(self):
        """Поиск записей по ключевому слову"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.refresh_table()
            return
        
        if not self.current_table or not self.tree:
            return
        
        # Очищаем таблицу
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Ищем по всем текстовым полям
        text_columns = [col['name'] for col in self.columns 
                       if 'varchar' in col.get('type', '') or 'text' in col.get('type', '')]
        
        if not text_columns:
            messagebox.showinfo("Инфо", "Нет текстовых полей для поиска")
            self.refresh_table()
            return
        
        conditions = " OR ".join([f"`{col}` LIKE %s" for col in text_columns])
        query = f"SELECT * FROM `{self.current_table}` WHERE {conditions}"
        
        try:
            params = tuple([f"%{keyword}%"] * len(text_columns))
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                self.tree.insert("", tk.END, values=row)
            
            self.status_bar.config(text=f"🔍 Найдено записей: {len(rows)}")
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def on_select(self, event):
        """При выборе строки заполняем поля ввода"""
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected[0])['values']
        
        # Заполняем поля ввода
        col_index = 0
        for col in self.columns:
            col_name = col['name']
            if col_name in self.entries:
                self.entries[col_name].delete(0, tk.END)
                if col_index < len(values) and values[col_index] is not None:
                    self.entries[col_name].insert(0, str(values[col_index]))
            col_index += 1
        
        self.status_bar.config(text=f"✏️ Выбрана запись для редактирования")
    
    def get_pk_name(self):
        """Вернуть имя первичного ключа"""
        for col in self.columns:
            if col.get('pk'):
                return col['name']
        return None
    
    def get_pk_value_from_selection(self):
        """Получить значение первичного ключа из выбранной строки"""
        selected = self.tree.selection()
        if not selected:
            return None
        
        pk_name = self.get_pk_name()
        if not pk_name:
            return None
        
        values = self.tree.item(selected[0])['values']
        pk_index = [col['name'] for col in self.columns].index(pk_name)
        return values[pk_index]
    
    def add_record(self):
        """Добавить новую запись"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Выберите таблицу")
            return
        
        # Собираем значения
        values = {}
        for col_name, entry in self.entries.items():
            values[col_name] = entry.get().strip()
        
        # Проверяем обязательные поля
        for col in self.columns:
            col_name = col['name']
            if col.get('required') and col_name in self.entries and not values[col_name]:
                messagebox.showwarning("Ошибка", f"Поле '{col['label']}' обязательно для заполнения")
                return
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        columns_names = list(values.keys())
        placeholders = ", ".join(["%s"] * len(columns_names))
        query = f"INSERT INTO `{self.current_table}` (`{'`, `'.join(columns_names)}`) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, list(values.values()))
            conn.commit()
            messagebox.showinfo("Успех", "Запись добавлена")
            self.clear_entries()
            self.refresh_table()
            self.status_bar.config(text="✅ Запись успешно добавлена")
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
            self.status_bar.config(text=f"❌ Ошибка: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def update_record(self):
        """Обновить выбранную запись"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Выберите таблицу")
            return
        
        pk_value = self.get_pk_value_from_selection()
        if not pk_value:
            messagebox.showwarning("Предупреждение", "Выберите запись для обновления")
            return
        
        # Собираем новые значения
        new_values = {}
        for col_name, entry in self.entries.items():
            new_values[col_name] = entry.get().strip()
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        pk_name = self.get_pk_name()
        set_clause = ", ".join([f"`{col}` = %s" for col in new_values.keys()])
        query = f"UPDATE `{self.current_table}` SET {set_clause} WHERE `{pk_name}` = %s"
        
        try:
            params = list(new_values.values()) + [pk_value]
            cursor.execute(query, params)
            conn.commit()
            messagebox.showinfo("Успех", "Запись обновлена")
            self.refresh_table()
            self.status_bar.config(text="✅ Запись успешно обновлена")
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
            self.status_bar.config(text=f"❌ Ошибка: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def delete_record(self):
        """Удалить выбранную запись"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Выберите таблицу")
            return
        
        pk_value = self.get_pk_value_from_selection()
        if not pk_value:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить запись?"):
            return
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        pk_name = self.get_pk_name()
        query = f"DELETE FROM `{self.current_table}` WHERE `{pk_name}` = %s"
        
        try:
            cursor.execute(query, (pk_value,))
            conn.commit()
            messagebox.showinfo("Успех", "Запись удалена")
            self.clear_entries()
            self.refresh_table()
            self.status_bar.config(text="🗑️ Запись успешно удалена")
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
            self.status_bar.config(text=f"❌ Ошибка: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def clear_entries(self):
        """Очистить поля ввода"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.status_bar.config(text="🧹 Поля ввода очищены")
    
    def export_to_csv(self):
        """Экспорт данных в CSV файл"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Выберите таблицу")
            return
        
        import csv
        from datetime import datetime
        
        filename = f"{self.current_table}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        conn = DatabaseManager.connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        columns_names = [col['name'] for col in self.columns]
        query = f"SELECT {', '.join([f'`{name}`' for name in columns_names])} FROM `{self.current_table}`"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Заголовки
                writer.writerow([col['label'] for col in self.columns])
                # Данные
                writer.writerows(rows)
            
            messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            self.status_bar.config(text=f"📁 Экспортировано в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.status_bar.config(text=f"❌ Ошибка экспорта: {e}")
        finally:
            cursor.close()
            conn.close()

# ======================== ЗАПУСК ========================
def main():
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()