from collections import deque

class GenerationQueue:
    """Менеджер приоритетных очередей генерации превью."""
    def __init__(self):
        self._high_priority = deque()
        self._low_priority = deque()

    def push(self, preset_name, metadata, high_priority=False):
        """Добавляет задачу в очередь, избегая дубликатов."""
        task = (preset_name, metadata)
        if high_priority:
            if task not in self._high_priority:
                self._high_priority.appendleft(task)  # Важные задачи ставим в начало
        else:
            if task not in self._low_priority and task not in self._high_priority:
                self._low_priority.append(task)

    def pop(self):
        """Забирает задачу с наивысшим приоритетом."""
        if self._high_priority:
            return self._high_priority.popleft()
        if self._low_priority:
            return self._low_priority.popleft()
        return None

    def clear(self):
        """Очищает все задачи."""
        self._high_priority.clear()
        self._low_priority.clear()

    def is_empty(self):
        return not self._high_priority and not self._low_priority