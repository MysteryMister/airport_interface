from random import gauss, randint
import time

from tkinter import (
    IntVar,
    StringVar,
    PhotoImage,
    Tk,
    Toplevel,
    ttk,
)
from tkinter import (
    BOTTOM,
    CENTER,
    END,
    LEFT,
    N,
    NS,
    NSEW,
    S,
    SOLID,
    VERTICAL,
)

from models import Airport, PlaneTypes, Request, Schedule


class PlaneTypesWindow(Toplevel):
    """Окно добавления типов самолетов."""

    def __init__(self, plane_types):
        super().__init__()

        # конфигурация окна
        self.title("Добавить типы самолетов")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", lambda: self.dismiss())
        self.rowconfigure(index=0, weight=3)
        self.rowconfigure(index=1, weight=1)
        self.rowconfigure(index=2, weight=1)
        self.rowconfigure(index=3, weight=1)
        for i in range(3):
            self.columnconfigure(index=i, weight=1)

        # переменные
        self.error_label = None
        self.plane_types = plane_types
        self.plane_type_var = StringVar(value="cargo")
        self.takeoff_time_var = IntVar(value=1)
        self.landing_time_var = IntVar(value=15)

        # определение элементов окна
        self.plane_types_table = ttk.Treeview(
            self,
            columns=("type", "takeoff", "landing"),
            show="headings",
        )
        self.plane_types_table.heading("type", text="тип самолета")
        self.plane_types_table.heading(
            "takeoff",
            text="время взлета (в минутах)",
        )
        self.plane_types_table.heading(
            "landing",
            text="время посадки (в минутах)",
        )
        self.plane_types_table.column("#1", stretch=True, anchor=CENTER)
        self.plane_types_table.column("#2", stretch=True, anchor=CENTER)
        self.plane_types_table.column("#3", stretch=True, anchor=CENTER)
        data = self.plane_types.get_plane_types()
        for plane_type in data:
            element = (plane_type, data[plane_type][0], data[plane_type][1])
            self.plane_types_table.insert("", END, values=element)
        self.table_scrollbar = ttk.Scrollbar(
            self,
            orient=VERTICAL,
            command=self.plane_types_table.yview,
        )
        self.plane_types_table.configure(
            yscrollcommand=self.table_scrollbar.set,
        )
        self.table_scrollbar.grid(row=0, column=3, sticky=NS)
        self.plane_types_table.grid(row=0, column=0, columnspan=3, sticky=NSEW)

        self.plane_type_entry = ttk.Entry(
            self,
            textvariable=self.plane_type_var,
            justify=CENTER,
        )
        self.plane_type_entry.grid(row=1, column=0)
        self.takeoff_time_spinbox = ttk.Spinbox(
            self,
            from_=1.0,
            to=15.0,
            state="readonly",
            textvariable=self.takeoff_time_var,
            justify=CENTER,
        )
        self.takeoff_time_spinbox.grid(row=1, column=1)
        self.landing_time_spinbox = ttk.Spinbox(
            self,
            from_=1.0,
            to=15.0,
            state="readonly",
            textvariable=self.landing_time_var,
            justify=CENTER,
        )
        self.landing_time_spinbox.grid(row=1, column=2)
        self.add_type_button = ttk.Button(
            self,
            text="ДОБАВИТЬ",
            command=lambda: self.add_plane_type(),
        )
        self.add_type_button.grid(row=3, column=0, ipadx=10, ipady=10)
        self.default_button = ttk.Button(
            self,
            text="ДЕФОЛТНЫЕ НАСТРОЙКИ",
            command=lambda: self.apply_default_settings(),
        )
        self.default_button.grid(row=3, column=1, ipadx=10, ipady=10)
        self.exit_button = ttk.Button(
            self,
            text="ВЫХОД",
            command=lambda: self.dismiss(),
        )
        self.exit_button.grid(row=3, column=2, ipadx=10, ipady=10)

        # захват ввода
        self.grab_set()

    def add_plane_type(self):
        """Добавляет введенные данные в базу данных."""
        # проверка корректности ввода
        plane_type = self.plane_type_var.get().strip()
        if plane_type == "":
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self,
                foreground="#B71C1C",
                font=('', 12),
                text="Недопустимое имя типа самолета!"
            )
            self.error_label.grid(row=2, column=0, columnspan=3)
            return
        if self.plane_types.is_existing_type(plane_type):
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self,
                foreground="#B71C1C",
                font=('', 12),
                text="Такой тип самолета уже существует!",
            )
            self.error_label.grid(row=2, column=0, columnspan=3)
            return
        takeoff_time = self.takeoff_time_var.get()
        landing_time = self.landing_time_var.get()

        # добавляем данные
        element = (plane_type, takeoff_time, landing_time)
        self.plane_types.add_type(*element)
        self.plane_types_table.insert("", END, values=element)

        # очищаем сообщение об ошибке, если нужно
        if self.error_label:
            self.error_label.destroy()
            self.error_label = None

    def apply_default_settings(self):
        """Заполняет базу данных дефолтными данными."""
        # удаляем старое наполнение базы данных
        for child in self.plane_types_table.get_children():
            self.plane_types_table.delete(child)

        # заполняем дефолтными значениями
        self.plane_types.use_default_settings()
        data = self.plane_types.get_plane_types()
        for plane_type in data:
            element = (plane_type, data[plane_type][0], data[plane_type][1])
            self.plane_types_table.insert("", END, values=element)

        # очищаем сообщение об ошибке, если нужно
        if self.error_label:
            self.error_label.destroy()
            self.error_label = None

    def dismiss(self):
        """Закрытие окна с освобождением ввода."""
        self.grab_release()
        self.destroy()


class ScheduleWindow(Toplevel):
    """Окно добавления расписания."""

    def __init__(self, flight_schedule, plane_types, start_time):
        super().__init__()

        # конфигурация окна
        self.title("Добавить расписание")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", lambda: self.dismiss())
        self.rowconfigure(index=0, weight=3)
        self.rowconfigure(index=1, weight=1)
        self.rowconfigure(index=2, weight=1)
        self.rowconfigure(index=3, weight=1)
        for i in range(3):
            self.columnconfigure(index=i, weight=1)

        # переменные
        self.error_label = None
        self.flight_schedule = flight_schedule
        self.plane_types = plane_types
        self.start_time = start_time
        self.plane_type_var = StringVar()
        self.flight_type_var = StringVar(value="взлет")
        self.expected_time_var = StringVar(value="00:00")

        # определение элементов окна
        self.schedule_table = ttk.Treeview(
            self,
            columns=("plane_type", "flight_type", "time"),
            show="headings",
        )
        self.schedule_table.heading("plane_type", text="тип самолета")
        self.schedule_table.heading(
            "flight_type",
            text="тип заявки (взлет/посадка)",
        )
        self.schedule_table.heading("time", text="ожидаемое время")
        self.schedule_table.column("#1", stretch=True, anchor=CENTER)
        self.schedule_table.column("#2", stretch=True, anchor=CENTER)
        self.schedule_table.column("#3", stretch=True, anchor=CENTER)
        plane_type_names = list(self.plane_types.get_plane_types().keys())
        initial_data = self.flight_schedule.get_schedule()
        # присутствуют лишние типы самолетов -> стираем старое расписание
        for flight in initial_data:
            if flight[0] not in plane_type_names:
                self.flight_schedule.clear_schedule()
                break
        self.flight_schedule.sort_schedule(self.start_time)
        data = self.flight_schedule.get_schedule()
        for flight in data:
            time_str_value = f'{flight[-1][0]}:{flight[-1][1]}'
            element = (flight[0], flight[1], time_str_value)
            self.schedule_table.insert("", END, values=element)
        self.table_scrollbar = ttk.Scrollbar(
            self,
            orient=VERTICAL,
            command=self.schedule_table.yview,
        )
        self.schedule_table.configure(yscrollcommand=self.table_scrollbar.set)
        self.table_scrollbar.grid(row=0, column=3, sticky=NS)
        self.schedule_table.grid(row=0, column=0, columnspan=3, sticky=NSEW)

        self.plane_type_combobox = ttk.Combobox(
            self,
            state="readonly",
            textvariable=self.plane_type_var,
            values=plane_type_names,
            justify=CENTER,
        )
        if plane_type_names:
            self.plane_type_combobox.current(0)
        self.plane_type_combobox.grid(row=1, column=0)
        self.flight_type_spinbox = ttk.Spinbox(
            self,
            values=["взлет", "посадка"],
            state="readonly",
            textvariable=self.flight_type_var,
            justify=CENTER,
        )
        self.flight_type_spinbox.grid(row=1, column=1)
        self.expected_time_entry = ttk.Entry(
            self,
            textvariable=self.expected_time_var,
            justify=CENTER,
        )
        self.expected_time_entry.grid(row=1, column=2)
        self.add_flight_button = ttk.Button(
            self,
            text="ДОБАВИТЬ",
            command=lambda: self.add_flight(),
        )
        self.add_flight_button.grid(row=3, column=0, ipadx=10, ipady=10)
        self.default_button = ttk.Button(
            self,
            text="ДЕФОЛТНЫЕ НАСТРОЙКИ",
            command=lambda: self.apply_default_settings(),
        )
        self.default_button.grid(row=3, column=1, ipadx=10, ipady=10)
        self.exit_button = ttk.Button(
            self,
            text="ВЫХОД",
            command=lambda: self.dismiss(),
        )
        self.exit_button.grid(row=3, column=2, ipadx=10, ipady=10)

        # захват ввода
        self.grab_set()

    def add_flight(self):
        """Добавляет рейс в базу данных."""
        # проверка корректности ввода
        plane_type = self.plane_type_var.get()
        if not self.plane_types.get_plane_types():
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self,
                foreground="#B71C1C",
                font=('', 12),
                text="Отсутствуют типы самолетов!",
            )
            self.error_label.grid(row=2, column=0, columnspan=3)
            return
        request_type = self.flight_type_var.get()
        expected_time = self.expected_time_var.get()
        try:
            time.strptime(expected_time, '%H:%M')
        except ValueError:
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self,
                foreground="#B71C1C",
                font=('', 12),
                text="Некорректный формат времени!",
            )
            self.error_label.grid(row=2, column=0, columnspan=3)
            return

        # добавляем данные
        self.flight_schedule.add_flight(
            plane_type,
            request_type,
            expected_time,
        )
        self.flight_schedule.sort_schedule(self.start_time)
        for child in self.schedule_table.get_children():
            self.schedule_table.delete(child)
        for flight in self.flight_schedule.get_schedule():
            parsed_time_str_value = f'{flight[-1][0]}:{flight[-1][1]}'
            element = (flight[0], flight[1], parsed_time_str_value)
            self.schedule_table.insert("", END, values=element)

        # очищаем сообщение об ошибке, если нужно
        if self.error_label:
            self.error_label.destroy()
            self.error_label = None

    def apply_default_settings(self):
        """Заполняет базу данных дефолтными данными."""
        # заполняем дефолтными значениями
        self.flight_schedule.use_default_settings(self.plane_types)
        is_default_applied = self.flight_schedule.is_default_used()
        if not is_default_applied:
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self,
                foreground="#B71C1C",
                font=('', 12),
                text="Не включены дефолтные типы самолетов!",
            )
            self.error_label.grid(row=2, column=0, columnspan=3)
            return
        self.flight_schedule.sort_schedule(self.start_time)

        # заменяем старое наполнение базы данных
        for child in self.schedule_table.get_children():
            self.schedule_table.delete(child)
        data = self.flight_schedule.get_schedule()
        for flight in data:
            parsed_time_str_value = f'{flight[-1][0]}:{flight[-1][1]}'
            element = (flight[0], flight[1], parsed_time_str_value)
            self.schedule_table.insert("", END, values=element)

        # очищаем сообщение об ошибке, если нужно
        if self.error_label:
            self.error_label.destroy()
            self.error_label = None

    def dismiss(self):
        """Закрытие окна с освобождением ввода."""
        self.grab_release()
        self.destroy()


class Dispatcher:
    """Система-диспетчер."""

    def __init__(self):
        # параметры модели
        # ----------------
        # прошедшее время в минутах
        self.current_time = None
        # время начала моделирования
        self.start_time = None
        # аэропорт
        self.airport = None
        # расписание полетов
        self.flight_schedule = Schedule()
        # время полетов с учетом отклонений
        self.true_flight_time_list = []
        # кол-во прошедших шагов
        self.passed_time_ticks = 0
        # время взлета/посадки различных типов самолетов
        self.plane_preparation_time = PlaneTypes()
        # список всех заявок
        self.requests = []
        # кол-во взлетно-посадочных полос
        self.runway_count = None
        # интервал между последовательными рейсами на 1 полосе
        self.safety_time_gap = None
        # отклонение от расписания (min_variance, max_variance)
        self.schedule_variance = None
        # шаг моделирования
        self.time_tick = None

        # интерфейс
        # ------------
        # главное окно
        self.root = Tk()
        self.root.title("Система-диспетчер")
        self.root.geometry("1280x720")

        self.main_icon = PhotoImage(
            master=self.root,
            file='./images/airport.png',
        )
        self.root.iconphoto(False, self.main_icon)

        self.root.rowconfigure(index=0, weight=1)
        self.root.columnconfigure(index=0, weight=1)
        self.root.columnconfigure(index=1, weight=3)
        self.root.columnconfigure(index=2, weight=1)

        # вспомогательные окна
        self.plane_types_window = None
        self.schedule_window = None

        # переменные
        self.error_label = None

        self.runway_count_var = IntVar(value=2)
        self.min_variance_var = IntVar(value=0)
        self.max_variance_var = IntVar(value=120)
        self.model_step_var = IntVar(value=5)
        self.flight_gap_var = IntVar(value=1)
        self.start_time_var = StringVar(value="00:00")

        self.current_time_var = StringVar(value=self.start_time_var.get())
        self.cur_queue_takeoff_var = IntVar(value=0)
        self.cur_queue_landing_var = IntVar(value=0)
        self.cur_runway_status_var = [StringVar(value='О')] * 10
        self.finished_flights_var = []

        self.total_requests_var = IntVar(value=0)
        self.max_delay_var = IntVar(value=0)
        self.avg_delay_var = IntVar(value=0)
        self.max_queue_takeoff_var = IntVar(value=0)
        self.max_queue_landing_var = IntVar(value=0)
        self.avg_queue_takeoff_var = IntVar(value=0)
        self.avg_queue_landing_var = IntVar(value=0)
        self.avg_runway_occupancy_var = [(i, 'NaN') for i in range(10)]

        # фрейм ввода параметров
        self.parameters_frame = ttk.Frame(
            self.root,
            borderwidth=1,
            relief=SOLID,
            padding=10,
        )

        self.parameters_title_label = ttk.Label(
            self.parameters_frame,
            text="Параметры:",
            font=('', 14),
        )
        self.parameters_title_label.pack(anchor=N)
        self.runway_count_label = ttk.Label(
            self.parameters_frame,
            text="количество взлетно-посадочных полос",
        )
        self.runway_count_label.pack(anchor=N, pady=10)
        self.runway_count_spinbox = ttk.Spinbox(
            self.parameters_frame,
            from_=2.0,
            to=10.0,
            state="readonly",
            textvariable=self.runway_count_var,
            justify=CENTER,
        )
        self.runway_count_spinbox.pack(anchor=N)
        self.schedule_variance_label = ttk.Label(
            self.parameters_frame,
            text="отклонение от расписания (в минутах)",
        )
        self.schedule_variance_label.pack(anchor=N, pady=10)

        self.parameters_subframe_1 = ttk.Frame(
            self.parameters_frame,
            borderwidth=0,
        )
        self.min_variance_spinbox = ttk.Spinbox(
            self.parameters_subframe_1,
            from_=0.0,
            to=120.0,
            state="readonly",
            increment=5.0,
            textvariable=self.min_variance_var,
            justify=CENTER,
        )
        self.min_variance_spinbox.pack(
            anchor=N,
            side=LEFT,
            expand=True,
            padx=5,
        )
        self.min_variance_label = ttk.Label(
            self.parameters_subframe_1,
            text="min",
        )
        self.min_variance_label.pack(anchor=N, side=LEFT, expand=True, padx=5)
        self.max_variance_spinbox = ttk.Spinbox(
            self.parameters_subframe_1,
            from_=0.0,
            to=120.0,
            state="readonly",
            increment=5.0,
            textvariable=self.max_variance_var,
            justify=CENTER,
        )
        self.max_variance_spinbox.pack(
            anchor=N,
            side=LEFT,
            expand=True,
            padx=5,
        )
        self.max_variance_label = ttk.Label(
            self.parameters_subframe_1,
            text="max",
        )
        self.max_variance_label.pack(anchor=N, side=LEFT, expand=True, padx=5)
        self.parameters_subframe_1.pack(anchor=N)

        self.model_step_label = ttk.Label(
            self.parameters_frame,
            text="шаг моделирования (в минутах)",
        )
        self.model_step_label.pack(anchor=N, pady=10)
        self.model_step_spinbox = ttk.Spinbox(
            self.parameters_frame,
            from_=5.0,
            to=30.0,
            state="readonly",
            textvariable=self.model_step_var,
            justify=CENTER,
        )
        self.model_step_spinbox.pack(anchor=N)
        self.flight_gap_label = ttk.Label(
            self.parameters_frame,
            text="интервал между рейсами на 1 полосе (в минутах)",
        )
        self.flight_gap_label.pack(anchor=N, pady=10)
        self.flight_gap_spinbox = ttk.Spinbox(
            self.parameters_frame,
            from_=1.0,
            to=10.0,
            state="readonly",
            textvariable=self.flight_gap_var,
            justify=CENTER,
        )
        self.flight_gap_spinbox.pack(anchor=N)
        self.start_time_label = ttk.Label(
            self.parameters_frame,
            text="начало работы (формат чч:мм, без пробелов)",
        )
        self.start_time_label.pack(anchor=N, pady=10)
        self.start_time_entry = ttk.Entry(
            self.parameters_frame,
            textvariable=self.start_time_var,
            justify=CENTER,
        )
        self.start_time_entry.pack(anchor=N)
        self.add_plane_button = ttk.Button(
            self.parameters_frame,
            text="добавить типы самолетов",
            command=lambda: self.create_plane_types_window(),
        )
        self.add_plane_button.pack(anchor=N, pady=40, ipadx=10, ipady=10)
        self.add_schedule_button = ttk.Button(
            self.parameters_frame,
            text="добавить суточное расписание",
            command=lambda: self.create_schedule_window(),
        )
        self.add_schedule_button.pack(anchor=N, ipadx=10, ipady=10)
        self.begin_refresh_button = ttk.Button(
            self.parameters_frame,
            text="НАЧАТЬ",
            command=lambda: self.start_modeling(),
        )
        self.begin_refresh_button.pack(
            anchor=N, side=BOTTOM, pady=20, ipadx=10, ipady=10
        )

        self.parameters_frame.grid(row=0, column=0, sticky=NSEW)

        # фрейм моделирования
        self.model_frame = ttk.Frame(
            self.root,
            borderwidth=1,
            relief=SOLID,
            padding=10,
        )

        self.model_title_label = ttk.Label(
            self.model_frame,
            text="Моделирование процесса:",
            font=('', 14),
        )
        self.model_title_label.pack(anchor=N)
        self.current_time_label = ttk.Label(
            self.model_frame,
            textvariable=self.current_time_var,
        )
        self.current_time_label.pack(anchor=N, pady=10)
        self.cur_queue_label = ttk.Label(
            self.model_frame,
            text="очереди: взлет/посадка",
        )
        self.cur_queue_label.pack(anchor=N)
        self.cur_queue_takeoff_label = ttk.Label(
            self.model_frame,
            textvariable=self.cur_queue_takeoff_var,
        )
        self.cur_queue_takeoff_label.pack(anchor=N)
        self.cur_queue_landing_label = ttk.Label(
            self.model_frame,
            textvariable=self.cur_queue_landing_var,
        )
        self.cur_queue_landing_label.pack(anchor=N)
        self.flight_schedule_label = ttk.Label(
            self.model_frame,
            text="график полетов:",
        )
        self.flight_schedule_label.pack(anchor=N, pady=10)

        self.model_subframe_1 = ttk.Frame(self.model_frame, borderwidth=0)
        for i in range(3):
            self.model_subframe_1.columnconfigure(index=i, weight=1)
        self.flight_schedule_table = ttk.Treeview(
            self.model_subframe_1,
            columns=("time", "runway_id", "request_type"),
            show="headings",
        )
        self.flight_schedule_table.heading("time", text="время")
        self.flight_schedule_table.heading("runway_id", text="ID полосы")
        self.flight_schedule_table.heading("request_type", text="тип заявки")
        self.flight_schedule_table.column("#1", stretch=True, anchor=CENTER)
        self.flight_schedule_table.column("#2", stretch=True, anchor=CENTER)
        self.flight_schedule_table.column("#3", stretch=True, anchor=CENTER)
        self.flight_schedule_table_scrollbar = ttk.Scrollbar(
            self.model_subframe_1,
            orient=VERTICAL,
            command=self.flight_schedule_table.yview,
        )
        self.flight_schedule_table.configure(
            yscrollcommand=self.flight_schedule_table_scrollbar.set,
        )
        self.flight_schedule_table_scrollbar.grid(row=0, column=3, sticky=NS)
        self.flight_schedule_table.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky=NSEW,
        )
        self.model_subframe_1.pack(anchor=N)

        self.cur_runway_occupancy_label = ttk.Label(
            self.model_frame,
            text="состояние полос (З-занята, С-свободна, О-отключена):",
        )
        self.cur_runway_occupancy_label.pack(anchor=N, pady=10)

        self.model_subframe_2 = ttk.Frame(self.model_frame, borderwidth=0)
        self.model_subframe_2.columnconfigure(index=0, weight=2)
        for i in range(1, 11):
            self.model_subframe_2.columnconfigure(index=i, weight=1)
        self.runway_id_label = ttk.Label(
            self.model_subframe_2,
            text="ID полосы:",
        )
        self.runway_id_label.grid(row=0, column=0)
        self.runway_status_label = ttk.Label(
            self.model_subframe_2,
            text="статус:",
        )
        self.runway_status_label.grid(row=1, column=0)
        for i in range(len(self.cur_runway_status_var)):
            tmp_label_1 = ttk.Label(self.model_subframe_2, text=f"{i}")
            tmp_label_1.grid(row=0, column=i + 1, ipadx=5, ipady=5)
        self.runway_label_0 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[0],
        )
        self.runway_label_0.grid(row=1, column=1, ipadx=5, ipady=5)
        self.runway_label_1 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[1],
        )
        self.runway_label_1.grid(row=1, column=2, ipadx=5, ipady=5)
        self.runway_label_2 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[2],
        )
        self.runway_label_2.grid(row=1, column=3, ipadx=5, ipady=5)
        self.runway_label_3 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[3],
        )
        self.runway_label_3.grid(row=1, column=4, ipadx=5, ipady=5)
        self.runway_label_4 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[4],
        )
        self.runway_label_4.grid(row=1, column=5, ipadx=5, ipady=5)
        self.runway_label_5 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[5],
        )
        self.runway_label_5.grid(row=1, column=6, ipadx=5, ipady=5)
        self.runway_label_6 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[6],
        )
        self.runway_label_6.grid(row=1, column=7, ipadx=5, ipady=5)
        self.runway_label_7 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[7],
        )
        self.runway_label_7.grid(row=1, column=8, ipadx=5, ipady=5)
        self.runway_label_8 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[8],
        )
        self.runway_label_8.grid(row=1, column=9, ipadx=5, ipady=5)
        self.runway_label_9 = ttk.Label(
            self.model_subframe_2,
            textvariable=self.cur_runway_status_var[9],
        )
        self.runway_label_9.grid(row=1, column=10, ipadx=5, ipady=5)
        self.model_subframe_2.pack(anchor=N)

        self.make_step_button = ttk.Button(
            self.model_frame,
            text="ШАГ",
            state=["disabled"],
            command=lambda: self.time_step(),
        )
        self.make_step_button.pack(
            anchor=S,
            side=LEFT,
            expand=True,
            pady=20,
            ipadx=10,
            ipady=10,
        )
        self.finish_model_button = ttk.Button(
            self.model_frame,
            text="ДО КОНЦА",
            state=["disabled"],
            command=lambda: self.finish_simulation(),
        )
        self.finish_model_button.pack(
            anchor=S,
            side=LEFT,
            expand=True,
            pady=20,
            ipadx=10,
            ipady=10,
        )

        self.model_frame.grid(row=0, column=1, sticky=NSEW)

        # фрейм статистики
        self.statistics_frame = ttk.Frame(
            self.root,
            borderwidth=1,
            relief=SOLID,
            padding=10,
        )

        self.statistics_title_label = ttk.Label(
            self.statistics_frame,
            text="Статистика:",
            font=('', 14),
        )
        self.statistics_title_label.pack(anchor=N)
        self.total_requests_label = ttk.Label(
            self.statistics_frame,
            text="обслужено заявок: шт.",
        )
        self.total_requests_label.pack(anchor=N)
        self.total_requests_label_1 = ttk.Label(
            self.statistics_frame,
            textvariable=self.total_requests_var,
        )
        self.total_requests_label_1.pack(anchor=N)
        self.max_delay_label = ttk.Label(
            self.statistics_frame,
            text="максимальная задержка: мин.",
        )
        self.max_delay_label.pack(anchor=N)
        self.max_delay_label_1 = ttk.Label(
            self.statistics_frame,
            textvariable=self.max_delay_var,
        )
        self.max_delay_label_1.pack(anchor=N)
        self.avg_delay_label = ttk.Label(
            self.statistics_frame,
            text="средняя задержка: мин.",
        )
        self.avg_delay_label.pack(anchor=N)
        self.avg_delay_label_1 = ttk.Label(
            self.statistics_frame,
            textvariable=self.avg_delay_var,
        )
        self.avg_delay_label_1.pack(anchor=N)
        self.max_queue_label = ttk.Label(
            self.statistics_frame,
            text="максимальная длина очереди: взлет/посадка",
        )
        self.max_queue_label.pack(anchor=N)
        self.max_queue_takeoff_label = ttk.Label(
            self.statistics_frame,
            textvariable=self.max_queue_takeoff_var,
        )
        self.max_queue_takeoff_label.pack(anchor=N)
        self.max_queue_landing_label = ttk.Label(
            self.statistics_frame,
            textvariable=self.max_queue_landing_var,
        )
        self.max_queue_landing_label.pack(anchor=N)
        self.avg_queue_label = ttk.Label(
            self.statistics_frame,
            text="средняя длина очереди: взлет/посадка",
        )
        self.avg_queue_label.pack(anchor=N)
        self.avg_queue_takeoff_label = ttk.Label(
            self.statistics_frame,
            textvariable=self.avg_queue_takeoff_var,
        )
        self.avg_queue_takeoff_label.pack(anchor=N)
        self.avg_queue_landing_label = ttk.Label(
            self.statistics_frame,
            textvariable=self.avg_queue_landing_var,
        )
        self.avg_queue_landing_label.pack(anchor=N)
        self.avg_runway_occupancy_label = ttk.Label(
            self.statistics_frame,
            text="средняя занятость полос (доля времени):",
        )
        self.avg_runway_occupancy_label.pack(anchor=N)
        self.avg_runway_occupancy_table = ttk.Treeview(
            self.statistics_frame,
            columns=("runway_id", "occupancy"),
            show="headings",
        )
        self.avg_runway_occupancy_table.heading("runway_id", text="ID полосы")
        self.avg_runway_occupancy_table.heading("occupancy", text="занятость")
        self.avg_runway_occupancy_table.column(
            "#1",
            stretch=True,
            width=100,
            anchor=CENTER,
        )
        self.avg_runway_occupancy_table.column(
            "#2",
            stretch=True,
            width=100,
            anchor=CENTER,
        )
        self.avg_runway_occupancy_table.pack(anchor=N)
        for runway in self.avg_runway_occupancy_var:
            self.avg_runway_occupancy_table.insert("", END, values=runway)
        self.exit_button = ttk.Button(
            self.statistics_frame,
            text="ВЫХОД",
            command=lambda: self.dismiss(),
        )
        self.exit_button.pack(
            anchor=N,
            side=BOTTOM,
            pady=20,
            ipadx=10,
            ipady=10,
        )

        self.statistics_frame.grid(row=0, column=2, sticky=NSEW)

        self.root.mainloop()

    def create_plane_types_window(self):
        """Создание окна-формы с типами самолетов."""
        self.plane_types_window = PlaneTypesWindow(self.plane_preparation_time)

    def create_schedule_window(self):
        """Создание окна-формы с расписанием."""
        try:
            start_time_value = time.strptime(
                self.start_time_var.get(),
                '%H:%M',
            )
        except ValueError:
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None
            self.error_label = ttk.Label(
                self.parameters_frame,
                foreground="#B71C1C",
                font=('', 12),
                text="Некорректный формат времени старта!",
            )
            self.error_label.pack(anchor=N, pady=20)
            return
        parsed_time = (start_time_value.tm_hour, start_time_value.tm_min)

        # очищаем сообщение об ошибке, если нужно
        if self.error_label:
            self.error_label.destroy()
            self.error_label = None
        self.schedule_window = ScheduleWindow(
            self.flight_schedule,
            self.plane_preparation_time,
            parsed_time,
        )

    def time_step(self):
        """Шаг работы диспетчера."""
        if self.current_time >= 24 * 60:
            return
        self.time_tick = self.model_step_var.get()
        self.current_time += self.time_tick
        self.passed_time_ticks += 1

        pending_requests = self.generate_requests()
        self.airport.add_to_request_queue(pending_requests)
        self.requests.extend(pending_requests)
        self.airport.time_tick(self.time_tick)

        self.get_model_state()

    def finish_simulation(self):
        """Заканчивает моделирование, вычисляя все шаги сразу."""
        while self.current_time < 24 * 60:
            self.time_step()

    def dismiss(self):
        """Закрытие окна."""
        self.root.destroy()

    def start_modeling(self):
        """запускает/обновляет моделирование."""
        # начинаем моделирование процесса
        if self.begin_refresh_button['text'] == 'НАЧАТЬ':
            # проверка корректности ввода
            try:
                start_time = time.strptime(self.start_time_var.get(), '%H:%M')
            except ValueError:
                if self.error_label:
                    self.error_label.destroy()
                    self.error_label = None
                self.error_label = ttk.Label(
                    self.parameters_frame,
                    foreground="#B71C1C",
                    font=('', 12),
                    text="Некорректный формат времени старта!",
                )
                self.error_label.pack(anchor=N, pady=20)
                return
            if self.min_variance_var.get() > self.max_variance_var.get():
                if self.error_label:
                    self.error_label.destroy()
                    self.error_label = None
                self.error_label = ttk.Label(
                    self.parameters_frame,
                    foreground="#B71C1C",
                    font=('', 12),
                    text="Некорректный диапазон величины отклонения!",
                )
                self.error_label.pack(anchor=N, pady=20)
                return

            # установка значений параметров
            self.start_time = (start_time.tm_hour, start_time.tm_min)
            self.current_time = 0
            self.time_tick = self.model_step_var.get()
            self.schedule_variance = (
                self.min_variance_var.get(),
                self.max_variance_var.get(),
            )
            self.runway_count = self.runway_count_var.get()
            self.safety_time_gap = self.flight_gap_var.get()
            self.airport = Airport(
                self.plane_preparation_time,
                self.runway_count,
                self.safety_time_gap
            )

            # блокировка ввода и изменение интерфейса
            self.add_plane_button['state'] = 'disabled'
            self.add_schedule_button['state'] = 'disabled'
            self.make_step_button['state'] = 'normal'
            self.finish_model_button['state'] = 'normal'
            self.begin_refresh_button['text'] = 'ЗАНОВО'
            self.runway_count_spinbox['state'] = 'disabled'
            self.min_variance_spinbox['state'] = 'disabled'
            self.max_variance_spinbox['state'] = 'disabled'
            self.flight_gap_spinbox['state'] = 'disabled'
            self.start_time_entry['state'] = 'disabled'

            # очищаем сообщение об ошибке, если нужно
            if self.error_label:
                self.error_label.destroy()
                self.error_label = None

            # создание списка полетов с учетом отклонений
            self.create_true_schedule()

            # запуск моделирования
            self.time_step()
        # перезапускаем моделирование процесса
        elif self.begin_refresh_button['text'] == 'ЗАНОВО':
            ...

    def get_model_state(self):
        """Собирает информацию для вывода статистики работы модели."""
        current_time = (
            self.start_time[0] * 60 + self.start_time[1] + self.current_time
        )
        if current_time >= 24 * 60:
            current_time -= 24 * 60
        current_time = (current_time // 60, current_time % 60)
        self.current_time_var.set(f'{current_time[0]}:{current_time[1]}')

        cur_landing_queue, cur_takeoff_queue = (
            self.airport.get_current_queue_length()
        )
        self.cur_queue_takeoff_var.set(cur_takeoff_queue)
        self.cur_queue_landing_var.set(cur_landing_queue)

        max_landing_queue, max_takeoff_queue = self.airport.get_queue_stats()
        self.max_queue_landing_var.set(max_landing_queue)
        self.max_queue_takeoff_var.set(max_takeoff_queue)

        avg_landing_queue, avg_takeoff_queue = (
            self.airport.get_avg_queue_length(self.passed_time_ticks)
        )
        self.avg_queue_landing_var.set(avg_landing_queue)
        self.avg_queue_takeoff_var.set(avg_takeoff_queue)

        cur_runway_statuses = self.airport.get_runway_statuses()
        for i in range(len(cur_runway_statuses)):
            runway_status = cur_runway_statuses[i]
            if runway_status == 'free':
                self.cur_runway_status_var[i].set('С')
            elif runway_status == 'busy':
                self.cur_runway_status_var[i].set('З')

        completed_requests = 0
        takeoff_request_count = 0
        max_delay = 0
        total_delay = 0
        for request in self.requests:
            if request.get_status() == 'ok':
                completed_requests += 1
            if request.get_request_type() == 'взлет':
                takeoff_request_count += 1
                delay = request.get_time_delay()
                total_delay += delay
                if delay > max_delay:
                    max_delay = delay
        if takeoff_request_count == 0:
            avg_delay = 0
        else:
            avg_delay = total_delay / takeoff_request_count
        self.total_requests_var.set(completed_requests)
        self.max_delay_var.set(max_delay)
        self.avg_delay_var.set(avg_delay)

        runway_stats = self.airport.get_runway_occupancy_stats(
            self.current_time,
        )
        for i in range(len(runway_stats)):
            self.avg_runway_occupancy_var[i] = (i, runway_stats[i])
        for child in self.avg_runway_occupancy_table.get_children():
            self.avg_runway_occupancy_table.delete(child)
        for runway in self.avg_runway_occupancy_var:
            self.avg_runway_occupancy_table.insert("", END, values=runway)

        for child in self.flight_schedule_table.get_children():
            self.flight_schedule_table.delete(child)
        self.finished_flights_var = self.airport.get_finished_requests_info(
            self.start_time,
        )
        for flight in self.finished_flights_var:
            flight_val = (
                f'{flight[0][0]}:{flight[0][1]}',
                flight[1],
                flight[2],
            )
            self.flight_schedule_table.insert("", END, values=flight_val)

    def create_true_schedule(self):
        """Создает расписание с учетом отклонений."""
        distribution_radius = (
            (self.schedule_variance[1] - self.schedule_variance[0]) / 2
        )
        distribution_center = self.schedule_variance[1] - distribution_radius
        start_time = self.start_time[0] * 60 + self.start_time[1]

        schedule = self.flight_schedule.get_schedule()
        for flight in schedule:
            flight_time = flight[-1][0] * 60 + flight[-1][1] - start_time
            if flight_time < 0:
                flight_time += 24 * 60

            random_variance = round(
                gauss(
                    mu=0.0,
                    sigma=1.0,
                ) * distribution_radius / 3 + distribution_center
            )
            if random_variance > self.schedule_variance[1]:
                random_variance = self.schedule_variance[1]
            if random_variance < self.schedule_variance[0]:
                random_variance = self.schedule_variance[0]
            is_negative = randint(0, 1)
            if is_negative:
                random_variance *= (-1)
            if flight[1] == 'взлет':
                random_variance = abs(random_variance)

            flight_time += random_variance
            true_flight = (flight[0], flight[1], random_variance, flight_time)
            self.true_flight_time_list.append(true_flight)

        self.true_flight_time_list.sort(key=lambda flight: flight[-1])

    def generate_requests(self):
        """Генерация заявок."""
        pending_requests = []
        for i in range(len(self.true_flight_time_list)):
            flight = self.true_flight_time_list[i]
            waiting_time = self.current_time - flight[-1]
            if waiting_time < 0:
                self.true_flight_time_list = self.true_flight_time_list[i:]
                break
            new_request = Request(flight[0], flight[1], flight[2], flight[-1])
            new_request.update_waiting_time(waiting_time)
            pending_requests.append(new_request)
        return pending_requests
