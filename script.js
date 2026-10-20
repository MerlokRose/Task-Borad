const buttons = document.querySelectorAll(".add-btn");
const modalOverlay = document.getElementById("modal-overlay");
const modalInput = document.getElementById("modal-input");
const modalSave = document.getElementById("modal-save");
const modalCancel = document.getElementById("modal-cancel")
const authScreen = document.getElementById("auth-screen");
const mainBoard = document.getElementById("main-board");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const authSubmit = document.getElementById("auth-submit");
const authTitle = document.getElementById("auth-title");
const authToggleText = document.getElementById("auth-toggle-text");
const authToggleLink = document.getElementById("auth-toggle-link");
const authError = document.getElementById("auth-error");
const logoutBtn = document.getElementById("logout-btn");

let isLoginMode = true; // true = вход, false = регистрация
let currentColumn = null;
let draggedTask = null; // Храним задачу которую тащим
const dropIndicator = document.createElement("div");
dropIndicator.classList.add("drop-indicator");

// Создание Задачи
function createTask(text = "") {
    const task = document.createElement("div");
    task.classList.add("task");
    task.draggable = false;

    task.addEventListener("dragstart", function() {
        draggedTask = task;
        setTimeout(() => task.classList.add("dragging"), 0);
    });

    task.addEventListener("dragend", function() {
        task.classList.remove("dragging");
        task.draggable = false;
    });

    const dragHandle = document.createElement("span");
    dragHandle.classList.add("drag-handle");
    dragHandle.textContent = "⠿"

    dragHandle.addEventListener("mousedown", function() {
        task.draggable = true;
    });

    const textSpan = document.createElement("span");
    textSpan.classList.add("task-text");
    textSpan.contentEditable = "true";
    textSpan.textContent = text;

    let originalText = text;
    
    textSpan.addEventListener("blur", function() {
        const newText = textSpan.textContent.trim();
        const taskId = task.dataset.id; // Берем ID задачи
        
        console.log("Пытаюсь сохранить:", newText, "ID", taskId);
        if (newText === originalText) {
            return;
        }

        // Если текст пустой, возвращаем как было (или можно удалять)
        if (!newText) {
            alert("Текст задачи не может быть пустым!");
            textSpan.textContent = originalText;
            return; 
        }

        // Если ID есть (задача уже в базе), отправляем PUT
        if (taskId) {
            fetch(`https://task-borad.onrender.com/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: newText }),
                credentials: 'include'
            })
            .then(() => {
                originalText = newText;
            });
        }
    });

    // ВАЖНО: Запрещаем тексту быть перетаскиваемым, чтобы он выделялся мышкой, а не тащил карточку
    textSpan.draggable = false;

    // Delete
    const deleteBtn = document.createElement("span");
    deleteBtn.textContent = "✕";
    deleteBtn.classList.add("delete-btn");

    // Click=delete all task
    deleteBtn.addEventListener("click", function (event) {
        event.stopPropagation(); // Чтобы клик не воспринимал как клик по задаче

        const taskId = task.dataset.id;
        if (!taskId) {
            task.remove();
            return;
        }
    
        fetch(`https://task-borad.onrender.com/api/tasks/${taskId}`, {
            method: 'DELETE',
            credentials: 'include'
        })
        .then(response => {
            if (response.ok) {
                task.remove();
            }
        });
    
        task.addEventListener("mousedown", function(event) {
            if (event.target !== textSpan) {
                event.preventDefault();
            }
        });
});

task.appendChild(dragHandle);
task.appendChild(textSpan);
task.appendChild(deleteBtn)

    return task;
}

// Кнопки
buttons.forEach(function(button) {
    button.addEventListener("click", function(){
        // 1. Запоминаем колонку, в которой нажали кнопку
        currentColumn = button.closest(".column");
        
        // 2. Открываем окно и очищаем поле
        modalInput.value = ""; 
        modalOverlay.classList.remove("hidden");
        
        // 3. Ставим курсор в поле ввода (с задержкой, чтобы анимация прошла)
        setTimeout(() => modalInput.focus(), 100);
    });
});

// Кнопка "Отмена"
modalCancel.addEventListener("click", function() {
    modalOverlay.classList.add("hidden");
});

// Кнопка "Добавить"
modalSave.addEventListener("click", function() {
    const text = modalInput.value.trim();
    if (!text) return; // Если пусто, ничего не делаем

    // Закрываем окно
    modalOverlay.classList.add("hidden");

    // Определяем статус (какая колонка была выбрана)
    const allColumns = Array.from(document.querySelectorAll(".column"));
    const columnIndex = allColumns.indexOf(currentColumn);
    
    let status = "todo";
    if (columnIndex === 1) status = "done";
    if (columnIndex === 2) status = "future";

    // Отправляем на Python
    fetch("https://task-borad.onrender.com/api/tasks", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: Date.now(), text: text, status: status }),
        credentials: 'include'
    })
    .then(() => loadAll()); // Перезагружаем задачи
});

const columns = document.querySelectorAll(".column");

columns.forEach(function(column) {
    column.addEventListener("dragover", function(event) {
        event.preventDefault();

        const tasks = [...column.querySelectorAll(".task:not(.dragging)")];
        const nextTask = tasks.find(function(task) {
            const rect = task.getBoundingClientRect();
            return event.clientY < rect.top + rect.height / 2;
        });

        const currentNext = draggedTask.nextElementSibling;
        if (nextTask === currentNext || (nextTask === null && currentNext === null)) {
            return;
        }

        const rectsBefore = new Map();
        column.querySelectorAll(".task").forEach(t => {
            if (t !== draggedTask) {
                rectsBefore.set(t, t.getBoundingClientRect().top);
            }
        });

        if (nextTask) {
            column.insertBefore(draggedTask, nextTask);
            column.insertBefore(dropIndicator, nextTask);
        } else {
            column.appendChild(draggedTask);
            column.appendChild(dropIndicator);
        }

        column.querySelectorAll(".task").forEach(t => {
            if (t === draggedTask) return;

            const topAfter = t.getBoundingClientRect().top;
            const topBefore = rectsBefore.get(t);
            const deltaY = topBefore - topAfter;

            if (deltaY !== 0) {
                t.style.transition = 'none';
                t.style.transform = `translateY(${deltaY}px)`;

                requestAnimationFrame(() => {

                    t.style.transition = 'transform 0.2s ease';
                    t.style.transform = '';
                });
            }  
        });
    });

    column.addEventListener("drop", function(event) {
        event.preventDefault();
        if (draggedTask) {
            const taskId = draggedTask.dataset.id;
            const allColumns = Array.from(document.querySelectorAll(".column"));
            const columnIndex = allColumns.indexOf(column);

            let newStatus = "todo";
            if (columnIndex === 1) newStatus = "done";
            if (columnIndex === 2) newStatus = "future";

            if (taskId) {
                fetch(`https://task-borad.onrender.com/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus }),
                    credentials: 'include'
                })
                .then(response => {
                    if (response.ok) {
                        console.log("Статус задачи обнавлен в базе!")
                    }
                });
            }
            draggedTask = null;
        }
         dropIndicator.remove();
    });    
    column.addEventListener("dragleave", function(event){
        if (!column.contains(event.relatedTarget)) {
            dropIndicator.remove();
        }
    });

    columns.forEach(function(column) {
        column.addEventListener("mousedown", function(event) {
        if (!event.target.closest('.task')) {
            event.preventDefault(); 
            if (window.getSelection) {
                window.getSelection().removeAllRanges();
            }
            if (document.activeElement) {
                document.activeElement.blur();
                }
            }
        });
    });
});

// Сохранение
function saveAll() {
    const data = {};

    document.querySelectorAll(".column").forEach(function (column, index) {
        const tasks = [];

        column.querySelectorAll(".task").forEach(function (task) {
            const textSpan = task.querySelector(".task-text");
            if (textSpan) {
                tasks.push(textSpan.textContent);
            }
        });

        data["column" + index] = tasks;
    });
    
    localStorage.setItem("tasks", JSON.stringify(data));
}

// Загрузка
function loadAll() {
    fetch("https://task-borad.onrender.com/api/tasks", {
        credentials: 'include'
    })
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll(".task").forEach(task => task.remove());
            const columns = document.querySelectorAll(".column");
            data.forEach(item => {
                const task = createTask(item.text);

                task.dataset.id = item.id;

                if (item.status === 'todo') {
                    columns[0].appendChild(task);
                } else if (item.status === 'done') {
                    columns[1].appendChild(task);
                } else {
                    columns[2].appendChild(task);
                }
            });
        })
        .catch(error => console.error("Ошибка:", error));
}

// --- ЛОГИКА АВТОРИЗАЦИИ ---

// Переключение между Входом и Регистрацией
authToggleLink.addEventListener("click", function(e) {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    authError.textContent = ""; // Очищаем ошибки

    if (isLoginMode) {
        authTitle.textContent = "Вход в систему";
        authSubmit.textContent = "Войти";
        authToggleText.textContent = "Нет аккаунта?";
        authToggleLink.textContent = "Зарегистрироваться";
    } else {
        authTitle.textContent = "Регистрация";
        authSubmit.textContent = "Создать аккаунт";
        authToggleText.textContent = "Уже есть аккаунт?";
        authToggleLink.textContent = "Войти";
    }
});

// Отправка формы
authSubmit.addEventListener("click", function() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        authError.textContent = "Заполните все поля!";
        return;
    }

    const endpoint = isLoginMode ? "/api/login" : "/api/register";

    fetch(`https://task-borad.onrender.com${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include' // <--- ОЧЕНЬ ВАЖНО! Разрешаем передавать куки (сессии)
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Ошибка");
        }
        return data;
    })
    .then(() => {
        // Если всё ок — проверяем статус и заходим на сайт
        checkAuth();
    })
    .catch(error => {
        authError.textContent = error.message;
    });
});

// Проверка: вошел ли пользователь?
function checkAuth() {
    fetch("https://task-borad.onrender.com/api/me", { credentials: 'include' })
    .then(response => {
        if (response.ok) {
            // Пользователь вошел
            authScreen.style.display = "none";
            mainBoard.style.display = "flex";
            loadAll(); // Загружаем его задачи
        } else {
            // Не вошел
            authScreen.style.display = "flex";
            mainBoard.style.display = "none";
        }
    })
    .catch(() => {
        authScreen.style.display = "flex";
        mainBoard.style.display = "none";
    });
}

// Кнопка Выйти
logoutBtn.addEventListener("click", function() {
    fetch("https://task-borad.onrender.com/api/logout", { 
        method: 'POST',
        credentials: 'include' 
    })
    .then(() => {
        usernameInput.value = "";
        passwordInput.value = "";
        checkAuth(); // Возвращаем на экран входа
    });
});

checkAuth();