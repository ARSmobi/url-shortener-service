let authToken = localStorage.getItem('authToken');

document.addEventListener('DOMContentLoaded', function () {
    if (typeof htmx !== 'undefined') {
        if (!htmx.config.headers) {
            htmx.config.headers = {};
        }

        if (authToken) {
            htmx.config.headers['Authorization'] = 'Bearer ' + authToken;
        } else {
            console.log("Заголовок не установлен, токен отсутствует");
        }

        checkAuthStatus();
    }
});

function checkAuthStatus() {
    if (authToken) {
        const loginSection = document.getElementById('login-section');
        const registerSection = document.getElementById('register-section');
        const appSection = document.getElementById('app-section');

        if (loginSection && appSection && registerSection) {
            loginSection.style.display = 'none';
            registerSection.style.display = 'none';
            appSection.style.display = 'block';
            console.log('Вы успешно авторизованы!');
            loadUserLinks();
        } else {
            console.error('Элементы не найдены');
        }
    } else {
        const loginSection = document.getElementById('login-section');
        const registerSection = document.getElementById('register-section');
        const appSection = document.getElementById('app-section');

        if (loginSection && appSection && registerSection) {
            loginSection.style.display = 'block';
            registerSection.style.display = 'none';
            appSection.style.display = 'none';
            console.log('Вы не авторизованы. Войдите, чтобы получить доступ к ссылкам.');
        } else {
            console.error('Элементы не найдены');
        }
    }
}

// Функция для загрузки ссылок с авторизацией
function loadUserLinks() {
    fetch('/links', {
        headers: {
            'Authorization': 'Bearer ' + authToken
        }
    })
    .then(response => {
        if (response.status === 401) {
            logout();
            throw new Error('Не авторизован');
        }
        return response.json();
    })
    .then(links => {
        displayLinks(links);
    })
    .catch(error => {
        console.error('Ошибка загрузки ссылок:', error);
        document.getElementById('links-list').innerHTML = '<p>Ошибка загрузки ссылок</p>';
    });
}

// Функция для отображения ссылок
function displayLinks(links) {
    const linksContainer = document.getElementById('links-list');
    if (links.length === 0) {
        linksContainer.innerHTML = '<p>У вас пока нет ссылок</p>';
        return;
    }

    linksContainer.innerHTML = links.map(link => `
        <div class="link-item">
            <p><strong>Оригинальная:</strong> ${link.original_url}</p>
            <p><strong>Короткая:</strong> <a href="/r/${link.short_url}" target="_blank">${window.location.origin}/r/${link.short_url}</a><span class="copy"> ⧉</span></p>
            <p><strong>Переходы:</strong> ${link.clicks}</p>
            <p><strong>Создана:</strong> ${new Date(link.created_at).toLocaleDateString()}</p>
            <button onclick="deleteLink(${link.id})" style="color: red;">Удалить</button>
        </div>
    `).join('');
}

// Обработка формы входа через fetch вместо HTMX
document.getElementById('login-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    try {
        const response = await fetch('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(data.username)}&password=${encodeURIComponent(data.password)}`
        });

        if (response.ok) {
            console.log('Проверка что ответ OK');
            const result = await response.json();
            console.log("JSON parsing => ", result); // ← добавлено
            authToken = result.access_token;
            localStorage.setItem('authToken', authToken);
            console.log('authToken => ', authToken);
            htmx.config.headers['Authorization'] = 'Bearer ' + authToken;
            console.log('Authorization header => ' + 'Bearer ' + authToken);

            document.getElementById('auth-result').innerHTML = '<p style="color: green;">Успешный вход!</p>';
            checkAuthStatus();
        } else {
            const errorText = await response.json();
            document.getElementById('auth-result').innerHTML = `<p style="color: red;">${errorText.detail}</p>`;
        }
    } catch (error) {
        document.getElementById('auth-result').innerHTML = '<p style="color: red;">Ошибка сети</p>';
        console.error(error);
    }
});

// Слушание событий клика для кнопки регистрации
function showRegisterForm() {
    if (document.getElementById('register-section').style.display === 'none') {
        document.getElementById('register-section').style.display = 'block';
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('app-section').style.display = 'none';
    } else {
        document.getElementById('register-section').style.display = 'none';
        document.getElementById('login-section').style.display = 'block';
        document.getElementById('app-section').style.display = 'none';
    }
}

// Обработка формы регистрации через fetch
document.getElementById('register-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
        email: formData.get('username'),
        password: formData.get('password')
    };

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })

        if (response.ok) {
            document.getElementById('register-result').innerHTML = '<p style="color: green;">Регистрация успешна!</p>';
            setTimeout(() => {
                showRegisterForm();
                document.getElementById('register-result').innerHTML = '<p style="color: green;"></p>';
            }, 2000);
        } else {
            const errorText = await response.text();
            document.getElementById('register-result').innerHTML = `
                <p style="color: red;">Ошибка регистрации</p>
                <p>${errorText}</p>
            `;
            console.error('Ошибка регистрации:', errorText);
        }

    } catch (error) {
        document.getElementById('register-result').innerHTML = `
            <p style="color: red;">Ошибка сети</p>
            <p>${error.message}</p>
        `;
        console.error('Ошибка сети:', error);
    }
});

// Обработка формы создания ссылки через fetch
document.querySelector('#create-link-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
        original_url: formData.get('original_url')
    };

    try {
        const response = await fetch('/links', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const newLink = await response.json();
            document.getElementById('link-result').innerHTML = `
                <p style="color: green;">Ссылка создана!</p>
                <p>Короткая ссылка: <a href="/r/${newLink.short_url}" target="_blank">${window.location.origin}/r/${newLink.short_url}</a></p>
            `;
            loadUserLinks(); // Обновляем список
        } else if (response.status === 401) {
            logout();
        } else {
            const errorText = await response.json();
            document.getElementById('link-result').innerHTML = `<p style="color: red;">${errorText.detail}</p>`;
        }
    } catch (error) {
        document.getElementById('link-result').innerHTML = '<p style="color: red;">Ошибка сети </p>';
    }
});

function deleteLink(linkId) {
    fetch(`/links/${linkId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': 'Bearer ' + authToken
        }
    })
    .then(response => {
        if (response.ok) {
            loadUserLinks(); // Обновляем список после удаления
        } else if (response.status === 401) {
            logout();
        } else {
            alert('Ошибка удаления ссылки');
        }
    })
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    delete htmx.config.headers['Authorization'];
    checkAuthStatus();
}

// Обработка ошибок для HTMX запросов
document.body.addEventListener('htmx:responseError', function(evt) {
    if (evt.detail.xhr.status === 401) {
        logout();
        alert('Сессия истекла. Войдите снова.');
    }
});
