import time


class Airport:
    """Аэропорт."""

    def __init__(self, plane_preparation_time, runway_count, safety_time_gap):
        # входные параметры
        # получены от агрегирующего класса (диспетчера)
        self.plane_preparation_time = plane_preparation_time
        self.safety_time_gap = safety_time_gap

        # взлетно-посадочные полосы == части целого (аэропорта)
        self.runways = []
        for i in range(runway_count):
            self.runways.append(Runway())
        # очередь заявок
        self.requests = []
        # кол-во новоприбывших заявок на одном шаге
        self.new_requests_count = 0

        # статистика работы аэропорта
        self.max_landing_queue = 0
        self.max_takeoff_queue = 0
        self.total_landing_queue = 0
        self.total_takeoff_queue = 0

    def time_tick(self, time_tick):
        """Шаг работы аэропорта."""
        # обновляем время ожидания старых заявок в очереди
        for i in range(len(self.requests) - self.new_requests_count):
            self.requests[i].update_waiting_time(time_tick)
        # шаг работы полос
        for runway in self.runways:
            runway.time_tick(time_tick, self.safety_time_gap)
        # распределяем заявки по полосам
        for runway in self.runways:
            if not self.requests:
                break
            current_request = self.requests[0]
            completion_time = self.get_request_completion_time(current_request)
            if runway.process_request(
                current_request,
                completion_time,
                self.safety_time_gap,
            ):
                self.requests.pop(0)
        # обновляем статистику по очередям
        self.update_max_queue_length()
        self.update_total_queue_length()

    def get_runway_statuses(self):
        """Возвращает состояние всех полос."""
        statuses = []
        for runway in self.runways:
            statuses.append(runway.get_status())
        return statuses

    def get_runway_occupancy_stats(self, passed_time):
        """Вычисляет статистику занятости полос."""
        avg_occupancies = []
        for runway in self.runways:
            avg_occupancies.append(runway.get_avg_occupancy(passed_time))
        return avg_occupancies

    def get_queue_stats(self):
        """Возвращает статистику по полосам."""
        return self.max_landing_queue, self.max_takeoff_queue

    def get_current_queue_length(self):
        """Вычисляет длины текущих очередей на В/П."""
        current_landing_queue, current_takeoff_queue = 0, 0
        for request in self.requests:
            if request.get_request_type() == 'landing':
                current_landing_queue += 1
            else:
                current_takeoff_queue += 1
        return current_landing_queue, current_takeoff_queue

    def update_max_queue_length(self):
        """Обновляет максимальные длины очередей на В/П."""
        current_landing_queue, current_takeoff_queue = (
            self.get_current_queue_length()
        )
        if current_landing_queue > self.max_landing_queue:
            self.max_landing_queue = current_landing_queue
        if current_takeoff_queue > self.max_takeoff_queue:
            self.max_takeoff_queue = current_takeoff_queue

    def update_total_queue_length(self):
        """Обновляет суммарные длины очередей на В/П."""
        current_landing_queue, current_takeoff_queue = (
            self.get_current_queue_length()
        )
        self.total_landing_queue += current_landing_queue
        self.total_takeoff_queue += current_takeoff_queue

    def get_avg_queue_length(self, passed_time_ticks):
        """Вычисляет средние длины очередей на В/П."""
        avg_landing_queue = self.total_landing_queue / passed_time_ticks
        avg_takeoff_queue = self.total_takeoff_queue / passed_time_ticks
        return avg_landing_queue, avg_takeoff_queue

    def get_request_completion_time(self, request):
        """Вычисляет время обслуживания заявки."""
        plane_type = request.get_plane_type()
        request_type = request.get_request_type()
        if request_type == 'takeoff':
            request_completion_time = (
                self.plane_preparation_time.get_plane_types()[plane_type][0]
            )
        else:
            request_completion_time = (
                self.plane_preparation_time.get_plane_types()[plane_type][1]
            )
        return request_completion_time

    def add_to_request_queue(self, requests):
        """Добавляет новые заявки в очередь."""
        self.requests.extend(requests)
        self.new_requests_count = len(requests)

    def get_finished_requests_info(self, start_time):
        """Получает информацию о совершенных рейсах."""
        finished_requests = []
        true_start_time = start_time[0] * 60 + start_time[1]
        plane_types = self.plane_preparation_time.get_plane_types()

        for i in range(len(self.runways)):
            runway_requests = self.runways[i].get_flight_history()
            for request in runway_requests:
                request_plane = request.get_plane_type()
                request_type = request.get_request_type()
                if request_type == 'взлет':
                    time_added = plane_types[request_plane][0]
                else:
                    time_added = plane_types[request_plane][1]
                request_time = request.get_process_time() + time_added
                request_time += true_start_time
                if request_time >= 24 * 60:
                    request_time -= 24 * 60
                elif request_time < 0:
                    request_time = 24 * 60 - request_time
                request_time = (request_time // 60, request_time % 60)
                finished_requests.append((request_time, i, request_type))

        finished_requests.sort(key=lambda flight: flight[0])
        if len(finished_requests):
            partition_index = 0
            for i in range(len(finished_requests)):
                if finished_requests[i][0] >= start_time:
                    partition_index = i
                    break
            partition_part = finished_requests[:partition_index]
            true_sorted_schedule = finished_requests[partition_index:]
            finished_requests = true_sorted_schedule
            finished_requests.extend(partition_part)

        return finished_requests


class Runway:
    """Взлетно-посадочная полоса."""

    def __init__(self):
        # занятость полосы: free/busy
        self.status = 'free'
        # обрабатываемая заявка
        self.current_request = None
        # время выполнения заявки
        self.request_completion_time = 0
        # текущее окно безопасности
        self.safety_time_gap = 0

        # статистика работы полосы
        self.flight_history = []
        self.occupancy_time = 0

    def time_tick(self, time_tick, safety_time_gap):
        """Шаг работы полосы."""
        if self.status == 'busy':
            remaining_time = time_tick - self.request_completion_time
            if remaining_time >= 0:
                # закрываем заявку
                if self.current_request:
                    self.occupancy_time += self.request_completion_time
                    self.current_request.update_status('ok')
                    self.update_flight_history(self.current_request)
                    self.current_request = None
                    self.request_completion_time = 0
                # освобождаем полосу
                if remaining_time >= self.safety_time_gap:
                    self.status = 'free'
                    self.safety_time_gap = 0
                else:
                    self.safety_time_gap -= remaining_time
            else:
                self.request_completion_time -= time_tick
                self.occupancy_time += time_tick

    def process_request(self, request, completion_time, safety_time_gap):
        """Определяет возможность обслуживания заявки."""
        if self.status == 'free':
            self.status = 'busy'
            self.current_request = request
            self.request_completion_time = completion_time
            self.safety_time_gap = safety_time_gap
            return True
        return False

    def get_status(self):
        """Возвращает статус занятости полосы."""
        return self.status

    def get_avg_occupancy(self, passed_time):
        """Вычисляет среднюю занятость полосы."""
        avg_occupancy = self.occupancy_time / passed_time
        return avg_occupancy

    def update_flight_history(self, request):
        """Пополняет список обслуженных полосой заявок."""
        self.flight_history.append(request)

    def get_flight_history(self):
        """Возвращает список обслуженных заявок."""
        return self.flight_history


class Request:
    """Заявка."""

    def __init__(
        self, plane_type, request_type, time_variance, submission_time
    ):
        # входные параметры
        # получены от агрегирующего класса (диспетчера)
        self.plane_type = plane_type
        self.request_type = request_type
        self.time_variance = time_variance
        self.submission_time = submission_time

        # статус заявки: ok/wait
        self.status = 'wait'
        # время ожидания
        self.waiting_time = 0

    def get_request_type(self):
        """Возвращает тип заявки."""
        return self.request_type

    def get_status(self):
        """Возвращает статус заявки."""
        return self.status

    def get_plane_type(self):
        """Возвращает тип самолета."""
        return self.plane_type

    def get_time_delay(self):
        """Подсчитывает величину задержки."""
        return self.time_variance + self.waiting_time

    def get_process_time(self):
        """Возвращает время начала выполнения заявки."""
        return self.submission_time + self.waiting_time

    def update_status(self, new_status):
        """Обновляет статус заявки."""
        self.status = new_status

    def update_waiting_time(self, passed_time):
        """Обновляет время ожидания заявки."""
        if self.status == 'wait':
            self.waiting_time += passed_time


class Schedule:
    """Расписание полетов."""

    def __init__(self):
        self.schedule = []
        # дефолтные настройки расписания полетов
        self.default_settings = [
            ('glider', 'посадка', (6, 35)),
            ('concorde', 'посадка', (7, 0)),
            ('concorde', 'взлет', (7, 0)),
            ('airbus', 'посадка', (7, 5)),
            ('airbus', 'посадка', (7, 20)),
            ('airbus', 'посадка', (7, 22)),
            ('airbus', 'взлет', (7, 27)),
            ('airbus', 'посадка', (8, 0)),
            ('crop duster', 'взлет', (12, 35)),
            ('light jet', 'взлет', (12, 35)),
            ('multi-purpose', 'взлет', (13, 40)),
            ('fighter', 'взлет', (17, 55)),
            ('fighter', 'взлет', (17, 55)),
            ('fighter', 'взлет', (17, 55)),
            ('bomber', 'взлет', (18, 10)),
            ('bomber', 'взлет', (18, 15)),
            ('heavy cargo', 'посадка', (18, 15)),
            ('airbus', 'посадка', (21, 0)),
            ('light cargo', 'взлет', (22, 0)),
            ('airbus', 'посадка', (23, 0)),
            ('light cargo', 'взлет', (0, 0)),
            ('airbus', 'посадка', (1, 0)),
            ('light cargo', 'взлет', (2, 0)),
            ('glider', 'взлет', (4, 0)),
            ('glider', 'взлет', (4, 0)),
            ('glider', 'взлет', (4, 2)),
            ('multi-purpose', 'взлет', (4, 3)),
            ('multi-purpose', 'взлет', (4, 5)),
            ('multi-purpose', 'взлет', (4, 10)),
            ('airbus', 'посадка', (4, 11)),
            ('airbus', 'посадка', (4, 15)),
            ('airbus', 'посадка', (4, 20)),
            ('airbus', 'посадка', (4, 22)),
            ('airbus', 'посадка', (4, 25)),
        ]
        self.default_used = False

    def get_schedule(self):
        """Возвращает существующее расписание полетов."""
        return self.schedule

    def clear_schedule(self):
        """Стирает расписание."""
        self.schedule = []
        self.default_used = False

    def add_flight(self, plane_type, request_type, scheduled_time):
        """Добавляет рейс в расписание."""
        # проверка корректности данных
        try:
            time_struct = time.strptime(scheduled_time, '%H:%M')
        except ValueError:
            return False
        parsed_time = (time_struct.tm_hour, time_struct.tm_min)
        # рейс: (тип самолета, тип заявки, (часы, минуты))
        self.schedule.append((plane_type, request_type, parsed_time))
        return True

    def sort_schedule(self, start_time):
        """Сортирует рейсы по запланированному времени."""
        self.schedule.sort(key=lambda flight: flight[-1])
        if len(self.schedule):
            partition_index = 0
            for i in range(len(self.schedule)):
                if self.schedule[i][-1] >= start_time:
                    partition_index = i
                    break
            partition_part = self.schedule[:partition_index]
            true_sorted_schedule = self.schedule[partition_index:]
            self.schedule = true_sorted_schedule
            self.schedule.extend(partition_part)

    def use_default_settings(self, plane_types):
        """Использует дефолтное, заранее заданное расписание."""
        if plane_types.is_default_used():
            self.schedule = self.default_settings.copy()
            self.default_used = True

    def is_default_used(self):
        """Проверяет, были ли использованы дефолтные настройки."""
        return self.default_used


class PlaneTypes:
    """Типы самолетов."""

    def __init__(self):
        self.types = dict()
        # дефолтные настройки типов самолетов
        self.default_settings = {
            'fighter': (1, 1),
            'light cargo': (4, 3),
            'heavy cargo': (15, 15),
            'multi-purpose': (5, 7),
            'glider': (3, 5),
            'bomber': (10, 9),
            'concorde': (12, 12),
            'crop duster': (4, 6),
            'light jet': (2, 3),
            'airbus': (11, 10),
        }
        self.default_used = False

    def get_plane_types(self):
        """Возвращает существующие в базе типы самолетов."""
        return self.types

    def add_type(self, type_name, takeoff_time, landing_time):
        """Добавляет тип самолета и его временные характеристики."""
        # тип самолета: имя типа -> (время взлета, время посадки)
        if not self.is_existing_type(type_name):
            self.types[type_name] = (takeoff_time, landing_time)
            return True
        return False

    def is_existing_type(self, type_name):
        """Проверяет тип на наличие в базе типов."""
        if type_name in self.types:
            return True
        return False

    def use_default_settings(self):
        """Использует дефолтные, заранее заданные типы самолетов."""
        self.types = self.default_settings.copy()
        self.default_used = True

    def is_default_used(self):
        """Проверяет, были ли использованы дефолтные настройки."""
        return self.default_used
